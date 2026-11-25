#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LaTeX 片段修复引擎。

背景：库里 216 张表的源码来自原作者 docx，是**论文片段**不是完整文档。
很多片段依赖完整论文的导言区（tcolorbox / tikz decorations / 自定义高亮宏），
直接塞进通用前导会编译失败。

三级降级策略（逐级尝试，前一级成功就用）：
  1. 原样编译（前导已很全）
  2. 剥离自定义宏 + 导言噪声，把 \\hlcell{foo} 这类包装器内联成 foo
  3. 只抽 tabular 内容，套最简环境渲染（丢掉外围的 table*/caption/colorbox）

目标不是「看起来一样」，而是**把表格本体排出来**——用户要的是能用的表。
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------- 噪声清理

_NOISE_ENVS = [
    "tikzset", "hypersetup", "epigraph", "DottedTextBox",
]

_NOISE_CMDS = [
    "setlength", "addtolength", "newtcolorbox", "tcbset", "tikzset",
    "pgfplotsset", "captionsetup", "sisetup", "setlist", "geometry",
    "hypersetup", "epigraphwidth", "epigraphrule", "vspace", "hspace",
    "usepackage", "RequirePackage", "definecolor", "DeclareMathOperator",
]


def strip_comments(tex: str) -> str:
    out = []
    for ln in tex.split("\n"):
        # 去掉未转义的 % 到行尾
        i = 0
        cut = -1
        while i < len(ln):
            if ln[i] == "\\" and i + 1 < len(ln) and ln[i + 1] == "%":
                i += 2
                continue
            if ln[i] == "%":
                cut = i
                break
            i += 1
        out.append(ln[:cut] if cut >= 0 else ln)
    return "\n".join(out)


def _match_braces(s: str, i: int) -> int:
    """从 s[i]=='{' 开始，返回配对 '}' 的下标（找不到返回 -1）。"""
    if i >= len(s) or s[i] != "{":
        return -1
    depth = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == "\\" and j + 1 < len(s):
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return -1


def collect_macros(tex: str) -> tuple[str, dict[str, int]]:
    """删掉 \\newcommand / \\NewDocumentCommand 定义，返回 (新文本, 宏名->参数个数)。"""
    macros: dict[str, int] = {}
    out = tex
    pat = re.compile(
        r"\\(?:(?:re|provide)?newcommand|NewDocumentCommand|DeclareRobustCommand)\*?"
        r"\s*\{?\s*\\?([A-Za-z@]+)\s*\}?"
        r"(?:\s*\[(\d)\])?"
        r"\s*\{")
    changed = True
    while changed:
        changed = False
        for m in pat.finditer(out):
            name = m.group(1)
            nargs = int(m.group(2) or 0)
            # 找参数定义体的起止
            brace_at = out.index("{", m.end() - 1)
            end = _match_braces(out, brace_at)
            if end < 0:
                continue
            macros.setdefault(name, nargs)
            out = out[:m.start()] + out[end + 1:]
            changed = True
            break
    return out, macros


def inline_macros(tex: str, macros: dict[str, int], rounds: int = 3) -> str:
    """把自定义宏的调用替换成它包着的参数（高亮包装器剥离后内容仍然在）。"""
    for _ in range(rounds):
        before = tex
        for name, nargs in macros.items():
            pat = re.compile(r"\\" + re.escape(name) + r"(?![A-Za-z@])")
            pos = 0
            parts = []
            while True:
                m = pat.search(tex, pos)
                if not m:
                    parts.append(tex[pos:])
                    break
                parts.append(tex[pos:m.start()])
                j = m.end()
                args = []
                ok = True
                for _k in range(nargs):
                    while j < len(tex) and tex[j] in " \t\n":
                        j += 1
                    if j < len(tex) and tex[j] == "[":
                        e = tex.find("]", j)
                        if e < 0:
                            ok = False
                            break
                        j = e + 1
                        while j < len(tex) and tex[j] in " \t\n":
                            j += 1
                    if j < len(tex) and tex[j] == "{":
                        e = _match_braces(tex, j)
                        if e < 0:
                            ok = False
                            break
                        args.append(tex[j + 1:e])
                        j = e + 1
                    else:
                        ok = False
                        break
                if ok:
                    parts.append("".join(args))
                    pos = j
                else:
                    parts.append(m.group(0))
                    pos = m.end()
            tex = "".join(parts)
        if tex == before:
            break
    return tex


def strip_noise(tex: str) -> str:
    """删掉 \\setlength{..}{..}、\\tikzset{..}、\\newtcolorbox{..}{..} 这类。"""
    out = tex
    for cmd in _NOISE_CMDS:
        pat = re.compile(r"\\" + cmd + r"\*?")
        guard = 0
        while guard < 200:
            guard += 1
            m = pat.search(out)
            if not m:
                break
            j = m.end()
            skip = 0
            while j < len(out) and skip < 3:
                while j < len(out) and out[j] in " \t\n":
                    j += 1
                if j < len(out) and out[j] == "{":
                    e = _match_braces(out, j)
                    if e < 0:
                        break
                    j = e + 1
                    skip += 1
                elif j < len(out) and out[j] == "[":
                    e = out.find("]", j)
                    if e < 0:
                        break
                    j = e + 1
                else:
                    break
            out = out[:m.start()] + out[j:]
    return out


