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


# ---- crop / lint / redraw-check ----
def _add_crop(p):
    p.add_argument("image")
    p.add_argument("regions", help='JSON 文件：[{"id","x","y","w","h"}, ...]')
    p.add_argument("-o", "--out", required=True, help="输出目录")


def _run_crop(a) -> int:
    import json

    from .redraw import crop_regions

    with open(a.regions, encoding="utf-8") as f:
        for p in crop_regions(a.image, json.load(f), a.out):
            print(p)
    return 0


def _add_lint(p):
    p.add_argument("scene")
    p.add_argument("--english-only", action="store_true", help="出现中日韩字符时报错")


def _run_lint(a) -> int:
    from .redraw import BLOCKING_LINT, lint_scene

    scene = _load_valid(a.scene)
    if scene is None:
        return 1
    issues = lint_scene(scene, english_only=a.english_only)
    for i in issues:
        print(f"[{i['rule']}] {i['id']}: {i['msg']}")
    blocking = BLOCKING_LINT | ({"cjk"} if a.english_only else set())
    return 1 if any(i["rule"] in blocking for i in issues) else 0


def _add_redraw_check(p):
    p.add_argument("original")
    p.add_argument("scene")
    p.add_argument("-o", "--out", required=True, help="输出目录")
    p.add_argument("--texts", help="原图全部文字，一行一条")
    p.add_argument("--allow-photo-heavy", action="store_true", help="原图以照片为主时放宽位图占比上限到 0.85")


def _run_redraw_check(a) -> int:
    from .redraw import redraw_check

    r = redraw_check(a.original, a.scene, a.out, texts_path=a.texts, allow_photo_heavy=a.allow_photo_heavy)
    if "errors" in r:
        print("\n".join(r["errors"]), file=sys.stderr)
        return 1
    print(_summary(r))
    print(f"bitmap_ratio      {r['bitmap_ratio']:.4f}  (<= {r['bitmap_limit']})")
    if r["missing_texts"]:
        print("missing_texts: " + " | ".join(r["missing_texts"]))
    for i in r["lint"]:
        print(f"[{i['rule']}] {i['id']}: {i['msg']}")
    for t in r["worst_tiles"]:
        print(f"worst tile x={t['x']} y={t['y']} w={t['w']} h={t['h']} recall={t['recall']:.3f}")
    print(f"failed: {r['failed']}  → 查看 {a.out}/heatmap.png（红=漏画，蓝=多画）")
    return 0 if r["passed"] else 1


SUBCOMMANDS["crop"] = (_add_crop, _run_crop)
SUBCOMMANDS["lint"] = (_add_lint, _run_lint)
SUBCOMMANDS["redraw-check"] = (_add_redraw_check, _run_redraw_check)
