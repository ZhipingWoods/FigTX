"""SVG → 位图。用 resvg（Rust，经 resvg-py）渲染：不需要浏览器，结果稳定可复现。"""
from __future__ import annotations

import io

import resvg_py
from PIL import Image

from .svg_export import scene_to_svg


def render_svg(svg: str, width: int, height: int) -> Image.Image:
    png = resvg_py.svg_to_bytes(svg_string=svg, width=int(width), height=int(height), background="#ffffff")
    return Image.open(io.BytesIO(bytes(png))).convert("RGB")


def render_scene(scene: dict) -> Image.Image:
    c = scene["canvas"]
    return render_svg(scene_to_svg(scene), c["width"], c["height"])