def strip_outer_tables(tex: str) -> str:
    """去掉 table / table* / figure 外壳，只留内部（caption 等一并丢）。"""
    out = tex
    for _ in range(6):
        m = re.search(r"\\begin\{(table\*?|figure\*?)\}", out)
        if not m:
            break
        env = m.group(1)
        e = out.find("\\end{%s}" % env, m.end())
        if e < 0:
            out = out[:m.start()]
            break
        out = out[:m.start()] + out[m.end():e] + out[e + len("\\end{%s}" % env):]
    # 删 caption
    out = re.sub(r"\\caption\*?\s*\{", lambda m: "\\caption{", out)
    return out


def balance_envs(tex: str) -> str:
    """补齐/删掉不配平的环境，按出现顺序栈式处理。"""
    envs = ["table*", "table", "tabular*", "tabularx", "tabular", "threeparttable",
            "minipage", "center", "adjustbox", "threeparttable*"]
    out = tex
    for env in envs:
        while True:
            b = len(re.findall(r"\\begin\{%s\}" % re.escape(env), out))
            e = len(re.findall(r"\\end\{%s\}" % re.escape(env), out))
            if b == e:
                break
            if b > e:
                out += "\\end{%s}\n" % env
            else:
                i = out.find("\\end{%s}" % env)
                if i < 0:
                    break
                out = out[:i] + out[i + len("\\end{%s}" % env):]
    return out


def extract_tabular_only(tex: str) -> str | None:
    """只取第一个 tabular 环境（最简可渲染单元）。"""
    m = re.search(r"\\begin\{(tabular\*?|tabularx)\}", tex)
    if not m:
        return None
    env = m.group(1)
    e = tex.find("\\end{%s}" % env, m.end())
    if e < 0:
        return None
    return tex[m.start(): e + len("\\end{%s}" % env)]



# ---------------------------------------------------------------- 深度抢救

_MATH_OK = set("_^&%#")


def sanitize_text(tex: str) -> str:
    """修正文里的特殊字符与空参数。

    典型错误：Missing number（\\vspace{} 空参）、Illegal unit of measure
    （\\resizebox{}{} 缺宽度）、Missing $ inserted（正文里裸 _ 或 ^）。
    """
    out = tex
    # 空参数的 vspace/hspace/setlength → 删掉
    out = re.sub(r"\\(?:vspace|hspace)\*?\{\s*\}", "", out)
    out = re.sub(r"\\(?:vspace|hspace)\*?\{[^}]*\}", "", out)
    out = re.sub(r"\\setlength\s*\{[^}]*\}\s*\{\s*\}", "", out)
    # resizebox/scalebox 缺参数 → 去掉包装
    out = re.sub(r"\\resizebox\s*\{[^}]*\}\s*\{[^}]*\}\s*\{", "{", out)
    # tabular 之外裸 _ ^ 加转义（tabular 内单元格默认也是文本模式，同样要转义）
    lines = out.split("\n")
    fixed = []
    for ln in lines:
        if ln.lstrip().startswith("%"):
            fixed.append(ln)
            continue
        # 只处理不在数学模式里的 _ 和 ^
        res, in_math = [], 0
        i = 0
        while i < len(ln):
            c = ln[i]
            if c == "\\" and i + 1 < len(ln):
                res.append(ln[i:i + 2]); i += 2; continue
            if c == "$":
                in_math = 1 - in_math
                res.append(c); i += 1; continue
            if not in_math and c in "_^" and (i == 0 or ln[i - 1] != "\\"):
                res.append("\\" + c); i += 1; continue
            res.append(c); i += 1
        fixed.append("".join(res))
    return "\n".join(fixed)


