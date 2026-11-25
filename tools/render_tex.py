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
\usetikzlibrary{arrows.meta,positioning,calc,fit,backgrounds,shapes.geometric,shadows,mindmap}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{threeparttable}
\usepackage{rotating}
\usepackage{xspace}
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


def compile_once(item: dict, workdir: str, texbin: str, use_graphic_fallback: bool,
                 extra_defs: list[str], nonstop: bool = False) -> tuple[bool, str, str]:
    body = prepare_body(item["latex"], use_graphic_fallback)
    # nonstop 由 preamble 控制（见 PREAMBLE 尾部）
    src = os.path.join(workdir, "main.tex")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(PREAMBLE + "\n".join(extra_defs) + "\n" + body + EPILOGUE)
    proc = subprocess.run(
        [texbin, "main.tex", "--outdir", workdir, "--keep-logs"],
        cwd=workdir, capture_output=True, text=True, timeout=300,
    )
    log = (proc.stderr or "") + (proc.stdout or "")
    pdf = os.path.join(workdir, "main.pdf")
    return os.path.exists(pdf), (pdf if os.path.exists(pdf) else log), log


def compile_with_repair(item: dict, workdir: str, texbin: str):
    extra_defs: list[str] = []
    graphic_fallback = False
    last_log = ""
    for _ in range(10):
        ok, info, log = compile_once(item, workdir, texbin, graphic_fallback, extra_defs)
        if ok:
            return True, info
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
        if "Undefined control sequence" in log:
            found = set(re.findall(r"\\([A-Za-z@]{2,30})", log))
            known = set(re.findall(r"\\([A-Za-z@]{2,30})", "\n".join(extra_defs)))
            new = [n for n in sorted(found - known) if re.fullmatch(r"[A-Za-z]{2,30}", n)]
            if new:
                extra_defs.append(r"\makeatletter")
                extra_defs.extend(r"\providecommand{\%s}{}" % n for n in new[:30])
                extra_defs.append(r"\makeatother")
                continue
        if "Missing $ inserted" in log or "Extra alignment" in log:
            break
        break
    # 最后兜底：nonstopmode 强行出 PDF（错误不中断，通常仍能排出可看的表格）
    ok, info, _log = compile_once(item, workdir, texbin, graphic_fallback, extra_defs, nonstop=True)
    if ok:
        return True, info
    errs = [l for l in last_log.split("\n") if "error:" in l][:2]
    return False, "; ".join(errs)[:300]


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
    for idx, item in enumerate(items, 1):
        base = os.path.join(args.out, item["id"])
        if not args.force and (os.path.exists(base + ".webp") or os.path.exists(base + ".png")):
            cached += 1
            ok += 1
            continue
        with tempfile.TemporaryDirectory() as tmp:
            good, info = compile_with_repair(item, tmp, texbin)
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
            png_to_webp(png, args.width, args.quality)
            ok += 1
        if idx % 10 == 0:
            print("  [%d/%d] ok=%d fail=%d cached=%d" % (idx, len(items), ok, fail, cached), flush=True)

    print("rendered ok=%d fail=%d (cached %d)" % (ok, fail, cached))
    if failures:
        with open(os.path.join(args.out, "_failures.json"), "w", encoding="utf-8") as fh:
            json.dump(failures, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
