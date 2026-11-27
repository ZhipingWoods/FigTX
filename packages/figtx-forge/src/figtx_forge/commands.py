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


# ---- export ----
def _add_export(p):
    p.add_argument("scene")
    p.add_argument("-o", "--out", required=True, help="输出目录")
    p.add_argument("--svg", action="store_true")
    p.add_argument("--pptx", action="store_true")


def _run_export(a) -> int:
    from pathlib import Path

    from .pptx_export import scene_to_pptx
    from .svg_export import scene_to_svg

    scene = _load_valid(a.scene)
    if scene is None:
        return 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(a.scene).stem
    both = not (a.svg or a.pptx)
    if a.svg or both:
        (out / f"{stem}.svg").write_text(scene_to_svg(scene), encoding="utf-8")
        print(out / f"{stem}.svg")
    if a.pptx or both:
        scene_to_pptx(scene, out / f"{stem}.pptx")
        print(out / f"{stem}.pptx")
    return 0


SUBCOMMANDS["export"] = (_add_export, _run_export)


# ---- tex / plot-run ----
def _add_tex(p):
    p.add_argument("tex")
    p.add_argument("-o", "--out", required=True, help="预览 PNG 路径")
    p.add_argument("--compare", help="截图路径：输出比对指标（仅供参考）")


def _print_reference_compare(original: str, rendered: str) -> None:
    from PIL import Image

    from .metrics import compare

    print("--- 与截图比对（仅供参考，字体不同会拉低分数）---")
    print(_summary(compare(Image.open(original), Image.open(rendered))))


def _run_tex(a) -> int:
    from .tex import compile_table, table_shape, tectonic_path

    with open(a.tex, encoding="utf-8") as f:
        shape = table_shape(f.read())
    print(f"rows={shape['rows']} cols={shape['cols']} multicolumn={shape['multicolumn']} multirow={shape['multirow']}")
    if not tectonic_path():
        print("未找到 tectonic。安装：brew install tectonic，或见 https://tectonic-typesetting.github.io", file=sys.stderr)
        return 2
    r = compile_table(a.tex, a.out)
    if not r["ok"]:
        print(r["log_tail"], file=sys.stderr)
        return 1
    print(r["png"])
    if a.compare:
        _print_reference_compare(a.compare, r["png"])
    return 0


def _add_plot_run(p):
    p.add_argument("script")
    p.add_argument("-o", "--out", required=True, help="输出目录")
    p.add_argument("--compare", help="截图路径：与生成的第一张 PNG 比对（仅供参考）")
    p.add_argument("--python", help="运行脚本用的 Python（需装有 matplotlib），默认当前解释器")


def _run_plot_run(a) -> int:
    from .plot import run_plot

    r = run_plot(a.script, a.out, python=a.python)
    for f in r["files"]:
        print(f)
    if not r["ok"]:
        print(r["stderr_tail"], file=sys.stderr)
        return 1
    pngs = [f for f in r["files"] if f.endswith(".png")]
    if a.compare and pngs:
        _print_reference_compare(a.compare, pngs[0])
    return 0


SUBCOMMANDS["tex"] = (_add_tex, _run_tex)
SUBCOMMANDS["plot-run"] = (_add_plot_run, _run_plot_run)
