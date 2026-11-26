#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为参考图批量预生成设计契约，缓存到 data/fig-contracts.json。

为什么要预生成：
  1. 每次生成都调视觉模型分析参考图，浪费时间与 token
  2. 设计契约是参考图的客观属性，生成一次就能复用
  3. 前端可以直接展示"这张图的配色/字号/密度"给人看

用法:
  python3 tools/figgen/build_contracts.py              # 只处理缺的
  python3 tools/figgen/build_contracts.py --force      # 全部重算
  python3 tools/figgen/build_contracts.py --only rep-05-architecture
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from figgen import contract as C

OUT = os.path.join(ROOT, "data", "fig-contracts.json")
ITEMS = os.path.join(ROOT, "src", "data", "items.json")

# 只对这些类型的图建契约（框架图相关）
TARGET_TYPES = {"architecture", "mechanism", "motivation", "results", "quantitative",
                "efficiency", "tradeoff", "style"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--types", nargs="*", default=None)
    args = ap.parse_args()

    if not os.path.exists(ITEMS):
        print("先把 items.json 生成出来：npm run data")
        return 1

    figs = [i for i in json.load(open(ITEMS, encoding="utf-8"))["items"]
            if i["category"] == "figure" and i.get("render")]
    want = set(args.types) if args.types else TARGET_TYPES
    figs = [f for f in figs if (f.get("figType") or "style") in want]
    if args.only:
        keep = set(args.only)
        figs = [f for f in figs if f["id"] in keep]

    cache: dict = {}
    if os.path.exists(OUT) and not args.force:
        try:
            cache = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            cache = {}

    todo = [f for f in figs if args.force or f["id"] not in cache]
    print("参考图共 %d 张，待分析 %d 张" % (len(figs), len(todo)))

    ok = 0
    for k, f in enumerate(todo, 1):
        img = os.path.join(ROOT, "public", f["render"])
        if not os.path.exists(img):
            print("  [%d/%d] %s 图缺失，跳过" % (k, len(todo), f["id"]))
            continue
        print("  [%d/%d] %s ..." % (k, len(todo), f["id"]), end="", flush=True)
        c = C.extract(img)
        if not c:
            print(" 失败")
            continue
        cache[f["id"]] = {
            "no": f.get("no"),
            "figType": f.get("figType"),
            "title": f.get("title"),
            "image": f["render"],
            "contract": c,
            "prompt": C.to_prompt(c),
        }
        ok += 1
        print(" ok")
        # 每张都落盘，避免中途失败丢进度
        json.dump(cache, open(OUT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    json.dump(cache, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("完成：%d 张契约 -> %s" % (len(cache), os.path.relpath(OUT, ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
