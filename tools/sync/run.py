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
from .merge import merge

ADAPTERS = {"topconf": sync_topconf, "papergallery": sync_papergallery}
ALL_SOURCES = ("topconf", "papergallery", "journal")


def _paths(root: Path) -> dict:
    return {
        "sources": root / "data" / "sources", "gallery": root / "data" / "raw-gallery.json",
        "tags": root / "data" / "tags.json", "manifest": root / "data" / "sources" / "assets-manifest.json",
        "dhash": root / "data" / "sources" / "dhash.json", "thumbs": root / "public" / "thumbs",
        "originals": root / ".cache" / "originals", "upstream": root / ".cache" / "upstream",
        "report": root / ".cache" / "sync-report.json",
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
    items, mrep = merge(records, roots, hashes=hashes)
    dump_json(P["dhash"], hashes)
    arep = sync_assets(items, roots, P["thumbs"], P["originals"], P["manifest"])
    bad = set(arep["bad"])
    items = [i for i in items if i["id"] not in bad]
    dump_json(P["gallery"], items)
    report.update(items=len(items), merged=mrep["merged"], suspects=mrep["suspects"], assets=arep)
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
    print(f"合并后条目：{rep['items']}（跨来源合并 {rep['merged']}）  疑似重复：{len(rep['suspects'])}")
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
    return 1 if rep["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
