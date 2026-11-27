"""npm run sync 的总入口：拉取各来源 → 合并去重 → 缩略图 → 打标 → 上传原图 → 编号 → 生成前端数据。

任何一个来源拉取失败（或这次突然一条都没有）时，沿用它上一次的数据，已有条目一个都不丢。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import sync_journal, sync_papergallery, sync_topconf
from .assets import sync_assets
from .common import ROOT, dump_json, load_json
from .merge import merge, seed_id_map

ADAPTERS = {"topconf": sync_topconf, "papergallery": sync_papergallery}
ALL_SOURCES = ("topconf", "papergallery", "journal")


def _paths(root: Path) -> dict:
    return {
        "sources": root / "data" / "sources", "gallery": root / "data" / "raw-gallery.json",
        "tags": root / "data" / "tags.json", "manifest": root / "data" / "sources" / "assets-manifest.json",
        "dhash": root / "data" / "sources" / "dhash.json", "thumbs": root / "public" / "thumbs",
        "originals": root / ".cache" / "originals", "upstream": root / ".cache" / "upstream",
        "report": root / ".cache" / "sync-report.json",
        "idmap": root / "data" / "sources" / "id-map.json", "takedown": root / "data" / "takedown.json",
    }


def _collect(src: str, root: Path, P: dict, local: dict, report: dict) -> tuple[list[dict], Path | None]:
    """返回 (该来源的来源记录, 上游根目录或 None)。失败时沿用上一次的记录。"""
    out = P["sources"] / f"{src}.json"
    previous = load_json(out, [])
    try:
        if src == "journal":
            recs, _ = sync_journal.parse(root / "data" / "journals.json", root, P["upstream"] / "journal")
            upstream = root
        else:
            mod = ADAPTERS[src]
            upstream = mod.fetch(P["upstream"], local.get(src))
            parsed = mod.parse(upstream)
            recs = parsed[0] if isinstance(parsed, tuple) else parsed
            if not recs and previous:
                raise sync_topconf.FetchError(f"{src} 这次解析出 0 条（上次 {len(previous)} 条），视为拉取异常")
    except (sync_topconf.FetchError, sync_papergallery.FetchError) as e:
        report["errors"][src] = str(e)
        return previous, None
    dump_json(out, recs)
    return recs, upstream


def _prune(items: list[dict], P: dict) -> int:
    """删除已不对应任何条目的缩略图和清单项（被合并掉、被下架的条目）。待从 HF 删除的下架项保留清单记录。"""
    alive = {i["id"] for i in items}
    manifest = load_json(P["manifest"], {})
    dead = sorted({k for k, v in manifest.items() if k not in alive and not v.get("takedown")} |
                  {p.stem for p in P["thumbs"].glob("*.webp") if p.stem not in alive})
    for k in dead:
        manifest.pop(k, None)
        (P["thumbs"] / f"{k}.webp").unlink(missing_ok=True)
    if dead:
        dump_json(P["manifest"], manifest)
    return len(dead)


def _takedown_ids(P: dict) -> set[str]:
    """data/takedown.json：[{"id": "tc-...", "reason": "...", "date": "..."}]（也接受纯字符串）。"""
    return {e["id"] if isinstance(e, dict) else str(e) for e in load_json(P["takedown"], [])}


def _apply_takedown(denied: set[str], P: dict) -> None:
    """已上传到 HF 的下架原图标记 takedown，等 push 删除；未上传的直接移出清单。"""
    manifest = load_json(P["manifest"], {})
    for k in denied & set(manifest):
        if manifest[k].get("uploaded"):
            manifest[k]["takedown"] = True
        else:
            manifest.pop(k)
    dump_json(P["manifest"], manifest)


def _carry_over(prev: list[dict], fresh: list[dict], denied: set[str]) -> list[dict]:
    """上游这次没有、也没被并进别的条目的旧条目：保留并标记 upstreamMissing（spec：只标记，不自动删）。"""
    seen = {(s["platform"], s["upstreamId"]) for it in fresh for s in it["sources"]}
    ids = {it["id"] for it in fresh}
    out = []
    for it in prev:
        if it["id"] in ids or it["id"] in denied:
            continue
        if any((s["platform"], s["upstreamId"]) in seen for s in it["sources"]):
            continue
        out.append(dict(it, upstreamMissing=True))
    return out


def _node_build(root: Path) -> None:
    subprocess.run(["node", "tools/build-data.mjs"], cwd=root, check=True, capture_output=True)


def run(sources=ALL_SOURCES, local: dict | None = None, no_tag: bool = False, no_push: bool = False,
        root: Path = ROOT) -> dict:
    root = Path(root)
    P = _paths(root)
    local = local or {}
    report = {"sources": {}, "errors": {}}
    records, roots = [], {}
    for src in ALL_SOURCES:
        if src in sources:
            recs, upstream = _collect(src, root, P, local, report)
        else:  # 本次不同步的来源：沿用上一次的记录，条目不丢
            recs, upstream = load_json(P["sources"] / f"{src}.json", []), None
        report["sources"][src] = len(recs)
        records += recs
        roots[src] = upstream
    hashes = load_json(P["dhash"], {})
    prev = load_json(P["gallery"], [])
    id_map = load_json(P["idmap"], None)
    if id_map is None:
        id_map = seed_id_map(prev)
    items, mrep = merge(records, roots, hashes=hashes, id_map=id_map)
    dump_json(P["dhash"], hashes)
    dump_json(P["idmap"], id_map)
    denied = _takedown_ids(P)
    removed = sorted(denied & ({i["id"] for i in items} | {i["id"] for i in prev}))
    items = [i for i in items if i["id"] not in denied]
    arep = sync_assets(items, roots, P["thumbs"], P["originals"], P["manifest"])
    bad = set(arep["bad"])
    items = [i for i in items if i["id"] not in bad]
    carried = _carry_over(prev, items, denied | bad)
    items = sorted(items + carried, key=lambda i: i["id"])
    dump_json(P["gallery"], items)
    _apply_takedown(denied, P)
    report["pruned"] = _prune(items, P)
    prev_ids = {i["id"] for i in prev}
    report.update(items=len(items), merged=mrep["merged"], suspects=mrep["suspects"], assets=arep,
                  bad_records=mrep["bad_records"], new=sum(i["id"] not in prev_ids for i in items),
                  missing=len(carried), removed=removed)
    if not no_tag:
        from tools.figgen import llm_client  # noqa: F401  导入时把 .env 读进环境变量

        from .tag import tag

        report["tags"] = tag(items, P["tags"])
    if not no_push:
        from .push_assets import push

        report["push"] = push(P["originals"], P["manifest"])
    _node_build(root)
    subprocess.run([sys.executable, "tools/assign_numbers.py", "--keep-missing"], cwd=root, check=True,
                   capture_output=True)
    _node_build(root)
    dump_json(P["report"], report)
    return report


def _print(rep: dict) -> None:
    print("来源：" + "，".join(f"{k} {v} 条" for k, v in rep["sources"].items()))
    print(f"合并后条目：{rep['items']}（新增 {rep['new']}，上游缺失但保留 {rep['missing']}，跨来源合并 {rep['merged']}）"
          f"  疑似重复：{len(rep['suspects'])}  下架：{len(rep['removed'])}")
    if rep["bad_records"]:
        print(f"读不了的上游图片：{len(rep['bad_records'])} {rep['bad_records'][:5]}")
    a = rep["assets"]
    print(f"缩略图：新增 {a['thumbs_new']}，跳过 {a['skipped']}，坏图 {len(a['bad'])} {a['bad'][:5]}")
    if "tags" in rep:
        print(f"打标：{rep['tags']}")
    if "push" in rep:
        print(f"上传 HF：{rep['push']}")
    for src, err in rep["errors"].items():
        print(f"⚠️ {src}：{err}（沿用上一次的数据）")
    print("完整报告：.cache/sync-report.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="同步上游图库到 FigTX")
    ap.add_argument("--local-topconf")
    ap.add_argument("--local-papergallery")
    ap.add_argument("--only", choices=ALL_SOURCES, action="append", help="只同步指定来源（可重复）")
    ap.add_argument("--no-tag", action="store_true", help="不调用模型打标")
    ap.add_argument("--no-push", action="store_true", help="不上传原图到 Hugging Face")
    a = ap.parse_args(argv)
    local = {k: Path(v) for k, v in (("topconf", a.local_topconf), ("papergallery", a.local_papergallery)) if v}
    rep = run(sources=tuple(a.only) if a.only else ALL_SOURCES, local=local, no_tag=a.no_tag, no_push=a.no_push)
    _print(rep)
    # 3 = 有来源拉取失败（已沿用旧数据，仍可开 PR）；未捕获的异常是 1，CI 据此区分
    return 3 if rep["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
