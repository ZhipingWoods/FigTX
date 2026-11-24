#!/usr/bin/env python3
r"""论文图复刻（1:1）：按参考图逐项复刻布局、配色、标注。

每个函数返回保存路径；函数源码会作为「完整代码」展示在卡片里。
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

from common import OUT_FIG  # noqa: E402

# 参考图统一风格
RC = {
    "figure.dpi": 120,
    "savefig.dpi": 300,                 # 投稿级
    "font.family": "serif",
    "font.serif": ["Palatino", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "dejavuserif",
    "font.size": 9,
    "axes.linewidth": 1.1,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "axes.spines.top": False,
    "axes.spines.right": False,
}

# 色值来自对参考图的像素统计（data/ref-analysis.json），误差 < 10 RGB
TEAL = "#08A8B8"      # 01 主色
YELLOW = "#E8B800"    # 01 中段
DRED = "#8C1D2F"      # 01/02/07 深红
DRED2 = "#781828"     # 02 实测
GRAY = "#585858"      # 01 梯度
MGRAY = "#888888"     # 02 BF16
LGRAY = "#A6A6A6"
NAVY = "#2F3A4F"
BLUE = "#3E8FB8"
MBLUE = "#7BB6B6"
SAGE = "#C8D5B9"
SAND = "#F5E6A8"
MAUVE = "#8B7A9E"
GREEN = "#7CB342"
HGREEN = "#38D888"    # 07 热图主色
GGRN = "#98C838"      # 03 柱状
SGY = "#A8B8B8"       # 04 横条灰绿
RED8 = "#A82818"      # 08 深红



def _save(fig, name):
    os.makedirs(OUT_FIG, exist_ok=True)
    p = os.path.join(OUT_FIG, name + ".png")
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def _hbar_stacked(ax, rows, segments, colors, ypos, height=0.78):
    """横向堆叠条。rows=[(label, [v1..vn], total_text)]"""
    for y, (label, vals, total) in zip(ypos, rows):
        left = 0.0
        for v, c in zip(vals, colors):
            ax.barh(y, v, left=left, height=height, color=c, edgecolor="white", linewidth=0.8)
            if v > 0.4:
                ax.text(left + v / 2, y, ("%g" % round(v, 2)).rstrip("0").rstrip("."),
                        ha="center", va="center", color="white", fontsize=11)
            left += v
        ax.text(left + 0.5, y, total, ha="left", va="center", fontsize=9, color="#333333")
    ax.set_yticks(ypos, [r[0] for r in rows])


# ---------------------------------------------------------------- 01 显存/延迟分解

def fig01():
    # 参考图 AR≈3.98；子图说明放在坐标区下方（不是 title）
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 3.76),
                                   gridspec_kw=dict(width_ratios=[1.34, 1.0], wspace=0.16))

    # ---- (a) 显存分解
    seg_cols = [TEAL, YELLOW, DRED, GRAY]
    rows = [
        ("BF16 LoRA", [22.59, 1.88, 2.02, 0.46], "26.95 GB"),
        ("NF4 QLoRA", [6.04, 1.88, 2.02, 0.46], "10.40 GB"),
        ("FourTune\n(Ours)", [7.71, 1.83, 2.00, 0.46], "12.00 GB"),
    ]
    ypos = [2, 1, 0]
    _hbar_stacked(ax1, rows, None, seg_cols, ypos)
    ax1.set_xlim(0, 33.5)
    ax1.set_ylim(-0.80, 2.55)
    ax1.set_xticks([])          # 参考图左侧无 x 轴刻度
    ax1.set_xlabel("")
    for sp in ("top", "right", "bottom"):
        ax1.spines[sp].set_visible(False)
    ax1.tick_params(axis="y", length=0, labelsize=11.5)

    # 图例放在短条右侧的空白区（参考图位置）
    handles = [Rectangle((0, 0), 1, 1, fc=c, ec="none") for c in seg_cols]
    ax1.legend(handles, ["Weight", "Forward Act.", "Backward Act.", "Gradient"],
               loc="center left", bbox_to_anchor=(0.72, 0.47), frameon=False, fontsize=10.5,
               handlelength=1.1, handleheight=0.8, borderpad=0.2, labelspacing=0.28)

    # 参考虚线 + 2.25x
    xref = 26.95
    ax1.plot([xref, xref], [2.30, -0.50], ls=(0, (2, 1.6)), lw=1.0, color=DRED)
    ax1.annotate("", xy=(12.0, -0.50), xytext=(xref, -0.50),
                 arrowprops=dict(arrowstyle="-|>", color=DRED, lw=1.1,
                                 mutation_scale=13, shrinkA=0, shrinkB=0))
    ax1.text((xref + 12.0) / 2, -0.40, "2.25×", color=DRED, fontsize=14,
             ha="center", va="bottom")
    ax1.set_xlabel("(a) GPU Memory Breakdown (GB) during\n"
                   "FLUX.1-dev Customization (1 × 1024 × 1024)",
                   fontsize=14, labelpad=10)

    # ---- (b) 端到端延迟
    lat = [("FourTune (Ours)", 0.86, DRED), ("NF4 QLoRA", 2.40, TEAL), ("BF16 LoRA", 1.95, GRAY)]
    for y, (lab, v, c) in zip([0, 1, 2], lat):
        ax2.barh(y, v, height=0.95, color=c, edgecolor="none")
        ax2.text(v - 0.05, y, ("%g s" % v), ha="right", va="center",
                 color="white", fontsize=13)
    # 参考图：类别标签在条形右侧
    ax2.set_yticks([0, 1, 2], [])
    ax2.set_xlim(0, 3.35)
    ax2.set_ylim(-0.62, 2.5)
    ax2.set_xticks([])
    for sp in ("top", "right"):
        ax2.spines[sp].set_visible(False)
    ax2.spines["left"].set_linewidth(1.4)
    ax2.tick_params(axis="y", length=4)
    for y, lab in [(0, "FourTune (Ours)"), (1, "NF4 QLoRA"), (2, "BF16 LoRA")]:
        val = {0: 0.86, 1: 2.40, 2: 1.95}[y]
        ax2.text(val + (2.42 - val) * 0 + 0.12 if y == 0 else val + 0.12, y, lab,
                 va="center", ha="left", fontsize=12.5)

    # 虚线连接：BF16 末端 → NF4 行；NF4 末端 → 下方
    ax2.plot([1.95, 1.95], [2.26, 1.0], ls=(0, (3, 2)), lw=0.9, color=GRAY)
    ax2.plot([2.40, 2.40], [1.26, 0.0], ls=(0, (3, 2)), lw=0.9, color=TEAL)

    ax2.annotate("", xy=(0.86, 0.52), xytext=(1.95, 0.52),
                 arrowprops=dict(arrowstyle="<|-", color="#555555", lw=0.9,
                                 mutation_scale=11, shrinkA=0, shrinkB=0))
    ax2.text(1.40, 0.60, "2.27×", ha="center", va="bottom", fontsize=15, color="#444444")

    ax2.annotate("", xy=(0.86, 0.20), xytext=(2.40, 0.20),
                 arrowprops=dict(arrowstyle="<|-", color=TEAL, lw=0.9,
                                 mutation_scale=11, shrinkA=0, shrinkB=0))
    ax2.text(1.62, 0.27, "2.79×", ha="center", va="bottom", fontsize=15, color=TEAL)

    ax2.set_xlabel("(b) End-to-End Training Step Latency (s) during\n"
                    "FLUX.1-dev Customization (1 × 1024 × 1024)",
                    fontsize=14, labelpad=10)
    fig.subplots_adjust(bottom=0.30, top=0.94, left=0.10, right=0.99)
    return _save(fig, "rep-01-memory-latency")


# ---------------------------------------------------------------- 02 逐项融合增益

def fig02():
    fig, ax = plt.subplots(figsize=(6.4, 4.54))  # AR≈1.53
    labels = ["BF16", "4-Bit\nw/o Fusion", "+ LoRA Fusion", "+ MLP Fusion\n(Ours)"]
    vals = [1541.0, 1233.8, 676.7, 612.4]
    cols = [LGRAY, DRED, DRED, DRED]
    ypos = [3, 2, 1, 0]
    for y, v, c in zip(ypos, vals, cols):
        ax.barh(y, v, height=0.78, color=c, edgecolor="none")
        ax.text(v + 26, y, "%.1f" % v, ha="left", va="center", fontsize=8.6, color="#333333")
    ax.set_yticks(ypos, labels)
    ax.set_xlim(0, 1880)
    ax.set_ylim(-0.75, 3.62)
    ax.set_xticks([])
    for sp in ("left", "bottom", "top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)

    # 参考虚线
    ax.plot([1541, 1541], [3.3, -0.55], ls=(0, (3, 2)), lw=1.0, color="#7A7A7A")

    # 相邻增益（弧形箭头 + 倍数）
    gains = [(2, 1, "1.82×", 0.0), (1, 0, "1.10×", 0.0)]
    # 1.25x：从 BF16 末端到 4-Bit 行（右上弧）
    # 参考图：箭头从上一根条末端向右外弧，再回指当前条末端
    ax.annotate("", xy=(1233.8, 2.22), xytext=(1541, 3.10),
                arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1.05,
                                connectionstyle="arc3,rad=-0.38", mutation_scale=12,
                                shrinkA=2, shrinkB=2))
    ax.text(1408, 2.62, "1.25×", color=TEAL, fontsize=11, ha="center")

    ax.annotate("", xy=(676.7, 1.22), xytext=(1233.8, 2.10),
                arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1.05,
                                connectionstyle="arc3,rad=-0.38", mutation_scale=12,
                                shrinkA=2, shrinkB=2))
    ax.text(944, 1.62, "1.82×", color=TEAL, fontsize=11, ha="center")

    ax.annotate("", xy=(612.4, 0.22), xytext=(676.7, 1.10),
                arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1.05,
                                connectionstyle="arc3,rad=-0.42", mutation_scale=12,
                                shrinkA=2, shrinkB=2))
    ax.text(830, 0.55, "1.10×", color=TEAL, fontsize=11, ha="left")

    # 总加速 2.52x
    ax.annotate("", xy=(1541, -0.55), xytext=(612.4, -0.55),
                arrowprops=dict(arrowstyle="<|-|>", color=TEAL, lw=1.2,
                                mutation_scale=11, shrinkA=0, shrinkB=0))
    ax.text(1078, -0.44, "2.52×", color=TEAL, fontsize=13, ha="center", va="bottom",
            fontweight="bold")

    ax.set_title("DiT Training Per-Step Latency (ms) on Single RTX 5090",
                 fontsize=10.5, fontweight="bold", pad=10)

    # 原图左下角有 Figure 9 的说明文字块
    fig.text(0.012, 0.015,
             "Figure 9.  Breakdown of efficiency gains from different kernel\n"
             "fusion strategies. The combined optimization results in a 2.52$\\times$\n"
             "speedup relative to 16-bit LoRA fine-tuning.",
             ha="left", va="bottom", fontsize=14, style="italic", linespacing=1.5)
    fig.subplots_adjust(bottom=0.30)
    return _save(fig, "rep-02-fusion-gain")


# ---------------------------------------------------------------- 03 权衡曲线 + 断轴

def fig03():
    fig = plt.figure(figsize=(13.4, 4.82))
    gs = fig.add_gridspec(2, 3, height_ratios=[0.14, 1.0], hspace=0.02, wspace=0.26)
    axleg = fig.add_subplot(gs[0, :]); axleg.axis("off")

    x = np.arange(50, 700, 100)
    series = [
        ("BF16", NAVY, "o", [74.8, 75.1, 75.3, 74.9, 74.2, 73.6, 72.5]),
        ("RTN", BLUE, "s", [74.9, 74.6, 73.4, 71.6, 69.6, 65.8, 60.4]),
        ("KIVI", MBLUE, "s", [74.9, 74.8, 73.6, 72.2, 70.4, 67.4, 61.2]),
        ("Quarot", SAGE, "s", [74.8, 73.4, 69.8, 66.0, 64.4, 62.6, 59.0]),
        ("QVG", SAND, "^", [74.6, 74.4, 73.9, 73.6, 72.6, 71.2, 68.6]),
        ("QVG-Pro", MAUVE, "^", [74.7, 74.5, 74.3, 74.1, 73.7, 72.4, 68.0]),
    ]
    h_leg = []
    for name, c, m, yv in series:
        h_leg.append(Line2D([], [], color=c, marker=m, ms=7.5, lw=2.1,
                            markerfacecolor="white" if m == "s" else c,
                            markeredgewidth=1.7, label=name))
    axleg.legend(handles=h_leg, loc="center", bbox_to_anchor=(0.36, 0.5), ncol=6,
                 frameon=False, fontsize=9.5, handlelength=1.0, columnspacing=1.8)

    def draw(ax, ymin, ymax, cache):
        for name, c, m, yv in series:
            ax.plot(x, yv, color=c, marker=m, ms=8.0, lw=2.6,
                    markerfacecolor="white" if m == "s" else c, markeredgewidth=2.0)
        ax.set_xlim(30, 690)
        ax.set_ylim(ymin, ymax)
        ax.set_xticks(x)
        ax.set_xlabel("%s KV Cache" % cache, fontsize=11)
        ax.grid(False)
        ax.tick_params(labelsize=10.5, length=5.5, width=1.4)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_linewidth(1.5)

    ax1 = fig.add_subplot(gs[1, 0])
    draw(ax1, 56, 76, "INT2")
    ax1.set_ylabel("Imaging Quality", fontsize=10)
    ax1.set_yticks([56, 61, 66, 71, 76])
    ax1.set_title("(a)", y=-0.30, fontsize=10.5)

    ax2 = fig.add_subplot(gs[1, 1])
    draw(ax2, 66, 76, "INT4")
    ax2.set_yticks([66, 68.5, 71, 73.5, 76])
    ax2.set_yticklabels(["66", "68.5", "71", "73.5", "76"])
    ax2.set_title("(b)", y=-0.30, fontsize=10.5)

    # (c) 断轴柱状
    gs_c = gs[1, 2].subgridspec(2, 1, height_ratios=[1.0, 0.62], hspace=0.06)
    axc_top = fig.add_subplot(gs_c[0])
    axc_bot = fig.add_subplot(gs_c[1])
    st = np.arange(1, 9)
    vals = np.array([5.83, 1.29, 1.19, 1.15, 1.13, 1.11, 1.10, 1.09])
    for ax, ylim in [(axc_top, (5.4, 6.6)), (axc_bot, (1.0, 1.42))]:
        ax.bar(st, vals, width=0.86, color=GREEN, edgecolor="black", linewidth=1.4)
        ax.set_xlim(0.4, 8.6)
        ax.set_ylim(*ylim)
    axc_top.spines["bottom"].set_visible(False)
    axc_top.tick_params(axis="x", bottom=False, labelbottom=False)
    axc_bot.spines["top"].set_visible(False)
    axc_top.set_yticks([6.0, 6.6])
    axc_top.tick_params(labelsize=10.5)
    axc_bot.set_yticks([1.0, 1.1, 1.2, 1.3])
    axc_bot.tick_params(labelsize=10.5, length=5, width=1.4)
    for sp in ("left", "bottom"):
        axc_bot.spines[sp].set_linewidth(1.5)
        axc_top.spines[sp].set_linewidth(1.5)
    axc_bot.set_xticks(st)
    for xi, v in zip(st, vals):
        ax = axc_top if v > 1.42 else axc_bot
        ax.text(xi, v + (0.06 if v > 1.42 else 0.013), "%.2f" % v,
                ha="center", va="bottom", fontsize=11)
    # 断轴标记：左边缘画一对斜线（上下各一条，错开）
    for ax, y0 in ((axc_top, 0.0), (axc_bot, 1.0)):
        ax.plot([-0.028, -0.004], [y0 - 0.030, y0 + 0.030], transform=ax.transAxes,
                color="k", clip_on=False, lw=1.1, solid_capstyle="butt")
    axc_bot.set_xlabel("Number of stages", fontsize=12, labelpad=6)
    axc_top.set_ylabel("Speedup (x)", fontsize=11)
    axc_bot.set_title("(c)", y=-0.78, fontsize=12.5)

    fig.subplots_adjust(bottom=0.20, top=0.88, left=0.055, right=0.985)
    return _save(fig, "rep-03-accuracy-tradeoff")


# ---------------------------------------------------------------- 04 延迟/显存扩展

def fig04():
    fig, axes = plt.subplots(1, 3, figsize=(13.4, 3.28),
                             gridspec_kw=dict(width_ratios=[1.12, 1.0, 1.0], wspace=0.30))

    # (b) 横向条 + 16x
    ax = axes[0]
    labels = ["SkyReelv2\n1.3B", "Wan2.1\n1.3B", "CogVideoX\n5B", "Wan2.2\n5B", "SANA-Video\n2B"]
    vals = [568, 403, 400, 116, 36]
    ypos = [4, 3, 2, 1, 0]
    for y, v, lab in zip(ypos, vals, labels):
        c = "#2E7D32" if lab.startswith("SANA") else "#A8B5AE"
        ax.barh(y, v, height=0.82, color=c, edgecolor="none")
        ax.text(v + 8, y, "%d" % v, va="center", fontsize=10,
                color="#1B5E20" if lab.startswith("SANA") else "#333333")
    ax.set_yticks(ypos, labels, fontsize=9.5)
    ax.set_xlim(0, 660)
    ax.set_xticks([0, 148, 295, 443, 590])
    ax.spines["left"].set_linewidth(1.2)
    ax.tick_params(axis="y", length=3.5)
    ax.plot([568, 568], [4.4, -0.55], ls=(0, (3, 2)), lw=1.0, color=DRED)
    ax.annotate("", xy=(36, -0.55), xytext=(568, -0.55),
                arrowprops=dict(arrowstyle="-|>", color=DRED, lw=1.1,
                                mutation_scale=12, shrinkA=0, shrinkB=0))
    ax.text(300, -0.42, "16×", color=DRED, fontsize=13, ha="center", va="bottom")
    ax.set_title("(b). Generation latency (s) on 720x1280x81\nvideo with default inference settings",
                 fontsize=13.5, y=-0.38)

    # (c) VRAM vs 长度
    ax = axes[1]
    L = np.array([1, 10, 30, 60, 65])
    vram_green = np.full_like(L, 7.2, dtype=float)
    vram_gray = np.array([15, 26, 46, 76, 80.0])
    ax.plot(L, vram_green, "-o", color="#4CAF50", ms=8.0, lw=2.6,
            label="Block Linear Attention")
    ax.plot(L, vram_gray, "--D", color="#9E9E9E", ms=7.5, lw=2.5,
            label="Causal Full Attention")
    for xi, yi in zip(L, vram_green):
        ax.text(xi, yi + 3.0, "%.1f" % yi, ha="center", fontsize=10.5, color="#1B5E20")
    for xi, yi in zip(L, vram_gray):
        ax.text(xi, yi + 4.2, "%.0f" % yi, ha="center", fontsize=10.5, color="#333333")
    ax.text(50, 63, "OOM", color="red", fontsize=9.5, ha="center")
    ax.set_xticks(L)
    ax.tick_params(labelsize=10.5)
    ax.set_xlabel("")
    ax.text(0.02, 1.02, "(GB)", transform=ax.transAxes, fontsize=9, va="bottom")
    ax.set_ylim(0, 90)
    ax.yaxis.grid(True, color="#A8A8A8", linewidth=1.1, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.24), fontsize=11,
              ncol=1, handlelength=1.3, prop={"weight": "bold", "size": 11})
    ax.set_title("(c). GPU VRAM v.s. video length (s)\non 480x832 resolution", fontsize=13.5, y=-0.38)

    # (d) 延迟 vs 长度
    ax = axes[2]
    L2 = np.array([5, 10, 30, 50])
    t_green = np.array([0.6, 2.0, 11.0, 20.0])
    t_gray = np.array([1.2, 5.0, 35.0, 93.0])
    ax.plot(L2, t_green, "-o", color="#4CAF50", ms=8.0, lw=2.6, label="SANA-Video-2B")
    ax.plot(L2, t_gray, "--D", color="#9E9E9E", ms=7.5, lw=2.5, label="Wan2.1-1.3B")
    for xi, yi in zip(L2, t_green):
        ax.text(xi, yi + 4.0, "%.0f" % yi, ha="center", fontsize=10.5, color="#1B5E20")
    for xi, yi in zip(L2, t_gray):
        ax.text(xi, yi + 4.0, "%.0f" % yi, ha="center", fontsize=10.5, color="#333333")
    ax.set_xticks(L2)
    ax.tick_params(labelsize=10.5, length=5, width=1.4)
    for sp in ("left", "bottom", "top", "right"):
        ax.spines[sp].set_visible(True)
        ax.spines[sp].set_linewidth(1.5)
    ax.text(0.02, 1.02, "(min)", transform=ax.transAxes, fontsize=10, va="bottom")
    ax.set_ylim(0, 105)
    ax.yaxis.grid(True, color="#A8A8A8", linewidth=1.1, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", handlelength=1.3,
              prop={"weight": "bold", "size": 11})
    ax.set_title("(d). Generation latency v.s. video\nlength (s) on 480x832 resolution",
                 fontsize=13.5, y=-0.38)
    fig.subplots_adjust(bottom=0.24, top=0.86)
    return _save(fig, "rep-04-latency-scaling")


REPLICAS = [
    ("01-memory-latency", fig01, "效率 · 显存分解 + 端到端延迟",
     "左侧破坏性堆叠条拆解显存（权重/前向/反向/梯度），右侧横向条对比端到端延迟，虚线+倍数标注加速比",
     "efficiency", ["ICML", "NeurIPS", "MLSys"], ["效率"]),
    ("02-fusion-gain", fig02, "效率 · 逐项融合增益",
     "四行横向条逐级下降，弧形箭头标出每步增益，底部括号给总加速比",
     "efficiency", ["MLSys", "ICML", "OSDI"], ["效率"]),
    ("03-accuracy-tradeoff", fig03, "权衡 · 精度曲线 + 断轴消融",
     "双折线对比多种量化方法随 cache 精度的衰减，(c) 用断轴柱状展示 stage 数的影响",
     "tradeoff", ["ICLR", "ICML", "NeurIPS"], ["量化"]),
    ("04-latency-scaling", fig04, "效率 · 延迟与显存扩展",
     "横向条对比生成延迟 + 两条扩展曲线（VRAM / 延迟 vs 视频长度），带 OOM 标注",
     "efficiency", ["CVPR", "ICCV", "NeurIPS"], ["生成"]),
]

# ---------------------------------------------------------------- 07 分组柱 + 并列热图

def fig07():
    fig = plt.figure(figsize=(6.6, 6.85))
    gs = fig.add_gridspec(2, 3, height_ratios=[0.82, 1.0], hspace=0.62, wspace=0.32)

    # ---- 上：分组柱（3 系列 × 6 稀疏度）
    ax = fig.add_subplot(gs[0, :])
    levels = [40, 50, 60, 70, 80, 90]
    series = {
        "MInference": ([40.4, 34.1, 27.3, 20.9, 14.3, 7.1], "#9E9E9E"),
        "LServe": ([30.0, 25.3, 20.3, 15.9, 10.8, 5.5], "#8C1D2F"),
        "Oracle": ([25.4, 21.2, 16.9, 12.7, 8.5, 4.2], "#FFFFFF"),
    }
    x = np.arange(len(levels))
    w = 0.26
    for i, (name, (vals, col)) in enumerate(series.items()):
        off = (i - 1) * w
        ec = "black" if name == "Oracle" else "none"
        ax.bar(x + off, vals, w, color=col, edgecolor=ec, linewidth=0.7,
               label=name, zorder=3)
    for i, (name, (vals, col)) in enumerate(series.items()):
        off = (i - 1) * w
        for xi, v in zip(x + off, vals):
            ax.text(xi, v + 0.7, "%.1f" % v, ha="center", va="bottom", fontsize=6.4,
                    rotation=90)
    ax.set_xticks(x, [str(l) for l in levels])
    ax.set_xlabel("Sparsity Level (%)", fontsize=11)
    ax.set_ylabel("Latency (ms)", fontsize=11)
    ax.set_ylim(0, 48)
    ax.set_yticks([0, 10, 20, 30, 40])
    ax.axhline(42.3, ls=(0, (2, 1.5)), color="#C0392B", lw=1.1, zorder=2)
    ax.text(5.3, 43.4, "Dense Attention: 42.3 ms", color="#C0392B", fontsize=8.2,
            ha="right", va="bottom", fontweight="bold")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=3, frameon=False,
              fontsize=9, handlelength=1.1)
    # 1.3x 标注
    ax.annotate("1.3 ×", xy=(x[0] + 0.0, 33), xytext=(x[0] - 0.62, 37),
                fontsize=8.6, color="#C0392B",
                arrowprops=dict(arrowstyle="-|>", color="#C0392B", lw=1.0,
                                connectionstyle="arc3,rad=0.3", mutation_scale=10))
    ax.annotate("1.3 ×", xy=(x[-1] + 0.0, 6.4), xytext=(x[-1] - 0.75, 9.4),
                fontsize=8.6, color="#C0392B",
                arrowprops=dict(arrowstyle="-|>", color="#C0392B", lw=1.0,
                                connectionstyle="arc3,rad=0.3", mutation_scale=10))
    ax.set_title("Figure 12: Prefilling Stage Attention Kernel Evaluation.",
                 fontsize=10.5, fontweight="bold", pad=30)

    # ---- 下：三张热图 + 共享色条
    from matplotlib.colors import LinearSegmentedColormap
    cmap_hm = LinearSegmentedColormap.from_list(
        'acc', ['#E24A33', '#F2C230', '#7FD8A0', '#20C080'])
    rng = np.random.default_rng(7)
    titles = ["(a) $N_P$ = 64, $N_L$ = 16,  Budget: 3072",
              "(b) $N_P$ = 32, $N_L$ = 16,  Budget: 3072",
              "(c) $N_P$ = 64, $N_L$ = 16,  Budget: 3072"]
    im = None
    axes_hm = []
    for k in range(3):
        axh = fig.add_subplot(gs[1, k])
        data = np.full((12, 7), 0.94)
        # 少量低分格子
        for _ in range(rng.integers(3, 6)):
            data[rng.integers(0, 12), rng.integers(0, 7)] = rng.choice([0.18, 0.30, 0.45])
        im = axh.imshow(data, cmap=cmap_hm, vmin=0.0, vmax=1.06, aspect="auto")
        axh.set_title(titles[k], fontsize=6.8, pad=3)
        axh.set_yticks(range(12))
        axh.set_yticklabels(["", "0", "", "22", "", "44", "", "67", "", "89", "", ""],
                            fontsize=5.6)
        axh.set_xticks(range(7))
        axh.set_xticklabels(["0K", "49K", "85K", "128K", "171K", "211K", "256K"],
                            fontsize=5.2, rotation=35, ha="right")
        if k == 0:
            axh.set_ylabel("Document Depth (%)", fontsize=6.6)
        axh.set_xlabel("Document Length", fontsize=6.6)
        axes_hm.append(axh)

    cax = fig.add_axes([0.92, 0.10, 0.012, 0.20])
    cb = fig.colorbar(im, cax=cax)
    cb.set_label("Accuracy", fontsize=6.6)
    cb.ax.tick_params(labelsize=5.6)

    fig.text(0.5, 0.008,
             "Figure 13: Hierarchical paging enables LServe to preserve the\n"
             "long-context retrieval capabilities of the original model without\n"
             "increasing the key-value (KV) token budget.  We use Llama-3-8B for the ablation.",
             ha="center", va="bottom", fontsize=11, fontweight="bold", linespacing=1.35)
    fig.subplots_adjust(bottom=0.16, top=0.93, left=0.10, right=0.90)
    return _save(fig, "rep-07-grouped-heatmap")


# ---------------------------------------------------------------- 08 共享图例 + 双行归一化柱

def fig08():
    fig, axes = plt.subplots(2, 1, figsize=(6.4, 3.64), sharex=False)
    methods = ["QServe", "vLLM", "DuoAttention", "MInference", "LServe (Ours)"]
    cols = ["#C8C8C8", "#A8A8A8", "#808080", "#303030", "#A02000"]
    rows = [
        ("A100\nLlama-3-8B", ["64K", "96K", "128K", "192K", "256K", "320K", "Geomean"],
         [[0.86, 0.78, 0.73, 0.58, 0.48, 0.34, 0.60],
          [0.56, 0.40, 0.45, 0.61, 0.53, 0.39, 0.48],
          [0.68, 0.80, 0.86, 0.84, 0.80, 0.86, 0.81],
          [0.72, 0.73, 0.77, 0.58, 0.48, 0.44, 0.56],
          [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]]),
        ("A100\nLlama-2-7B", ["16K", "32K", "64K", "96K", "128K", "160K", "Geomean"],
         [[0.90, 0.97, 0.85, 0.78, 0.72, 0.69, 0.81],
          [0.76, 0.63, 0.48, 0.43, 0.29, 0.45, 0.56],
          [0.81, 0.75, 0.79, 0.79, 0.79, 0.81, 0.79],
          [0.34, 0.36, 0.70, 0.72, 0.48, 0.56, 0.47],
          [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]]),
    ]
    w = 0.225
    for ax, (ylabel, xt, mat) in zip(axes, rows):
        x = np.arange(len(xt))
        for i, (m, c) in enumerate(zip(methods, cols)):
            off = (i - 2) * w
            ax.bar(x + off, mat[i], w * 0.98, color=c, edgecolor="black" if c == "#000000" else "none",
                   linewidth=0.9)
            for xi, v in zip(x + off, mat[i]):
                ax.text(xi, v + 0.022, "%.2f" % v, ha="center", va="bottom",
                        fontsize=6.0, rotation=90)
        ax.set_xticks(x, xt, fontsize=9)
        ax.tick_params(axis="x", pad=3)
        ax.set_ylim(0, 1.14)
        ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_ylabel(ylabel, fontsize=9.5, rotation=0, ha="right", va="center", labelpad=18)
        ax.tick_params(axis="y", labelsize=8.5, length=4, width=1.2)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)

    handles = [Rectangle((0, 0), 1, 1, fc=c, ec="black" if c == "#303030" else "none",
                         lw=0.6) for c in cols]
    fig.legend(handles, methods, loc="upper center", bbox_to_anchor=(0.5, 1.03),
               ncol=5, frameon=False, fontsize=9.5, handlelength=1.1, columnspacing=1.1)
    fig.text(0.5, 0.005,
             "Figure 11: Prefilling Speed Evaluation. Performance comparison\n"
             "of long-sequence prefilling across different serving frameworks,\n"
             "normalized to LServe's speed.",
             ha="center", va="bottom", fontsize=9.5, fontweight="bold")
    fig.subplots_adjust(top=0.91, bottom=0.18, left=0.135, right=0.998, hspace=0.22)
    return _save(fig, "rep-08-shared-legend")


# ---------------------------------------------------------------- 09 激活热图 + 重要通道

def fig09():
    rng = np.random.default_rng(12)
    fig, axes = plt.subplots(2, 1, figsize=(6.6, 6.17))
    n_ch, n_tok = 1536, 400

    # (上) 输入激活：通道基准 × token 调制，再叠"块状"增强（真实激活的局部相关结构）
    ch_base = rng.lognormal(0.0, 0.75, n_ch)
    act = ch_base[:, None] * np.ones((1, n_tok))
    # 竖向块：均匀铺满整幅（原图不是中间一坨，而是全宽分布）
    for _ in range(34):
        c0 = int(rng.integers(0, n_ch - 40))
        t0 = int(rng.integers(0, n_tok - 12))
        c1 = c0 + int(rng.integers(25, 180))
        t1 = t0 + int(rng.integers(10, 90))
        act[c0:c1, t0:t1] *= rng.uniform(1.6, 3.4)
    # 高亮通道带（原图最明显的是横向橙色条带）
    for _ in range(14):
        c0 = int(rng.integers(0, n_ch - 60))
        act[c0:c0 + int(rng.integers(15, 55)), :] *= rng.uniform(2.4, 4.2)
    # 暗通道带（原图黑/亮交替的关键）
    for _ in range(16):
        c0 = int(rng.integers(0, n_ch - 50))
        act[c0:c0 + int(rng.integers(12, 45)), :] *= rng.uniform(0.06, 0.22)
    # token 方向的细粒度调制（形成原图那种竖向细密条纹）
    tok_fine = rng.gamma(4.0, 0.22, n_tok)
    act *= tok_fine[None, :]
    # token 分段的强弱起伏（原图有明显的"暗段/亮段"竖向节奏）
    seg = np.ones(n_tok)
    pos = 0
    while pos < n_tok:
        w = int(rng.integers(6, 26))
        seg[pos:pos + w] = rng.uniform(0.08, 1.70)
        pos += w + int(rng.integers(0, 8))
    act *= seg[None, :]
    # 额外的"亮竖条"：少数 token 列整体极亮（原图最显眼的特征）
    for _ in range(46):
        c0 = int(rng.integers(0, n_tok))
        w = int(rng.integers(1, 4))
        act[:, c0:c0 + w] *= rng.uniform(3.0, 7.0)
    # 通道方向的细粒度调制（横向细纹）
    ch_fine = rng.gamma(6.0, 0.16, n_ch)
    act *= ch_fine[:, None]
    # 散点噪声
    act *= rng.gamma(3.0, 0.24, (n_ch, n_tok))
    # 少数 outlier 通道整体更亮
    out_ch = rng.choice(n_ch, 90, replace=False)
    act[out_ch, :] *= rng.uniform(2.5, 6.0, (90, 1))
    # 图像/语言两段的整体差异
    act[:, :164] *= 1.15
    act[:, 266:] *= 0.9

    ax = axes[0]
    # 真实激活图常用 log 归一化；再叠 gamma 拉伸提高对比
    act_disp = np.log1p(act)
    act_disp = (act_disp - act_disp.min()) / (act_disp.max() - act_disp.min() + 1e-9)
    act_disp = act_disp ** 0.55
    act_disp = np.clip((act_disp - 0.48) * 1.35 + 0.48, 0, 1)
    ax.imshow(act_disp, aspect="auto", cmap="magma", origin="upper",
              extent=[0, n_tok, n_ch, 0],
              vmin=np.percentile(act_disp, 8), vmax=np.percentile(act_disp, 92))
    ax.set_title("Input Activations", fontsize=12)
    ax.set_ylabel("Channel Index", fontsize=10)
    ax.set_xlabel("Token Index", fontsize=10)
    ax.text(70, 110, "Visual Tokens", fontsize=8.5, color="k",
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=2))
    ax.text(300, 110, "Language Tokens", fontsize=8.5, color="k",
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=2))
    for xv, c, ls in [(16, "green", "-"), (164, "green", "--"), (266, "red", "-")]:
        ax.axvline(xv, color=c, ls=ls, lw=1.4)

    # (下) 重要通道：密集亮点 + 通道带聚集（原图是横贯全宽的亮条纹）
    imp = np.zeros((n_ch, n_tok))
    base_dens = rng.beta(0.60, 4.0, n_ch) * 0.36    # 每通道基础密度
    for ci in range(n_ch):
        if base_dens[ci] > 0.004:
            cols = rng.random(n_tok) < base_dens[ci]
            imp[ci, cols] = rng.uniform(0.75, 1.0, cols.sum())
    # 强调通道带（对应上图高亮区）
    for lo, hi in [(0, 140), (400, 560), (1120, 1290)]:
        band = rng.random((hi - lo, n_tok)) < rng.uniform(0.30, 0.55)
        imp[lo:hi, :] = np.maximum(imp[lo:hi, :], band * rng.uniform(0.95, 1.0))

    ax = axes[1]
    ax.imshow(imp, aspect="auto", cmap="hot", origin="upper",
              extent=[0, n_tok, n_ch, 0], vmin=0, vmax=0.20)
    ax.set_title("Important Channels", fontsize=12)
    ax.set_ylabel("Channel Index", fontsize=10)
    ax.set_xlabel("Token Index", fontsize=10)
    for xv, c, ls in [(16, "green", "-"), (164, "green", "--"), (266, "red", "-")]:
        ax.axvline(xv, color=c, ls=ls, lw=1.4)

    handles = [Line2D([], [], color="green", lw=1.6, label="Image Token Start"),
               Line2D([], [], color="green", lw=1.6, ls="--", label="Image Token End"),
               Line2D([], [], color="red", lw=1.6, label="Generation Token Start")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.19),
              ncol=3, frameon=True, fontsize=8.5, handlelength=1.8)
    fig.text(0.5, -0.085,
             "Figure 2. Visualization of a Transformer block in Qwen2VL-2B,\n"
             "illustrating token value distributions (top) and the positions of im-\n"
             "portant channels (bottom).  In the top panel, brightness reflects\n"
             "token magnitude, while in the bottom panel, highlighted positions\n"
             "denote important channels.",
             ha="center", va="bottom", fontsize=13.5, linespacing=1.45)
    fig.subplots_adjust(top=0.95, bottom=0.24, left=0.12, right=0.98, hspace=0.34)
    return _save(fig, "rep-09-activation-heatmap")


def fig10():
    rng = np.random.default_rng(3)
    fig, axes = plt.subplots(2, 1, figsize=(6.4, 5.95))
    n = 1536
    idx = np.arange(n)

    # (上) 频率分布：指数衰减 + 双色阴影 + 红叉 + 蓝星
    tau = 165.0
    freq = 0.78 * np.exp(-idx / tau) + 0.0035
    ax = axes[0]
    k = 48
    ax.plot(idx, freq, color="royalblue", lw=1.2, label="Frequency")
    ax.fill_between(idx[:k], freq[:k], color="#8FCBE8", alpha=1.0,
                    label="Token-independent Channels")
    ax.fill_between(idx[k:], freq[k:], color="#F5B0AC", alpha=1.0,
                    label="Token-dependent Channels")
    # 红叉沿曲线分布：前段密、后段疏（与参考图一致）
    sel = np.unique(np.round(np.geomspace(1, 700, 44)).astype(int))
    ax.plot(sel, freq[sel], "x", color="red", ms=5.0, mew=1.1,
            label=r"Important Channels by $\mathbf{x}\odot\mathbf{w}$", zorder=5)
    ax.plot([0], [freq[0]], "*", color="navy", ms=15, label="Maximum", zorder=6)
    ax.set_xlabel("Important Channel Index", fontsize=10)
    ax.set_ylabel("Frequency", fontsize=10)
    ax.set_xlim(0, n)
    ax.set_ylim(0, 0.86)
    ax.set_xticks([0, k, 256, 576, 1024], ["0", "$k$", "256", "576", "1024"])
    ax.legend(loc="upper right", frameon=True, fontsize=8.2, handlelength=1.6,
              borderpad=0.5, labelspacing=0.35)
    ax.set_title("Frequency Distribution", fontsize=12)

    # (下) 异常值均值：尖峰折线 + 橙星
    # 基线缓慢上升 + 伽马分布尖峰（原图就是这个形态）
    base = 0.0042 + 0.0030 * (idx / n) ** 0.7
    val = base + rng.normal(0, 0.0006, n)
    spikes = rng.random(n) < 0.26
    val[spikes] += rng.gamma(2.4, 0.0014, spikes.sum())
    val = np.clip(val, 0, None)
    ax = axes[1]
    ax.plot(idx, val, color="#F5C242", lw=0.95, label="Mean Value")
    ax.plot([0], [val[0]], "*", color="orange", ms=14, label="Maximum")
    ax.set_xlabel("Important Channel Index", fontsize=10)
    ax.set_ylabel("Value", fontsize=10)
    ax.set_xlim(0, n)
    ax.set_xticks([0, k, 256, 576, 1024], ["0", "$k$", "256", "576", "1024"])
    ax.legend(loc="upper left", frameon=True, fontsize=8.2, handlelength=1.6,
              borderpad=0.5, labelspacing=0.35)
    ax.set_title("Outlier Mean Value", fontsize=12)

    fig.text(0.5, -0.025,
             "Figure 3. Visualization of a Transformer block in Qwen2VL-2B,\n"
             "illustrating important channel behavior.  The top panel shows ac-\n"
             "tivation frequencies, while the bottom depicts average activation\n"
             "values.  Red crosses mark important channel positions identified\n"
             "by the static global method on the calibration dataset.",
             ha="center", va="bottom", fontsize=12, linespacing=1.3)
    fig.subplots_adjust(top=0.95, bottom=0.33, left=0.12, right=0.98, hspace=0.48)
    return _save(fig, "rep-10-frequency-outlier")


REPLICAS += [
    ("07-grouped-heatmap", fig07, "结果 · 分组柱 + 并列热图",
     "上方三系列分组柱（MInference/LServe/Oracle）带密集参考线，下方三联热图共享色条",
     "results", ["MLSys", "ISCA", "ASPLOS"], ["系统"]),
    ("08-shared-legend", fig08, "结果 · 共享图例双行归一化柱",
     "两行分组柱（不同模型规模），全部归一化到本文方法=1.00，顶部共享图例",
     "results", ["MLSys", "NeurIPS", "ICML"], ["系统"]),
    ("09-activation-heatmap", fig09, "动机 · 激活与重要通道热图",
     "上：token×channel 激活热图；下：重要通道稀疏亮点；绿色/红色虚线标 token 边界",
     "motivation", ["NeurIPS", "ICML", "ICLR"], ["多模态"]),
    ("10-frequency-outlier", fig10, "动机 · 频率与异常值分布",
     "上：通道激活频率指数衰减 + 双色阴影 + 红叉标记；下：均值尖峰折线 + 最值星标",
     "motivation", ["ICLR", "NeurIPS", "ACL"], ["量化"]),
]

