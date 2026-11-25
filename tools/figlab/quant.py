#!/usr/bin/env python3
r"""实验图 · 定量（quantitative）：折线、柱、散点、雷达、热力图等。"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from common import OUT_FIG  # noqa: E402

RC = {
    "figure.dpi": 110, "savefig.dpi": 320, "font.size": 9,
    "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8,
    "axes.spines.top": False, "axes.spines.right": False,
    "mathtext.fontset": "cm", "font.family": "serif",
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
}
PAL = ["#2E5E8C", "#C97B8B", "#6B9E78", "#C9A227", "#8B6BA8", "#7A7A7A"]


def _save(fig, name):
    p = os.path.join(OUT_FIG, name + ".png")
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    return p


def convergence():
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.4, 2.9))
        it = np.arange(0, 300, 3)
        for i, (k, lab) in enumerate([(60, "w/o ours"), (38, "ours (full)"), (46, "ours (abbr.)")]):
            y = 0.35 + 0.62 * (1 - np.exp(-it / k)) + np.random.default_rng(i).normal(0, 0.008, len(it))
            ax.plot(it, y, color=PAL[i], lw=1.2, label=lab)
        ax.set_xlabel("Iteration (k)"); ax.set_ylabel("Validation accuracy")
        ax.legend(frameon=False, loc="lower right")
        ax.set_title("Convergence speed")
        return _save(fig, "fig-qua-convergence")


def ablation_bars():
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.6, 2.9))
        names = ["Base", "+A", "+A+B", "+A+B+C\n(Ours)"]
        vals = [68.2, 71.4, 74.1, 76.8]
        bars = ax.bar(names, vals, color=["#B0B7C3", "#C3CBD6", "#D8B4BC", "#C97B8B"],
                      edgecolor="#6B7280", linewidth=0.6)
        ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=7.5)
        ax.set_ylim(60, 82); ax.set_ylabel("mAP (%)")
        ax.set_title("Ablation study")
        return _save(fig, "fig-qua-ablation")


def error_band():
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.4, 2.9))
        x = np.linspace(0, 10, 60)
        for i, (mu, c) in enumerate([(0.55, PAL[0]), (0.72, PAL[1])]):
            y = 1 - np.exp(-x * mu)
            sd = 0.03 + 0.02 * x / 10
            ax.plot(x, y, color=c, lw=1.3, label=["Baseline", "Ours"][i])
            ax.fill_between(x, y - sd, y + sd, color=c, alpha=0.18, lw=0)
        ax.set_xlabel("Distance threshold (m)"); ax.set_ylabel("Recall")
        ax.legend(frameon=False, loc="lower right")
        ax.set_title("Recall@τ with std over 5 runs")
        return _save(fig, "fig-qua-errorband")


def radar():
    with plt.rc_context(RC):
        labels = ["Accuracy", "Robustness", "Efficiency", "Generalization", "Calibration"]
        n = len(labels)
        ang = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist(); ang += ang[:1]
        a = [0.72, 0.61, 0.83, 0.65, 0.58]; a += a[:1]
        b = [0.81, 0.78, 0.79, 0.74, 0.71]; b += b[:1]
        fig, ax = plt.subplots(figsize=(3.6, 3.4), subplot_kw=dict(polar=True))
        ax.plot(ang, a, color="#9AA3AF", lw=1.2, label="Baseline")
        ax.fill(ang, a, color="#9AA3AF", alpha=0.18)
        ax.plot(ang, b, color="#C97B8B", lw=1.4, label="Ours")
        ax.fill(ang, b, color="#C97B8B", alpha=0.22)
        ax.set_xticks(ang[:-1], labels, fontsize=8)
        ax.set_yticklabels([]); ax.set_ylim(0, 1)
        ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1.25, 1.12))
        ax.set_title("Multi-dimensional comparison", fontsize=10, pad=14)
        return _save(fig, "fig-qua-radar")


def heatmap():
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.2, 3.2))
        rng = np.random.default_rng(4)
        m = np.clip(rng.normal(0.6, 0.16, (6, 8)), 0, 1)
        m[4:, :] += 0.18
        im = ax.imshow(m, cmap="RdYlBu_r", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(8), [f"L{i+1}" for i in range(8)], fontsize=7.5)
        ax.set_yticks(range(6), [f"M{i+1}" for i in range(6)], fontsize=7.5)
        ax.grid(False)
        fig.colorbar(im, ax=ax, label="score", fraction=0.046, pad=0.03)
        ax.set_title("Per-language / per-model scores")
        return _save(fig, "fig-qua-heatmap")


def box_violin():
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.4, 2.9))
        rng = np.random.default_rng(8)
        data = [rng.normal(70, 5, 40), rng.normal(76, 4, 40), rng.normal(80, 3.2, 40)]
        parts = ax.violinplot(data, showmeans=True, showextrema=False)
        for i, pc in enumerate(parts["bodies"]):
            pc.set_facecolor(PAL[i]); pc.set_alpha(0.55); pc.set_edgecolor("none")
        ax.boxplot(data, widths=0.12, showfliers=False,
                   medianprops=dict(color="black", lw=1.0))
        ax.set_xticks([1, 2, 3], ["Baseline", "Variant", "Ours"])
        ax.set_ylabel("Score over 5 seeds")
        ax.set_title("Distribution across seeds")
        return _save(fig, "fig-qua-violin")


def pareto():
    """精度-延迟权衡：延迟越大精度越高，前沿是「同延迟下精度最高」的包络。"""
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.4, 3.0))
        rng = np.random.default_rng(2)
        xs = np.linspace(40, 180, 26)
        # 边际收益递减：开方曲线 + 噪声
        ys = 62 + 16 * np.sqrt((xs - 30) / 150) + rng.normal(0, 0.6, len(xs))
        ax.scatter(xs, ys, s=18, c="#B0B7C3", label="candidates", zorder=2)

        # 帕累托前沿：延迟递增时，精度严格创新高的点
        order = np.argsort(xs)
        keep, best = [], -1e9
        for i in order:
            if ys[i] > best:
                best = ys[i]
                keep.append(i)
        ax.plot(xs[keep], ys[keep], "-", color="#C97B8B", lw=1.4, label="Pareto front", zorder=3)
        ax.scatter(xs[keep], ys[keep], s=34, c="#C97B8B",
                   edgecolors="white", linewidths=0.6, zorder=4)
        ax.annotate("ours", xy=(xs[keep[-1]], ys[keep[-1]]),
                    xytext=(-26, -14), textcoords="offset points",
                    fontsize=8, color="#8C3B4A",
                    arrowprops=dict(arrowstyle="-", lw=0.6, color="#8C3B4A"))
        ax.set_xlabel("Latency (ms)"); ax.set_ylabel("Top-1 (%)")
        ax.legend(frameon=False, loc="lower right")
        ax.set_title("Accuracy vs. latency")
        return _save(fig, "fig-qua-pareto")


def grouped_hatch():
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.6, 2.9))
        groups = ["CIFAR-10", "CIFAR-100", "ImageNet"]
        base = [94.1, 76.3, 79.2]; ours = [95.0, 79.8, 81.6]
        x = np.arange(3); w = 0.34
        ax.bar(x - w/2, base, w, label="Baseline", color="#DDE1E7",
               edgecolor="#6B7280", hatch="//", linewidth=0.6)
        ax.bar(x + w/2, ours, w, label="Ours", color="#EBD3D8",
               edgecolor="#8C3B4A", hatch="\\\\", linewidth=0.6)
        ax.set_xticks(x, groups); ax.set_ylim(70, 100)
        ax.set_ylabel("Accuracy (%)")
        ax.legend(frameon=False, loc="lower right")
        ax.set_title("Cross-dataset comparison (hatched = ours)")
        return _save(fig, "fig-qua-grouped-hatch")


def sensitivity():
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.4, 2.9))
        lam = np.logspace(-3, 1, 30)
        acc = 78.5 - 6 * (np.log10(lam) + 1) ** 2
        ax.plot(lam, acc, color="#2E5E8C", lw=1.4)
        bi = np.argmax(acc)
        ax.scatter([lam[bi]], [acc[bi]], s=60, c="#C97B8B", zorder=4)
        ax.annotate(r"$\lambda^*=%.3f$" % lam[bi], xy=(lam[bi], acc[bi]),
                    xytext=(lam[bi]*3, acc[bi]-2.5), fontsize=8, color="#8C3B4A")
        ax.set_xscale("log"); ax.set_xlabel(r"$\lambda$"); ax.set_ylabel("Accuracy (%)")
        ax.set_title("Hyper-parameter sensitivity")
        return _save(fig, "fig-qua-sensitivity")


def cumulative():
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(4.4, 2.8))
        x = np.arange(1, 21)
        for i, (a, lab) in enumerate([(0.55, "Ours"), (0.38, "Baseline")]):
            y = 1 - (1 - a) ** x
            ax.plot(x, y * 100, "o-", ms=3, color=PAL[i], label=lab)
        ax.axhline(95, ls=":", color="#8A8580", lw=0.8)
        ax.set_xlabel("Number of attempts"); ax.set_ylabel("Cumulative success (%)")
        ax.legend(frameon=False, loc="lower right")
        ax.set_title("Pass@k style cumulative curve")
        return _save(fig, "fig-qua-cumulative")


TEMPLATES = [
    ("convergence", convergence, "收敛速度对比", "多方法训练曲线，看谁先收敛/更稳", ["通用"], ["NeurIPS", "ICLR", "ICML"]),
    ("ablation", ablation_bars, "消融实验柱状图", "逐项加模块看增益，末项标 Ours", ["通用"], ["CVPR", "ICLR", "NeurIPS", "ACL"]),
    ("errorband", error_band, "多次实验的误差带", "均值 ± 标准差阴影，比单条线更可信", ["通用"], ["CVPR", "ICML", "NeurIPS"]),
    ("radar", radar, "多维能力雷达图", "五维对比，适合强调均衡而非单项刷分", ["通用"], ["CVPR", "ACL", "NeurIPS"]),
    ("heatmap", heatmap, "模型×语言的成绩热力图", "矩阵式呈现，颜色区分强弱", ["LLM"], ["ACL", "EMNLP", "NeurIPS"]),
    ("violin", box_violin, "多种子分布（小提琴图）", "展示方差而非只报最优值", ["通用"], ["ICML", "NeurIPS", "ICLR"]),
    ("pareto", pareto, "帕累托前沿", "精度-延迟散点 + 前沿连线", ["系统"], ["MLSys", "ISCA", "MICRO", "HPCA"]),
    ("grouped-hatch", grouped_hatch, "跨数据集分组柱（带纹理）", "黑白打印也能区分的 hatch 画法", ["通用"], ["CVPR", "ECCV", "ICCV"]),
    ("sensitivity", sensitivity, "超参敏感性曲线", "log 轴 + 最优点标注", ["量化"], ["ICLR", "ICML", "DAC"]),
    ("cumulative", cumulative, "累积成功曲线（pass@k）", "多次尝试的累积成功率", ["RL"], ["NeurIPS", "ICLR", "ICML"]),
]