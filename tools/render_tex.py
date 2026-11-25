#!/usr/bin/env python3
r"""把 LaTeX 片段编译成 PNG/WebP 预览图（构建期工具）。

依赖：
  * tectonic        编译引擎（必装）  brew install tectonic
  * pdftoppm        转图（推荐）      brew install poppler
    macOS 无 poppler 时自动退回 qlmanage / sips
  * cwebp           体积优化（可选）  brew install webp

用法:
    python3 tools/render_tex.py --items data/items.json --out public/renders
    python3 tools/render_tex.py --only table-276 --force
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import latex_repair as _LR
except Exception:
    _LR = None

PREAMBLE = r"""
\documentclass[10pt]{article}
\usepackage{amsmath,amssymb,amsfonts,bm}
\usepackage{graphicx}
\usepackage[table,x11names,svgnames,usenames,dvipsnames]{xcolor}
\usepackage{colortbl}
\usepackage{booktabs,multirow,array,makecell,tabularx,longtable,float,wrapfig}
\usepackage{adjustbox}
\usepackage{siunitx}
\usepackage{hhline}
\usepackage{bigdelim,bigstrut}
\usepackage{arydshln}
\usepackage{dcolumn}
\usepackage{ltxtable}
\usepackage{tabu}
\usepackage{threeparttablex}
\usepackage{gensymb}
\usepackage{mathtools}
\usepackage{bm}
\usepackage{stmaryrd}
\usepackage{mathrsfs}
\usepackage{dsfont}
\usepackage{bbm}
\usepackage{tikz-cd}
\usepackage{cellspace}
\usepackage{diagbox}
\usepackage{boldline}
\usepackage{nicematrix}
\usepackage{algorithm2e}
\usepackage[noend]{algpseudocode}
\usepackage{cancel}
\usepackage{ulem}
\usepackage{relsize}
\usepackage{ulem}
\usepackage{caption,subcaption}
\usepackage{enumitem}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc,fit,backgrounds,shapes.geometric,shadows,mindmap,decorations.pathreplacing,decorations.shapes,decorations.markings,patterns}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{threeparttable}
\usepackage{rotating}
\usepackage{xspace}
\usepackage{pifont}
\usepackage{soul}
\usepackage{color}
\usepackage{verbatim}
\usepackage{textcomp}
\usepackage{xparse}
\usepackage{tcolorbox}
\tcbuselibrary{skins,breakable}
\usepackage{epigraph}
\usepackage{ulem}
\usepackage{pifont}
\usepackage[active,tightpage]{preview}
\setlength\PreviewBorder{18pt}
\setlength{\parindent}{0pt}
% 纸张足够大 + 版心足够高：长表格不会跨页被截断；
% 但 textwidth 保持论文正常值，让 resizebox{textwidth} 的缩放比例贴近真实论文。
\pdfpagewidth=1600pt
\pdfpageheight=9000pt
\paperwidth=1600pt
\paperheight=9000pt
\textwidth=468pt
\textheight=8800pt
\hoffset=-1in
\voffset=-1in
\topskip=0pt
\pagestyle{empty}
\begin{document}
\begin{preview}
"""

EPILOGUE = r"""
\end{preview}
\end{document}
"""

DROP_LINE = re.compile(r"^\s*\\(documentclass|usepackage|RequirePackage|PassOptionsToPackage)\b")
FLOAT_BEGIN = re.compile(r"\\begin\{(table\*?|figure\*?)\}(?:\s*\[[^\]]*\])?")
FLOAT_END = re.compile(r"\\end\{(table\*?|figure\*?)\}")
NOISE = [
    re.compile(r"\\begin\{document\}"),
    re.compile(r"\\end\{document\}"),
    re.compile(r"\\maketitle"),
    re.compile(r"\\begin\{abstract\}.*?\\end\{abstract\}", re.S),
]
GRAPHICS_FALLBACK = (
    r"\renewcommand{\includegraphics}[2][]{\fbox{\parbox[c][1.2cm][c]{2.2cm}"
    r"{\centering\scriptsize figure}}}"
)


DEF_RE = re.compile(r"^\s*\\(?:re)?newcommand\*?\s*\{?\\([A-Za-z@]+)\}?")


NEWCMD = re.compile(r'\\newcommand\*?')


def soften_newcommands(body: str) -> str:
    """片段里的 newcommand 若与宏包已定义的同名命令冲突会报错；
    换成 providecommand：已存在则沿用，不存在则定义。
    """
    return NEWCMD.sub(lambda _m: '\\providecommand', body)


def dedupe_definitions(body: str) -> str:
    """同一个命令被 \newcommand 定义两次会报 "already defined"，保留第一次。"""
    seen: set[str] = set()
    out: list[str] = []
    for line in body.split("\n"):
        m = DEF_RE.match(line)
        if m:
            name = m.group(1)
            if name in seen:
                continue
            seen.add(name)
        out.append(line)
    return "\n".join(out)


def prepare_body(latex: str, use_graphic_fallback: bool) -> str:
    lines = [ln for ln in latex.split("\n") if not DROP_LINE.match(ln)]
    body = "\n".join(lines)
    # 浮动体在 preview 盒子里会报 "Not in outer par mode"，降级成 center
    body = FLOAT_BEGIN.sub(r"\\begin{center}", body)
    body = FLOAT_END.sub(r"\\end{center}", body)
    # subtable / subfigure 在非浮动环境里会报 "outside float"，降级成 minipage
    body = re.sub(r"\\begin\{(subtable|subfigure)\}(?:\s*\[[^\]]*\])?(\s*\{[^{}]*\})?",
                  lambda m: r"\\begin{minipage}" + (m.group(2) or "{0.45\\linewidth}"), body)
    body = re.sub(r"\\end\{(subtable|subfigure)\}", r"\\end{minipage}", body)
    body = body.replace(r"\caption{", r"\captionof{table}{")
    body = re.sub(r"\\centering\b", "", body)
    for pat in NOISE:
        body = pat.sub("", body)
    body = dedupe_definitions(body)
    body = soften_newcommands(body)
    if use_graphic_fallback:
        body = GRAPHICS_FALLBACK + "\n" + body
    return body



# 期刊模板 sty 拿不到（aaai2026 / neurips_2024 等），它们基本只影响版式，
# 不影响表格能不能排出来 → 换成 article 兼容前导。
_MISSING_STY = (
    r"aaai\d*|neurips\w*|iclr\w*|cvpr\w*|acl\w*|icml\w*|eccv\w*|iccv\w*|nips\w*"
)


_STUB_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paper_stub.sty.txt")


def _install_stubs(raw: str, workdir: str) -> list[str]:
    """给缺失的论文模板 .sty 生成桩文件，让完整文档能按原样编译。

    表格片段来自完整论文，导言区 \\usepackage{aaai2026} 之类我们拿不到。
    与其改写文档（容易破坏结构），不如提供同名桩文件——文档原封不动，
    保真度最高。返回实际生成的列表。
    """
    made = []
    try:
        with open(_STUB_SRC, encoding="utf-8") as fh:
            tpl = fh.read()
    except Exception:
        return made
    for m in re.finditer(r"\\usepackage(?:\[[^\]]*\])?\{([^}]*)\}", raw):
        for name in m.group(1).split(","):
            name = name.strip()
            if not name:
                continue
            p = os.path.join(workdir, name + ".sty")
            if os.path.exists(p):
                continue
            # 只给「论文模板类」生成桩：名字里带会议/期刊特征
            if not re.search(r"(aaai|neurips|nips|iclr|icml|cvpr|iccv|eccv|acl|"
                             r"emnlp|naacl|coling|kdd|wsdm|sigir|tmlr|jmlr|"
                             r"ieee|acm|springer|elsarticle|lipics|usenix)", name, re.I):
                continue
            try:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(tpl.replace("__STUB__", name))
                made.append(name)
            except Exception:
                pass
    if made:
        print("[stub] %s 生成桩文件: %s" % (workdir.split("/")[-1], ", ".join(made)),
              file=sys.stderr)
    return made


def _standalone_doc(raw: str, extra_defs: list[str]) -> str:
    """把自带 documentclass 的完整文档改成可编译的 article。"""
    out = raw
    m = re.search(r"\\documentclass(?:\[[^\]]*\])?\{([^}]*)\}", out)
    if m:
        out = out[:m.start()] + r"\documentclass[10pt]{article}" + out[m.end():]
    # 期刊 sty 不再剥掉——由 _install_stubs 生成同名桩文件满足它，
    # 这样文档结构（\maketitle 之类）保持原样
    pass
    # 这些模板自带的自定义命令去掉，避免未定义报错
    for bad in (r"\def\UrlFont{\rm}", r"\urlstyle{rm}", r"\frenchspacing",
                r"\usepackage{times}", r"\usepackage{helvet}", r"\usepackage{courier}"):
        out = out.replace(bad, "% " + bad)
    # 补文档里用到但没定义的列类型（实测 table-262/236 用了 C{1.4cm} 却没定义）。
    # 注意：ensure_coltypes 是把定义**前置**的，而 \newcolumntype 只能在导言区，
    # 所以先取出增量定义，再插到 \documentclass 之后。
    if _LR is not None:
        try:
            probed = _LR.ensure_coltypes(out)
            if probed != out and probed.endswith(out):
                defs_only = probed[: len(probed) - len(out)]
                _m = re.search(r"\\documentclass(?:\[[^\]]*\])?\{[^}]*\}", out)
                if _m:
                    out = out[:_m.end()] + "\n" + defs_only + out[_m.end():]
                else:
                    out = defs_only + out
        except Exception:
            pass

    # 只注入文档自己没加载的宏包（否则 xcolor 之类会 Option clash）
    _WANT = [p for p in (
        "amsmath and amssymb and amsfonts and bm and graphicx and xcolor and colortbl and "
        "booktabs and multirow and array and makecell and tabularx and longtable and float and "
        "adjustbox and siunitx and hhline and bigdelim and bigstrut and arydshln and dcolumn and "
        "tabu and threeparttable and threeparttablex and nicematrix and pifont and soul and "
        "textcomp and xspace and preview and caption and subcaption and enumitem and rotating and "
        "tikz and pgfplots and ulem and relsize and cancel and mathtools and mathrsfs and dsfont"
    ).split(" and ")]
    _loaded = set()
    for _m in re.finditer(r"\\usepackage(?:\[[^\]]*\])?\{([^}]*)\}", out):
        for _n in _m.group(1).split(","):
            _loaded.add(_n.strip())
    _need = [p for p in _WANT if p not in _loaded]
    inject = (r"\usepackage{" + ",".join(_need) + "}") if _need else "% (no extra packages)"

    inject_unused = (
        r"\usepackage{amsmath,amssymb,amsfonts,bm,graphicx,xcolor,colortbl,"
        r"booktabs,multirow,array,makecell,tabularx,longtable,float,adjustbox,"
        r"siunitx,hhline,bigdelim,bigstrut,arydshln,dcolumn,tabu,"
        r"threeparttable,threeparttablex,nicematrix,pifont,soul,textcomp,xspace,"
        r"preview,caption,subcaption,enumitem,rotating,"
        r"tikz,pgfplots,ulem,relsize,cancel,mathtools,mathrsfs,dsfont}")
    m2 = re.search(r"\\documentclass(?:\[[^\]]*\])?\{[^}]*\}", out)
    if m2:
        # 注意：不要在这注入 extra_defs——那些是给「片段模式」补宏用的，
        # 注入到完整文档里反而会和原文的 \\newcommand/\\relax 冲突
        # （实测 table-172/240 就是这样被自己的补丁搞挂的）。
        out = out[:m2.end()] + "\n" + inject + "\n" + out[m2.end():]
    return out


def compile_once(item: dict, workdir: str, texbin: str, use_graphic_fallback: bool,
                 extra_defs: list[str], nonstop: bool = False,
                 latex: str | None = None) -> tuple[bool, str, str]:
    raw = latex if latex is not None else item["latex"]
    # 自带 \documentclass 的是完整文档，再套一层前导会报「双 documentclass」
    if "\\documentclass" in raw:
        prefix = ""
        _install_stubs(raw, workdir)          # 缺的期刊 .sty 用桩补上
        body = _standalone_doc(raw, extra_defs)
        suffix = ""
    else:
        body = prepare_body(raw, use_graphic_fallback)
        # 片段自带 \begin{document} / \end{document} 要去掉：
        # 前导里已经有一对，再来一次就是双重 document（table-262 就是这么挂的）
        body = body.replace("\\begin{document}", "").replace("\\end{document}", "")
        prefix = PREAMBLE + "\n".join(extra_defs) + "\n"
        # 片段里用到但没定义的列类型（C{1.4cm} 之类）→ \newcolumntype 放导言区
        if _LR is not None:
            try:
                _probed = _LR.ensure_coltypes(body)
                if _probed != body and _probed.endswith(body):
                    prefix = prefix + _probed[: len(_probed) - len(body)] + "\n"
                    body = _probed[len(_probed) - len(body):] if False else body
            except Exception:
                pass
        suffix = EPILOGUE
    src = os.path.join(workdir, "main.tex")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(prefix + body + suffix)
    proc = subprocess.run(
        [texbin, "main.tex", "--outdir", workdir, "--keep-logs"],
        cwd=workdir, capture_output=True, text=True, timeout=300,
    )
    log = (proc.stderr or "") + (proc.stdout or "")
    pdf = os.path.join(workdir, "main.pdf")
    return os.path.exists(pdf), (pdf if os.path.exists(pdf) else log), log


# ---------------------------------------------------------------- 源码级修复
# 这 31 张表的失败原因多是「Overleaf 能跑、但 aaai 模板缺宏/缺包」，
# 靠加前导解决不了，必须改写源码本身。

_COL_TYPES = "CI LS RMBGN DAE TorZ"


def _fix_columntypes(latex: str) -> tuple[str, bool]:
    """未定义的列类型（Illegal pream-token）→ 补 \newcolumntype。

    这类表通常自带 \newcolumntype{C}{...}，但定义被 docx 抽取截掉了。
    补一个「居中 + 可换行」的通用定义即可正常排版。
    """
    used = set()
    # 列格式可能是 lC{1.4cm}C{1.4cm} 这种带参数的，必须用括号配对而不是 [^}]*
    for m in re.finditer(r"\begin\{(?:tabular\*?|tabularx|tabulary|longtable)\}", latex):
        j = m.end()
        # 跳过可选位置参数与宽度参数
        for _ in range(2):
            while j < len(latex) and latex[j] in " \t\n":
                j += 1
            if j < len(latex) and latex[j] == "[":
                e = latex.find("]", j)
                if e < 0:
                    break
                j = e + 1
        while j < len(latex) and latex[j] in " \t\n":
            j += 1
        if j < len(latex) and latex[j] == "{":
            depth, k = 0, j
            while k < len(latex):
                if latex[k] == "{":
                    depth += 1
                elif latex[k] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            spec = latex[j + 1:k]
            # 去掉 {..} 参数，只看列型字母
            spec_flat = re.sub(r"\{[^{}]*\}", "", spec)
            used |= set(re.findall(r"[A-Za-z]", spec_flat))
    # 只处理大写自定义列型（小写是标准 l/c/r/p/m/b/X）
    custom = sorted(c for c in used if c.isupper())
    if not custom:
        return latex, False
    defs = []
    for c in custom:
        if "newcolumntype{%s}" % c in latex:
            continue
        defs.append(r"\newcolumntype{%s}{>{\centering\arraybackslash}p{2.1cm}}" % c)
    if not defs:
        return latex, False
    print("[render] 补列类型定义:", ", ".join(custom))
    return "\n".join(defs) + "\n" + latex, True


def _fix_stray_newline(latex: str) -> tuple[str, bool]:
    """There's no line here to end → 去掉紧邻环境边界的 \\。"""
    out = re.sub(r"\\\s*(\\end\{(?:table|tabular)[^}]*\})", r"\1", latex)
    out = re.sub(r"(\begin\{(?:table|tabular)[^}]*\})\s*\\\s*\n", r"\1\n", out)
    return out, out != latex


