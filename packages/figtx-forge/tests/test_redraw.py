import json

from PIL import Image

from figtx_forge.cli import main
from figtx_forge.redraw import bitmap_area_ratio, crop_regions, lint_scene, redraw_check
from figtx_forge.render import render_scene
from helpers import FIXTURE, fixture_scene, scene_with_text


def _original(tmp_path):
    p = tmp_path / "original.png"
    render_scene(fixture_scene()).save(p)
    return p


def _write_scene(tmp_path, scene, name="scene.json"):
    p = tmp_path / name
    p.write_text(json.dumps(scene))
    return p


def test_crop_clamps(tmp_path):
    orig = _original(tmp_path)
    paths = crop_regions(orig, [{"id": "a", "x": -5, "y": 10, "w": 5000, "h": 20}], tmp_path / "crops")
    assert paths == [str(tmp_path / "crops" / "a.png")]
    assert Image.open(paths[0]).size == (1092, 20)


def test_bitmap_ratio_full_page_fails(tmp_path):
    orig = _original(tmp_path)
    crop_regions(orig, [{"id": "full", "x": 0, "y": 0, "w": 1092, "h": 599}], tmp_path / "crops")
    scene = {"version": 1, "canvas": {"width": 1092, "height": 599},
             "nodes": [{"id": "img", "type": "image", "x": 0, "y": 0, "w": 1092, "h": 599, "href": "crops/full.png"}]}
    report = redraw_check(orig, _write_scene(tmp_path, scene), tmp_path / "out")
    assert report["bitmap_ratio"] == 1.0
    assert report["passed"] is False


def _photo_scene(tmp_path):
    orig = _original(tmp_path)
    crop_regions(orig, [{"id": "big", "x": 0, "y": 0, "w": 655, "h": 599}], tmp_path / "crops")
    scene = fixture_scene()
    scene["nodes"].insert(0, {"id": "img", "type": "image", "x": 0, "y": 0, "w": 655, "h": 599, "href": "crops/big.png"})
    return orig, _write_scene(tmp_path, scene)


def test_photo_heavy_flag(tmp_path):
    orig, scene = _photo_scene(tmp_path)
    r1 = redraw_check(orig, scene, tmp_path / "o1")
    assert abs(r1["bitmap_ratio"] - 0.6) < 0.01 and r1["passed"] is False and r1["bitmap_limit"] == 0.40
    r2 = redraw_check(orig, scene, tmp_path / "o2", allow_photo_heavy=True)
    assert r2["bitmap_limit"] == 0.85 and r2["note"] == "photo-heavy" and r2["passed"] is True


def test_missing_text_reported(tmp_path):
    orig = _original(tmp_path)
    texts = tmp_path / "texts.txt"
    texts.write_text("Encoder\n  Decoder \n\nClassifier\n")
    report = redraw_check(orig, FIXTURE, tmp_path / "out", texts_path=texts)
    assert report["missing_texts"] == ["Classifier"]
    assert report["passed"] is False


def test_lint_overflow():
    issues = lint_scene(scene_with_text("A very long label", w=40, fontSize=18))
    assert issues[0]["rule"] == "text-overflow"


def test_lint_overlap_and_canvas_and_cjk():
    s = scene_with_text("中文标签", w=120)
    s["nodes"].append({"id": "t2", "type": "text", "x": 15, "y": 25, "w": 120, "h": 40, "text": "B", "fontSize": 12})
    s["nodes"].append({"id": "r", "type": "rect", "x": 150, "y": 50, "w": 100, "h": 20})
    rules = {(i["id"], i["rule"]) for i in lint_scene(s, english_only=True)}
    assert ("t2", "text-overlap") in rules or ("t", "text-overlap") in rules
    assert ("r", "out-of-canvas") in rules
    assert ("t", "cjk") in rules
    assert not any(i["rule"] == "cjk" for i in lint_scene(s))


def test_redraw_check_self_passes(tmp_path):
    orig = _original(tmp_path)
    texts = tmp_path / "texts.txt"
    texts.write_text("Input\nEncoder\nDecoder\nOutput\n")
    report = redraw_check(orig, FIXTURE, tmp_path / "out", texts_path=texts)
    assert report["passed"] is True, report["failed"]
    for f in ("render.png", "heatmap.png", "scene.svg", "report.json"):
        assert (tmp_path / "out" / f).exists()


def test_cli_redraw_check_and_crop(tmp_path):
    orig = _original(tmp_path)
    regions = tmp_path / "regions.json"
    regions.write_text(json.dumps([{"id": "a", "x": 0, "y": 0, "w": 10, "h": 10}]))
    assert main(["crop", str(orig), str(regions), "-o", str(tmp_path / "c")]) == 0
    assert main(["redraw-check", str(orig), str(FIXTURE), "-o", str(tmp_path / "out")]) == 0
    assert main(["lint", str(FIXTURE)]) == 0


def test_lint_serif_narrower_than_sans():
    serif = scene_with_text("transferred", w=66, fontSize=14, fontFamily="Times New Roman")
    sans = scene_with_text("transferred", w=66, fontSize=14, fontFamily="Arial")
    assert lint_scene(serif) == []
    assert lint_scene(sans)[0]["rule"] == "text-overflow"
