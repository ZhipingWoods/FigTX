"""场景 → PPTX 原生形状。每个场景节点变成一个可单独选中、编辑的 PowerPoint 对象（形状名 = 节点 id）。"""
from __future__ import annotations

from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

from .geometry import path_to_polylines

EMU_PER_PX = 9525
_ALIGN = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}
_VALIGN = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}


def _px(v: float) -> Emu:
    return Emu(int(round(v * EMU_PER_PX)))


def _rgb(color: str) -> RGBColor:
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return RGBColor.from_string(c.upper())


def _alpha(fill_parent, opacity) -> None:
    if opacity is None or opacity >= 1:
        return
    clr = fill_parent.find(".//" + qn("a:srgbClr"))
    if clr is not None:
        etree.SubElement(clr, qn("a:alpha")).set("val", str(int(opacity * 100000)))


def _style(shape, n: dict, default_fill: str | None) -> None:
    fill = n.get("fill", default_fill)
    if fill in (None, "none"):
        shape.fill.background()
    else:
        shape.fill.solid()
        shape.fill.fore_color.rgb = _rgb(fill)
        _alpha(shape.fill._xPr, n.get("opacity"))
    _line(shape, n)


def _line(shape, n: dict) -> None:
    stroke = n.get("stroke")
    if stroke in (None, "none"):
        shape.line.fill.background()
        return
    shape.line.color.rgb = _rgb(stroke)
    shape.line.width = Pt(n.get("strokeWidth", 1) * 0.75)
    if n.get("dash"):
        shape.line.dash_style = MSO_LINE.DASH


def _arrows(shape, n: dict) -> None:
    ln = shape.line._get_or_add_ln()
    for key, tag in (("arrowStart", "a:headEnd"), ("arrowEnd", "a:tailEnd")):
        if n.get(key):
            el = etree.SubElement(ln, qn(tag))
            el.set("type", "triangle")


def _text(slide, n: dict):
    shape = slide.shapes.add_textbox(_px(n["x"]), _px(n["y"]), _px(n["w"]), _px(n["h"]))
    tf = shape.text_frame
    tf.word_wrap = False
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = _VALIGN.get(n.get("valign", "middle"), MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    p.alignment = _ALIGN.get(n.get("align", "left"), PP_ALIGN.LEFT)
    run = p.add_run()
    run.text = n["text"]
    f = run.font
    f.size = Pt(n.get("fontSize", 16) * 0.75)
    f.bold = str(n.get("fontWeight", "")).lower() in ("bold", "600", "700", "800", "900")
    f.italic = n.get("fontStyle") == "italic"
    f.name = n.get("fontFamily", "Arial").split(",")[0].strip().strip("'\"")
    f.color.rgb = _rgb(n.get("fill", "#000000"))
    return shape


def _freeform(slide, pts, closed: bool):
    b = slide.shapes.build_freeform(pts[0][0], pts[0][1], scale=EMU_PER_PX)
    b.add_line_segments([tuple(p) for p in pts[1:]], close=closed)
    return b.convert_to_shape()


def _node(slide, n: dict, base_dir: str | None) -> list:
    t = n["type"]
    if t in ("rect", "ellipse"):
        if t == "rect":
            kind = MSO_SHAPE.ROUNDED_RECTANGLE if n.get("rx") else MSO_SHAPE.RECTANGLE
            shape = slide.shapes.add_shape(kind, _px(n["x"]), _px(n["y"]), _px(n["w"]), _px(n["h"]))
            if n.get("rx"):
                shape.adjustments[0] = min(0.5, n["rx"] / min(n["w"], n["h"]))
        else:
            shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, _px(n["cx"] - n["rx"]), _px(n["cy"] - n["ry"]),
                                           _px(2 * n["rx"]), _px(2 * n["ry"]))
        _style(shape, n, "#FFFFFF")
        return [shape]
    if t == "line":
        shape = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, _px(n["x1"]), _px(n["y1"]), _px(n["x2"]), _px(n["y2"]))
        _line(shape, dict(n, stroke=n.get("stroke", "#000000")))
        _arrows(shape, n)
        return [shape]
    if t in ("polyline", "path"):
        polys = [n["points"]] if t == "polyline" else path_to_polylines(n["d"])
        closed = n.get("closed", False) if t == "polyline" else n["d"].strip()[-1:] in ("z", "Z")
        shapes = [_freeform(slide, pts, closed) for pts in polys]
        for s in shapes:
            _style(s, n, None)
            _arrows(s, n)
        return shapes
    if t == "text":
        return [_text(slide, n)]
    if t == "image":
        src = str(Path(base_dir) / n["href"]) if base_dir else n["href"]
        return [slide.shapes.add_picture(src, _px(n["x"]), _px(n["y"]), _px(n["w"]), _px(n["h"]))]
    raise ValueError(f"unknown node type {t}")


def scene_to_pptx(scene: dict, out_path) -> None:
    c = scene["canvas"]
    prs = Presentation()
    prs.slide_width, prs.slide_height = _px(c["width"]), _px(c["height"])
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    for n in scene.get("nodes", []):
        shapes = _node(slide, n, scene.get("_base_dir"))
        for i, s in enumerate(shapes):
            s.name = n["id"] if i == 0 else f"{n['id']}#{i + 1}"
    prs.save(str(out_path))