def _fix_relax_clash(latex: str) -> tuple[str, bool]:
    """Command \relax already defined → 删掉重定义 \relax 的行。"""
    out = re.sub(r"\\[a-zA-Z]*newcommand\*?\{\\relax\}[^\n]*\n", "", latex)
    return out, out != latex


def _fix_blank_in_newcommand(latex: str) -> tuple[str, bool]:
    """Paragraph ended before \provide@command → 宏定义体内的空行要去掉。"""
    def _strip(m):
        head, body, tail = m.group(1), m.group(2), m.group(3)
        return head + re.sub(r"\n\s*\n", "\n", body) + tail
    out = re.sub(r"(\\(?:providecommand|newcommand)\*?\{[^}]*\}(?:\[[^\]]*\])*\{)"
                 r"(.*?)(\n\})", _strip, latex, flags=re.S)
    return out, out != latex


def _fix_tblr(latex: str) -> tuple[str, bool]:
    """Environment tblr undefined（tabularray 写法）→ 换回 tabular。"""
    if "tblr" not in latex:
        return latex, False
    out = latex.replace("\\begin{tblr}", "\\begin{tabular}")
    out = out.replace("\\end{tblr}", "\\end{tabular}")
    # tblr 的列格式写法 {colspec={...}} 不兼容，退化成等宽
    out = re.sub(r"\\begin\{tabular\}\s*\[[^\]]*\]\s*\{[^}]*colspec[^}]*\}",
                 r"\\begin{tabular}{" + "c" * 12 + "}", out)
    return out, out != latex


