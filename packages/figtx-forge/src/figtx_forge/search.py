"""检索 FigTX 精简索引（public/index.json，网站上为 <base>/index.json）。"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://zhipingwoods.github.io/FigTX/"
CACHE = Path.home() / ".cache" / "figtx" / "index.json"
CACHE_TTL = 24 * 3600
_NUMBER = re.compile(r"^[TFtf]\d{3,}$")


def _fetch(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_index(src: str | None = None) -> dict:
    """src 可以是路径或 URL；为 None 时依次用 $FIGTX_INDEX、本地缓存（24 小时）、线上索引。"""
    src = src or os.environ.get("FIGTX_INDEX")
    if src:
        if src.startswith(("http://", "https://")):
            return _fetch(src)
        return json.loads(Path(src).read_text(encoding="utf-8"))
    if CACHE.exists() and time.time() - CACHE.stat().st_mtime < CACHE_TTL:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    data = _fetch(DEFAULT_BASE + "index.json")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def _lower_join(values) -> str:
    return " ".join(str(v) for v in (values or [])).lower()


def _score(item: dict, tokens: list[str]) -> int:
    title = (item.get("title") or "").lower()
    meta = " ".join(_lower_join(item.get(k)) for k in ("domains", "problems", "tags", "venues"))
    caption = (item.get("caption") or "").lower()
    return sum(3 * (t in title) + 2 * (t in meta) + (t in caption) for t in tokens)


def search(index: dict, query: str, category: str | None = None, fig_type: str | None = None,
           limit: int = 20) -> list[dict]:
    items = [i for i in index.get("items", [])
             if (category is None or i.get("category") == category)
             and (fig_type is None or i.get("figType") == fig_type)]
    q = query.strip()
    if _NUMBER.match(q):
        return [i for i in items if (i.get("no") or "").upper() == q.upper()][:limit]
    tokens = q.lower().split()
    scored = [(s, i) for i in items if (s := _score(i, tokens)) > 0]
    scored.sort(key=lambda si: (-si[0], -(si[1].get("year") or 0)))
    return [i for _, i in scored[:limit]]


def preview_url(index: dict, item: dict) -> str:
    return (index.get("base") or DEFAULT_BASE) + (item.get("preview") or "")
