#!/usr/bin/env python3
r"""把科学绘图样式库（SciencePlots 等）渲染成可直接浏览的「图」条目。

输出:
    public/renders-fig/<id>.png     示范图
    data/raw-figures.json           条目元数据

用法:
    .venv-fig/bin/python tools/ingest_figures.py
"""
from __future__ import annotations

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import scienceplots  # noqa: F401,E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "renders-fig")

REPO = {
    "repo": "garrettj403/SciencePlots",
    "url": "https://github.com/garrettj403/SciencePlots",
    "license": "MIT",
    "stars": 9416,
}

# (id, styles, 标题, 说明)
STYLES: list[tuple[str, list[str], str, str]] = [
    ("science", ["science"], "Science 基础风格", "SciencePlots 默认：细刻度朝内、上下左右都有刻度、蓝绿橙红紫灰六色循环"),
    ("science-ieee", ["science", "ieee"], "Science + IEEE", "IEEE 双栏：黑色优先 + 线型区分（黑实线/红虚线/蓝点线），黑白打印也能分清"),
    ("science-nature", ["science", "nature"], "Science + Nature", "Nature 版式：更紧凑的字号与边距，适合单栏窄图"),
    ("science-grid", ["science", "grid"], "Science + 网格", "开启网格线，便于读数值"),
    ("science-notebook", ["science", "notebook"], "Science + Notebook", "Jupyter 宽幅版式，屏幕阅读更舒服"),
    ("science-scatter", ["science", "scatter"], "Science + 散点", "针对散点图优化点大小与透明度"),
    ("science-sans", ["science", "sans"], "Science 无衬线", "改用无衬线字体，投影/海报也清晰"),
    ("science-bright", ["science", "bright"], "Science + 明亮配色", "高亮度色板，适合少量类别对比"),
    ("science-vibrant", ["science", "vibrant"], "Science + 鲜艳配色", "更饱和的色板，适合强调差异"),
    ("science-muted", ["science", "muted"], "Science + 低饱和配色", "灰调色板，正文排版更克制"),
    ("science-retro", ["science", "retro"], "Science + 复古配色", "低对比复古色板"),
    ("science-highvis", ["science", "high-vis"], "Science + 高可视", "高辨识度配色，色觉障碍友好"),
    ("science-light", ["science", "light"], "Science 浅色", "浅灰背景与浅色坐标轴"),
    ("science-dark", ["science", "dark_background"], "Science + 深色", "深色背景，适合幻灯片"),
    ("science-cjk", ["science", "cjk-sc-font"], "Science + 中文字体", "中文论文：坐标轴与图例可正常显示中文"),
    ("matplotlib-default", [], "matplotlib 默认", "对照组：不加任何样式的原生效果"),
]