def _fix_preamble_leak(latex: str) -> tuple[str, bool]:
    """Can be used only in preamble → 把正文里的 \\newcommand 提到最前。"""
    lines = latex.split("\n")
    moved, keep = [], []
    for ln in lines:
        st = ln.strip()
        if st.startswith(("\\newcommand", "\\providecommand", "\\def\\", "\\usepackage",
                          "\\newcolumntype", "\\definecolor", "\\makeatletter",
                          "\\makeatother")):
            moved.append(ln)
        else:
            keep.append(ln)
    if not moved:
        return latex, False
    return "\n".join(moved) + "\n" + "\n".join(keep), True



def _fix_balance_envs(latex: str) -> tuple[str, bool]:
    """补/删不配平的环境——这 31 张表全是 docx 抽取的残缺片段。

    实测 table-262 有 4 个 \begin{tabular} 但只有 3 个 \end{tabular}，
    table-75 有 2 个 \begin{table} 但只有 1 个 \end{table}。
    少补多删，按嵌套顺序补齐。
    """
    envs = ["table*", "table", "tabular*", "tabularx", "tabular", "tabularray",
            "threeparttable", "center", "minipage"]
    out = latex
    changed = False
    for env in envs:
        b = len(re.findall(r"\\begin\{%s\}" % re.escape(env), out))
        e = len(re.findall(r"\\end\{%s\}" % re.escape(env), out))
        if b == e:
            continue
        if b > e:
            out += ("\n" if not out.endswith("\n") else "") +                    ("\\end{%s}\n" % env) * (b - e)
        else:
            for _ in range(e - b):
                i = out.find("\\end{%s}" % env)
                if i < 0:
                    break
                out = out[:i] + out[i + len("\\end{%s}" % env):]
        changed = True
    return out, changed


