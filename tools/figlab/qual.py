#!/usr/bin/env python3
r"""实验图 · 定性（qualitative）：检测框、分割掩码、注意力热图、检索结果、失败案例。

用程序化生成的"合成图像"示意布局，代码可直接替换为自己的真实图片。
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402
import numpy as np  # noqa: E402

from common import OUT_FIG  # noqa: E402

RC = {
    "figure.dpi": 110, "savefig.dpi": 180, "font.size": 8.5,
    "axes.titlesize": 9, "mathtext.fontset": "cm", "font.family": "serif",
}


def _save(fig, name):
    p = os.path.join(OUT_FIG, name + ".png")
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    return p


def _fake_scene(seed=0, size=72):
    """合成一张"像照片"的底图：低频余弦叠加 + 柔和色团，避免白噪声感。"""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size] / size
    base = np.zeros((size, size, 3))
    # 3~4 个低频分量，构成平滑的大色块
    for ch in range(3):
        acc = np.full((size, size), 0.45 + 0.15 * rng.random())
        for _ in range(4):
            fx, fy = rng.uniform(0.6, 2.2, 2)
            ph = rng.uniform(0, 2 * np.pi)
            amp = rng.uniform(0.06, 0.16)
            acc += amp * np.sin(2 * np.pi * (fx * xx + fy * yy) + ph)
        base[..., ch] = acc
    # 若干柔和高斯色团（模拟物体）
    for _ in range(5):
        cy, cx = rng.uniform(0.15, 0.85, 2) * size
        s = rng.uniform(0.10, 0.22) * size
        blob = np.exp(-(((yy * size - cy) ** 2 + (xx * size - cx) ** 2) / (2 * s ** 2)))
        tone = rng.uniform(0.2, 0.6, 3)
        base += blob[..., None] * (tone - 0.4)
    # 轻微颗粒
    base += rng.normal(0, 0.012, base.shape)
    return np.clip(base, 0, 1)


def detection_grid():
    """检测结果：GT 框 vs 预测框。"""
    with plt.rc_context(RC):
        fig, axes = plt.subplots(2, 3, figsize=(6.0, 4.1))
        for r in range(2):
            for c in range(3):
                ax = axes[r][c]
                img = _fake_scene(seed=r * 3 + c)
                ax.imshow(img)
                ax.grid(False)
                rng = np.random.default_rng(r * 3 + c)
                for _ in range(3):
                    x, y = rng.integers(6, 40, 2)
                    w, h = rng.integers(14, 26, 2)
                    color = "#2E8B57" if r == 0 else "#C0392B"
                    ax.add_patch(mpatches.Rectangle((x, y), w, h, fill=False,
                                                    ec=color, lw=1.2))
                    ax.text(x, max(y - 2, 1), rng.choice(["car", "dog", "person"]),
                            fontsize=5.5, color="white",
                            bbox=dict(fc=color, ec="none", pad=0.8, alpha=0.9))
                ax.set_xticks([]); ax.set_yticks([])
                if r == 0 and c == 0:
                    ax.set_ylabel("Ours", fontsize=9, fontweight="bold")
                if r == 1 and c == 0:
                    ax.set_ylabel("Prior", fontsize=9, fontweight="bold")
        fig.tight_layout()
        return _save(fig, "fig-qual-detection")


def segmentation_compare():
    """分割掩码对比：原图 / GT / 预测。"""
    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 3, figsize=(6.0, 2.4))
        img = _fake_scene(seed=7)
        mask = np.zeros(img.shape[:2])
        mask[18:52, 14:48] = 1
        mask[30:60, 50:68] = 2
        axes[0].imshow(img); axes[0].set_title("Image")
        axes[1].imshow(mask, cmap="tab20"); axes[1].set_title("Ground truth")
        pred = mask.copy()
        pred[40:52, 40:48] = 2          # 误分类
        pred[30:38, 50:58] = 0          # 漏检
        axes[2].imshow(pred, cmap="tab20"); axes[2].set_title("Ours")
        for ax in axes:
            ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        fig.tight_layout()
        return _save(fig, "fig-qual-segmentation")


def attention_overlay():
    """注意力热图叠加。"""
    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 3, figsize=(6.0, 2.3))
        img = _fake_scene(seed=12)
        h, w = img.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        for ax, (cy, cx, s, t) in zip(axes, [(25, 30, 9, "Baseline"), (40, 48, 12, "Ours"),
                                             (20, 52, 10, "Ours + A")]):
            heat = np.exp(-(((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * s ** 2)))
            ax.imshow(img)
            ax.imshow(heat, cmap="jet", alpha=0.45)
            ax.set_title(t); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        fig.tight_layout()
        return _save(fig, "fig-qual-attention")


def retrieval_topk():
    """图文检索 top-k 结果卡。"""
    with plt.rc_context(RC):
        fig, axes = plt.subplots(2, 5, figsize=(6.2, 2.9))
        rng = np.random.default_rng(9)
        for r in range(2):
            for c in range(5):
                ax = axes[r][c]
                ax.imshow(_fake_scene(seed=r * 5 + c + 20))
                ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
                ok = rng.random() > (0.1 if r == 0 else 0.45)
                ax.add_patch(mpatches.Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                                                fill=False, ec="#2E8B57" if ok else "#C0392B",
                                                lw=2.0, clip_on=False))
                ax.set_title(("Rank %d " % (c + 1)) + ("O" if ok else "x"), fontsize=7,
                             color="#2E8B57" if ok else "#C0392B")
            axes[r][0].set_ylabel("Ours" if r == 0 else "Prior",
                                  fontsize=9, fontweight="bold")
        fig.tight_layout()
        return _save(fig, "fig-qual-retrieval")


def failure_panel():
    """失败案例分析面板。"""
    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 4, figsize=(6.4, 2.1))
        cases = [("Small object", 8), ("Heavy blur", 2), ("Occlusion", 5), ("Low contrast", 3)]
        for ax, (t, seed) in zip(axes, cases):
            img = _fake_scene(seed=seed)
            if t == "Heavy blur":
                img = np.apply_along_axis(lambda r: np.convolve(r, np.ones(7) / 7, "same"), 1, img)
            if t == "Low contrast":
                img = 0.5 + (img - 0.5) * 0.35
            ax.imshow(np.clip(img, 0, 1))
            ax.add_patch(mpatches.Rectangle((22, 22), 16, 16, fill=False, ec="#C0392B", lw=1.3))
            ax.set_title(t, fontsize=8); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        fig.tight_layout()
        return _save(fig, "fig-qual-failure")


def super_resolution():
    """超分/复原：LR / Baseline / Ours 三联。"""
    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 3, figsize=(6.0, 2.3))
        hr = _fake_scene(seed=15, size=96)
        lr = hr[::4, ::4].repeat(4, 0).repeat(4, 1)
        blur = np.apply_along_axis(lambda r: np.convolve(r, np.ones(5) / 5, "same"), 0, lr)
        for ax, (im, t) in zip(axes, [(lr, "Low-res input"), (blur, "Baseline"),
                                      (hr, "Ours")]):
            ax.imshow(np.clip(im, 0, 1)); ax.set_title(t)
            ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        fig.tight_layout()
        return _save(fig, "fig-qual-superres")


def depth_maps():
    """深度图 / 点云渲染对比。"""
    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 3, figsize=(6.0, 2.2))
        h, w = 60, 80
        yy, xx = np.mgrid[0:h, 0:w]
        depth = 1.0 / (1 + np.exp(-(yy - h / 2) / 8.0)) + 0.15 * np.sin(xx / 6.0)
        for ax, (d, t, cm) in zip(axes, [(depth, "GT depth", "viridis"),
                                         (depth + 0.05 * np.random.default_rng(1).normal(size=depth.shape),
                                          "Baseline", "viridis"),
                                         (depth, "Ours (points)", "magma")]):
            im = ax.imshow(d, cmap=cm)
            ax.set_title(t); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        fig.colorbar(im, ax=axes, fraction=0.02, pad=0.02, label="depth (m)")
        return _save(fig, "fig-qual-depth")


def video_frames():
    """视频序列关键帧对比。"""
    with plt.rc_context(RC):
        fig, axes = plt.subplots(2, 5, figsize=(6.2, 2.8))
        for r in range(2):
            for c in range(5):
                ax = axes[r][c]
                img = _fake_scene(seed=30 + c)
                if r == 1:
                    img = np.clip(img + 0.10 * np.sin(c), 0, 1)   # 模拟漂移/伪影
                ax.imshow(np.clip(img, 0, 1))
                ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
                ax.set_title("t=%d" % (c * 5), fontsize=7)
            axes[r][0].set_ylabel("Ours" if r == 0 else "Prior",
                                  fontsize=9, fontweight="bold")
        fig.tight_layout()
        return _save(fig, "fig-qual-video")


TEMPLATES = [
    ("detection", detection_grid, "检测结果对比网格", "2×3 网格，上排本文/下排对比方法，框与类别标注", ["检测"], ["CVPR", "ICCV", "ECCV"]),
    ("segmentation", segmentation_compare, "分割掩码对比", "原图 / GT / 预测三联，色块表示类别", ["分割"], ["CVPR", "ECCV", "MICCAI"]),
    ("attention", attention_overlay, "注意力热图叠加", "热力图叠在输入上，展示模型关注区域", ["多模态"], ["CVPR", "ICCV", "ACL"]),
    ("retrieval", retrieval_topk, "检索 Top-K 结果", "两行分别本文/对比，绿框正确红框错误", ["多模态"], ["CVPR", "ACM MM", "ACL"]),
    ("failure", failure_panel, "失败案例四连图", "把失败原因分类标注，审稿人很看重", ["通用"], ["CVPR", "NeurIPS", "ICLR"]),
    ("superres", super_resolution, "超分/复原对比", "低分输入 / 基线 / 本文", ["生成"], ["CVPR", "ECCV", "ICCV"]),
    ("depth", depth_maps, "深度图对比", "伪彩色深度图 + 色标", ["检测"], ["CVPR", "ICCV", "ICRA"]),
    ("video", video_frames, "视频关键帧对比", "两行×5 帧，展示时序一致性", ["生成"], ["CVPR", "ICCV", "NeurIPS"]),
]