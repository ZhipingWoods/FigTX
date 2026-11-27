"""场景 JSON：一比一复刻与新图生成的唯一真源。SVG / PPTX 都从它导出。"""
from __future__ import annotations

import json
import re
from pathlib import Path

NODE_TYPES = {"rect", "ellipse", "line", "polyline", "path", "text", "image"}

REQUIRED = {
    "rect": ("x", "y", "w", "h"),
    "ellipse": ("cx", "cy", "rx", "ry"),
    "line": ("x1", "y1", "x2", "y2"),
    "polyline": ("points",),
    "path": ("d",),
    "text": ("x", "y", "w", "h", "text"),
    "image": ("x", "y", "w", "h", "href"),
}

COLOR_KEYS = ("fill", "stroke")
_COLOR_RE = re.compile(r"^(none|#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6})$")


def load_scene(path: str | Path) -> dict:
    """读取场景 JSON，并把所在目录记到 scene['_base_dir']（用于解析 image.href）。"""
    p = Path(path)
    scene = json.loads(p.read_text(encoding="utf-8"))
    scene["_base_dir"] = str(p.resolve().parent)
    return scene


def _check_canvas(scene: dict) -> list[str]:
    c = scene.get("canvas")
    if not isinstance(c, dict):
        return ["canvas: missing"]
    errs = []
    for k in ("width", "height"):
        v = c.get(k)
        if not isinstance(v, (int, float)) or v <= 0:
            errs.append(f"canvas: {k} must be a positive number")
    return errs


def _check_image(node: dict, base_dir: str | None) -> list[str]:
    if not base_dir:
        return []
    base = Path(base_dir).resolve()
    target = (base / str(node["href"])).resolve()
    if base != target and base not in target.parents:
        return [f"node {node['id']}: href outside scene dir"]
    if not target.is_file():
        return [f"node {node['id']}: href not found: {node['href']}"]
    return []


def _check_node(node: dict, base_dir: str | None) -> list[str]:
    nid = node.get("id", "?")
    t = node.get("type")
    if t not in NODE_TYPES:
        return [f"node {nid}: unknown type {t!r}"]
    errs = [f"node {nid}: missing {k}" for k in REQUIRED[t] if k not in node]
    for k in COLOR_KEYS:
        v = node.get(k)
        if v is not None and not (isinstance(v, str) and _COLOR_RE.match(v)):
            errs.append(f"node {nid}: bad color {k}={v!r}")
    if t == "polyline" and "points" in node:
        pts = node["points"]
        if not isinstance(pts, list) or len(pts) < 2 or any(len(p) != 2 for p in pts):
            errs.append(f"node {nid}: points must be a list of [x, y] pairs (>=2)")
    if t == "image" and not errs:
        errs += _check_image(node, base_dir)
    return errs


def validate_scene(scene: dict) -> list[str]:
    """返回错误列表；空列表表示场景合法。"""
    errs = _check_canvas(scene)
    nodes = scene.get("nodes")
    if not isinstance(nodes, list):
        return errs + ["nodes: must be a list"]
    seen: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict) or "id" not in node:
            errs.append("node without id")
            continue
        if node["id"] in seen:
            errs.append(f"duplicate id {node['id']}")
        seen.add(node["id"])
        errs += _check_node(node, scene.get("_base_dir"))
    return errs