def _fix_orphan_newcommand(latex: str) -> tuple[str, bool]:
    """把残缺的 \\newcommand 行整段删掉（定义被截断会连锁报错）。"""
    bad = []
    for m in re.finditer(r"\\(?:newcommand|providecommand|renewcommand)\*?\{\\[A-Za-z@]+\}"
                         r"(?:\[[^\]]*\])*\{(?:[^{}]|\{[^{}]*\})*\n", latex):
        bad.append(m.group(0))
    if not bad:
        return latex, False
    out = latex
    for b in bad:
        out = out.replace(b, "")
    return out, out != latex



def _fix_nested_tabular(latex: str) -> tuple[str, bool]:
    """tabular 套 tabular 是非法的（docx 抽取常见的结构错）→ 内层降级为普通内容。"""
    out = latex
    changed = False
    for _ in range(6):
        # 找到 内层 \begin{tabular}{...} ... \begin{tabular}  的相邻嵌套
        m = re.search(r"(\\begin\{tabular\*?\}(?:\[[^\]]*\])?(?:\{[^}]*\})?\{[^}]*\})"
                      r"((?:(?!\\begin\{tabular).)*?)"
                      r"(\\begin\{tabular\*?\}(?:\[[^\]]*\])?(?:\{[^}]*\})?\{[^}]*\})",
                      out, flags=re.S)
        if not m:
            break
        # 内层的 begin 去掉列格式，改成纯环境
        out = out[:m.start(3)] + "\\begin{tabular}" + out[m.end(3):]
        changed = True
    return out, changed


