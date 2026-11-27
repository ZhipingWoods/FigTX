"""一比一复刻的流程工具：抠图、场景 lint、redraw-check（渲染 + 比对 + 文字核对 + 位图占比）。"""
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image

from .geometry import node_bbox
from .metrics import compare, diff_heatmap
from .render import render_scene
from .scene import load_scene, validate_scene
from .svg_export import scene_to_svg

BITMAP_LIMIT = 0.40
BITMAP_LIMIT_PHOTO = 0.85
_CJK = re.compile(r"[　-〿぀-ヿ㐀-䶿一-鿿가-힯＀-￯]")
BLOCKING_LINT = {"text-overflow", "out-of-canvas"}
_SAFE_ID = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9_.-]*$")


def crop_regions(image_path, regions: list[dict], out_dir) -> list[str]:
    """按 [{"id","x","y","w","h"}] 从原图裁出位图对象，越界部分截到图像范围内。"""
    img = Image.open(image_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for r in regions:
        if not _SAFE_ID.match(str(r.get("id", ""))):
            raise ValueError(f"region id {r.get('id')!r}: only letters, digits, '-', '_' and '.' (not leading) allowed")
        x0, y0 = max(0, int(r["x"])), max(0, int(r["y"]))
        x1, y1 = min(img.width, int(r["x"] + r["w"])), min(img.height, int(r["y"] + r["h"]))
        if x1 <= x0 or y1 <= y0:
            raise ValueError(f"region {r['id']} is empty after clamping")
        p = out / f"{r['id']}.png"
        img.crop((x0, y0, x1, y1)).save(p)
        paths.append(str(p))
    return paths


def bitmap_area_ratio(scene: dict) -> float:
    c = scene["canvas"]
    area = sum(abs(n["w"] * n["h"]) for n in scene.get("nodes", []) if n["type"] == "image")
    return min(1.0, area / float(c["width"] * c["height"]))


_SERIF = ("times", "serif", "georgia", "computer modern", "cmu", "garamond", "palatino", "stix")


def _text_width(text: str, size: float, family: str = "") -> float:
    """粗估文字宽度：衬线字体平均字宽约 0.42em，无衬线约 0.55em，中日韩字符 1em。"""
    fam = family.lower()
    latin = 0.42 if any(k in fam for k in _SERIF) and "sans" not in fam else 0.55
    return sum(size * (1.0 if _CJK.match(ch) else latin) for ch in text)


def _overlap(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    iw = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    ih = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    small = min(aw * ah, bw * bh)
    return 0.0 if small <= 0 else iw * ih / small


def lint_scene(scene: dict, english_only: bool = False) -> list[dict]:
    issues = []
    W, H = scene["canvas"]["width"], scene["canvas"]["height"]
    texts = [n for n in scene.get("nodes", []) if n["type"] == "text"]
    for n in texts:
        if _text_width(n["text"], n.get("fontSize", 16), n.get("fontFamily", "")) > n["w"] * 1.05:
            issues.append({"id": n["id"], "rule": "text-overflow", "msg": f"文字 {n['text']!r} 超出文字框宽度 {n['w']}"})
        if english_only and _CJK.search(n["text"]):
            issues.append({"id": n["id"], "rule": "cjk", "msg": f"文字 {n['text']!r} 含中日韩字符"})
    for i, a in enumerate(texts):
        for b in texts[i + 1:]:
            if _overlap(node_bbox(a), node_bbox(b)) > 0.15:
                issues.append({"id": b["id"], "rule": "text-overlap", "msg": f"文字框 {a['id']} 与 {b['id']} 重叠"})
    for n in scene.get("nodes", []):
        x, y, w, h = node_bbox(n)
        if x < -2 or y < -2 or x + w > W + 2 or y + h > H + 2:
            issues.append({"id": n["id"], "rule": "out-of-canvas", "msg": f"节点 {n['id']} 超出画布"})
    return issues


def _norm(s: str) -> str:
    return " ".join(s.split())


def _text_diff(scene: dict, texts_path) -> tuple[list[str], list[str]]:
    """返回 (原图有、场景缺的文字, 场景有、原图没有的文字)。"""
    if not texts_path:
        return [], []
    have = [_norm(n["text"]) for n in scene.get("nodes", []) if n["type"] == "text"]
    want = [t for t in (_norm(line) for line in Path(texts_path).read_text(encoding="utf-8").splitlines()) if t]
    return [t for t in want if t not in set(have)], [t for t in have if t and t not in set(want)]


def redraw_check(original_path, scene_path, out_dir, texts_path=None, allow_photo_heavy: bool = False) -> dict:
    """渲染场景并与原图比对，产出 render.png / heatmap.png / scene.svg / report.json。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    scene = load_scene(scene_path)
    errors = validate_scene(scene)
    if errors:
        report = {"passed": False, "failed": ["invalid-scene"], "errors": errors}
    else:
        original = Image.open(original_path)
        rendered = render_scene(scene)
        rendered.save(out / "render.png")
        diff_heatmap(original, rendered).save(out / "heatmap.png")
        (out / "scene.svg").write_text(scene_to_svg(scene), encoding="utf-8")
        report = compare(original, rendered)
        report["bitmap_ratio"] = round(bitmap_area_ratio(scene), 4)
        report["bitmap_limit"] = BITMAP_LIMIT_PHOTO if allow_photo_heavy else BITMAP_LIMIT
        if allow_photo_heavy:
            report["note"] = "photo-heavy"
        report["missing_texts"], report["extra_texts"] = _text_diff(scene, texts_path)
        report["texts_checked"] = bool(texts_path)
        report["lint"] = lint_scene(scene)
        if report["bitmap_ratio"] > report["bitmap_limit"]:
            report["failed"].append("bitmap_ratio")
        if report["missing_texts"]:
            report["failed"].append("missing_texts")
        if report["extra_texts"]:
            report["failed"].append("extra_texts")
        if any(i["rule"] in BLOCKING_LINT for i in report["lint"]):
            report["failed"].append("lint")
        report["passed"] = not report["failed"]
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
