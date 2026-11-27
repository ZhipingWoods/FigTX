"""最终评审发现的问题的回归测试。"""
import copy
import json
import signal

import pytest

from figtx_forge.cli import main
from figtx_forge.geometry import path_to_polylines
from figtx_forge.redraw import bitmap_area_ratio, crop_regions, redraw_check
from figtx_forge.render import render_scene
from figtx_forge.scene import validate_scene
from helpers import FIXTURE, base, fixture_scene


def _errs(node):
    return validate_scene(base(nodes=[node]))


def test_validate_rejects_nonpositive_size():
    errs = _errs({"id": "i", "type": "rect", "x": 0, "y": 0, "w": -200, "h": 10})
    assert any("w must be a positive number" in e for e in errs)
    assert any("rx must be a positive number" in e
               for e in _errs({"id": "e", "type": "ellipse", "cx": 5, "cy": 5, "rx": 0, "ry": 3}))


def test_bitmap_ratio_uses_absolute_area():
    s = base(nodes=[{"id": "a", "type": "image", "x": 0, "y": 0, "w": 200, "h": 100, "href": "a.png"},
                    {"id": "b", "type": "image", "x": 0, "y": 0, "w": -200, "h": 100, "href": "b.png"}])
    assert bitmap_area_ratio(s) == 1.0


def test_validate_rejects_bad_stroke_and_dash():
    line = {"id": "l", "type": "line", "x1": 0, "y1": 0, "x2": 10, "y2": 0, "stroke": "#000000"}
    assert any("strokeWidth" in e for e in _errs(dict(line, strokeWidth=0)))
    assert any("dash" in e for e in _errs(dict(line, dash=[0, 4])))


def test_validate_rejects_control_chars():
    errs = _errs({"id": "t", "type": "text", "x": 0, "y": 0, "w": 50, "h": 20, "text": "a\x0bb"})
    assert any("control character" in e for e in errs)


def test_path_numbers_after_z_raises():
    def boom(*_):
        raise TimeoutError("path parser hung")

    signal.signal(signal.SIGALRM, boom)
    signal.alarm(3)
    try:
        with pytest.raises(ValueError):
            path_to_polylines("M0 0 L10 10 Z 5 5")
    finally:
        signal.alarm(0)


def test_validate_rejects_unparseable_or_empty_path():
    assert any("bad path" in e for e in _errs({"id": "p", "type": "path", "d": "M0 0 L10 10 Z 5 5"}))
    assert any("bad path" in e for e in _errs({"id": "p", "type": "path", "d": "M10 10"}))


def test_extra_texts_fail(tmp_path):
    orig = tmp_path / "o.png"
    render_scene(fixture_scene()).save(orig)
    s = copy.deepcopy(fixture_scene())
    s["nodes"].append({"id": "x", "type": "text", "x": 30, "y": 40, "w": 160, "h": 30, "text": "Hallucinated",
                       "fontSize": 20, "fill": "#111111"})
    sp = tmp_path / "s.json"
    sp.write_text(json.dumps(s))
    texts = tmp_path / "t.txt"
    texts.write_text("Input\nEncoder\nDecoder\nOutput\n")
    r = redraw_check(orig, sp, tmp_path / "out", texts_path=texts)
    assert r["extra_texts"] == ["Hallucinated"] and "extra_texts" in r["failed"] and not r["passed"]


def test_redraw_check_without_texts_is_flagged(tmp_path):
    orig = tmp_path / "o.png"
    render_scene(fixture_scene()).save(orig)
    r = redraw_check(orig, FIXTURE, tmp_path / "out")
    assert r["texts_checked"] is False


def test_crop_rejects_bad_id(tmp_path):
    orig = tmp_path / "o.png"
    render_scene(fixture_scene()).save(orig)
    with pytest.raises(ValueError):
        crop_regions(orig, [{"id": "../../x", "x": 0, "y": 0, "w": 10, "h": 10}], tmp_path / "crops")


def test_cli_search_network_error(capsys):
    assert main(["search", "x", "--index", "http://127.0.0.1:9/index.json"]) == 1
    assert "--index" in capsys.readouterr().err
