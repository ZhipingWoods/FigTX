#!/usr/bin/env python3
r"""动机图（motivation / teaser）模板：用 matplotlib 生成，强调"提出问题"。

典型结构：左「现有方法为何失效」，右「本文做法」；或 scatter/bar 展示 gap。
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from common import OUT_FIG  # noqa: E402

RC = {
    "figure.dpi": 110,
    "savefig.dpi": 180,
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "mathtext.fontset": "cm",
    "font.family": "serif",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
}


def _save(fig, name: str) -> str:
    out = os.path.join(OUT_FIG, name + ".png")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def gap_bar() -> str:
    """柱状 gap：现有方法 vs 本文，标出差距。"""
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.6, 2.9))
        groups = ["Short", "Medium", "Long"]
        base = [72.4, 61.2, 43.8]
        ours = [78.9, 71.5, 58.3]
        x = np.arange(len(groups))
        w = 0.34
        b1 = ax.bar(x - w / 2, base, w, label="Existing", color="#B0B7C3", edgecolor="#6B7280")
        b2 = ax.bar(x + w / 2, ours, w, label="Ours", color="#D27D8C", edgecolor="#8C3B4A")
        for bars in (b1, b2):
            ax.bar_label(bars, fmt="%.1f", padding=1.5, fontsize=7)
        for i in range(len(groups)):
            ax.annotate("", xy=(x[i] + w, ours[i] - 1.5), xytext=(x[i] - w, base[i] + 1.5),
                        arrowprops=dict(arrowstyle="-|>", color="#8C3B4A", lw=1.0,
                                        connectionstyle="arc3,rad=-0.25"))
        ax.set_xticks(x, groups)
        ax.set_ylabel("Accuracy (%)")
        ax.set_ylim(0, 95)
        ax.legend(frameon=False, loc="upper right")
        ax.set_title("Gap grows with sequence length")
        return _save(fig, "fig-mot-gap-bar")


def failure_cases() -> str:
    """失败案例示意：三张小图 + 红框标注。"""
    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 3, figsize=(6.2, 2.3))
        rng = np.random.default_rng(3)
        titles = ["Occlusion", "Low light", "Motion blur"]
        for ax, t in zip(axes, titles):
            img = rng.normal(0.62, 0.13, (64, 64))
            if t == "Occlusion":
                img[18:40, 22:44] = 0.15
            elif t == "Low light":
                img = img * 0.35
            else:
                img = np.apply_along_axis(lambda r: np.convolve(r, np.ones(5) / 5, "same"), 1, img)
            ax.imshow(img, cmap="gray", vmin=0, vmax=1)
            ax.add_patch(plt.Rectangle((20, 16), 26, 26, fill=False, ec="#C0392B", lw=1.4))
            ax.set_title(t, fontsize=8.5)
            ax.set_xticks([]); ax.set_yticks([])
            ax.grid(False)
        fig.suptitle("Failure modes of prior work", fontsize=10, y=1.04)
        return _save(fig, "fig-mot-failure-cases")


def tradeoff_scatter() -> str:
    """精度-代价散点：展示帕累托改进。"""
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.4, 3.0))
        rng = np.random.default_rng(11)
        ax.scatter(rng.normal(120, 14, 14), rng.normal(70, 3.0, 14), s=26,
                   c="#9AA3AF", label="Prior arts", edgecolors="white", linewidths=0.6)
        ax.scatter([96], [79.5], s=110, marker="*", c="#8C3B4A", label="Ours", zorder=5)
        ax.annotate("better ↑\ncheaper ←", xy=(96, 79.5), xytext=(104, 76.5),
                    fontsize=7.5, color="#8C3B4A",
                    arrowprops=dict(arrowstyle="-", lw=0.6, color="#8C3B4A", ls=":"))
        ax.set_xlabel("Inference cost (GFLOPs)")
        ax.set_ylabel("Accuracy (%)")
        ax.legend(frameon=False, loc="lower left")
        ax.set_title("Pushing the Pareto frontier")
        return _save(fig, "fig-mot-tradeoff")


def attention_shift() -> str:
    """注意力分布对比：左塌缩、右分散。"""
    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.5), sharey=True)
        n = 40
        x = np.arange(n)
        collapsed = np.exp(-((x - 8) ** 2) / 6)
        spread = 0.55 * np.exp(-((x - 6) ** 2) / 12) + 0.45 * np.exp(-((x - 26) ** 2) / 20)
        axes[0].bar(x, collapsed, color="#9AA3AF", width=0.8)
        axes[0].set_title("Prior: attention collapse", fontsize=9)
        axes[1].bar(x, spread, color="#C97B8B", width=0.8)
        axes[1].set_title("Ours: spatially balanced", fontsize=9)
        for ax in axes:
            ax.set_xlabel("Token index")
            ax.grid(False)
        axes[0].set_ylabel("Attention weight")
        fig.suptitle("Motivation: where the model looks", fontsize=10, y=1.03)
        return _save(fig, "fig-mot-attention-shift")


def scaling_gap() -> str:
    """规模增大时差距拉大（双线 + 阴影）。"""
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.4, 2.9))
        s = np.array([7, 13, 30, 70, 130])
        base = np.array([41, 52, 61, 66, 68])
        ours = np.array([45, 60, 72, 80, 85])
        ax.plot(s, base, "o-", color="#9AA3AF", label="Baseline", ms=4)
        ax.plot(s, ours, "s-", color="#8C3B4A", label="Ours", ms=4)
        ax.fill_between(s, base, ours, color="#D27D8C", alpha=0.15)
        ax.annotate("gap widens", xy=(90, 74), fontsize=8, color="#8C3B4A")
        ax.set_xscale("log")
        ax.set_xlabel("Model size (B params)")
        ax.set_ylabel("Zero-shot score")
        ax.legend(frameon=False, loc="lower right")
        ax.set_title("Benefit scales with capacity")
        return _save(fig, "fig-mot-scaling")


def concept_drift() -> str:
    """概念漂移示意：分布随时间偏移。"""
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.6, 2.8))
        rng = np.random.default_rng(5)
        for i, (mu, c, lab) in enumerate([(-1.1, "#9AA3AF", "t=0"), (0.2, "#C9A227", "t=50"),
                                          (1.4, "#C97B8B", "t=100")]):
            ax.hist(rng.normal(mu, 0.55, 400), bins=26, alpha=0.55, color=c,
                    label=lab, edgecolor="white", linewidth=0.4)
        ax.set_xlabel("Feature projection")
        ax.set_ylabel("#samples")
        ax.legend(frameon=False, title="time step", title_fontsize=7.5)
        ax.set_title("Distribution drift over time")
        return _save(fig, "fig-mot-concept-drift")


TEMPLATES = [
    ("gap-bar", gap_bar, "差距对比柱状图", "分组柱 + 箭头标出提升幅度，用于说明「现有方法与本文差距」",
     ["通用"], ["CVPR", "ICLR", "NeurIPS", "ICML", "ACL"]),
    ("failure-cases", failure_cases, "失败案例拼图", "三连图 + 红框标注失败区域，动机章节最常用",
     ["检测"], ["CVPR", "ICCV", "ECCV"]),
    ("tradeoff", tradeoff_scatter, "精度-代价权衡散点", "把已有工作铺开、本文点标星，直观展示帕累托推进",
     ["通用"], ["CVPR", "ICML", "MLSys", "NeurIPS"]),
    ("attention-shift", attention_shift, "注意力分布对比", "左右对照：先验方法注意力塌缩 vs 本文空间均衡",
     ["多模态"], ["CVPR", "ICCV", "ACL"]),
    ("scaling", scaling_gap, "规模-收益曲线", "双折线 + 阴影 gap，说明优势随规模放大（log x 轴）",
     ["LLM"], ["NeurIPS", "ICLR", "ICML"]),
    ("concept-drift", concept_drift, "分布漂移示意", "三时刻直方图叠加，用于持续学习/在线推理的动机",
     ["RL"], ["ICLR", "NeurIPS", "KDD"]),
]