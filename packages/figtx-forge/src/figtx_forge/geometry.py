"""几何工具：SVG path d 解析与采样、节点包围盒。"""
from __future__ import annotations

import re

_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_ARGC = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}

Point = tuple[float, float]


def _bezier(p0: Point, ctrl: list[Point], p3: Point, samples: int) -> list[Point]:
    pts = [p0, *ctrl, p3]
    out = []
    for i in range(1, samples + 1):
        t = i / samples
        layer = pts
        while len(layer) > 1:  # de Casteljau
            layer = [((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1]) for a, b in zip(layer, layer[1:])]
        out.append((float(layer[0][0]), float(layer[0][1])))
    out[-1] = (float(p3[0]), float(p3[1]))
    return out


def _tokens(d: str):
    cmd = None
    toks = _TOKEN.findall(d)
    i = 0
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                yield cmd, []
                continue
        if cmd is None:
            raise ValueError(f"path must start with a command: {d[:30]!r}")
        if cmd in "Zz":
            raise ValueError(f"numbers after Z without a command: {d[:30]!r}")
        n = _ARGC[cmd.upper()]
        args = [float(x) for x in toks[i:i + n]]
        if len(args) < n:
            raise ValueError(f"path command {cmd} needs {n} numbers")
        i += n
        yield cmd, args
        if cmd == "M":
            cmd = "L"  # 隐式 lineto
        elif cmd == "m":
            cmd = "l"


def path_to_polylines(d: str, samples: int = 16) -> list[list[Point]]:
    """把 path d 采样成若干条折线（每个子路径一条）。曲线每段 samples 个点；A 弧按直线近似。"""
    polys: list[list[Point]] = []
    cur: Point = (0.0, 0.0)
    start: Point = (0.0, 0.0)
    last_ctrl: Point | None = None
    last_cmd = ""
    poly: list[Point] = []

    def flush():
        if len(poly) > 1:
            polys.append(list(poly))

    for cmd, a in _tokens(d):
        rel = cmd.islower()
        C = cmd.upper()
        ox, oy = cur if rel else (0.0, 0.0)
        if C == "M":
            flush()
            cur = (ox + a[0], oy + a[1])
            start = cur
            poly = [cur]
        elif C == "Z":
            if poly and poly[-1] != start:
                poly.append(start)
            flush()
            poly = [start]
            cur = start
        else:
            if not poly:
                poly = [cur]
            if C == "L" or C == "T" or C == "A":
                end = (ox + a[-2], oy + a[-1])
                if C == "T":
                    ctrl = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) if last_cmd in "QT" and last_ctrl else cur
                    poly += _bezier(cur, [ctrl], end, samples)
                    last_ctrl = ctrl
                else:
                    poly.append(end)
                cur = end
            elif C == "H":
                cur = (ox + a[0] if rel else a[0], cur[1])
                poly.append(cur)
            elif C == "V":
                cur = (cur[0], oy + a[0] if rel else a[0])
                poly.append(cur)
            elif C == "C":
                c1, c2, end = (ox + a[0], oy + a[1]), (ox + a[2], oy + a[3]), (ox + a[4], oy + a[5])
                poly += _bezier(cur, [c1, c2], end, samples)
                last_ctrl, cur = c2, end
            elif C == "S":
                c1 = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) if last_cmd in "CS" and last_ctrl else cur
                c2, end = (ox + a[0], oy + a[1]), (ox + a[2], oy + a[3])
                poly += _bezier(cur, [c1, c2], end, samples)
                last_ctrl, cur = c2, end
            elif C == "Q":
                c1, end = (ox + a[0], oy + a[1]), (ox + a[2], oy + a[3])
                poly += _bezier(cur, [c1], end, samples)
                last_ctrl, cur = c1, end
        last_cmd = C
    flush()
    return polys


def node_bbox(node: dict) -> tuple[float, float, float, float]:
    """节点包围盒 (x, y, w, h)，单位为画布像素。"""
    t = node["type"]
    if t in ("rect", "text", "image"):
        return (node["x"], node["y"], node["w"], node["h"])
    if t == "ellipse":
        return (node["cx"] - node["rx"], node["cy"] - node["ry"], 2 * node["rx"], 2 * node["ry"])
    if t == "line":
        xs, ys = (node["x1"], node["x2"]), (node["y1"], node["y2"])
        return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
    pts = node["points"] if t == "polyline" else [p for poly in path_to_polylines(node["d"]) for p in poly]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