def _fix_enddoc_early(latex: str) -> tuple[str, bool]:
    """\\end{document} 之后还有内容 → 把尾部内容挪到 (document) 里面。"""
    i = latex.rfind("\\end{document}")
    if i < 0:
        return latex, False
    tail = latex[i + len("\\end{document}"):].strip()
    if not tail:
        return latex, False
    head = latex[:i]
    return head + tail + "\n\\end{document}\n", True


_SRC_FIXES = [_fix_enddoc_early, _fix_nested_tabular, _fix_balance_envs,
              _fix_orphan_newcommand, _fix_tblr,
              _fix_relax_clash, _fix_blank_in_newcommand, _fix_stray_newline,
              _fix_preamble_leak, _fix_columntypes]


_repaired: list[dict] = []


def compile_with_repair(item: dict, workdir: str, texbin: str):
    extra_defs: list[str] = []
    graphic_fallback = False
    last_log = ""
    cur_latex = item["latex"]
    tried = set()
    for _ in range(14):
        ok, info, log = compile_once(item, workdir, texbin, graphic_fallback,
                                     extra_defs, latex=cur_latex)
        if ok:
            return True, info, "direct"
        last_log = log
        if "Unable to load picture or PDF file" in log and not graphic_fallback:
            graphic_fallback = True
            continue
        # 重复定义交给 LaTeX 自己报，不再注入 \let（会引入新错误）
        mcolor = re.search(r"Undefined color `([A-Za-z0-9]+)'", log)
        if mcolor:
            name = mcolor.group(1)
            known_c = set(re.findall(r"\\definecolor\{([^}]+)\}", "\n".join(extra_defs)))
            if name not in known_c:
                extra_defs.append(r"\definecolor{%s}{gray}{0.55}" % name)
                continue
        _is_doc = "\\documentclass" in cur_latex
        if "Undefined control sequence" in log and not _is_doc:
            # 完整文档自带宏定义，硬注入 providecommand 会和原文冲突
            found = set(re.findall(r"\\([A-Za-z@]{2,30})", log))
            known = set(re.findall(r"\\([A-Za-z@]{2,30})", "\n".join(extra_defs)))
            new = [n for n in sorted(found - known) if re.fullmatch(r"[A-Za-z]{2,30}", n)]
            if new:
                extra_defs.append(r"\makeatletter")
                extra_defs.extend(r"\providecommand{\%s}{}" % n for n in new[:30])
                extra_defs.append(r"\makeatother")
                continue
        # 源码级修复：按错误类型逐个尝试，每种只试一次
        for fix in _SRC_FIXES:
            if fix.__name__ in tried:
                continue
            new_latex, changed = fix(cur_latex)
            if changed:
                tried.add(fix.__name__)
                cur_latex = new_latex

                break
        else:

            break
        continue
    # 最后兜底：nonstopmode 强行出 PDF（错误不中断，通常仍能排出可看的表格）
    ok, info, _log = compile_once(item, workdir, texbin, graphic_fallback, extra_defs,
                                  nonstop=True, latex=cur_latex)
    if ok:
        return True, info, "nonstop"

    # 三级降级：剥离自定义宏 → 只留 tabular → 纯文本单元格
    if _LR is not None:
        _stages = _LR.salvage(item["latex"])
        # 完整文档优先走「桩 + 保结构」（table-with-defs 已在 staged 最前）；
        # plain-cells 是保底，不该抢在保结构之前。
        for stage, src in _stages:
            # 先修列类型（salvage 出来的 tabular 常带 C{1.4cm} / I 这类自定义列型）
            fixed, _ = _fix_columntypes(src)
            for cand in (fixed, src):
                # 关键：这里必须用**空**的 extra_defs。
                # 前面循环累积的补丁（providecommand 等）会和原文冲突，
                # 实测带着它们连「已剥成纯文本」的 tabular 都编不过。
                ok, info, log = compile_once(item, workdir, texbin, False,
                                             [], nonstop=True, latex=cand)
                if ok:
                    print("[salvage] %s 用 %s 渲染成功" % (item.get("id"), stage),
                          file=sys.stderr)
                    _repaired.append({"id": item["id"], "stage": stage})
                    return True, info, stage

    errs = [l for l in last_log.split("\n") if "error:" in l][:2]
    return False, "; ".join(errs)[:300], ""


