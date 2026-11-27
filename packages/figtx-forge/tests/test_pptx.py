import copy
import json

from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from figtx_forge.cli import main
from figtx_forge.pptx_export import scene_to_pptx
from helpers import FIXTURE, fixture_scene, scene_with_text


def _shapes(path):
    return list(Presentation(str(path)).slides[0].shapes)


def test_pptx_shape_count(tmp_path):
    out = tmp_path / "a.pptx"
    scene_to_pptx(fixture_scene(), out)
    assert len(_shapes(out)) == 9


def test_pptx_text_preserved(tmp_path):
    out = tmp_path / "a.pptx"
    scene_to_pptx(fixture_scene(), out)
    texts = {s.text_frame.text for s in _shapes(out) if s.has_text_frame}
    assert {"Input", "Encoder", "Decoder", "Output"} <= texts


def test_pptx_keeps_special_text(tmp_path):
    out = tmp_path / "a.pptx"
    scene_to_pptx(scene_with_text("A & B <x> 中文"), out)
    assert [s.text_frame.text for s in _shapes(out) if s.has_text_frame] == ["A & B <x> 中文"]


def test_pptx_slide_size(tmp_path):
    out = tmp_path / "a.pptx"
    scene_to_pptx(fixture_scene(), out)
    prs = Presentation(str(out))
    assert prs.slide_width == 1092 * 9525 and prs.slide_height == 599 * 9525


def test_pptx_arrow_xml(tmp_path):
    out = tmp_path / "a.pptx"
    scene_to_pptx(fixture_scene(), out)
    arrows = [s for s in _shapes(out) if s.name == "arrow-1"]
    xml = arrows[0]._element.xml
    assert "tailEnd" in xml and 'type="triangle"' in xml


def test_pptx_shapes_named_by_node_id(tmp_path):
    out = tmp_path / "a.pptx"
    scene_to_pptx(fixture_scene(), out)
    assert {s.name for s in _shapes(out)} == {n["id"] for n in fixture_scene()["nodes"]}


def test_pptx_picture_and_freeform(tmp_path):
    (tmp_path / "crops").mkdir()
    Image.new("RGB", (10, 10), (0, 128, 0)).save(tmp_path / "crops" / "a.png")
    scene = copy.deepcopy(fixture_scene())
    scene["_base_dir"] = str(tmp_path)
    scene["nodes"] += [
        {"id": "img", "type": "image", "x": 10, "y": 10, "w": 50, "h": 50, "href": "crops/a.png"},
        {"id": "curve", "type": "path", "d": "M 10 500 C 100 450 200 450 300 500", "stroke": "#333333", "strokeWidth": 2},
        {"id": "tri", "type": "polyline", "points": [[400, 500], [450, 450], [500, 500]], "closed": True, "fill": "#EEEEEE"},
    ]
    out = tmp_path / "b.pptx"
    scene_to_pptx(scene, out)
    shapes = _shapes(out)
    assert sum(s.shape_type == MSO_SHAPE_TYPE.PICTURE for s in shapes) == 1
    assert {"curve", "tri"} <= {s.name for s in shapes}


def test_cli_export_both(tmp_path):
    assert main(["export", str(FIXTURE), "-o", str(tmp_path)]) == 0
    assert (tmp_path / "pipeline_scene.svg").exists() and (tmp_path / "pipeline_scene.pptx").exists()
    assert main(["export", str(FIXTURE), "-o", str(tmp_path / "s"), "--svg"]) == 0
    assert not (tmp_path / "s" / "pipeline_scene.pptx").exists()
