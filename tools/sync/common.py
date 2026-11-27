"""图库同步的公共工具：id、标题归一化、arXiv id、会议名规范化、dHash、稳定 JSON 读写。"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]

_VENUES = {
    "neurips": "NeurIPS", "nips": "NeurIPS", "iclr": "ICLR", "icml": "ICML", "cvpr": "CVPR", "iccv": "ICCV",
    "eccv": "ECCV", "acl": "ACL", "emnlp": "EMNLP", "naacl": "NAACL", "aaai": "AAAI", "ijcai": "IJCAI",
    "siggraph": "SIGGRAPH", "siggraph asia": "SIGGRAPH Asia", "tpami": "TPAMI", "ijcv": "IJCV", "arxiv": "arXiv",
    "mm": "ACM MM", "acm mm": "ACM MM", "kdd": "KDD", "icra": "ICRA", "iros": "IROS", "rss": "RSS", "wacv": "WACV",
    "tog": "TOG", "corl": "CoRL", "3dv": "3DV",
}
_ARXIV = re.compile(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?", re.I)


def slug(s: str) -> str:
    """小写、非 [a-z0-9] 连续字符替换为 '-'、去首尾 '-'、最长 80。"""
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")[:80].strip("-")


def norm_title(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s or "")).lower()
    return " ".join(re.sub(r"[^\w\s]|_", " ", s).split())


def arxiv_id(url: str | None) -> str | None:
    m = _ARXIV.search(url or "")
    return m.group(1) if m else None


def canon_venue(s: str | None) -> str:
    v = str(s or "").strip()
    if not v:
        return "Unknown"
    return _VENUES.get(v.lower(), v.upper())


def dhash(img, size: int = 8) -> str:
    """64 位差值哈希（灰度 → 9×8 → 比较左右相邻像素），16 位十六进制。"""
    im = img if isinstance(img, Image.Image) else Image.open(img)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, "white")
        bg.alpha_composite(im)
        im = bg
    a = np.asarray(im.convert("L").resize((size + 1, size), Image.LANCZOS), dtype=np.int16)
    bits = (a[:, 1:] > a[:, :-1]).flatten()
    return "".join(f"{int(''.join('1' if b else '0' for b in bits[i:i + 4]), 2):x}" for i in range(0, 64, 4))


def hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def load_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def dump_json(path, obj) -> None:
    """稳定输出：键排序、UTF-8、缩进 1、结尾换行——保证 sync 幂等（无变化时 git diff 为空）。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