def demo(sty: list[str], out_png: str, cjk: bool = False) -> list[str]:
    plt.style.use(sty + ["no-latex"] if sty else ["default"])
    plt.rcdefaults()                      # 关键：清掉上一个样式的残留（如深色背景）
    matplotlib.style.use(sty + ["no-latex"] if sty else ["default"])
    rc = {
        "figure.figsize": (8.4, 6.2) if cjk else (7.2, 5.0),
        "figure.dpi": 110,
        "savefig.dpi": 170,
        "axes.titlesize": 10,
        "legend.frameon": True,
    }
    if cjk:
        rc["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Songti SC", "Arial Unicode MS"]
        rc["font.family"] = "sans-serif"
        rc["axes.unicode_minus"] = False

    with plt.rc_context(rc):
        fig, axes = plt.subplots(2, 2)
        x = np.linspace(0, 2 * np.pi, 40)
        zh = cjk

        ax = axes[0][0]
        for k in (1, 1.5, 2):
            ax.plot(x, np.sin(k * x) / k, marker="o", markersize=3,
                    label=("谐波 ω=%s" % k) if zh else (r"$\omega=%s$" % k))
        ax.set_xlabel("相位 Phase (rad)" if zh else "Phase (rad)")
        ax.set_ylabel("幅值 Amplitude" if zh else "Amplitude")
        ax.set_title("谐波响应" if zh else "Harmonic response")
        ax.legend()

        ax = axes[0][1]
        labels = ["A", "B", "C", "D"]
        ax.bar(labels, [0.42, 0.68, 0.55, 0.81], yerr=[0.05, 0.08, 0.04, 0.06], capsize=3)
        ax.set_ylabel("准确率" if zh else "Accuracy")
        ax.set_title("误差棒" if zh else "Error bars")

        ax = axes[1][0]
        rng = np.random.default_rng(0)
        sc = ax.scatter(rng.normal(size=80), rng.normal(size=80),
                        c=rng.random(80), s=18)
        fig.colorbar(sc, ax=ax, label="分数" if zh else "score")
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.set_title("散点" if zh else "Scatter")

        ax = axes[1][1]
        t = np.linspace(0, 6, 100)
        y = 1 - np.exp(-t)
        ax.plot(t, y, label="拟合" if zh else "fit")
        ax.fill_between(t, y * 0.9, y * 1.1, alpha=0.25)
        ax.set_xlabel("时间" if zh else "Time (s)")
        ax.set_ylabel("覆盖率" if zh else "Coverage")
        ax.set_title("拟合与区间" if zh else "Fit & band")

        fig.tight_layout()
        fig.savefig(out_png, bbox_inches="tight")

        cycle = []
        try:
            for c in matplotlib.rcParams["axes.prop_cycle"].by_key().get("color", [])[:6]:
                cycle.append(c if c.startswith("#") else matplotlib.colors.to_hex(c))
        except Exception:
            pass
        plt.close(fig)
    return cycle


