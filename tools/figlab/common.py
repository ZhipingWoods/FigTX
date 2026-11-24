#!/usr/bin/env python3
r"""figlab 公共工具：TikZ 编译 + 图片转码。

框架图/动机图用 TikZ 画（矢量、可直接嵌进论文），
定量/定性图用 matplotlib 生成。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_FIG = os.path.join(ROOT, "public", "renders-fig")

# 框架图通用导言区：足够覆盖常见画法
TIKZ_PREAMBLE = r"""\documentclass[border=6pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{xcolor}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc,fit,backgrounds,shapes.geometric,
                shapes.multipart,shadows.blur,decorations.pathreplacing,
                patterns,matrix,chains}
\usepackage{amsmath,amssymb,bm}
% 统一的语义配色：一眼能分清模块角色
\definecolor{cinput}{HTML}{E8EEF6}
\definecolor{cinputb}{HTML}{A8BEDA}
\definecolor{cback}{HTML}{EDF3EA}
\definecolor{cbackb}{HTML}{9DBE93}
\definecolor{cmod}{HTML}{FDF0E6}
\definecolor{cmodb}{HTML}{E0A36B}
\definecolor{cours}{HTML}{FBE9EC}
\definecolor{coursb}{HTML}{D27D8C}
\definecolor{closs}{HTML}{F2EFF7}
\definecolor{clossb}{HTML}{A99BC4}
\definecolor{cgr}{HTML}{EFEFEF}
\definecolor{cgrb}{HTML}{9E9E9E}
% 中文支持（XeTeX）
\usepackage{xeCJK}
\setCJKmainfont{PingFang SC}
\begin{document}
"""


def compile_tikz(tex_body: str, out_webp: str, width: int = 1600,
                 assets: bool = False) -> bool:
    """把一段 TikZ 编译成 PNG→WebP。

    assets=True 时把 tools/figlab/assets/ 下的图片拷进编译目录，
    供 \includegraphics 引用（程序合成的"照片感"占位图）。
    """
    texbin = shutil.which("tectonic")
    if not texbin:
        print("tectonic 未安装", flush=True)
        return False
    os.makedirs(os.path.dirname(out_webp) or ".", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        if assets:
            adir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
            if os.path.isdir(adir):
                for f in os.listdir(adir):
                    shutil.copy2(os.path.join(adir, f), os.path.join(tmp, f))
        src = os.path.join(tmp, "main.tex")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(TIKZ_PREAMBLE + tex_body + "\n\\end{document}\n")
        proc = subprocess.run(
            [texbin, "main.tex", "--outdir", tmp, "--keep-logs"],
            cwd=tmp, capture_output=True, text=True, timeout=300,
        )
        pdf = os.path.join(tmp, "main.pdf")
        if not os.path.exists(pdf):
            errs = [l for l in (proc.stderr or "").split("\n") if "error:" in l][:2]
            print("   ! tikz 编译失败 %s: %s" % (os.path.basename(out_webp), "; ".join(errs)[:200]), flush=True)
            return False
        png = os.path.join(tmp, "main.png")
        if not _pdf_to_png(pdf, png):
            return False
        return _png_to_webp(png, out_webp, width)


def _pdf_to_png(pdf: str, out_png: str) -> bool:
    if shutil.which("pdftoppm"):
        try:
            subprocess.run(["pdftoppm", "-png", "-r", "200", "-f", "1", "-l", "1",
                            "-singlefile", pdf, out_png[:-4]],
                           capture_output=True, timeout=180, check=True)
            if os.path.exists(out_png):
                return True
        except Exception:
            pass
    if shutil.which("qlmanage"):
        d = os.path.dirname(out_png)
        try:
            subprocess.run(["qlmanage", "-t", "-s", "2000", "-o", d, pdf],
                           capture_output=True, timeout=180, check=True)
            produced = os.path.join(d, os.path.basename(pdf) + ".png")
            if os.path.exists(produced):
                os.replace(produced, out_png)
                return True
        except Exception:
            pass
    if shutil.which("sips"):
        try:
            subprocess.run(["sips", "-s", "format", "png", pdf, "--out", out_png],
                           capture_output=True, timeout=180, check=True)
            return os.path.exists(out_png)
        except Exception:
            pass
    return False


def _trim_white(png: str, pad: int = 6) -> str:
    """裁掉四周近白边距（standalone/qlmanage 会留下不对称留白）。

    只裁「整行/整列都接近纯白」的部分，保留 pad 像素缓冲，
    让最终图的墨迹占比不被无意义的空白稀释。
    """
    try:
        from PIL import Image
        import numpy as np
    except Exception:
        return png
    im = Image.open(png).convert("RGB")
    a = np.asarray(im)
    nonwhite = (a.min(axis=2) < 250)
    rows = np.where(nonwhite.any(axis=1))[0]
    cols = np.where(nonwhite.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return png
    y0 = max(0, rows[0] - pad)
    y1 = min(a.shape[0], rows[-1] + 1 + pad)
    x0 = max(0, cols[0] - pad)
    x1 = min(a.shape[1], cols[-1] + 1 + pad)
    if (x1 - x0) >= a.shape[1] - 2 and (y1 - y0) >= a.shape[0] - 2:
        return png
    out = png[:-4] + "_trim.png"
    im.crop((x0, y0, x1, y1)).save(out)
    return out


def _png_to_webp(png: str, out_webp: str, width: int) -> bool:
    if not shutil.which("cwebp"):
        shutil.copy2(png, out_webp[:-5] + ".png")
        return False
    png = _trim_white(png)
    r = subprocess.run(["cwebp", "-quiet", "-q", "88", "-m", "6",
                        "-resize", str(width), "0", png, "-o", out_webp],
                       capture_output=True, timeout=120)
    return r.returncode == 0 and os.path.exists(out_webp) and os.path.getsize(out_webp) > 0


def emit(items: list[dict], name: str) -> None:
    import json
    out = os.path.join(ROOT, "data", name)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)
    print("wrote %s (%d)" % (out, len(items)), flush=True)
