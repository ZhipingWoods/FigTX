#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""半自动修复 LaTeX 残缺表 → data/latex-fixed/<id>.tex

思路：不改渲染引擎，直接产出「修好的源码」。渲染管线优先读 latex-fixed。

做的事：
  1. 去掉 document 环境（前导由渲染管线提供）
  2. 拍平 float（table*/table/figure）—— preview 环境里浮动体非法
  3. 删 caption / label / centering（拍平后这些在顶层会报怪错）
  4. 迭代编译：从日志抓未定义宏，补 \\providecommand，直到通过
  5. 通过就写入 latex-fixed

用法：
  python3 tools/handfix_tables.py table-213 table-172 ...
  python3 tools/handfix_tables.py --all-broken
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "figlab"))

FIXDIR = os.path.join(ROOT, "data", "latex-fixed")
OUT = os.path.join(ROOT, "public", "renders")
TEXBIN = "tectonic"


def _prep(src: str) -> str:
    """纯行过滤实现：删掉导言类命令行，拍平 float，删 caption。

    不用正则处理反斜杠（踩过太多次转义坑），改用字符串前缀判断。
    """
    BS = chr(92)
    PRE_LINE_PREFIX = (BS + "documentclass", BS + "usepackage", BS + "RequirePackage",
                       BS + "newcommand", BS + "renewcommand", BS + "providecommand",
                       BS + "DeclareMathOperator", BS + "newlength",
                       BS + "newenvironment", BS + "hypersetup", BS + "urlstyle",
                       BS + "frenchspacing", BS + "def", BS + "let",
                       BS + "usepackage", BS + "pdfauthor", BS + "pdfkeywords")
    out = []
    for ln in src.split(chr(10)):
        st = ln.strip()
        # 删 document 环境标记
        if st in (BS + "begin{document}", BS + "end{document}"):
            continue
        # 删 float 环境标记
        if st.startswith((BS + "begin{table", BS + "end{table",
                          BS + "begin{figure", BS + "end{figure")):
            continue
        # 删纯位置参数行 [t] / [htbp]
        if st.startswith("[") and st.endswith("]") and len(st) < 12:
            continue
        # 删导言类命令行
        if st.startswith((BS + "includegraphics", BS + "resizebox")):
            continue
        if st.startswith(PRE_LINE_PREFIX):
            continue
        out.append(ln)
    t = chr(10).join(out)

    # 删 caption（括号配对，逐字符）
    while True:
        i = t.find(BS + "caption")
        if i < 0:
            break
        j = t.find("{", i)
        if j < 0:
            break
        depth, k = 0, j
        while k < len(t):
            if t[k] == "{":
                depth += 1
            elif t[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        t = t[:i] + t[k + 1:]

    # 删 label / centering / 间距命令（简单子串）
    lines2 = []
    for ln in t.split(chr(10)):
        st = ln.strip()
        while (BS + "label{") in ln:
            a = ln.find(BS + "label{")
            b = ln.find("}", a)
            if b < 0:
                break
            ln = ln[:a] + ln[b + 1:]
        ln = ln.replace(BS + "centering", "")
        if st.startswith(BS + "vspace") or st.startswith(BS + "hspace"):
            continue
        lines2.append(ln)
    t = chr(10).join(lines2)
    # px -> pt（Xhline 等）
    t = t.replace("1px", "1pt").replace("0.5px", "0.5pt")
    return t.strip()


def _undefined(log: str) -> list:
    """从日志抓未定义宏。l.NN 行要抓整行所有宏，不只第一个。"""
    names = set()
    for m in re.finditer(r"<argument>([^\n]*)", log):
        hits = re.findall(r"\\([A-Za-z@]{2,40})", m.group(1))
        if hits:
            names.add(hits[-1])
    for m in re.finditer(r"^l\.(\d+)(.)([^\n]*)", log, flags=re.M):
        line_txt = m.group(2) + m.group(3)
        for h in re.findall(r"\\([A-Za-z@]{2,40})", line_txt):
            names.add(h)
    skip = {"begin", "end", "item", "par", "relax", "protect", "csname",
            "endcsname", "newline", "hline", "multicolumn", "multirow",
            "caption", "label", "centering", "toprule", "midrule",
            "bottomrule", "cmidrule", "makecell", "xhline", "rowcolor",
            "cellcolor", "textcolor", "color", "textbf", "textit", "hline"}
    return [n for n in sorted(names)
            if n.lower() not in skip and re.fullmatch(r"[A-Za-z]{2,40}", n)]


def _coltypes(log: str) -> list:
    BS2 = chr(92)
    # 日志报 Illegal pream-token (X) 时，说明列型 X 未定义，动态补上
    out = []
    for m in re.finditer(r"Illegal pream-token \(([A-Za-z])\)", log):
        c = m.group(1)
        out.append(BS2 + "newcolumntype{" + c + "}{>{" + BS2 + "centering" + BS2 + "arraybackslash}p{1.3cm}}")
    return out


def try_fix(tid: str, src: str, verbose=True):
    """迭代编译直到通过，返回 (ok, 修好的源码, 补的宏数)。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "rt", os.path.join(ROOT, "tools", "render_tex.py"))
    rt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rt)

    # 预置常用的引用类宏定义（natbib 等），这些缺失很常见
    CITE_STUBS = [
        "\\providecommand{\\cite}[1]{}",
        "\\providecommand{\\citet}[1]{}",
        "\\providecommand{\\citep}[1]{}",
        "\\providecommand{\\citeyear}[1]{}",
        "\\providecommand{\\citeauthor}[1]{}",
        "\\providecommand{\\citealp}[1]{}",
        "\\providecommand{\\citealt}[1]{}",
        "\\providecommand{\\ref}[1]{}",
    ]
    # 正文里的导言类命令：颜色定义等要提到前面复用，其余删掉
    HOIST_PAT = re.compile(r"\\definecolor\{[^}]*\}\{[^}]*\}\{[^}]*\}")
    hoisted = HOIST_PAT.findall(src)
    body = _prep(src)
    EXTRA_DEFS = [
        # 常见但 xcolor 基础库没有的颜色名
        "\\providecolor{darkgreen}{rgb}{0,0.5,0}",
        "\\providecolor{darkred}{rgb}{0.55,0,0}",
        "\\providecolor{darkblue}{rgb}{0,0,0.55}",
        "\\providecolor{lightblue}{rgb}{0.68,0.85,0.9}",
        "\\providecolor{lightgreen}{rgb}{0.86,1,0.86}",
        "\\providecolor{lightgray}{rgb}{0.83,0.83,0.83}",
        "\\providecolor{mygray}{rgb}{0.92,0.92,0.92}",
        "\\providecolor{myfrozen}{rgb}{0.85,0.9,1}",
        # 常见自定义列型
    ]
    defs: list = hoisted + list(CITE_STUBS) + EXTRA_DEFS
    for rnd in range(10):
        cand = ("\n".join(defs) + "\n" + body) if defs else body
        with tempfile.TemporaryDirectory() as tmp:
            item = {"latex": cand}
            ok, info, _log = rt._compile_raw(item, tmp, TEXBIN, cand, [])
            lgp = os.path.join(tmp, "main.log")
            log = (open(lgp, encoding="utf-8", errors="replace").read()
                   if os.path.exists(lgp) else str(info))
        if ok:
            return True, cand, len(defs)
        _ct = _coltypes(log)
        new = [n for n in _undefined(log)
               if ("\\providecommand{\\" + n + "}") not in "\n".join(defs)]
        if not new and not _ct:
            if verbose:
                i = log.find("! ")
                print("    卡在:", log[i:i + 110].replace("\n", " "))
            return False, cand, len(defs)
        defs += _ct
        defs += ["\\providecommand{\\" + n + "}{}" for n in new[:8]]
    return False, body, len(defs)


def main() -> int:
    os.makedirs(FIXDIR, exist_ok=True)
    items = {i["id"]: i for i in
             json.load(open(os.path.join(ROOT, "data", "raw-items.json"),
                            encoding="utf-8"))}
    args = [a for a in sys.argv[1:]]
    if not args:
        print("用法: handfix_tables.py <id> [<id> ...]")
        return 1
    okn = 0
    for tid in args:
        if tid not in items:
            print(tid, "不存在")
            continue
        src = items[tid]["latex"]
        ok, fixed, ndef = try_fix(tid, src)
        if ok:
            p = os.path.join(FIXDIR, tid + ".tex")
            open(p, "w", encoding="utf-8").write(fixed + "\n")
            print("%-12s 修复成功（补 %d 个宏）-> %s" % (tid, ndef, os.path.basename(p)))
            okn += 1
        else:
            print("%-12s 仍失败" % tid)
    print("成功 %d / %d" % (okn, len(args)))
    return 0 if okn else 2


if __name__ == "__main__":
    raise SystemExit(main())
