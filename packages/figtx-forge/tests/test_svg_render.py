import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

from figtx_forge.geometry import node_bbox, path_to_polylines
from figtx_forge.render import render_scene
from figtx_forge.svg_export import scene_to_svg
from helpers import fixture_scene, scene_with_line, scene_with_rect, scene_with_text

SVG_NS = "{http://www.w3.org/2000/svg}"


def test_rect_fill_rendered():
    img = render_scene(scene_with_rect(fill="#FF0000"))
    assert img.getpixel((50, 30)) == (255, 0, 0)


def test_svg_has_viewbox():
    assert 'viewBox="0 0 1092 599"' in scene_to_svg(fixture_scene())


def test_svg_escapes_text():
    text = 'A & B <x> "q" 中文 🚀'
    root = ET.fromstring(scene_to_svg(scene_with_text(text)))
    texts = ["".join(t.itertext()) for t in root.iter(SVG_NS + "text")]
    assert texts == [text]


def test_text_rendered_dark_pixels():
    img = np.asarray(render_scene(scene_with_text("Encoder")).convert("L"))
    assert (img[20:60, 10:190] < 128).sum() > 50


def test_arrow_end_has_marker():
    assert "marker-end" in scene_to_svg(scene_with_line(arrowEnd=True))
    assert "marker-end" not in scene_to_svg(scene_with_line(arrowEnd=False))


def test_path_curve_samples():
    pts = path_to_polylines("M 0 0 C 0 10 10 10 10 0")[0]
    assert len(pts) == 17 and pts[-1] == (10.0, 0.0)


def test_path_relative_and_close():
    polys = path_to_polylines("m 5 5 h 10 v 10 z")
    assert polys[0][:3] == [(5.0, 5.0), (15.0, 5.0), (15.0, 15.0)]
    assert polys[0][-1] == (5.0, 5.0)


def test_node_bbox_line():
    assert node_bbox({"type": "line", "x1": 10, "y1": 50, "x2": 4, "y2": 60}) == (4, 50, 6, 10)


def test_image_embedded_base64(tmp_path):
    (tmp_path / "crops").mkdir()
    Image.new("RGB", (10, 10), (0, 128, 0)).save(tmp_path / "crops" / "a.png")
    scene = {"version": 1, "canvas": {"width": 50, "height": 50}, "_base_dir": str(tmp_path),
             "nodes": [{"id": "i", "type": "image", "x": 0, "y": 0, "w": 20, "h": 20, "href": "crops/a.png"}]}
    svg = scene_to_svg(scene)
    assert "data:image/png;base64," in svg
    assert render_scene(scene).getpixel((10, 10)) == (0, 128, 0)
