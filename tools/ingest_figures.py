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


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    items = []
    for sid, styles, title, desc in STYLES:
        png = os.path.join(OUT_DIR, "fig-" + sid + ".png")
        cjk = sid.endswith("cjk")
        cycle = demo(styles, png, cjk=cjk)
        code = "import matplotlib.pyplot as plt\nimport scienceplots\n\n"
        code += "plt.style.use(%r)\n" % (styles + ["no-latex"])
        code += "plt.figure(figsize=(3.5, 2.6))\n"
        code += "plt.plot(x, y, marker='o', label='Ours')\n"
        code += "plt.xlabel('Phase (rad)'); plt.ylabel('Amplitude')\n"
        code += "plt.legend()\n"
        code += "plt.savefig('fig.pdf', bbox_inches='tight')  # 投稿用矢量图\n"
        items.append({
            "id": "fig-" + sid,
            "category": "figure",
            "kind": "chart",
            "title": title,
            "caption": desc,
            "styles": styles + ["no-latex"],
            "code": code,
            "codeLang": "python",
            "render": "renders-fig/fig-%s.png" % sid,
            "palette": cycle,
            "source": {
                "repo": REPO["repo"],
                "repoUrl": REPO["url"],
                "license": REPO["license"],
                "stars": REPO["stars"],
                "path": "src/scienceplots/styles",
            },
        })
        print("  rendered", sid, "palette", cycle[:3])

    out = os.path.join(ROOT, "data", "raw-figures.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)
    print("wrote %s (%d items)" % (out, len(items)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
