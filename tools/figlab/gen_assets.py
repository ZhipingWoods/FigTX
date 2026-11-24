#!/usr/bin/env python3
r"""生成框架图里用的"照片感"占位图（程序合成，非真实照片）。

输出到 tools/figlab/assets/，供 TikZ \includegraphics 引用。
为了贴近论文里的真实生成图，这里刻意加高频细节与强对比。
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _fractal_noise(rng, h, w, octaves=5):
    """多尺度分形噪声，制造高频纹理。"""
    out = np.zeros((h, w))
    amp = 1.0
    for o in range(octaves):
        gh, gw = max(2, h >> (octaves - o)), max(2, w >> (octaves - o))
        g = rng.random((gh, gw))
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += amp * (np.asarray(im, dtype=float) / 255.0)
        amp *= 0.55
    out -= out.min()
    return out / (out.max() + 1e-9)


def scene(seed: int, size=(240, 240)) -> Image.Image:
    """合成一张暗色调、高细节的"照片感"图。"""
    rng = np.random.default_rng(seed)
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w] / max(w, h)

    # 深色背景：径向渐变
    cx, cy = rng.uniform(0.35, 0.65, 2)
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    base = np.clip(0.50 - 1.1 * r, 0, 1) ** 1.3

    img = np.zeros((h, w, 3))
    img[..., 0] = base * 0.22
    img[..., 1] = base * 0.88
    img[..., 2] = base * 1.00

    # 暖色副光（右下）
    warm = np.clip(1.25 - 2.4 * np.sqrt((xx - 0.80) ** 2 + (yy - 0.76) ** 2), 0, 1) ** 1.8
    img[..., 0] += warm * 1.00
    img[..., 1] += warm * 0.34
    img[..., 2] += warm * 0.20
    # 洋红高光（左上）
    mag = np.clip(1.15 - 2.6 * np.sqrt((xx - 0.18) ** 2 + (yy - 0.24) ** 2), 0, 1) ** 1.8
    img[..., 0] += mag * 0.85
    img[..., 1] += mag * 0.08
    img[..., 2] += mag * 0.72

    # 高频分形纹理（模拟真实图像的细节）
    tex = _fractal_noise(rng, h, w, 5)
    img *= (0.45 + 1.10 * tex)[..., None]

    # 强对比：拉一道 S 曲线
    img = np.clip(img, 0, 1)
    img = img ** 1.25
    img = np.clip((img - 0.5) * 1.45 + 0.5, 0, 1)

    # 主体剪影（不规则块 + 边缘）
    sil = np.zeros((h, w))
    for _ in range(4):
        bx, by = rng.uniform(0.18, 0.82, 2)
        bw, bh = rng.uniform(0.15, 0.45, 2)
        m = ((np.abs(xx - bx) < bw / 2) & (np.abs(yy - by) < bh / 2)).astype(float)
        sil = np.maximum(sil, m)
    img[sil > 0] *= 0.22
    # 剪影边缘提亮一圈（轮廓光）
    edge = np.abs(Image.fromarray((sil * 255).astype(np.uint8))
                  .filter(ImageFilter.FIND_EDGES)).astype(float) / 255.0
    img += np.clip(edge, 0, 1)[..., None] * np.array([0.95, 0.55, 0.30]) * 0.55

    # 细颗粒
    img += rng.normal(0, 0.022, img.shape)
    img = np.clip(img, 0, 1)

    im = Image.fromarray((img * 255).astype(np.uint8))
    return im.filter(ImageFilter.GaussianBlur(0.35))


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    for i in range(4):
        p = os.path.join(OUT, "frame%d.png" % i)
        scene(i + 1).save(p, optimize=True)
        print("wrote", p)
    scene(9, (200, 220)).save(os.path.join(OUT, "input.png"), optimize=True)
    print("wrote input.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
