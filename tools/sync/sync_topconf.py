"""topconf-paper-figure-gallery 适配器：拉取上游，把 data/figures.json 转成统一的来源记录。"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .common import ROOT, canon_venue, dump_json, load_json

UPSTREAM = "https://github.com/qwdwqfwq/topconf-paper-figure-gallery"
REPO = UPSTREAM


class FetchError(RuntimeError):
    pass


def _git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True, text=True, timeout=1800)


def fetch(cache_dir: Path, local: Path | None = None) -> Path:
    """返回上游仓库根目录：local 优先；否则浅克隆（已存在则 pull --ff-only）到 cache_dir/topconf。"""
    if local:
        if not Path(local).is_dir():
            raise FetchError(f"本地上游路径不存在：{local}")
        return Path(local)
    dest = Path(cache_dir) / "topconf"
    try:
        if (dest / ".git").exists():
            _git("-C", str(dest), "pull", "--ff-only", "-q")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            _git("clone", "--depth", "1", "-q", UPSTREAM, str(dest))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        raise FetchError(f"topconf 拉取失败：{e}") from e
    return dest


def _none(v):
    return v if v not in ("", None) else None


def parse(root: Path) -> list[dict]:
    root = Path(root)
    out = []
    for f in load_json(root / "data" / "figures.json", []):
        img = f.get("image") or ""
        if not img or not (root / img).is_file():
            continue
        out.append({
            "source": "topconf", "upstreamId": f["id"], "kind": f.get("pattern") or "teaser",
            "title": (f.get("title") or "").strip(), "authors": list(f.get("authors") or []),
            "venue": canon_venue(f.get("venue")), "year": int(f["year"]) if f.get("year") else None,
            "tier": _none(f.get("tier")), "award": _none(f.get("award")), "tags": [],
            "paper": _none(f.get("paper")), "pdf": _none(f.get("pdf_source")),
            "code": None, "project": None, "bibtex": None,
            "image": img, "w": f.get("w"), "h": f.get("h"),
        })
    return sorted(out, key=lambda r: r["upstreamId"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="同步 topconf 图库元数据")
    ap.add_argument("--local", help="本地上游仓库路径（不填则浅克隆到 .cache/upstream）")
    ap.add_argument("--out", default=str(ROOT / "data" / "sources" / "topconf.json"))
    a = ap.parse_args(argv)
    try:
        root = fetch(ROOT / ".cache" / "upstream", Path(a.local) if a.local else None)
    except FetchError as e:
        print(e, file=sys.stderr)
        return 1
    recs = parse(root)
    dump_json(a.out, recs)
    print(f"topconf: {len(recs)} 条 -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
