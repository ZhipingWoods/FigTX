"""场景 → SVG 字符串。每个场景节点对应一个 SVG 元素（id 保持一致），便于在 Illustrator/Inkscape 里逐个编辑。"""
from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

DEFAULT_FONT = "Arial, Helvetica, 'PingFang SC', 'Noto Sans CJK SC', sans-serif"
_ANCHOR = {"left": "start", "center": "middle", "right": "end"}


def _attrs(**kw) -> str:
    return "".join(f" {k.replace('_', '-')}={quoteattr(str(v))}" for k, v in kw.items() if v is not None)


def _paint(n: dict, default_fill: str = "none") -> dict:
    a = {"fill": n.get("fill", default_fill), "stroke": n.get("stroke"),
         "stroke_width": n.get("strokeWidth") if n.get("stroke") else None}
    if n.get("dash"):
        a["stroke_dasharray"] = " ".join(str(v) for v in n["dash"])
    if n.get("opacity") is not None and n.get("opacity") != 1:
        a["opacity"] = n["opacity"]
    return a


def _marker_id(color: str) -> str:
    return "arr-" + color.lstrip("#").lower()


def _markers(nodes: list[dict]) -> str:
    colors = sorted({n.get("stroke", "#000000") for n in nodes
                     if n["type"] in ("line", "polyline", "path") and (n.get("arrowEnd") or n.get("arrowStart"))})
    return "".join(
        f'<marker id="{_marker_id(c)}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4"'
        f' orient="auto-start-reverse" markerUnits="strokeWidth"><path d="M0,0 L10,5 L0,10 z" fill={quoteattr(c)}/></marker>'
        for c in colors)


def _arrows(n: dict) -> dict:
    mid = f"url(#{_marker_id(n.get('stroke', '#000000'))})"
    return {"marker_end": mid if n.get("arrowEnd") else None, "marker_start": mid if n.get("arrowStart") else None}


def _image_href(n: dict, base_dir: str | None, embed: bool) -> str:
    if not (embed and base_dir):
        return n["href"]
    p = Path(base_dir) / n["href"]
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def _text(n: dict) -> str:
    valign = n.get("valign", "middle")
    y = {"top": n["y"], "bottom": n["y"] + n["h"]}.get(valign, n["y"] + n["h"] / 2)
    baseline = {"top": "hanging", "bottom": "text-after-edge"}.get(valign, "central")
    align = n.get("align", "left")
    x = {"center": n["x"] + n["w"] / 2, "right": n["x"] + n["w"]}.get(align, n["x"])
    a = _attrs(id=n["id"], x=x, y=y, font_family=n.get("fontFamily", DEFAULT_FONT), font_size=n.get("fontSize", 16),
               font_weight=n.get("fontWeight"), font_style=n.get("fontStyle"), fill=n.get("fill", "#000000"),
               text_anchor=_ANCHOR.get(align, "start"), dominant_baseline=baseline,
               opacity=n.get("opacity") if n.get("opacity") not in (None, 1) else None)
    return f"<text{a}>{escape(n['text'])}</text>"


def _node(n: dict, base_dir: str | None, embed: bool) -> str:
    t = n["type"]
    if t == "rect":
        return f"<rect{_attrs(id=n['id'], x=n['x'], y=n['y'], width=n['w'], height=n['h'], rx=n.get('rx'), **_paint(n, '#ffffff'))}/>"
    if t == "ellipse":
        return f"<ellipse{_attrs(id=n['id'], cx=n['cx'], cy=n['cy'], rx=n['rx'], ry=n['ry'], **_paint(n, '#ffffff'))}/>"
    if t == "line":
        paint = _paint(n)
        paint["stroke"] = paint["stroke"] or "#000000"
        paint["stroke_width"] = n.get("strokeWidth", 1)
        return f"<line{_attrs(id=n['id'], x1=n['x1'], y1=n['y1'], x2=n['x2'], y2=n['y2'], **paint, **_arrows(n))}/>"
    if t == "polyline":
        pts = " ".join(f"{x},{y}" for x, y in n["points"])
        tag = "polygon" if n.get("closed") else "polyline"
        return f"<{tag}{_attrs(id=n['id'], points=pts, **_paint(n), **_arrows(n))}/>"
    if t == "path":
        return f"<path{_attrs(id=n['id'], d=n['d'], **_paint(n), **_arrows(n))}/>"
    if t == "text":
        return _text(n)
    if t == "image":
        return (f"<image{_attrs(id=n['id'], x=n['x'], y=n['y'], width=n['w'], height=n['h'], preserveAspectRatio='none')}"
                f" href={quoteattr(_image_href(n, base_dir, embed))}/>")
    raise ValueError(f"unknown node type {t}")


def scene_to_svg(scene: dict, embed_images: bool = True) -> str:
    c = scene["canvas"]
    w, h = c["width"], c["height"]
    nodes = scene.get("nodes", [])
    base_dir = scene.get("_base_dir")
    bg = c.get("background", "#FFFFFF")
    body = "".join(_node(n, base_dir, embed_images) for n in nodes)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f"<defs>{_markers(nodes)}</defs><rect id=\"_background\" width=\"{w}\" height=\"{h}\" fill={quoteattr(bg)}/>"
            f"{body}</svg>")
