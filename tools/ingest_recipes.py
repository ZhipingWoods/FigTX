#!/usr/bin/env python3
r"""把 paper-plot-skills 里的绘图脚本跑出成图，做成「图」条目。

不修改原脚本：运行时 monkeypatch savefig 重定向输出，并关掉 usetex。

用法:
    .venv-fig/bin/python tools/ingest_recipes.py --repo /tmp/xhs/repos/paper-plot-skills-main
"""
from __future__ import annotations

import argparse
import json
import os
import runpy
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "renders-fig")

REPO = {
    "repo": "Trae1ounG/paper-plot-skills",
    "url": "https://github.com/Trae1ounG/paper-plot-skills",
    "license": "见仓库",
    "stars": 973,
}

# 脚本名 → (标题, 说明)
RECIPES = {
    "line_loss_inset": ("训练曲线 + 局部放大", "L 形坐标轴 + 箭头，右下角 inset 放大局部并画虚线连接，论文里最常用的“损失曲线”画法"),
    "line_aime": ("多方法收敛曲线", "多条曲线 + 图例，适合展示随训练步数的指标变化"),
    "line_selfdistill": ("蒸馏训练曲线（双图）", "主图 + 缩放对比图，突出后期差异"),
    "bar_spice": ("分组柱状图", "多组对比 + 数值标注，适合 baseline 比较"),
    "bar_memevolve": ("横向/分组柱状图", "强调组间差异的柱状布局"),
    "radar_dora": ("雷达图（双序列）", "多维度能力对比，适合展示模型在多个任务上的均衡性"),
    "scatter_break": ("断轴散点", "坐标轴断开处理离群点，避免压缩主体分布"),
    "scatter_tsne": ("t-SNE 聚类散点", "类别着色 + 图例，展示特征空间可分性"),
}

_SAVE_TARGET: list[str] = []
_ORIG_SAVEFIG = Figure.savefig
_ORIG_UPDATE = matplotlib.rcParams.update


def _no_usetex_update(self, *a, **kw):
    """脚本自己会 rcParams.update({text.usetex: True})，这里统一压掉。"""
    d = dict(*a, **kw)
    d.pop('text.usetex', None)
    return _ORIG_UPDATE(d)


def _patched_savefig(self, fname, *a, **kw):  # noqa: D401
    target = _SAVE_TARGET[0] if _SAVE_TARGET else str(fname)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    kw.pop("bbox_inches", None)
    return _ORIG_SAVEFIG(self, target, bbox_inches="tight", dpi=kw.pop("dpi", 170), **kw)


def run_recipe(script: str, out_png: str) -> bool:
    _SAVE_TARGET[:] = [out_png]
    old = plt.rcParams.get("text.usetex", False)
    try:
        plt.rcdefaults()
        matplotlib.rcParams["text.usetex"] = False
        matplotlib.rcParams["font.family"] = "serif"
        matplotlib.rcParams["font.serif"] = ["STIXGeneral", "DejaVu Serif"]
        matplotlib.rcParams["mathtext.fontset"] = "cm"
        Figure.savefig = _patched_savefig
        matplotlib.rcParams.update = _no_usetex_update.__get__(matplotlib.rcParams)
        runpy.run_path(script, run_name="__main__")
        return os.path.exists(out_png) and os.path.getsize(out_png) > 0
    except Exception as e:  # noqa: BLE001
        print("   ! %s: %s" % (os.path.basename(script), str(e)[:160]), file=sys.stderr)
        return False
    finally:
        Figure.savefig = _ORIG_SAVEFIG
        matplotlib.rcParams.update = _ORIG_UPDATE
        matplotlib.rcParams["text.usetex"] = old


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    args = ap.parse_args()

    scripts_dir = os.path.join(args.repo, "plot-from-data", "scripts")
    os.makedirs(OUT_DIR, exist_ok=True)
    items = []
    for name, (title, desc) in RECIPES.items():
        script = os.path.join(scripts_dir, name + ".py")
        if not os.path.exists(script):
            print("  skip (missing)", name)
            continue
        rid = "fig-" + name.replace("_", "-")
        png = os.path.join(OUT_DIR, rid + ".png")
        ok = run_recipe(script, png)
        print(("  ok " if ok else "  fail ") + name)
        if not ok:
            continue
        code = open(script, encoding="utf-8").read()
        items.append({
            "id": rid,
            "category": "figure",
            "kind": "chart",
            "title": title,
            "caption": desc,
            "styles": ["matplotlib", "paper-plot-skills"],
            "code": code,
            "codeLang": "python",
            "render": "renders-fig/%s.png" % rid,
            "palette": [],
            "source": {
                "repo": REPO["repo"],
                "repoUrl": REPO["url"],
                "license": REPO["license"],
                "stars": REPO["stars"],
                "path": "plot-from-data/scripts/%s.py" % name,
            },
        })

    out = os.path.join(ROOT, "data", "raw-recipes.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)
    print("wrote %s (%d items)" % (out, len(items)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
