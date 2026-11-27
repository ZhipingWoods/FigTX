"""PaperGallery 适配器：拉取 web 分支（稀疏检出），只取 frontmatter 里的事实性元数据和图片。

md 正文（作者写的摘要）一律丢弃；PaperGallery 的网站代码不复制。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image

from .common import ROOT, canon_venue, dump_json

UPSTREAM = "https://github.com/LongHZ140516/PaperGallery"
REPO = UPSTREAM
KINDS = ("pipeline", "header")
FIELDS = ("title", "authors", "year", "conference", "tags", "image", "paper", "code", "project", "bibtex")
_LINE = re.compile(r'^(\w+):\s*(.*?)\s*$')


class FetchError(RuntimeError):
    pass


def _git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True, text=True, timeout=1800)


def fetch(cache_dir: Path, local: Path | None = None) -> Path:
    if local:
        if not Path(local).is_dir():
            raise FetchError(f"本地上游路径不存在：{local}")
        return Path(local)
    dest = Path(cache_dir) / "papergallery"
    try:
        if (dest / ".git").exists():
            _git("-C", str(dest), "pull", "--ff-only", "-q")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            _git("clone", "--depth", "1", "--branch", "web", "--filter=blob:none", "--sparse", "-q", UPSTREAM, str(dest))
            _git("-C", str(dest), "sparse-checkout", "set", "src/content/images", "public/images")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        raise FetchError(f"PaperGallery 拉取失败：{e}") from e
    return dest


def _split(text: str) -> str | None:
    m = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.S)
    return m.group(1) if m else None


def _fallback(head: str) -> dict:
    """YAML 写坏时的逐行解析：只取单行的 key: "value" 和 key: ["a", "b"]；bibtex 不可靠，丢弃。"""
    out = {}
    for line in head.splitlines():
        m = _LINE.match(line)
        if not m or m.group(1) not in FIELDS or m.group(1) == "bibtex":
            continue
        key, val = m.groups()
        if val.startswith("["):
            out[key] = re.findall(r'"([^"]*)"', val)
        elif len(val) >= 2 and val[0] == val[-1] == '"':
            out[key] = val[1:-1]
        else:
            out[key] = val.strip("'\"")
    return out


def parse_frontmatter(text: str) -> dict | None:
    """返回 frontmatter 字典（附带 _fallback 标记）；没有 title 和 image 时返回 None。"""
    head = _split(text)
    if head is None:
        return None
    try:
        data = yaml.safe_load(head)
        fb = False
        if not isinstance(data, dict):
            raise yaml.YAMLError("not a mapping")
    except yaml.YAMLError:
        data, fb = _fallback(head), True
    if not data.get("title") and not data.get("image"):
        return None
    data = {k: data.get(k) for k in FIELDS}
    data["_fallback"] = fb
    return data


def _none(v):
    v = v.strip() if isinstance(v, str) else v
    return v or None


def _year(v):
    try:
        return int(str(v).strip()[:4])
    except (TypeError, ValueError):
        return None


def parse(root: Path) -> tuple[list[dict], dict]:
    root = Path(root)
    stats = {"parsed": 0, "fallback": 0, "failed": 0, "missing_image": 0, "bad_image": 0}
    out = []
    for kind in KINDS:
        for md in sorted((root / "src/content/images" / kind / "paper").glob("*.md")):
            fm = parse_frontmatter(md.read_text(encoding="utf-8", errors="replace"))
            if fm is None:
                stats["failed"] += 1
                continue
            rel = f"public/images/{kind}/{fm.get('image') or ''}"
            if not fm.get("image") or not (root / rel).is_file():
                stats["missing_image"] += 1
                continue
            try:
                with Image.open(root / rel) as im:
                    w, h = im.size
            except (OSError, SyntaxError, ValueError):
                stats["bad_image"] += 1
                continue
            stats["parsed"] += 1
            stats["fallback"] += int(fm["_fallback"])
            out.append({
                "source": "papergallery", "upstreamId": md.stem, "kind": kind,
                "title": str(fm.get("title") or "").strip(), "authors": [str(a) for a in (fm.get("authors") or [])],
                "venue": canon_venue(fm.get("conference")), "year": _year(fm.get("year")),
                "tier": None, "award": None, "tags": [str(t) for t in (fm.get("tags") or [])],
                "paper": _none(fm.get("paper")), "pdf": None, "code": _none(fm.get("code")),
                "project": _none(fm.get("project")), "bibtex": None if fm["_fallback"] else _none(fm.get("bibtex")),
                "image": rel, "w": w, "h": h,
            })
    return sorted(out, key=lambda r: (r["kind"], r["upstreamId"])), stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="同步 PaperGallery 元数据（只取 frontmatter 与图片）")
    ap.add_argument("--local", help="本地 web 分支检出路径")
    ap.add_argument("--out", default=str(ROOT / "data" / "sources" / "papergallery.json"))
    a = ap.parse_args(argv)
    try:
        root = fetch(ROOT / ".cache" / "upstream", Path(a.local) if a.local else None)
    except FetchError as e:
        print(e, file=sys.stderr)
        return 1
    recs, st = parse(root)
    dump_json(a.out, recs)
    print(f"papergallery: {len(recs)} 条 -> {a.out}  {st}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
