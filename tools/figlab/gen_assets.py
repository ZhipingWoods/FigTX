#!/usr/bin/env python3
r"""生成框架图里用的"照片感"占位图（程序合成，非真实照片）。

输出到 tools/figlab/assets/，供 TikZ \includegraphics 引用。
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def scene(seed: int, size=(220, 220)) -> Image.Image:
    """合成一张暗色调、有主体与高光的"照片感"图。"""
    rng = np.random.default_rng(seed)
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w] / max(w, h)

    # 深色背景：径向渐变 + 轻微噪声
    cx, cy = rng.uniform(0.35, 0.65, 2)
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    base = np.clip(0.42 - 0.9 * r, 0, 1)

    img = np.zeros((h, w, 3))
    # 青色主光
    img[..., 0] = base * 0.25
    img[..., 1] = base * 0.85
    img[..., 2] = base * 1.00
    # 暖色副光（右下）
    warm = np.clip(1.2 - 2.2 * np.sqrt((xx - 0.82) ** 2 + (yy - 0.78) ** 2), 0, 1) ** 2
    img[..., 0] += warm * 0.95
    img[..., 1] += warm * 0.32
    img[..., 2] += warm * 0.22
    # 洋红/紫高光（左上）
    mag = np.clip(1.1 - 2.4 * np.sqrt((xx - 0.20) ** 2 + (yy - 0.26) ** 2), 0, 1) ** 2
    img[..., 0] += mag * 0.72
    img[..., 1] += mag * 0.10
    img[..., 2] += mag * 0.62

    # 主体剪影（不规则块，模拟物体）
    sil = np.zeros((h, w))
    for _ in range(3):
        bx, by = rng.uniform(0.2, 0.8, 2)
        bw, bh = rng.uniform(0.18, 0.42, 2)
        m = ((np.abs(xx - bx) < bw / 2) & (np.abs(yy - by) < bh / 2)).astype(float)
        sil = np.maximum(sil, m)
    img[sil > 0] *= 0.32

    img += rng.normal(0, 0.020, img.shape)          # 颗粒
    img = np.clip(img, 0, 1)

    im = Image.fromarray((img * 255).astype(np.uint8))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    return im


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    for i in range(4):
        p = os.path.join(OUT, "frame%d.png" % i)
        scene(i + 1).save(p, optimize=True)
        print("wrote", p)
    # 输入叠层用的小图
    scene(9, (180, 200)).save(os.path.join(OUT, "input.png"), optimize=True)
    print("wrote input.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