def pdf_to_png(pdf_path: str, out_png: str) -> bool:
    stem = out_png[:-4]
    if shutil.which("pdftoppm"):
        try:
            subprocess.run(["pdftoppm", "-png", "-r", "300", "-f", "1", "-l", "1",
                            "-singlefile", pdf_path, stem],
                           capture_output=True, timeout=180, check=True)
            if os.path.exists(out_png):
                return True
        except Exception:
            pass
    if shutil.which("qlmanage"):
        tmpdir = os.path.dirname(out_png)
        try:
            subprocess.run(["qlmanage", "-t", "-s", "3000", "-o", tmpdir, pdf_path],
                           capture_output=True, timeout=180, check=True)
            produced = os.path.join(tmpdir, os.path.basename(pdf_path) + ".png")
            if os.path.exists(produced):
                os.replace(produced, out_png)
                return True
        except Exception:
            pass
    if shutil.which("sips"):
        try:
            subprocess.run(["sips", "-s", "format", "png", pdf_path, "--out", out_png],
                           capture_output=True, timeout=180, check=True)
            if os.path.exists(out_png):
                return True
        except Exception:
            pass
    for tool in ("magick", "convert"):
        if shutil.which(tool):
            try:
                subprocess.run([tool, "-density", "200", pdf_path + "[0]", out_png],
                               capture_output=True, timeout=180, check=True)
                if os.path.exists(out_png):
                    return True
            except Exception:
                continue
    return False


