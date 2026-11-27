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


def _order(rec: dict):
    return (SOURCE_ORDER.get(rec["source"], 9), rec["upstreamId"])


def _hash(rec: dict, roots: dict, hashes: dict | None) -> str:
    key = f"{rec['source']}:{rec['upstreamId']}"
    if hashes is not None and key in hashes:
        return hashes[key]
    h = dhash(Path(roots[rec["source"]]) / rec["image"])
    if hashes is not None:
        hashes[key] = h
    return h


def _paper_value(rec: dict, field: str):
    if field == "url":
        return rec.get("paper")
    v = rec.get(field)
    if field == "venue" and v == "Unknown":
        return None
    return v if v not in ("", [], None) else None


def _build(cluster: list[tuple[dict, str]]) -> dict:
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
        "id": item_id(primary),
        "figType": FIGTYPE_ALIAS.get(primary["kind"], primary["kind"]),
        "title": paper["title"] or "",
        "paper": paper,
        "tags": tags,
        "sources": sorted(({"platform": r["source"], "upstreamId": r["upstreamId"], "repo": REPOS.get(r["source"])}
                           for r in recs), key=lambda s: (s["platform"], s["upstreamId"])),
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


def merge(records: list[dict], roots: dict, hashes: dict | None = None) -> tuple[list[dict], dict]:
    groups = _group(sorted(records, key=_order))
    items, group_of = [], {}
    for key in sorted(groups):
        clusters: list[list[tuple[dict, str]]] = []
        for r in groups[key]:
            h = _hash(r, roots, hashes)
            home = next((c for c in clusters if any(hamming(h, ch) <= SAME_IMAGE for _, ch in c)), None)
            (home.append((r, h)) if home is not None else clusters.append([(r, h)]))
        for c in clusters:
            it = _build(c)
            items.append(it)
            group_of[it["id"]] = key
    items.sort(key=lambda i: i["id"])
    report = {"items": len(items), "merged": sum(len(i["sources"]) > 1 for i in items),
              "suspects": _suspects(items, group_of)}
    return items, report
