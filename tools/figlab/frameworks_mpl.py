#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文图复刻（matplotlib 版）· 05 架构图 / 06 机制图

按 paper-plot-skills 的复现方法论：
  量 AR → 抽色 → 字体/spine 规范 → 渲染对照 → 修差异
针对 TikZ 版的线条问题，这里所有连接线都用 FancyArrowPatch + 显式
正交路径（严格水平/垂直），杜绝斜线与错位。
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

from common import OUT_FIG  # noqa: E402

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Palatino", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "dejavuserif",
    "savefig.dpi": 300,
})

# 实测配色
C_BLUE = "#D6E8F7"
C_SCALE = "#FBF0C4"
C_MM = "#DCDCDC"
C_ROPE = "#F7941E"
C_RELU = "#FBE4E0"
C_GRN = "#D5F0D0"
C_PINK = "#FADBD8"
C_BK = "#000000"


def _save(fig, name):
    os.makedirs(OUT_FIG, exist_ok=True)
    p = os.path.join(OUT_FIG, name + ".png")
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def _save_ar(fig, name, target_ar):
    """保存并补白到目标宽高比（tight bbox 会随内容裁剪，这里兜底对齐）。"""
    os.makedirs(OUT_FIG, exist_ok=True)
    p = os.path.join(OUT_FIG, name + ".png")
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    from PIL import Image as _Im
    im = _Im.open(p).convert("RGB")
    w, h = im.size
    if w / h < target_ar:                      # 太窄 → 加宽
        nw = int(round(h * target_ar))
        cv = _Im.new("RGB", (nw, h), "white")
        cv.paste(im, ((nw - w) // 2, 0))
    else:                                      # 太高 → 加高
        nh = int(round(w / target_ar))
        cv = _Im.new("RGB", (w, nh), "white")
        cv.paste(im, (0, (nh - h) // 2))
    cv.save(p)
    return p


def _box(ax, cx, cy, w, h, text, fc, fs=10, rot=0, lw=1.6, pad_r=0.18):
    ax.add_patch(FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0,rounding_size=%.2f" % (min(w, h) * pad_r),
        facecolor=fc, edgecolor=C_BK, linewidth=lw, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, zorder=4,
            fontweight="bold", rotation=rot, linespacing=1.2)


def _arw(ax, pts, lw=1.2, color=C_BK, ms=9):
    """正交折线箭头：中间点用纯直线连接，末段带箭头。"""
    for i in range(len(pts) - 2):
        ax.plot([pts[i][0], pts[i + 1][0]], [pts[i][1], pts[i + 1][1]],
                color=color, lw=lw, solid_capstyle="butt", zorder=2)
    ax.add_patch(FancyArrowPatch(
        pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=ms,
        color=color, lw=lw, shrinkA=0, shrinkB=0, zorder=2))


def _dim(ax, x, y, t, fs=7.5, ha="left"):
    ax.text(x, y, t, fontsize=fs, ha=ha, va="center", zorder=6,
            bbox=dict(fc="white", ec="none", pad=0.4))


def _stack(ax, x, y, size, n=5, grey=False):
    """叠层图块：从后往前画，每层偏移一点。"""
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


# ---------------------------------------------------------------- 05 架构图

def fig05_arch():
    fig = plt.figure(figsize=(13.24, 5.66))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 230)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.axis("off")

    # 分隔线
    ax.plot([124.5, 124.5], [0, 100], ls=(0, (4, 3)), color="k", lw=1.5, zorder=1)
    ax.plot([0, 123], [56, 56], ls=(0, (4, 3)), color="k", lw=1.5, zorder=1)

    # ============ (a) 分块自回归训练 ============
    cx = [14, 43, 72, 101]
    for i, x in enumerate(cx):
        _stack(ax, x, 82, 21, grey=(i == 3))
    tv = ["0", "0.2", "0.7", "1"]
    for i, x in enumerate(cx):
        ax.text(x, 68.0, r"$Block_{%d}^{t=%s}$" % (i, tv[i]),
                ha="center", va="top", fontsize=11.5, style="italic")

    # 6 条弧线：起于块 i 顶边右侧，止于块 j 顶边左侧
    for i in range(4):
        for j in range(i + 1, 4):
            d = j - i
            ax.add_patch(FancyArrowPatch(
                (cx[i] + 8.0, 96.2), (cx[j] - 8.0, 96.2),
                connectionstyle="arc3,rad=-%.3f" % (0.13 * d + 0.018 * d * d),
                arrowstyle="-|>", mutation_scale=9, color="k",
                lw=1.1, shrinkA=0, shrinkB=0, zorder=3))

    ax.text(60, 59.5, "(a). Block-wise autoregressive training pipeline",
            ha="center", va="bottom", fontsize=13.5, fontweight="bold")

    # ============ (b) 整体架构 ============
    _stack(ax, 13, 30, 17, n=5)
    ax.text(13, 17.5, r"$[1\!+\!T, H, W, 3]$", ha="center", va="top", fontsize=11)

    # AutoEncoder：右侧收窄梯形
    ax.add_patch(Polygon([[30, 21.5], [57, 25.0], [57, 35.0], [30, 38.5]], closed=True,
                         fc="#E8EEF6", ec=C_BK, lw=1.5, zorder=2))
    ax.text(43.5, 30, "AutoEncoder", ha="center", va="center", fontsize=12.5, zorder=4)

    _arw(ax, [(22, 30), (30, 30)], lw=1.9, ms=13)
    _arw(ax, [(57, 30), (63.5, 30)], lw=1.9, ms=13)

    # N× 主框
    ax.add_patch(FancyBboxPatch((63.5, 15.5), 56, 29,
                                boxstyle="round,pad=0,rounding_size=2.6",
                                fc=C_BLUE, ec=C_BK, lw=1.9, zorder=2))
    ax.text(64.5, 16.8, r"$\mathbf{N\times}$", ha="left", va="bottom",
            fontsize=13.5, color="#8C1D23", zorder=5)
    # 三条竖带
    for x0, w0, fc, txt in [(70, 12.5, "#DCEBF8", "Linear Attn"),
                            (87, 12.5, C_PINK, "Cross Attn"),
                            (104, 12.5, C_GRN, "Mix FFN")]:
        ax.add_patch(Rectangle((x0, 17.5), w0, 25, fc=fc, ec="none", zorder=2,
                               alpha=0.95))
        ax.text(x0 + w0 / 2, 30, txt, ha="center", va="center", fontsize=11.5,
                rotation=90, zorder=4)
    _arw(ax, [(82.5, 30), (87, 30)], lw=1.3, ms=9)
    _arw(ax, [(99.5, 30), (104, 30)], lw=1.3, ms=9)
    _arw(ax, [(116.5, 30), (119.5, 30)], lw=1.3, ms=9)
    ax.add_patch(Circle((121.8, 30), 2.0, fc="white", ec=C_BK, lw=1.5, zorder=5))
    ax.text(121.8, 30, "+", ha="center", va="center", fontsize=14, zorder=6)
    _arw(ax, [(123.8, 30), (124, 30)], lw=1.6, ms=11)

    # 雪花
    sx, sy = 61, 42.5
    for a in range(0, 180, 30):
        rad = np.deg2rad(a)
        for sgn in (1, -1):
            ax.plot([sx, sx + sgn * 2.8 * np.cos(rad)], [sy, sy + sgn * 2.8 * np.sin(rad)],
                    color="#86BEDB", lw=2.0, solid_capstyle="round", zorder=3)
    ax.add_patch(Circle((sx, sy), 0.6, fc="#86BEDB", ec="none", zorder=4))

    # 文本分支
    yrow = 9.4
    ax.add_patch(FancyBboxPatch((2.5, yrow - 3.8), 30, 7.6,
                                boxstyle="round,pad=0,rounding_size=1.6",
                                fc="white", ec=C_BK, lw=1.4, zorder=3))
    ax.text(17.5, yrow, 'A cyberpunk cat with a\nsian that says "SANA"',
            ha="center", va="center", fontsize=8.6, style="italic", zorder=4,
            linespacing=1.25)
    _box(ax, 47, yrow, 19, 6.0, "Rewriter", C_PINK, fs=10.5)
    _box(ax, 75, yrow, 21, 6.0, "Small LLM", C_PINK, fs=10.5)
    _box(ax, 103, yrow, 18, 6.0, "Time Emb", C_PINK, fs=10.5)
    _arw(ax, [(32.5, yrow), (37.5, yrow)], lw=1.7, ms=12)
    _arw(ax, [(56.5, yrow), (64.5, yrow)], lw=1.7, ms=12)
    _arw(ax, [(85.5, yrow), (94, yrow)], lw=1.7, ms=12)
    _arw(ax, [(75, yrow + 3.2), (75, 13.2), (84, 13.2), (84, 15.3)], lw=1.7, ms=12)
    _arw(ax, [(103, yrow + 3.2), (103, 13.2), (110, 13.2), (110, 15.3)], lw=1.7, ms=12)

    ax.text(60, 0.4, "(b). Architecture overview of our SANA-Video.",
            ha="center", va="bottom", fontsize=13.5, fontweight="bold")

    # ============ (c) Linear DiT 模块 ============
    # 面板底
    ax.add_patch(FancyBboxPatch((127, 12), 53, 82,
                                boxstyle="round,pad=0,rounding_size=3.5",
                                fc=C_BLUE, ec="none", zorder=1))
    ax.add_patch(FancyBboxPatch((184, 12), 44, 82,
                                boxstyle="round,pad=0,rounding_size=3.5",
                                fc=C_BLUE, ec="none", zorder=1))
    ax.text(153.5, 96.5, "Linear Attention", ha="center", va="bottom",
            fontsize=13.5, fontweight="bold")
    ax.text(206, 96.5, "Mix-FFN", ha="center", va="bottom",
            fontsize=13.5, fontweight="bold")
    ax.text(178, 7.4, "(c). Linear DiT module", ha="center", va="bottom",
            fontsize=13.5, fontweight="bold")

    # ---- Linear Attention 内部 ----
    xL, xM, xR = 136, 152, 168      # 三列 x
    yQ, yLin, yReLU, yRoPE = 20.5, 26, 36.5, 47
    yMMlow, yMMup, yScale = 60, 69.5, 79.5

    _box(ax, xL, yLin, 13, 6.2, "Linear", "white", fs=10)
    _box(ax, xM, yLin, 13, 6.2, "Linear", "white", fs=10)
    _box(ax, xR, yLin, 13, 6.2, "Linear", "white", fs=10)
    _box(ax, xL, yReLU, 13, 6.2, "ReLU", C_RELU, fs=10)
    _box(ax, xM, yReLU, 13, 6.2, "ReLU", C_RELU, fs=10)
    _box(ax, xL, yRoPE, 14, 6.6, "3D RoPE", C_ROPE, fs=10)
    _box(ax, xM, yRoPE, 14, 6.6, "3D RoPE", C_ROPE, fs=10)
    _box(ax, 148, yMMup, 30, 6.4, "MatMul", C_MM, fs=10.5)
    _box(ax, 160, yMMlow, 30, 6.4, "MatMul", C_MM, fs=10.5)
    _box(ax, xL + 6.5, yScale, 16, 6.6, "Scale", C_SCALE, fs=10.5)

    # Q K V 输入箭头
    for x, t in [(xL, "Q"), (xM, "K"), (xR, "V")]:
        ax.text(x, 16.2, t, ha="center", va="center", fontsize=10.5, style="italic")
        _arw(ax, [(x, 18.2), (x, yLin - 3.1)], lw=1.25, ms=8)
    # Linear → ReLU
    for x in (xL, xM):
        _arw(ax, [(x, yLin + 3.1), (x, yReLU - 3.1)], lw=1.25, ms=8)
    # ReLU → RoPE
    for x in (xL, xM):
        _arw(ax, [(x, yReLU + 3.1), (x, yRoPE - 3.3)], lw=1.25, ms=8)
    # RoPE(左) → MatMul(上)  纯垂直
    _arw(ax, [(xL, yRoPE + 3.3), (xL, yMMup - 3.2)], lw=1.25, ms=8)
    # RoPE(中) → MatMul(下)  纯垂直
    _arw(ax, [(xM, yRoPE + 3.3), (xM, yMMlow - 3.2)], lw=1.25, ms=8)
    # Linear(V) → MatMul(下) 纯垂直（穿过右列）
    _arw(ax, [(xR, yLin + 3.1), (xR, yMMlow - 3.2)], lw=1.25, ms=8)
    # MatMul(下) → MatMul(上)：两者水平重叠，纯垂直短箭头
    _arw(ax, [(155, yMMlow + 3.2), (155, yMMup - 3.2)], lw=1.25, ms=8)
    # MatMul(上) → Scale → 输出
    _arw(ax, [(xL + 6.5, yMMup + 3.2), (xL + 6.5, yScale - 3.3)], lw=1.25, ms=8)
    _arw(ax, [(xL + 6.5, yScale + 3.3), (xL + 6.5, 89)], lw=1.25, ms=8)

    # 尺寸标签（贴着竖线右侧，白底）
    _dim(ax, xL + 0.9, (yRoPE + yMMup) / 2 + 2, r"$n\times d$")
    _dim(ax, xM + 0.9, (yRoPE + yMMlow) / 2, r"$d\times n$")
    _dim(ax, xR + 0.9, (yLin + yMMlow) / 2 + 6, r"$n\times d$")
    _dim(ax, 143.5, (yMMlow + yMMup) / 2, r"$n\times d$", ha="right")
    _dim(ax, 156.6, (yMMlow + yMMup) / 2, r"$d\times d$")
    _dim(ax, xL + 7.6, (yLin + yReLU) / 2 + 1, r"$n\times d$")
    _dim(ax, xM + 7.6, (yLin + yReLU) / 2 + 1, r"$d\times n$")
    ax.text(153.5, 14.0, r"Cost: $\mathcal{O}(n)$", ha="center", va="bottom",
            fontsize=10.5)

    # ---- Mix-FFN 内部 ----
    xc = 206
    y_b1, y_b2, y_b3, y_ot, y_silu, y_c1, y_temp = 20, 29.5, 40, 50, 46, 60, 71
    _box(ax, xc, y_b1, 26, 6.2, "1 x 1 ConvLayer", C_GRN, fs=10)
    _box(ax, xc, y_b2, 26, 7.4, "1 x 3 x 3\nConvLayer", C_GRN, fs=10)
    _box(ax, 214, y_silu, 14, 6.2, "SiLU", C_RELU, fs=10)
    _box(ax, xc, y_c1, 26, 6.2, "1 x 1 ConvLayer", C_GRN, fs=10)
    _box(ax, xc, y_temp, 26, 9.0, "Temporal\n3 x 1 x 1 ConvLayer", C_ROPE, fs=9.6)

    _arw(ax, [(xc, 16.2), (xc, y_b1 - 3.1)], lw=1.25, ms=8)
    _arw(ax, [(xc, y_b1 + 3.1), (xc, y_b2 - 3.7)], lw=1.25, ms=8)
    # 分叉：中点 → 上（到 ⊗）与 右（到 SiLU）
    ax.plot([xc, xc], [y_b2 + 3.7, 45], color="k", lw=1.25, zorder=2)
    ax.plot([xc, 200], [45, 45], color="k", lw=1.25, zorder=2)
    _arw(ax, [(200, 45), (200, y_silu - 3.1)], lw=1.25, ms=8)
    # ⊗
    ax.add_patch(Circle((198, y_ot), 2.4, fc="white", ec=C_BK, lw=1.5, zorder=5))
    ax.text(198, y_ot, r"$\otimes$", ha="center", va="center", fontsize=13, zorder=6)
    _arw(ax, [(xc, 45), (xc, y_ot - 2.6)], lw=1.25, ms=8)
    ax.plot([xc, xc], [y_b2 + 3.7, 45], color="k", lw=1.25, zorder=2)
    # SiLU → ⊗（水平左向）
    _arw(ax, [(207.6, y_silu), (204.6, y_silu), (204.6, y_ot), (200.6, y_ot)],
         lw=1.25, ms=8)
    # ⊗ → ConvLayer → Temporal
    _arw(ax, [(198, y_ot + 2.6), (198, y_c1 - 3.1)], lw=1.25, ms=8)
    ax.plot([198, 198], [y_ot + 2.6, y_c1 - 3.1], color="k", lw=1.25, zorder=2)
    _arw(ax, [(xc, y_c1 + 3.1), (xc, y_temp - 4.6)], lw=1.25, ms=8)
    # Temporal 输出 + 右侧残差回路
    _arw(ax, [(xc, y_temp + 4.6), (xc, 89)], lw=1.25, ms=8)
    ax.plot([226, 226], [83, y_temp], color="k", lw=1.25, zorder=2)
    ax.plot([226, xc + 13.2], [83, 83], color="k", lw=1.25, zorder=2)
    _arw(ax, [(226, y_temp), (xc + 13.2, y_temp)], lw=1.25, ms=8)

    return _save_ar(fig, "rep-05-architecture", 2.30)


if __name__ == "__main__":
    print(fig05_arch())


# ---------------------------------------------------------------- 06 机制图

C_GRN2 = "#78B808"
C_KV = "#A81838"
C_MASK2 = "#B4B4B4"
C_CELL = "#DCEBF8"
C_PAD = "#1B6FD6"


def _grid(ax, x0, y0, cw, ch, ncols, nrows, colors_fn, lw=1.8):
    """画 nrows×ncols 网格，colors_fn(r,c) 返回填充色。"""
    for r in range(nrows):
        for c in range(ncols):
            ax.add_patch(Rectangle(
                (x0 + c * cw, y0 + (nrows - 1 - r) * ch), cw, ch,
                fc=colors_fn(r, c), ec="black", lw=lw, zorder=3))


def fig06_mech():
    fig = plt.figure(figsize=(14.06, 4.38))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 321)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.axis("off")

    # ================= 图例 =================
    ly, lh = 94.6, 4.8
    lx = 30
    for fc, txt in [("white", "Token"), (C_MASK2, "Mask"),
                    (C_KV, "KV Cache"), (C_GRN2, "Compute")]:
        ax.add_patch(Rectangle((lx, ly), lh, lh, fc=fc, ec="black", lw=1.3, zorder=3))
        ax.text(lx + lh + 1.4, ly + lh / 2, txt, ha="left", va="center", fontsize=10)
        lx += lh + 2.6 + len(txt) * 1.72

    # 竖向虚线分隔
    for x in (98, 162, 250, 258):
        ax.plot([x, x], [8, 86], ls=(0, (3, 2.5)), color="k", lw=1.4, zorder=1)

    # ================= 1. Vanilla Attention =================
    gx, gy, cw, ch = 8.0, 20.0, 15.4, 15.4
    _grid(ax, gx, gy, cw, ch, 4, 4, lambda r, c: C_GRN2)
    # Q 标签
    for i, r in enumerate([0, 3]):
        ax.text(gx - 3.0, gy + (3 - r) * ch + ch / 2, r"$Q_%d$" % (1 if r == 0 else 4),
                ha="right", va="center", fontsize=10.5)
    for r in (1, 2):
        ax.text(gx - 3.0, gy + (3 - r) * ch + ch / 2, r"$\vdots$",
                ha="right", va="center", fontsize=10)
    # K 表头
    ax.text(gx + cw * 0.5, gy + 4 * ch + 3.0, r"$K_1$", ha="center", va="bottom", fontsize=10.5)
    ax.text(gx + cw * 3.5, gy + 4 * ch + 3.0, r"$K_N$", ha="center", va="bottom", fontsize=10.5)
    for c in (1, 2):
        ax.text(gx + (c + 0.5) * cw, gy + 4 * ch + 3.0, r"$\cdots$",
                ha="center", va="bottom", fontsize=10)
    ax.text(gx + 2 * cw, 15.5, "Vanilla Attention", ha="center", va="top", fontsize=12)

    # ×
    ax.text(gx + 4 * cw + 2.2, gy + 2 * ch, r"$\times$", ha="center", va="center",
            fontsize=21, fontweight="bold")

    # V 列
    vx = gx + 4 * cw + 13.5
    _grid(ax, vx, gy, cw, ch, 1, 4, lambda r, c: C_CELL)
    ax.text(vx + cw / 2, gy + 4 * ch + 3.0, "d", ha="center", va="bottom", fontsize=10.5)
    for i in range(4):
        ax.text(vx + cw / 2, gy + (3 - i) * ch + ch / 2, r"$V_%d$" % (i + 1),
                ha="center", va="center", fontsize=9.5)
    ax.text(vx - 2.6, gy + 2 * ch, "N", ha="right", va="center", fontsize=10.5)

    # ================= 2. Linear Attention =================
    lx2 = 104.0
    ch2 = ch / 2.0
    _grid(ax, lx2, gy, cw, ch2, 1, 8, lambda r, c: C_CELL)
    ax.text(lx2 + cw / 2, gy + 8 * ch2 + 3.0, "d", ha="center", va="bottom", fontsize=10.5)
    ax.text(lx2 - 3.0, gy + 4 * ch2, "N", ha="right", va="center", fontsize=10.5)
    for i in range(4):
        ax.text(lx2 + cw / 2, gy + (7 - i) * ch2 + ch2 / 2, r"$Q_%d$" % (i + 1),
                ha="center", va="center", fontsize=9.2)
        ax.text(lx2 + cw / 2, gy + (3 - i) * ch2 + ch2 / 2, r"$V_%d$" % (i + 1),
                ha="center", va="center", fontsize=9.2)
    # 左侧大括号（用折线近似）
    for y0b, y1b, lbl, xb in [(gy + 4 * ch2 + 1.0, gy + 8 * ch2 - 1.0, "Block$_1$", lx2 - 4.2),
                              (gy + 1.0, gy + 4 * ch2 - 1.0, "Block$_N$", lx2 - 4.2)]:
        ax.plot([xb, xb - 1.3, xb - 1.3, xb], [y1b, y1b, y0b, y0b], color="k", lw=1.1, zorder=4)
        ax.text(xb - 1.2, (y0b + y1b) / 2, lbl, ha="center", va="center", fontsize=7.6, rotation=90)

    ax.text(lx2 + cw + 5.2, gy + 4 * ch2, r"$\times$", ha="center", va="center",
            fontsize=21, fontweight="bold")

    # Σ 小方块
    sx, sy = lx2 + cw + 12.0, gy + 4 * ch2 - 8.5
    ax.add_patch(Rectangle((sx, sy), 17, 17, fc=C_GRN2, ec="black", lw=1.3, zorder=3))
    ax.text(sx + 8.5, sy + 8.5, r"$\sum_{i=1}^{k}K_iV_i$", ha="center", va="center", fontsize=9)
    ax.text(sx + 8.5, sy + 19.0, "d", ha="center", va="bottom", fontsize=10.5)
    ax.text(sx + 19.2, sy + 8.5, "d", ha="left", va="center", fontsize=10.5)
    ax.text(lx2 + cw / 2, 15.5, "Linear Attention", ha="center", va="top", fontsize=12)

    # ================= 3. Causal Linear Attention =================
    cx0 = 180.0
    ax.text(cx0 + 2 * cw, gy + 4 * ch + 3.0, "d", ha="center", va="bottom", fontsize=10.5)
    ax.text(cx0 - 12.5, gy + 3 * ch, "d", ha="center", va="center", fontsize=10.5)

    def _causal(r, c):
        if c == r + 1:
            return C_GRN2
        if c <= r:
            return C_KV
        return C_MASK2

    _grid(ax, cx0, gy, cw, ch, 4, 4, _causal)
    # 白色累加箭头 + Σ 标签
    for r in range(3):
        yy = gy + (3 - r) * ch + ch / 2
        ax.annotate("", xy=(cx0 + (r + 0.9) * cw, yy), xytext=(cx0 + 0.15 * cw, yy),
                    arrowprops=dict(arrowstyle="-|>", color="white", lw=2.0,
                                    mutation_scale=11), zorder=6)
        ax.text(cx0 + (r + 1.5) * cw, yy + 2.2, r"$\sum_{i=1}^{%d}K_iV_i$" % (r + 1),
                ha="center", va="bottom", fontsize=7.4, zorder=7,
                bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.85))
    ax.text(cx0 + 0.9 * cw, gy + 0.5 * ch, "Cumulative Sum", ha="left", va="center",
            fontsize=9.4, color="white", fontweight="bold", zorder=7)

    # 左侧大括号
    for y0b, y1b, lbl in [(gy + 2 * ch + 1.0, gy + 4 * ch - 1.0, "Block$_1$"),
                          (gy + 1.0, gy + 2 * ch - 1.0, "Block$_N$")]:
        xb = cx0 - 6.0
        ax.plot([xb, xb - 1.3, xb - 1.3, xb], [y1b, y1b, y0b, y0b], color="k", lw=1.1, zorder=4)
        ax.text(xb - 2.2, (y0b + y1b) / 2, lbl, ha="right", va="center",
                fontsize=8.2, rotation=90)
    ax.text(cx0 + 2 * cw, 15.5, "Causal Linear Attention", ha="center", va="top", fontsize=12)

    # ================= 4. Block Causal Mix-FFN =================
    bx = 272.0
    bw, bh = 30.0, 7.4
    rows = [("Token-2", C_GRN2, "white"), ("Token-1", C_GRN2, "white"),
            ("Zero Padding", C_PAD, "white"), (None, None, None),
            ("Cached Token-1", C_KV, "white"), ("Token$_0$", C_GRN2, "white"),
            ("Token$_1$", C_GRN2, "white")]
    ycur = gy + 4 * ch + 2.0
    ys = {}
    for name, fc, tc in rows:
        if name is None:
            ycur -= 4.6
            continue
        ycur -= bh
        ax.add_patch(FancyBboxPatch((bx, ycur), bw, bh,
                                    boxstyle="round,pad=0,rounding_size=1.5",
                                    fc=fc, ec="black", lw=1.5, zorder=3))
        ax.text(bx + bw / 2, ycur + bh / 2, name, ha="center", va="center",
                fontsize=10.5, fontweight="bold", color=tc, zorder=4)
        ys[name] = ycur + bh / 2
        ycur -= 1.4
    # 上下点线
    for yy in (ycur + bh + 8.0, ycur + 0.6):
        ax.plot([bx + bw / 2] * 2, [yy, yy + 5.0], ls=(0, (2, 2)), color="k", lw=1.6)
    # 大括号
    for y0b, y1b, lbl in [(ys["Token-1"] - bh / 2 - 1.0, ys["Token-2"] + bh / 2 + 1.0, "Block$_1$"),
                          (ys["Token$_1$"] - bh / 2 - 1.0, ys["Cached Token-1"] + bh / 2 + 1.0, "Block$_2$")]:
        xb = bx - 4.0
        ax.plot([xb, xb - 1.4, xb - 1.4, xb], [y1b, y1b, y0b, y0b], color="k", lw=1.2, zorder=4)
        ax.text(xb - 2.4, (y0b + y1b) / 2, lbl, ha="right", va="center",
                fontsize=8.6, rotation=90, fontweight="bold")
    # 蓝色弧形箭头 Token-1 → Cached Token-1
    ax.add_patch(FancyArrowPatch(
        (bx + bw + 0.8, ys["Token-1"]), (bx + bw + 0.8, ys["Cached Token-1"]),
        connectionstyle="arc3,rad=-0.55", arrowstyle="-|>", mutation_scale=13,
        color=C_PAD, lw=2.0, shrinkA=0, shrinkB=0, zorder=5))

    # ================= 底部说明 =================
    ax.text(112, 3.2, "(a) Block Causal Linear Attention", ha="center", va="bottom",
            fontsize=13, fontweight="bold")
    ax.text(283, 3.2, "(b) Block Causal Mix-FFN", ha="center", va="bottom",
            fontsize=13, fontweight="bold")

    return _save_ar(fig, "rep-06-mechanism", 3.21)

