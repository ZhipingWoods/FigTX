#!/usr/bin/env python3
r"""汇总论文图复刻 → data/raw-replicas.json"""
from __future__ import annotations

import inspect
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import replicas  # noqa: E402
import reps_tikz  # noqa: E402


def src_of(fn) -> str:
    return inspect.getsource(fn).strip()


def main() -> int:
    items = []
    for slug, fn, title, desc, figtype, venues, domain in replicas.REPLICAS:
        png = os.path.join(common.OUT_FIG, "rep-" + slug + ".png")
        webp = os.path.join(common.OUT_FIG, "rep-" + slug + ".webp")
        # 只要 PNG 比 WebP 新就重转，否则改了代码看不到效果
        need = os.path.exists(png) and (
            not os.path.exists(webp)
            or os.path.getmtime(png) > os.path.getmtime(webp))
        if need:
            common._png_to_webp(png, webp, 1500)
        if not os.path.exists(webp):
            print("  ! missing", slug)
            continue
        items.append({
            "id": "rep-" + slug,
            "group": "replicas",
            "category": "figure",
            "figType": figtype,
            "kind": "chart",
            "title": title,
            "caption": desc,
            "domain": domain,
            "venues": venues,
            "styles": ["matplotlib"],
            "code": src_of(fn),
            "codeLang": "python",
            "render": "renders-fig/rep-%s.webp" % slug,
            "palette": [],
            "source": {"repo": None, "repoUrl": None,
                       "license": "本项目原创复刻", "stars": 0, "path": None},
        })

    for slug, fn, title, desc, figtype, venues, domain in reps_tikz.REPLICAS:
        webp = os.path.join(common.OUT_FIG, "rep-" + slug + ".webp")
        # TikZ 图每次重建（要带 assets 目录里的占位图）
        if not common.compile_tikz(reps_tikz.ARCH_STYLES + fn(), webp, assets=True):
            print("  ! tikz failed", slug)
            continue
        items.append({
            "id": "rep-" + slug,
            "group": "replicas",
            "category": "figure",
            "figType": figtype,
            "kind": "diagram",
            "title": title,
            "caption": desc,
            "domain": domain,
            "venues": venues,
            "styles": ["tikz"],
            "code": reps_tikz.ARCH_STYLES.strip() + "\n\n" + src_of(fn),
            "codeLang": "latex",
            "render": "renders-fig/rep-%s.webp" % slug,
            "palette": [],
            "source": {"repo": None, "repoUrl": None,
                       "license": "本项目原创复刻", "stars": 0, "path": None},
        })

    common.emit(items, "raw-replicas.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
