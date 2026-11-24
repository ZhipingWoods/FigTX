# -*- coding: utf-8 -*-
"""FigTX 论文图复刻 · 完整可运行代码（框架图）

保存为 .py 后运行即可生成同名 PNG。依赖：pip install matplotlib numpy pillow
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import (Circle, FancyArrowPatch, FancyBboxPatch,  # noqa: E402
                                Polygon, Rectangle)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Palatino", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "dejavuserif",
    "savefig.dpi": 300,
})

# ---- 实测配色 ----
C_BLUE = "#D6E8F7"
C_SCALE = "#FBF0C4"
C_MM = "#DCDCDC"
C_ROPE = "#F7941E"
C_RELU = "#FBE4E0"
C_GRN = "#D5F0D0"
C_PINK = "#FADBD8"
C_BK = "#000000"
C_GRN2 = "#78B808"
C_KV = "#A81838"
C_MASK2 = "#B4B4B4"
C_CELL = "#DCEBF8"
C_PAD = "#1B6FD6"


def _save_ar(fig, name, target_ar):
    """保存并补白到目标宽高比。"""
    import os
    fig.savefig(name + ".png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    from PIL import Image as _Im
    p = name + ".png"
    im = _Im.open(p).convert("RGB")
    w, h = im.size
    if w / h < target_ar:
        nw = int(round(h * target_ar))
        cv = _Im.new("RGB", (nw, h), "white")
        cv.paste(im, ((nw - w) // 2, 0))
    else:
        nh = int(round(w / target_ar))
        cv = _Im.new("RGB", (w, nh), "white")
        cv.paste(im, (0, (nh - h) // 2))
    cv.save(p)
    print("saved", p)
    return p


def _box(ax, cx, cy, w, h, text, fc, fs=10, rot=0, lw=1.6, pad_r=0.18):
    """圆角方框 + 居中文字（中心定位）。"""
    ax.add_patch(FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0,rounding_size=%.2f" % (min(w, h) * pad_r),
        facecolor=fc, edgecolor=C_BK, linewidth=lw, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, zorder=4,
            fontweight="bold", rotation=rot, linespacing=1.2)


def _arw(ax, pts, lw=1.2, color=C_BK, ms=9):
    """正交折线箭头：中间各段直线，末段带箭头。"""
    for i in range(len(pts) - 2):
        ax.plot([pts[i][0], pts[i + 1][0]], [pts[i][1], pts[i + 1][1]],
                color=color, lw=lw, solid_capstyle="butt", zorder=2)
    ax.add_patch(FancyArrowPatch(
        pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=ms,
        color=color, lw=lw, shrinkA=0, shrinkB=0, zorder=2))


def _dim(ax, x, y, t, fs=7.5, ha="left"):
    """尺寸标签（白底不压线）。"""
    ax.text(x, y, t, fontsize=fs, ha=ha, va="center", zorder=6,
            bbox=dict(fc="white", ec="none", pad=0.4))


def _stack(ax, x, y, size, n=5, grey=False):
    """叠层图块（照片感占位）。"""
    for k in range(n - 1, -1, -1):
        o = k * size * 0.030
        if grey:
            ax.add_patch(Rectangle((x - size / 2 + o, y - size / 2 + o), size, size,
                                   fc="#9A9A9A", ec="#5A5A5A", lw=0.6, zorder=2))
            continue
        ax.add_patch(Rectangle((x - size / 2 + o, y - size / 2 + o), size, size,
                               fc="#12101A", ec="#5A5A5A", lw=0.6, zorder=2))
        s = size / 18.0
        ax.add_patch(Rectangle((x - 6 * s + o, y - 3 * s + o), 8 * s, 9 * s,
                               fc="#1B7E96", alpha=0.50, ec="none", zorder=2))
        ax.add_patch(Rectangle((x + 1 * s + o, y - 5 * s + o), 7 * s, 5 * s,
                               fc="#B03A2E", alpha=0.45, ec="none", zorder=2))
        ax.add_patch(Rectangle((x - 3 * s + o, y + 1 * s + o), 4 * s, 6 * s,
                               fc="#7D3C98", alpha=0.35, ec="none", zorder=2))


def _grid(ax, x0, y0, cw, ch, ncols, nrows, colors_fn, lw=1.1):
    """画 nrows×ncols 网格。"""
    for r in range(nrows):
        for c in range(ncols):
            ax.add_patch(Rectangle(
                (x0 + c * cw, y0 + (nrows - 1 - r) * ch), cw, ch,
                fc=colors_fn(r, c), ec="black", lw=lw, zorder=3))
