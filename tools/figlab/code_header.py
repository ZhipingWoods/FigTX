# -*- coding: utf-8 -*-
"""FigTX 论文图复刻 · 完整可运行代码

保存为 .py 后运行即可生成同名 PNG 文件。
依赖：pip install matplotlib numpy
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

# ---- 全局风格：与论文图一致（serif + 300dpi） ----
plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "font.family": "serif",
    "font.serif": ["Palatino", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "dejavuserif",
    "font.size": 9,
    "axes.linewidth": 1.1,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# ---- 语义配色（取自参考图像素统计，误差 <10 RGB） ----
TEAL = "#08A8B8"
YELLOW = "#E8B800"
DRED = "#8C1D2F"
DRED2 = "#781828"
GRAY = "#585858"
MGRAY = "#888888"
LGRAY = "#A6A6A6"
NAVY = "#2F3A4F"
BLUE = "#3E8FB8"
MBLUE = "#7BB6B6"
SAGE = "#C8D5B9"
SAND = "#F5E6A8"
MAUVE = "#8B7A9E"
GREEN = "#7CB342"
HGREEN = "#38D888"
GGRN = "#98C838"
SGY = "#A8B8B8"
RED8 = "#A82818"


def _save(fig, name):
    """保存为 PNG（300dpi，自动裁白边）。"""
    fig.savefig(name + ".png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name + ".png")


def _hbar_stacked(ax, rows, segments, colors, ypos, height=0.78):
    """横向堆叠条（图 01 用）。"""
    for y, (label, vals, total) in zip(ypos, rows):
        left = 0.0
        for v, c in zip(vals, colors):
            ax.barh(y, v, left=left, height=height, color=c,
                    edgecolor="white", linewidth=0.8)
            if v > 0.4:
                ax.text(left + v / 2, y, ("%g" % round(v, 2)).rstrip("0").rstrip("."),
                        ha="center", va="center", color="white", fontsize=9.5)
            left += v
        ax.text(left + 0.6, y, total, ha="left", va="center", fontsize=11,
                color="#333333")
    ax.set_yticks(ypos, [r[0] for r in rows])