def png_to_webp(png: str, max_width: int, quality: int) -> str:
    if not shutil.which("cwebp"):
        return png
    webp = png[:-4] + ".webp"
    try:
        subprocess.run(["cwebp", "-quiet", "-q", str(quality), "-m", "6",
                        "-resize", str(max_width), "0", png, "-o", webp],
                       capture_output=True, timeout=120, check=True)
        if os.path.exists(webp) and os.path.getsize(webp) > 0:
            os.remove(png)
            return webp
    except Exception:
        pass
    return png


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default="data/items.json")
    ap.add_argument("--out", default="public/renders")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--width", type=int, default=1300)
    ap.add_argument("--quality", type=int, default=82)
    args = ap.parse_args()

    texbin = shutil.which("tectonic")
    if not texbin:
        print("tectonic 未安装：brew install tectonic", file=sys.stderr)
        return 2

    items = json.load(open(args.items, encoding="utf-8"))
    if args.only:
        want = set(args.only.split(","))
        items = [i for i in items if i["id"] in want]
    if args.limit:
        items = items[: args.limit]

    os.makedirs(args.out, exist_ok=True)
    ok = fail = cached = 0
    failures = []
    global _repaired
    _repaired = []
    for idx, item in enumerate(items, 1):
        base = os.path.join(args.out, item["id"])
        if not args.force and (os.path.exists(base + ".webp") or os.path.exists(base + ".png")):
            cached += 1
            ok += 1
            continue
        with tempfile.TemporaryDirectory() as tmp:
            good, info, stage = compile_with_repair(item, tmp, texbin)
            if not good:
                fail += 1
                failures.append({"id": item["id"], "error": info})
                print("  ! %s: %s" % (item["id"], str(info)[:150]), file=sys.stderr)
                continue
            png = os.path.join(args.out, item["id"] + ".png")
            if not pdf_to_png(info, png):
                fail += 1
                failures.append({"id": item["id"], "error": "pdf->png failed"})
                continue
            # 宽表按列数加宽：12 列的表挤在 1300px 里每列只有 ~100px，
            # 显示时看不清。按列数线性加宽，最多 3000px。
            try:
                from PIL import Image as _Im
                _w, _h = _Im.open(png).size
                _ncol = max(1, int(round(_w / max(1, _h) * 3)))  # 粗估不了列数，改用宽高比
            except Exception:
                _ncol = 1
            _target = args.width
            # 用「渲染出来的表格本身很扁」作为宽表信号
            try:
                from PIL import Image as _Im2
                _w2, _h2 = _Im2.open(png).size
                if _h2 > 0 and _w2 / _h2 > 2.0:      # 很扁 → 列多
                    _target = min(3000, int(args.width * min(2.3, _w2 / _h2)))
            except Exception:
                pass
            png_to_webp(png, _target, args.quality)
            ok += 1
        if idx % 10 == 0:
            print("  [%d/%d] ok=%d fail=%d cached=%d" % (idx, len(items), ok, fail, cached), flush=True)

    print("rendered ok=%d fail=%d (cached %d)" % (ok, fail, cached))
    try:
        with open(os.path.join(args.out, "_repaired.json"), "w", encoding="utf-8") as fh:
            json.dump(_repaired, fh, ensure_ascii=False, indent=1)
        print("自动修复渲染: %d 张（已写入 _repaired.json）" % len(_repaired))
    except Exception:
        pass
    if failures:
        with open(os.path.join(args.out, "_failures.json"), "w", encoding="utf-8") as fh:
            json.dump(failures, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
