#!/usr/bin/env python3
r"""渲染 figlab 里的所有图，产出 data/raw-figs2.json。

分组：
    motivation  动机图
    quant       实验图·定量
    qual        实验图·定性

用法:
    .venv-fig/bin/python tools/figlab/build.py
    .venv-fig/bin/python tools/figlab/build.py --only motivation
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import motivation  # noqa: E402
import qual  # noqa: E402
import quant  # noqa: E402

# 类型 → (figType, 生成函数, codeLang)
GROUPS = {
    "motivation": ("motivation", "matplotlib", motivation.TEMPLATES),
    "quant": ("quantitative", "matplotlib", quant.TEMPLATES),
    "qual": ("qualitative", "matplotlib", qual.TEMPLATES),
}

PREFIX = {"framework": "fra", "motivation": "mot", "quantitative": "qx", "qualitative": "ql"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=",".join(GROUPS))
    args = ap.parse_args()

    wanted = [g.strip() for g in args.only.split(",") if g.strip()]
    existing_path = os.path.join(common.ROOT, "data", "raw-figs2.json")
    items = []
    if os.path.exists(existing_path):
        import json
        keep = {g for g in GROUPS if g not in wanted}
        old = json.load(open(existing_path, encoding="utf-8"))
        items = [i for i in old if i.get("group") in keep]
        print("keep %d from other groups" % len(items))

    for g in wanted:
        if g not in GROUPS:
            print("unknown group", g)
            continue
        fig_type, lang, fn = GROUPS[g]
        tmpl = fn() if callable(fn) else fn
        print("[%s] %d templates" % (g, len(tmpl)))
        for t in tmpl:
            if True:
                slug, fnc, title, desc, domain, venues = t
                fid = "fig-%s-%s" % (PREFIX[fig_type], slug)
                png = fnc()
                if not png or not os.path.exists(png):
                    continue
                # 直接把 matplotlib 源码作为可复制代码
                code, code_lang = _source_of(fnc), "python"
                out = png
            webp = os.path.join(common.OUT_FIG, fid + ".webp")
            if not os.path.exists(webp):
                common._png_to_webp(out, webp, 1500)
            print("  ok", fid)
            items.append({
                "id": fid,
                "group": g,
                "category": "figure",
                "figType": fig_type,
                "kind": "diagram" if lang == "tikz" else "chart",
                "title": title,
                "caption": desc,
                "domain": domain,
                "venues": venues,
                "styles": [code_lang],
                "code": code,
                "codeLang": code_lang,
                "render": "renders-fig/%s.webp" % fid,
                "palette": [],
                "source": {
                    "repo": None, "repoUrl": None,
                    "license": "本项目原创模板", "stars": 0, "path": None,
                },
            })

    common.emit(items, "raw-figs2.json")
    return 0


def _source_of(fnc) -> str:
    """取出生成函数自身的源码，作为可复制代码。"""
    import inspect
    import re
    src = inspect.getsource(fnc)
    # 去掉装饰器与函数定义行，保留函数体
    src = re.sub(r"^@.*\n", "", src, flags=re.M)
    return src.strip()


if __name__ == "__main__":
    raise SystemExit(main())
