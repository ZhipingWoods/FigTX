"""期刊图（Nature / Science / Cell / NMI 等）：从手工维护的清单 data/journals.json 读取。

清单每项：{"doi", "figure", "venue", "year", "title", "authors", "image"}；
image 可以是本地路径（相对仓库根或绝对路径）或图片 URL（下载到 .cache/upstream/journal）。
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

from .common import load_json, slug


def _local_image(image: str, root: Path, cache: Path) -> Path | None:
    if image.startswith(("http://", "https://")):
        cache.mkdir(parents=True, exist_ok=True)
        dst = cache / (slug(image)[-60:] + Path(image.split("?")[0]).suffix.lower())
        if not dst.exists():
            try:
                urllib.request.urlretrieve(image, dst)
            except (OSError, ValueError):
                return None
        return dst
    p = Path(image)
    p = p if p.is_absolute() else root / p
    return p if p.is_file() else None


def parse(path, root, cache=None) -> tuple[list[dict], dict]:
    root = Path(root)
    cache = Path(cache) if cache else root / ".cache" / "upstream" / "journal"
    stats = {"parsed": 0, "skipped": 0}
    out = []
    for e in load_json(path, []):
        img = _local_image(str(e.get("image") or ""), root, cache) if e.get("image") else None
        if not e.get("doi") or img is None:
            stats["skipped"] += 1
            continue
        from PIL import Image

        try:
            with Image.open(img) as im:
                w, h = im.size
        except (OSError, SyntaxError, ValueError):
            stats["skipped"] += 1
            continue
        try:  # 仓库内的图存相对路径：不暴露本机目录，CI 与本地结果一致
            img_path = str(img.resolve().relative_to(root.resolve()))
        except ValueError:
            img_path = str(img.resolve())
        stats["parsed"] += 1
        out.append({
            "source": "journal", "upstreamId": slug(f"{e['doi']} {e.get('figure', '')}"), "kind": "framework",
            "title": str(e.get("title") or "").strip(), "authors": list(e.get("authors") or []),
            "venue": str(e.get("venue") or "Unknown"), "year": e.get("year"), "tier": None, "award": None,
            "tags": list(e.get("tags") or []), "paper": f"https://doi.org/{e['doi']}", "pdf": None,
            "code": None, "project": None, "bibtex": None, "image": img_path, "w": w, "h": h,
        })
    return sorted(out, key=lambda r: r["upstreamId"]), stats
