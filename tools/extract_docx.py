#!/usr/bin/env python3
"""从 .docx 附件中抽取 LaTeX 源码，生成 data/latex/*.tex 与 data/raw-items.json。

用法:
    python3 tools/extract_docx.py --docx-dir ../xhs-docx/爱芝芝爱科研 \
                                  --notes /tmp/xhs/full_notes.json \
                                  --out .
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import zipfile

# ---------------------------------------------------------------- docx 解析

def docx_paragraphs(path: str) -> list[str]:
    """按段落返回纯文本，保留 LaTeX 的换行语义。"""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    paras = re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)
    out: list[str] = []
    for p in paras:
        # 段落内可能有多个 run，<w:br/> 表示软换行
        p = re.sub(r"<w:br\s*/>", "\n", p)
        p = re.sub(r"<w:tab\s*/>", "\t", p)
        runs = re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, re.S)
        text = "".join(runs)
        text = html.unescape(text)
        # docx 里偶尔残留 CDATA / XML 包裹，直接清掉
        text = text.replace("<![CDATA[", "").replace("]]>", "")
        text = re.sub(r"<[a-zA-Z/!][^>]{0,40}>", "", text)
        out.append(text)
    return out


def trim_install_notes(latex: str) -> str:
    """有些 docx 前半是「怎么安装 xx.bst」的说明，后面才是真正要用的代码。

    这类文件行数极多且包含多个 documentclass，只保留最后一个 documentclass 之后的部分。
    """
    lines = latex.split(chr(10))
    if len(lines) < 600:
        return latex
    marker = chr(92) + 'documentclass'
    start = -1
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith(marker):
            start = i
    if start <= 0:
        return latex
    return chr(10).join(lines[start:])


def clean_latex(paras: list[str]) -> str:
    lines = [ln.rstrip() for ln in "\n".join(paras).split("\n")]
    # 去掉首尾空行
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 特征识别

RE_TABLE = re.compile(r"\\begin\{table\*?\}")
RE_FIGURE = re.compile(r"\\begin\{figure\*?\}|\\begin\{tikzpicture\}|\\includegraphics")
RE_CAPTION = re.compile(r"\\caption\{")
RE_COLOR = re.compile(r"\\definecolor\{([^}]+)\}\{[^}]*\}\{([^}]+)\}")

VENUES = [
    "ACL", "EMNLP", "NAACL", "COLING", "EACL", "AACL",
    "CVPR", "ICCV", "ECCV", "WACV", "AAAI", "IJCAI",
    "NeurIPS", "ICLR", "ICML", "NIPS", "KDD", "SIGIR", "WWW",
    "TPAMI", "TIP", "TMM", "TNNLS", "TCSVT",
    "SIGMOD", "VLDB", "ICDE", "OSDI", "SOSP", "ASPLOS", "ISCA",
    "MICCAI", "ICRA", "IROS", "RSS", "CoRL",
    "CHI", "UIST", "CSCW",
]


def detect_kind(latex: str) -> str:
    has_t = bool(RE_TABLE.search(latex))
    has_f = bool(RE_FIGURE.search(latex))
    if has_t and has_f:
        return "mixed"
    if has_t:
        return "table"
    if has_f:
        return "figure"
    return "snippet"


def detect_caption(latex: str) -> str:
    m = RE_CAPTION.search(latex)
    if not m:
        return ""
    i = m.end()
    depth = 1
    buf = []
    while i < len(latex) and depth > 0:
        ch = latex[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        buf.append(ch)
        i += 1
    cap = "".join(buf)
    cap = re.sub(r"\\[a-zA-Z]+\*?", "", cap)
    cap = cap.replace("{", "").replace("}", "").replace("\\%", "%")
    return re.sub(r"\s+", " ", cap).strip()


def detect_venues(*texts: str) -> list[str]:
    """只认「会议名 + 年份」这种真正指向论文出处的写法。

    小红书正文里的 #CVPR[话题]# 之类是话题标签，不是论文会议，必须先剔除。
    """
    blob = " ".join(t for t in texts if t)
    blob = re.sub(r"#[^#\s]{1,30}\[话题\]#", " ", blob)   # 小红书话题标签
    blob = re.sub(r"#[^\s#]{1,30}", " ", blob)             # 普通 hashtag
    blob = blob.upper()
    found: list[str] = []
    for v in VENUES:
        pat = r"(?<![A-Z])" + re.escape(v) + r"\s*['\u2019]?\s*(20\d{2})(?![0-9])"
        if re.search(pat, blob) and v not in found:
            found.append(v)
    return found


def detect_year(*texts: str) -> int | None:
    blob = " ".join(t for t in texts if t)
    years = [int(y) for y in re.findall(r"\b(20[2-3]\d)\b", blob)]
    return max(years) if years else None


def detect_colors(latex: str) -> list[dict]:
    cols = []
    for name, value in RE_COLOR.findall(latex):
        cols.append({"name": name.strip(), "value": value.strip()})
    return cols


def detect_palette(latex: str) -> list[str]:
    """抽取模板里出现的十六进制色板，用于卡片色条。"""
    hexes = re.findall(r"#?([0-9A-Fa-f]{6})\b", latex)
    seen, out = set(), []
    for h in hexes:
        h = h.upper()
        if h not in seen:
            seen.add(h)
            out.append("#" + h)
        if len(out) >= 6:
            break
    return out


def slug_from_filename(name: str) -> str:
    base = os.path.splitext(os.path.basename(name))[0]
    m = re.search(r"(\d+)", base)
    if base.startswith("table") and m:
        return "table-" + m.group(1)
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def number_from_filename(name: str) -> int | None:
    base = os.path.splitext(os.path.basename(name))[0]
    m = re.fullmatch(r"table(\d+)_tex", base)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- 主流程

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docx-dir", required=True)
    ap.add_argument("--notes", required=True, help="full_notes.json（笔记元数据）")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    notes = json.load(open(args.notes, encoding="utf-8"))
    by_doc_name: dict[str, dict] = {}
    for nid, n in notes.items():
        f = n.get("file")
        if f and f.get("name"):
            by_doc_name[f["name"]] = n

    latex_dir = os.path.join(args.out, "data", "latex")
    os.makedirs(latex_dir, exist_ok=True)

    items = []
    for fn in sorted(os.listdir(args.docx_dir)):
        if not fn.lower().endswith(".docx"):
            continue
        path = os.path.join(args.docx_dir, fn)
        try:
            paras = docx_paragraphs(path)
        except Exception as e:  # noqa: BLE001
            print("  ! skip %s: %s" % (fn, e), file=sys.stderr)
            continue
        latex = trim_install_notes(clean_latex(paras))
        if len(latex.strip()) < 20:
            continue

        item_id = slug_from_filename(fn)
        with open(os.path.join(latex_dir, item_id + ".tex"), "w", encoding="utf-8") as fh:
            fh.write(latex)

        note = by_doc_name.get(fn, {})
        title = note.get("title", "")
        desc = note.get("desc", "")
        kind = detect_kind(latex)
        caption = detect_caption(latex)
        # 只从标题/描述/caption 判断会议，避免 \usepackage{cvpr} 之类的误判
        venues = detect_venues(title, desc, caption)
        year = detect_year(title, desc)

        items.append({
            "id": item_id,
            "file": fn,
            "latexFile": "data/latex/%s.tex" % item_id,
            "latex": latex,
            "kind": kind,
            "caption": caption,
            "number": number_from_filename(fn),
            "venues": venues,
            "year": year,
            "colors": detect_colors(latex),
            "palette": detect_palette(latex),
            "title": title,
            "desc": desc,
            "noteId": note.get("id"),
            "docId": (note.get("file") or {}).get("docId"),
            "images": note.get("images", []),
            "tags": note.get("tags", []),
            "publishedAt": note.get("time"),
            "source": "xiaohongshu/爱芝芝爱科研",
        })

    raw_path = os.path.join(args.out, "data", "raw-items.json")
    with open(raw_path, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)

    kinds: dict[str, int] = {}
    for it in items:
        kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
    print("extracted %d items -> %s" % (len(items), raw_path))
    print("kinds:", kinds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
