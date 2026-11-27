import json

from figtx_forge.scene import load_scene, validate_scene


def _scene(nodes, canvas=None):
    return {"version": 1, "canvas": canvas or {"width": 200, "height": 100}, "nodes": nodes}


GOOD_NODES = [
    {"id": "n1", "type": "rect", "x": 10, "y": 10, "w": 50, "h": 30, "fill": "#77AADA", "stroke": "#222"},
    {"id": "n2", "type": "ellipse", "cx": 100, "cy": 50, "rx": 10, "ry": 8, "fill": "#FFF"},
    {"id": "n3", "type": "line", "x1": 60, "y1": 25, "x2": 90, "y2": 25, "stroke": "#333", "arrowEnd": True},
    {"id": "n4", "type": "polyline", "points": [[0, 0], [10, 0], [10, 10]], "closed": True, "fill": "#EEE"},
    {"id": "n5", "type": "path", "d": "M 10 10 C 40 0 60 0 90 10", "stroke": "#333", "fill": "none"},
    {"id": "n6", "type": "text", "x": 10, "y": 60, "w": 80, "h": 20, "text": "Encoder", "fontSize": 14, "fill": "#111"},
]


def test_validate_ok(tmp_path):
    p = tmp_path / "scene.json"
    p.write_text(json.dumps(_scene(GOOD_NODES)))
    assert validate_scene(load_scene(p)) == []


def test_validate_unknown_type():
    errs = validate_scene(_scene([{"id": "a", "type": "star"}]))
    assert any("unknown type" in e for e in errs)


def test_validate_missing_canvas():
    assert any("canvas" in e for e in validate_scene({"version": 1, "nodes": []}))


def test_validate_duplicate_id():
    n = {"id": "a", "type": "rect", "x": 0, "y": 0, "w": 1, "h": 1}
    assert any("duplicate id a" in e for e in validate_scene(_scene([n, dict(n)])))


def test_validate_missing_field():
    errs = validate_scene(_scene([{"id": "a", "type": "rect", "x": 0, "y": 0, "w": 1}]))
    assert any("missing h" in e for e in errs)


def test_validate_bad_color():
    n = {"id": "a", "type": "rect", "x": 0, "y": 0, "w": 1, "h": 1, "fill": "blue"}
    assert any("color" in e for e in validate_scene(_scene([n])))


def test_validate_image_href_outside_dir(tmp_path):
    p = tmp_path / "scene.json"
    bad = {"id": "i", "type": "image", "x": 0, "y": 0, "w": 5, "h": 5, "href": "../../etc/x.png"}
    p.write_text(json.dumps(_scene([bad])))
    assert any("outside scene dir" in e for e in validate_scene(load_scene(p)))
    missing = dict(bad, href="crops/missing.png")
    p.write_text(json.dumps(_scene([missing])))
    assert any("not found" in e for e in validate_scene(load_scene(p)))
