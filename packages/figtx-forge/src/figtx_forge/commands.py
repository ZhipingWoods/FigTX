"""figtx 的各个子命令（参数定义 + 调用对应模块）。"""
from __future__ import annotations

import sys

from .cli import SUBCOMMANDS
from .scene import load_scene, validate_scene


def _load_valid(path: str) -> dict | None:
    scene = load_scene(path)
    errs = validate_scene(scene)
    for e in errs:
        print(e, file=sys.stderr)
    return None if errs else scene


# ---- render ----
def _add_render(p):
    p.add_argument("scene")
    p.add_argument("-o", "--out", required=True, help="输出 PNG 路径")


def _run_render(a) -> int:
    from .render import render_scene

    scene = _load_valid(a.scene)
    if scene is None:
        return 1
    render_scene(scene).save(a.out)
    print(a.out)
    return 0


SUBCOMMANDS["render"] = (_add_render, _run_render)


# ---- compare ----
def _add_compare(p):
    p.add_argument("original")
    p.add_argument("rendered")
    p.add_argument("--json", help="把指标写入 JSON 文件")
    p.add_argument("--heatmap", help="把差异热力图写入 PNG")


def _summary(m: dict) -> str:
    from .metrics import THRESHOLDS

    rows = [f"{k:17s} {m[k]:.4f}  (>= {v})  {'OK' if m[k] >= v else 'FAIL'}" for k, v in THRESHOLDS.items()]
    return "\n".join(rows + [f"passed: {m['passed']}"])


def _run_compare(a) -> int:
    import json

    from PIL import Image

    from .metrics import compare, diff_heatmap

    o, r = Image.open(a.original), Image.open(a.rendered)
    m = compare(o, r)
    print(_summary(m))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=2)
    if a.heatmap:
        diff_heatmap(o, r).save(a.heatmap)
    return 0 if m["passed"] else 1


SUBCOMMANDS["compare"] = (_add_compare, _run_compare)