def plain_cells(tex: str) -> str | None:
    """核弹级：把 tabular 的单元格内容剥成纯文本，重建一个干净的表格。

    任何表格只要能读出「几行几列、每格写什么」，就能排出来。
    """
    # 支持 tabular / tabular* / tabularx / tabu / longtable
    m = re.search(r"\\begin\{(tabular\*?|tabularx|tabu|longtable)\}", tex)
    if not m:
        return None
    _env = m.group(1)
    # 取列格式
    j = m.end()
    while j < len(tex) and tex[j] in " \t\n":
        j += 1
    ncol = 4
    # tabularx 形如 egin{tabularx}{	extwidth}{XXX} —— 先跳过宽度参数
    if _env == "tabularx" and j < len(tex) and tex[j] == "{":
        k0 = _match_braces(tex, j)
        if k0 > j:
            j = k0 + 1
            while j < len(tex) and tex[j] in " \t\n":
                j += 1
    if j < len(tex) and tex[j] == "{":
        k = _match_braces(tex, j)
        if k > j:
            spec = tex[j + 1:k]
            # 去掉 {1.4cm} 这类参数，只数列型字母
            spec_flat = re.sub(r"\{[^{}]*\}", "", spec)
            n = len(re.findall(r"[lcrXpmbSwW]", spec_flat))
            ncol = max(1, n)
            j = k + 1
    e = tex.find("\\end{%s}" % _env, j)
    body = tex[j:] if e < 0 else tex[j:e]

    def clean(cell: str) -> str:
        t = cell
        t = re.sub(r"\\(?:multicolumn|multirow)\s*\{[^}]*\}\s*\{[^}]*\}", "", t)
        t = re.sub(r"\\[a-zA-Z@]+\*?(?:\[[^\]]*\])?", "", t)   # 去所有命令
        t = t.replace("{", "").replace("}", "")
        t = t.replace("&", " ")
        t = t.replace("%", "")          # % 是 LaTeX 注释，留着会把后文全吃掉
        # 注意：不要剥 $ —— $..$ 里是真正的数值内容，剥了会丢整列数字
        t = re.sub(r"\b\w*?(\w)\1{5,}\w*\b", "", t)   # 抽噪声：awwwww / wwwww
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) > 26:
            t = t[:25] + "…"
        return t

    rows = []
    for raw in re.split(r"\\\\", body):
        raw = raw.split("\\midrule")[0].split("\\hline")[0]
        raw = raw.split("\\toprule")[0].split("\\bottomrule")[0]
        if "\\cmidrule" in raw:
            raw = re.sub(r"\\cmidrule(?:\([^)]*\))?\{[^}]*\}", "", raw)
        cells = [clean(c) for c in raw.split("&")]
        if not any(cells):
            continue
        rows.append(cells[:ncol])
        if len(rows) >= 26:
            break
    if not rows:
        return None
    # 列格式残渣清理：首行若「第 1 格像列格式、其余全空」，说明是 spec 泄漏，丢掉
    def _spec_like(v: str) -> bool:
        v2 = v.replace("…", "").replace(".", "", 0)
        v2 = re.sub(r"[\s|…]", "", v2)
        if not v2:
            return False
        return bool(re.fullmatch(r"(?:[lcrXpmbSwW]|[CI](?:\d+(?:\.\d+)?cm)?"
                                 r"|@\{[^}]*\}|>[{][^}]*[}]|gray!?\d*"
                                 r"|\d+[-\d.]*)+", v2))
    while rows and rows[0]:
        rest_empty = all(not c.strip() for c in rows[0][1:])
        first = rows[0][0]
        # 只有「首格是纯列格式残渣 + 其余全空」才算泄漏行；
        # 首格有真实文字（如方法名）时保留——早期版本这里丢过整列标签。
        if rest_empty and _spec_like(first) and not re.search(r"[A-Za-z]{3,}", re.sub(r"[|<>{}@\d.]", "", first)):
            rows.pop(0)
            continue
        break
    # 每格再清一遍颜色/线宽残渣
    for r in rows:
        for idx, c in enumerate(r):
            r[idx] = re.sub(r"\d+(?:\.\d+)?-\d+(?:\.\d+)?\s*", "", c)
            r[idx] = re.sub(r"^(?:gray|black|white|red|blue|green)!?\d*\s*", "", r[idx]).strip()
    if not rows:
        return None
    colspec = "|".join(["l"] * ncol)
    # 最终转义：任何残留的特殊字符都不能破坏 LaTeX
    def _esc(v: str) -> str:
        v = v.replace("\\", "")
        for ch, rep in (("&", r"\&"), ("%", r"\%"), ("#", r"\#"),
                        ("$", r"\$"), ("_", r"\_"), ("^", r"\^{}"),
                        ("{", ""), ("}", ""), ("~", r"\ ")):
            v = v.replace(ch, rep)
        return v.strip()

    out = ["\\begin{tabular}{" + colspec + "}", "\\hline"]
    for r in rows:
        while len(r) < ncol:
            r.append("")
        out.append(" & ".join(_esc(c) for c in r) + " \\\\")
        out.append("\\hline")
    out.append("\\end{tabular}")
    return "\n".join(out)


def salvage(tex: str) -> list[tuple[str, str]]:
    """返回 [(策略名, 修复后源码)]，按「保真度」从高到低排列。"""
    stages: list[tuple[str, str]] = []
    cur = strip_comments(tex)

    s2 = cur
    s2, macros = collect_macros(s2)
    s2 = inline_macros(s2, macros)
    s2 = strip_noise(s2)
    s2 = strip_outer_tables(s2)
    s2 = balance_envs(s2)
    if s2.strip() != cur.strip():
        stages.append(("strip-macros", s2))

    s3 = sanitize_text(s2)
    if s3.strip() != s2.strip():
        stages.append(("sanitize", balance_envs(s3)))

    tab = extract_tabular_only(s2) or extract_tabular_only(cur)
    if tab:
        stages.append(("tabular-only", balance_envs(tab.strip())))
        pc = plain_cells(tab)
        if pc:
            stages.append(("plain-cells", pc))
    pc2 = plain_cells(cur)
    if pc2:
        stages.append(("plain-cells-doc", pc2))
    return stages
