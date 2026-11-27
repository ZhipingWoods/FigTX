"""测试用的场景构造工具（只在 tests/ 里用）。"""
import copy
import json
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "pipeline_scene.json"


def fixture_scene() -> dict:
    return json.loads(FIXTURE.read_text())


def base(width=200, height=100, nodes=None) -> dict:
    return {"version": 1, "canvas": {"width": width, "height": height}, "nodes": nodes or []}


def scene_with_rect(fill="#FF0000", **kw) -> dict:
    node = {"id": "r", "type": "rect", "x": 10, "y": 10, "w": 100, "h": 50, "fill": fill}
    node.update(kw)
    return base(nodes=[node])


def scene_with_text(text, w=180, fontSize=18, **kw) -> dict:
    node = {"id": "t", "type": "text", "x": 10, "y": 20, "w": w, "h": 40, "text": text,
            "fontSize": fontSize, "fill": "#000000"}
    node.update(kw)
    return base(nodes=[node])


def scene_with_line(arrowEnd=True) -> dict:
    return base(nodes=[{"id": "l", "type": "line", "x1": 10, "y1": 50, "x2": 150, "y2": 50,
                        "stroke": "#333333", "strokeWidth": 3, "arrowEnd": arrowEnd}])


def without(scene: dict, node_id: str) -> dict:
    s = copy.deepcopy(scene)
    s["nodes"] = [n for n in s["nodes"] if n["id"] != node_id]
    return s


def recolor(scene: dict, node_id: str, fill: str) -> dict:
    s = copy.deepcopy(scene)
    for n in s["nodes"]:
        if n["id"] == node_id:
            n["fill"] = fill
    return s