def gallery(out_png: str) -> None:
    """16 种样式各画一小图，再拼成 4x4 画廊（中文标题用 PIL + PingFang 绘制）。

    注意：必须在 plt.style.context() 内部**新建** figure，
    rcParams 才会真正作用到该子图上（先建图再套样式是无效的）。
    """
    from PIL import Image as _Im, ImageDraw, ImageFont
    import tempfile

    x = np.linspace(0, 2 * np.pi, 30)
    tmpd = tempfile.mkdtemp()
    tiles = []
    for sid, styles, title, _desc in STYLES:
        plt.rcdefaults()
        with plt.style.context(styles + ["no-latex"] if styles else ["default"]):
            fig, ax = plt.subplots(figsize=(3.05, 1.95))
            for w, ls in ((1, "-"), (1.5, "--"), (2, ":")):
                ax.plot(x, np.sin(w * x) / w, ls, lw=1.15, marker="o",
                        markersize=1.8, label="w=%s" % w)
            ax.legend(loc="upper right", fontsize=5.4, handlelength=1.1,
                      frameon=True)
            ax.set_xlabel("x", fontsize=6)
            ax.set_ylabel("y", fontsize=6)
            ax.tick_params(labelsize=5.4)
            fig.tight_layout(pad=0.35)
            p = os.path.join(tmpd, sid + ".png")
            fig.savefig(p, dpi=170, facecolor="white")
            plt.close(fig)
        tiles.append((sid, title, p))

    # 拼图
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    probes = _Im.open(tiles[0][2])
    tw, th = probes.size
    probes.close()
    lab_h, gap = 30, 12
    cw, chh = tw + gap * 2, th + lab_h + gap
    W, H = cw * cols, chh * rows

    font = None
    for fp in ("/System/Library/Fonts/Hiragino Sans GB.ttc",
               "/System/Library/Fonts/Supplemental/Songti.ttc",
               "/Library/Fonts/Arial Unicode.ttf"):
        try:
            font = ImageFont.truetype(fp, 16, index=0)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    canvas = _Im.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(canvas)
    for k, (sid, title, p) in enumerate(tiles):
        r_, c_ = k // cols, k % cols
        ox, oy = c_ * cw + gap, r_ * chh
        canvas.paste(_Im.open(p), (ox, oy + lab_h))
        dr.text((ox + tw // 2, oy + lab_h - 10), title, font=font,
                fill=(15, 15, 15), anchor="mm")
    canvas.save(out_png)
    # 应用/审计约定用 webp
    webp = os.path.splitext(out_png)[0] + ".webp"
    try:
        import subprocess
        subprocess.run(["cwebp", "-q", "88", "-resize", "1600", "0",
                        out_png, "-o", webp],
                       check=True, capture_output=True)
        print("  gallery ->", out_png, canvas.size, "| webp", os.path.getsize(webp) // 1024, "KB")
    except Exception as e:
        print("  ! webp 转换失败:", str(e)[:60])

def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)

    # SciencePlots 的 16 种样式原本是 16 张几乎相同的图（dHash 测出 93 对近重复，
    # 其中 2 对完全相同）。合并成一张 4x4 画廊：一屏看全，选中再复制样式名。
    png = os.path.join(OUT_DIR, "fig-science-gallery.png")
    gallery(png)

    code = (
        "import matplotlib.pyplot as plt\n"
        "import matplotlib\n"
        "import scienceplots  # pip install SciencePlots\n"
        "import numpy as np\n\n"
        "# 16 种样式，名字直接抄到 plt.style.use 里用\n"
        "STYLES = [\n"
    )
    for _sid, styles, title, _d in STYLES:
        code += "    (%r, %r),\n" % (title, styles + ["no-latex"])
    code += (
        "]\n\n"
        "x = np.linspace(0, 2 * np.pi, 30)\n"
        "y = np.sin(x) / 1.0\n\n"
        "# 画一张 4x4 画廊\n"
        "fig, axes = plt.subplots(4, 4, figsize=(13.6, 8.6))\n"
        "for k, (name, sty) in enumerate(STYLES):\n"
        "    ax = axes[k // 4][k % 4]\n"
        "    plt.rcdefaults()                 # 关键：先清掉上个样式的残留\n"
        "    matplotlib.style.use(sty)\n"
        "    for w, ls in ((1, '-'), (1.5, '--'), (2, ':')):\n"
        "        ax.plot(x, np.sin(w * x) / w, ls, lw=1.3, marker='o', markersize=2,\n"
        "                label=r'$\\omega=%s$' % w)\n"
        "    ax.set_title(name, fontweight='bold')\n"
        "    ax.legend(loc='upper right')\n"
        "plt.tight_layout()\n"
        "plt.savefig('style-gallery.pdf', bbox_inches='tight')  # 投稿用矢量图\n"
        "\n"
        "# 只用其中一种：\n"
        "# plt.style.use(['science', 'ieee', 'no-latex'])\n"
    )

    items = [{
        "id": "fig-science-gallery",
        "category": "figure",
        "kind": "chart",
        "title": "SciencePlots 样式合集（16 种）",
        "caption": "同一张图套 16 种期刊样式，一屏对比：基础 / IEEE / Nature / 网格 / "
                   "Notebook / 散点 / 无衬线 / 明亮 / 鲜艳 / 低饱和 / 复古 / 高可视 / "
                   "浅色 / 深色 / 中文字体 / matplotlib 默认。选好样式名直接复制到 "
                   "plt.style.use() 即可。",
        "styles": ["science", "no-latex", "gallery"],
        "code": code,
        "codeLang": "python",
        "render": "renders-fig/fig-science-gallery.webp",
        "palette": ["#0C5DA5", "#00B945", "#FF9500", "#FF2C00",
                    "#845B97", "#474747"],
        "source": {
            "repo": REPO["repo"],
            "repoUrl": REPO["url"],
            "license": REPO["license"],
            "stars": REPO["stars"],
            "path": "src/scienceplots/styles",
        },
    }]

    out = os.path.join(ROOT, "data", "raw-figures.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)
    print("wrote %s (%d items)" % (out, len(items)))
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
