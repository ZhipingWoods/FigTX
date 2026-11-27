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
