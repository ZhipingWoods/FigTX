"""缩略图（入库）与原图暂存（.cache，随后上传 HF）。用 sha256 清单保证增量和幂等。"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from PIL import Image, ImageOps

from .common import dump_json, load_json

THUMB_MAX = 800
THUMB_QUALITY = 80


class BadImage(RuntimeError):
    pass


def _rgb(im: Image.Image) -> Image.Image:
    if im.mode in ("RGBA", "LA", "P", "PA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        return bg.convert("RGB")
    return im.convert("RGB")


def make_thumb(src: Path, dst: Path, max_px: int = THUMB_MAX, quality: int = THUMB_QUALITY) -> tuple[int, int]:
    """最长边缩到 max_px（不放大），白底 RGB，保存为 webp。图片损坏时抛 BadImage。"""
    try:
        with Image.open(src) as im:
            im.load()
            im = _rgb(ImageOps.exif_transpose(im))
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as e:
        raise BadImage(f"{src}: {e}") from e
    im.thumbnail((max_px, max_px), Image.LANCZOS)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "WEBP", quality=quality, method=6)
    return im.size


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ext(p: Path) -> str:
    e = p.suffix.lower().lstrip(".")
    return "jpg" if e == "jpeg" else e


def sync_assets(items: list[dict], roots: dict, thumbs_dir, originals_dir, manifest_path) -> dict:
    thumbs_dir, originals_dir = Path(thumbs_dir), Path(originals_dir)
    manifest = load_json(manifest_path, {})
    rep = {"thumbs_new": 0, "skipped": 0, "bad": []}
    rep["unavailable"] = 0
    for it in items:
        base = roots.get(it["image"]["source"])
        if base is None:  # 该来源本次拉取失败：沿用已有缩略图和清单，不当作坏图
            rep["unavailable"] += 1
            continue
        src = Path(base) / it["image"]["path"]
        thumb = thumbs_dir / f"{it['id']}.webp"
        try:
            sha = _sha256(src)
        except OSError:
            rep["bad"].append(it["id"])
            continue
        entry = manifest.get(it["id"])
        changed = not entry or entry.get("sha256") != sha
        if not changed and thumb.exists():
            rep["skipped"] += 1
        else:
            try:
                make_thumb(src, thumb)
            except BadImage:
                rep["bad"].append(it["id"])
                continue
            rep["thumbs_new"] += 1
        with Image.open(src) as im:
            w, h = im.size
        uploaded = bool(entry and not changed and entry.get("uploaded"))
        ext = _ext(src)
        orig = originals_dir / f"{it['id']}.{ext}"
        if not uploaded and (changed or not orig.exists()):
            originals_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, orig)
        manifest[it["id"]] = {"sha256": sha, "ext": ext, "w": w, "h": h, "uploaded": uploaded}
    dump_json(manifest_path, manifest)
    if not rep["unavailable"]:
        rep.pop("unavailable")
    return rep
