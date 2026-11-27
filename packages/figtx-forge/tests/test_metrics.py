import copy

import numpy as np
from PIL import Image, ImageChops

from figtx_forge.cli import main
from figtx_forge.metrics import THRESHOLDS, compare, diff_heatmap
from figtx_forge.render import render_scene, render_svg
from figtx_forge.svg_export import scene_to_svg
from helpers import fixture_scene, recolor

SMALL_LABEL = {"id": "lbl-note", "type": "text", "x": 30, "y": 40, "w": 120, "h": 30, "text": "note",
               "fontSize": 20, "fill": "#111111"}


def _with_small_label():
    s = copy.deepcopy(fixture_scene())
    s["nodes"].append(dict(SMALL_LABEL))
    return s


def test_thresholds_match_spec():
    assert THRESHOLDS == {"composite": 0.98, "dark_recall": 0.98, "local_recall": 0.97,
                          "edge_f1": 0.97, "color_similarity": 0.98}


def test_identical_passes():
    img = render_scene(fixture_scene())
    m = compare(img, img.copy())
    assert m["passed"] and m["failed"] == []
    assert min(m[k] for k in THRESHOLDS) >= 0.999


def test_shift_fails():
    img = render_scene(fixture_scene())
    m = compare(img, ImageChops.offset(img, 8, 0))
    assert not m["passed"] and "dark_recall" in m["failed"]


def test_color_change_fails():
    orig = render_scene(fixture_scene())
    m = compare(orig, render_scene(recolor(fixture_scene(), "box-enc", "#DA7777")))
    assert "color_similarity" in m["failed"]


def test_missing_label_hits_local():
    orig = render_scene(_with_small_label())
    m = compare(orig, render_scene(fixture_scene()))
    assert m["local_recall"] < 0.97
    assert m["dark_recall"] > 0.95
    assert "local_recall" in m["failed"]
    x, y = m["worst_tiles"][0]["x"], m["worst_tiles"][0]["y"]
    assert x <= 30 + 120 and y <= 40 + 30


def test_compare_resizes_render():
    s = fixture_scene()
    big = render_svg(scene_to_svg(s), 2 * 1092, 2 * 599)
    assert compare(render_scene(s), big)["passed"]


def test_compare_blank_original():
    white = Image.new("RGB", (100, 80), "white")
    m = compare(white, white.copy())
    assert m["passed"] and all(m[k] == 1.0 for k in THRESHOLDS)


def test_heatmap_marks_missing_red():
    orig = render_scene(_with_small_label())
    heat = np.asarray(diff_heatmap(orig, render_scene(fixture_scene())))
    o = np.asarray(orig.convert("L"))
    ys, xs = np.nonzero(o[40:70, 30:150] < 100)
    r, g, _ = heat[40 + ys[0], 30 + xs[0]]
    assert r > 200 and g < 80


def test_cli_compare_exit_codes(tmp_path):
    a = tmp_path / "a.png"
    render_scene(fixture_scene()).save(a)
    b = tmp_path / "b.png"
    ImageChops.offset(Image.open(a), 8, 0).save(b)
    assert main(["compare", str(a), str(a), "--json", str(tmp_path / "m.json")]) == 0
    assert main(["compare", str(a), str(b), "--heatmap", str(tmp_path / "h.png")]) == 1
    assert (tmp_path / "h.png").exists() and (tmp_path / "m.json").exists()
