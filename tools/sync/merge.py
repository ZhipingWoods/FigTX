"""跨来源合并去重：同一篇论文（arXiv id 或 标题+年份）内，dHash 相近的图合并为一个条目。"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .common import arxiv_id, dhash, hamming, norm_title, slug
from .sync_papergallery import REPO as PG_REPO
from .sync_topconf import REPO as TC_REPO

SAME_IMAGE = 6          # hamming ≤ 6 视为同一张图
SUSPECT_IMAGE = 8       # 跨来源、不同论文但 hamming ≤ 8 的图进疑似重复报告（9–12 实测几乎都是不同论文的相似示意图）
TITLE_PREFIX = 60       # 标题只比较前 60 个字母数字（大小写、标点、空格、PDF 抽取断词都忽略）
SOURCE_ORDER = {"topconf": 0, "papergallery": 1, "journal": 2}
REPOS = {"topconf": TC_REPO, "papergallery": PG_REPO, "journal": None}
FIGTYPE_ALIAS = {"header": "teaser"}
PAPER_FIELDS = ("title", "authors", "venue", "year", "url", "pdf", "code", "project", "bibtex", "tier", "award")


def _compact(title: str | None) -> str:
    return re.sub(r"[^0-9a-z]", "", norm_title(title))[:TITLE_PREFIX]


def paper_keys(rec: dict) -> list[str]:
    """一条记录的所有论文标识：arXiv id、紧凑标题前缀。共享任一标识的记录视为同一篇论文。
    不看年份：arXiv 年份和会议年份常差一年（实测 SOLAMI、DPLM-2）。"""
    keys = []
    aid = arxiv_id(rec.get("paper")) or arxiv_id(rec.get("pdf"))
    if aid:
        keys.append(f"arxiv:{aid}")
    t = _compact(rec.get("title"))
    if len(t) >= 12:  # 太短的标题不足以认定同一篇论文
        keys.append(f"title:{t}")
    return keys or [f"id:{rec['source']}:{rec['upstreamId']}"]


def paper_key(rec: dict) -> str:
    return paper_keys(rec)[0]


def _group(records: list[dict]) -> dict[str, list[dict]]:
    """并查集：共享任一论文标识的记录归为一组；组名取组内排序最前的记录，保证确定性。"""
    parent = list(range(len(records)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owner: dict[str, int] = {}
    for i, r in enumerate(records):
        for k in paper_keys(r):
            if k in owner:
                a, b = find(i), find(owner[k])
                parent[max(a, b)] = min(a, b)
            else:
                owner[k] = i
    groups: dict[str, list[dict]] = defaultdict(list)
    for i, r in enumerate(records):
        root = records[find(i)]
        groups[f"{root['source']}:{root['upstreamId']}"].append(r)
    return groups


def item_id(rec: dict) -> str:
    if rec["source"] == "topconf":
        return f"tc-{rec['upstreamId']}"
    if rec["source"] == "papergallery":
        return f"pg-{rec['kind']}-{slug(rec['upstreamId'])}"
    return f"{rec['source'][:2]}-{slug(rec['upstreamId'])}"


KIND_RANK = {"header": 1}   # 同一来源同名时 pipeline 优先于 header（header 会被映射成 teaser）


def rec_key(rec: dict) -> str:
    """来源记录的稳定键。PaperGallery 同一个 stem 可能同时出现在 pipeline 和 header 两个目录，所以带上 kind。"""
    if rec["source"] == "papergallery":
        return f"papergallery:{rec['kind']}:{rec['upstreamId']}"
    return f"{rec['source']}:{rec['upstreamId']}"


def _order(rec: dict):
    return (SOURCE_ORDER.get(rec["source"], 9), rec["upstreamId"], KIND_RANK.get(rec.get("kind"), 0))


def _hash(rec: dict, roots: dict, hashes: dict | None) -> str | None:
    """dHash，按「来源 + 图片路径」缓存。图片读不了时返回 None（该记录记为坏记录，不让整个同步崩溃）。"""
    key = f"{rec['source']}:{rec['image']}"
    if hashes is not None and key in hashes:
        return hashes[key]
    base = roots.get(rec["source"])
    if base is None:
        return None
    try:
        h = dhash(Path(base) / rec["image"])
    except (OSError, ValueError, SyntaxError):
        return None
    if hashes is not None:
        hashes[key] = h
    return h


def _safe_url(v):
    return v if isinstance(v, str) and v.startswith(("https://", "http://")) else None


def seed_id_map(prev_items: list[dict]) -> dict:
    """从上一次的 raw-gallery 推出「记录键 → 条目 id」，让旧条目沿用原 id（编号随之不变）。"""
    out = {}
    for it in prev_items:
        img_kind = "header" if "/header/" in ((it.get("image") or {}).get("path") or "") else None
        id_kind = "header" if it["id"].startswith("pg-header-") else "pipeline" if it["id"].startswith("pg-pipeline-") else None
        for s in it.get("sources", []):
            if s["platform"] == "papergallery":
                kinds = [s["kind"]] if s.get("kind") else [img_kind or id_kind] if (img_kind or id_kind) else ["pipeline", "header"]
                for k in kinds:
                    out.setdefault(f"papergallery:{k}:{s['upstreamId']}", it["id"])
            else:
                out.setdefault(f"{s['platform']}:{s['upstreamId']}", it["id"])
    return out


def _paper_value(rec: dict, field: str):
    if field == "url":
        return _safe_url(rec.get("paper"))
    v = rec.get(field)
    if field in ("pdf", "code", "project"):
        return _safe_url(v)
    if field == "venue" and v == "Unknown":
        return None
    return v if v not in ("", [], None) else None


def _build(cluster: list[tuple[dict, str]], item_id_: str) -> dict:
    recs = [r for r, _ in cluster]
    primary = recs[0]
    paper = {f: next((v for r in recs if (v := _paper_value(r, f)) is not None), None) for f in PAPER_FIELDS}
    paper["venue"] = paper["venue"] or "Unknown"
    paper["authors"] = paper["authors"] or []
    best = max(cluster, key=lambda rh: ((rh[0].get("w") or 0) * (rh[0].get("h") or 0), -SOURCE_ORDER.get(rh[0]["source"], 9)))
    tags: list[str] = []
    for r in recs:
        tags += [t for t in r.get("tags") or [] if t not in tags]
    return {
        "id": item_id_,
        "figType": FIGTYPE_ALIAS.get(primary["kind"], primary["kind"]),
        "title": paper["title"] or "",
        "paper": paper,
        "tags": tags,
        "sources": sorted(({"platform": r["source"], "upstreamId": r["upstreamId"], "kind": r["kind"],
                            "repo": REPOS.get(r["source"])} for r in recs),
                          key=lambda s: (s["platform"], s["upstreamId"], s["kind"])),
        "image": {"source": best[0]["source"], "path": best[0]["image"], "w": best[0].get("w"), "h": best[0].get("h")},
        "dhash": best[1],
    }


def _suspects(items: list[dict], groups: dict[str, str]) -> list[dict]:
    out = []
    tc = [it for it in items if any(s["platform"] == "topconf" for s in it["sources"]) and len(it["sources"]) == 1]
    other = [it for it in items if all(s["platform"] != "topconf" for s in it["sources"])]
    tc_h = [(it["id"], int(it["dhash"], 16)) for it in tc]
    for it in other:
        h = int(it["dhash"], 16)
        for tid, th in tc_h:
            d = bin(h ^ th).count("1")
            if d <= SUSPECT_IMAGE and groups[tid] != groups[it["id"]]:
                out.append({"a": tid, "b": it["id"], "reason": f"dhash {d}"})
    return sorted(out, key=lambda s: (s["a"], s["b"], s["reason"]))


def _choose_id(cluster, id_map: dict, used: set) -> str:
    """优先沿用记录键已映射的旧 id（保证编号稳定）；没有旧 id 才按主记录新建，冲突时加后缀。"""
    for r, _ in cluster:
        old = id_map.get(rec_key(r))
        if old and old not in used:
            return old
    base = item_id(cluster[0][0])
    new, n = base, 2
    while new in used:
        new, n = f"{base}-{n}", n + 1
    return new


def merge(records: list[dict], roots: dict, hashes: dict | None = None,
          id_map: dict | None = None) -> tuple[list[dict], dict]:
    """id_map（记录键 → 条目 id）会被原地更新；传入上一次的映射即可让已有条目的 id 和编号保持不变。"""
    id_map = {} if id_map is None else id_map
    groups = _group(sorted(records, key=_order))
    items, group_of, used, bad = [], {}, set(), []
    for key in sorted(groups):
        clusters: list[list[tuple[dict, str]]] = []
        for r in groups[key]:
            h = _hash(r, roots, hashes)
            if h is None:
                bad.append(rec_key(r))
                continue
            home = next((c for c in clusters if any(hamming(h, ch) <= SAME_IMAGE for _, ch in c)), None)
            (home.append((r, h)) if home is not None else clusters.append([(r, h)]))
        for c in clusters:
            cid = _choose_id(c, id_map, used)
            used.add(cid)
            for r, _ in c:
                id_map[rec_key(r)] = cid
            it = _build(c, cid)
            items.append(it)
            group_of[it["id"]] = key
    items.sort(key=lambda i: i["id"])
    report = {"items": len(items), "merged": sum(len(i["sources"]) > 1 for i in items),
              "suspects": _suspects(items, group_of), "bad_records": sorted(bad)}
    return items, report
