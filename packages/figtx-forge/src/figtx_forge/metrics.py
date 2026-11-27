"""一比一比对：原图 vs 渲染图。

门槛来自设计文档 §5.7（与 topconf FigureForge 的终稿校验对齐）。
算法是本包自己的定义：深色笔画召回/精确（2px 容差）、Sobel 边缘 F1、8×8 网格局部召回、Lab ΔE 颜色相似度。
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

THRESHOLDS = {"composite": 0.98, "dark_recall": 0.98, "local_recall": 0.97, "edge_f1": 0.97, "color_similarity": 0.98}

DARK_LUMA = 160      # 亮度低于此值视为「深色笔画」
EDGE_MAG = 40        # Sobel 幅值高于此值视为边缘
TOL_FILTER = 5       # MaxFilter 尺寸 5 = 半径 2px 容差
GRID = 8
TILE_MIN_FRAC = 0.002
NEAR_WHITE = 235


def _prep(original: Image.Image, rendered: Image.Image) -> tuple[Image.Image, Image.Image]:
    def flat(im: Image.Image) -> Image.Image:
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGBA", im.size, "white")
            bg.alpha_composite(im)
            im = bg
        return im.convert("RGB")

    o, r = flat(original), flat(rendered)
    if r.size != o.size:
        r = r.resize(o.size, Image.LANCZOS)
    return o, r


def _luma(im: Image.Image) -> np.ndarray:
    a = np.asarray(im, dtype=np.float32)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def _dilate(mask: np.ndarray) -> np.ndarray:
    im = Image.fromarray(mask.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(TOL_FILTER))
    return np.asarray(im) > 0


def _ratio(num: int, den: int) -> float:
    return 1.0 if den == 0 else float(num) / float(den)


def _sobel_edges(gray: np.ndarray) -> np.ndarray:
    p = np.pad(gray, 1, mode="edge")
    gx = (p[:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[1:-1, :-2] + p[2:, :-2])
    gy = (p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[:-2, 1:-1] + p[:-2, 2:])
    return np.hypot(gx, gy) > EDGE_MAG


def _f1(a: np.ndarray, b: np.ndarray) -> float:
    recall = _ratio(int((a & _dilate(b)).sum()), int(a.sum()))
    precision = _ratio(int((b & _dilate(a)).sum()), int(b.sum()))
    return 0.0 if recall + precision == 0 else 2 * recall * precision / (recall + precision)


def _srgb_to_lab(im: Image.Image) -> np.ndarray:
    c = np.asarray(im, dtype=np.float64) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = np.einsum("...j,ij->...i", c, m) / np.array([0.95047, 1.0, 1.08883])  # einsum：避开 macOS Accelerate 的 matmul 误报警告
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def _color_similarity(o: Image.Image, r: Image.Image) -> float:
    mask = (np.asarray(o) < NEAR_WHITE).any(axis=-1)
    if not mask.any():
        return 1.0
    lo = _srgb_to_lab(o.filter(ImageFilter.GaussianBlur(2)))
    lr = _srgb_to_lab(r.filter(ImageFilter.GaussianBlur(2)))
    de = np.sqrt(((lo - lr) ** 2).sum(axis=-1))[mask].mean()
    return float(np.clip(1 - de / 100.0, 0, 1))


def _tiles(od: np.ndarray, rd_dil: np.ndarray) -> list[dict]:
    h, w = od.shape
    ys = np.linspace(0, h, GRID + 1).astype(int)
    xs = np.linspace(0, w, GRID + 1).astype(int)
    out = []
    for i in range(GRID):
        for j in range(GRID):
            t = od[ys[i]:ys[i + 1], xs[j]:xs[j + 1]]
            area = t.size
            n = int(t.sum())
            if area == 0 or n < TILE_MIN_FRAC * area:
                continue
            hit = int((t & rd_dil[ys[i]:ys[i + 1], xs[j]:xs[j + 1]]).sum())
            out.append({"x": int(xs[j]), "y": int(ys[i]), "w": int(xs[j + 1] - xs[j]),
                        "h": int(ys[i + 1] - ys[i]), "recall": _ratio(hit, n)})
    return sorted(out, key=lambda t: t["recall"])


def compare(original: Image.Image, rendered: Image.Image) -> dict:
    o, r = _prep(original, rendered)
    lo, lr = _luma(o), _luma(r)
    od, rd = lo < DARK_LUMA, lr < DARK_LUMA
    od_dil, rd_dil = _dilate(od), _dilate(rd)
    tiles = _tiles(od, rd_dil)
    m = {
        "dark_recall": _ratio(int((od & rd_dil).sum()), int(od.sum())),
        "dark_precision": _ratio(int((rd & od_dil).sum()), int(rd.sum())),
        "edge_f1": _f1(_sobel_edges(lo), _sobel_edges(lr)),
        "local_recall": tiles[0]["recall"] if tiles else 1.0,
        "color_similarity": _color_similarity(o, r),
    }
    m["composite"] = float(np.mean([m["dark_recall"], m["dark_precision"], m["edge_f1"], m["color_similarity"]]))
    m["failed"] = [k for k, v in THRESHOLDS.items() if m[k] < v]
    m["passed"] = not m["failed"]
    m["worst_tiles"] = tiles[:5]
    m["size"] = list(o.size)
    return m


def diff_heatmap(original: Image.Image, rendered: Image.Image) -> Image.Image:
    """红 = 原图有、渲染图漏画；蓝 = 渲染图多画。底图是淡化的原图。"""
    o, r = _prep(original, rendered)
    od, rd = _luma(o) < DARK_LUMA, _luma(r) < DARK_LUMA
    base = 255 - 0.35 * (255 - _luma(o))
    out = np.stack([base] * 3, axis=-1).astype(np.uint8)
    out[od & ~_dilate(rd)] = (230, 30, 30)
    out[rd & ~_dilate(od)] = (30, 90, 230)
    return Image.fromarray(out)
