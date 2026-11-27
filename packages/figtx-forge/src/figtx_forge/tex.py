"""LaTeX 表格：结构统计（行/列/合并单元格）与 tectonic 编译预览。"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

PREAMBLE = r"""\documentclass[border=6pt]{standalone}
\usepackage{booktabs,multirow,makecell,array,tabularx,graphicx,amsmath,amssymb,pifont}
\usepackage[table]{xcolor}
\begin{document}
"""
_ENV = re.compile(r"\\begin\{(tabularx|tabular\*?|tblr)\}")
_COL_LETTERS = set("lcrpXmbS")


def _braced(s: str, i: int) -> tuple[str, int]:
    """s[i] 应为 '{'，返回 (花括号内文本, 右括号之后的位置)。"""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise ValueError("unbalanced braces")


def _skip_ws(s: str, i: int) -> int:
    while i < len(s) and s[i] in " \t\n":
        i += 1
    return i


def _expand_stars(spec: str) -> str:
    while "*{" in spec:
        k = spec.index("*{")
        n, j = _braced(spec, k + 1)
        inner, j = _braced(spec, _skip_ws(spec, j))
        spec = spec[:k] + inner * int(n) + spec[j:]
    return spec


def _count_cols(spec: str) -> int:
    spec = _expand_stars(spec)
    cols, i = 0, 0
    while i < len(spec):
        ch = spec[i]
        if ch in "@!><" and i + 1 < len(spec) and spec[i + 1] == "{":
            _, i = _braced(spec, i + 1)
            continue
        if ch == "{":
            _, i = _braced(spec, i)
            continue
        if ch in _COL_LETTERS:
            cols += 1
        i += 1
    return cols


def table_shape(tex: str) -> dict:
    m = _ENV.search(tex)
    if not m:
        return {"rows": 0, "cols": 0, "multicolumn": 0, "multirow": 0}
    env = m.group(1)
    i = _skip_ws(tex, m.end())
    if env in ("tabularx", "tabular*"):
        _, i = _braced(tex, i)
        i = _skip_ws(tex, i)
    spec, i = _braced(tex, i)
    if env == "tblr":
        cm = re.search(r"colspec\s*=\s*\{", spec)
        if cm:
            spec, _ = _braced(spec, cm.end() - 1)
    end = tex.find(f"\\end{{{env}}}", i)
    body = tex[i:end if end >= 0 else len(tex)]
    return {"rows": len(re.findall(r"\\\\", body)), "cols": _count_cols(spec),
            "multicolumn": body.count("\\multicolumn"), "multirow": body.count("\\multirow")}


def _strip_float(tex: str) -> str:
    tex = re.sub(r"\\begin\{table\*?\}(\[[^\]]*\])?|\\end\{table\*?\}|\\centering", "", tex)
    for cmd in ("\\caption", "\\label"):
        while cmd + "{" in tex:
            k = tex.index(cmd + "{")
            _, j = _braced(tex, k + len(cmd))
            tex = tex[:k] + tex[j:]
    return tex


def wrap_document(tex: str) -> str:
    if "\\documentclass" in tex:
        return tex
    return PREAMBLE + _strip_float(tex).strip() + "\n\\end{document}\n"


def tectonic_path() -> str | None:
    return shutil.which("tectonic")


def compile_table(tex_path, out_png, dpi: int = 300) -> dict:
    exe = tectonic_path()
    if not exe:
        raise FileNotFoundError("tectonic")
    src = Path(tex_path).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        doc = Path(tmp) / "table.tex"
        doc.write_text(wrap_document(src), encoding="utf-8")
        proc = subprocess.run([exe, "--outdir", tmp, str(doc)], capture_output=True, text=True, timeout=300)
        pdf = Path(tmp) / "table.pdf"
        log_tail = (proc.stdout + proc.stderr)[-2000:]
        if proc.returncode != 0 or not pdf.exists():
            return {"ok": False, "log_tail": log_tail, "png": None}
        import pypdfium2 as pdfium

        page = pdfium.PdfDocument(str(pdf))[0]
        page.render(scale=dpi / 72).to_pil().convert("RGB").save(out_png)
    return {"ok": True, "log_tail": log_tail, "png": str(out_png)}
