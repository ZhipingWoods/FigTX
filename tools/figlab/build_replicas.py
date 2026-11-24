#!/usr/bin/env python3
r"""汇总论文图复刻 → data/raw-replicas.json"""
from __future__ import annotations

import inspect
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import replicas  # noqa: E402
import reps_tikz  # noqa: E402


_HEADER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code_header.py")


_TIKZ_HEADER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "code_header_tikz.tex")


def _tikz_body(fn) -> str:
    """调用 figXX() 拿到纯 TikZ 字符串（不含 Python 包装）。"""
    return fn().strip()


# 框架图（matplotlib 重绘版）
import frameworks_mpl  # noqa: E402

FRAMEWORK_REPLICAS = [
    ("05-architecture", frameworks_mpl.fig05_arch,
     "架构 · 三面板流程与模块放大",
     "左侧破坏性堆叠条拆解显存、右侧横向条对比端到端延迟；面板 (a) 分块自回归 "
     "训练流程、(b) 整体架构、(c) Linear DiT 模块。所有连线用正交折线绘制，无斜线。",
     "architecture", ["CVPR", "ICCV", "NeurIPS"], ["生成"]),
    ("06-mechanism", frameworks_mpl.fig06_mech,
     "机制 · 张量结构与缓存策略",
     "四联面板：Vanilla Attention 全绿矩阵、Linear Attention 双块堆叠、"
     "Causal Linear Attention 的 KV Cache/Mask/Compute 三色划分、Mix-FFN 分块缓存。",
     "mechanism", ["ICLR", "ICML", "NeurIPS"], ["效率"]),
]


def _mpl_code(fn) -> str:
    """matplotlib 图的完整可运行代码（含 import/配色/助手）。"""
    name = fn.__name__
    body = inspect.getsource(fn).strip()
    fw_hdr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code_header_fw.py")
    with open(fw_hdr, encoding="utf-8") as fh:
        head = fh.read().rstrip()
    return head + "\n\n\n" + body + "\n\n\nif __name__ == \"__main__\":\n    " + name + "()\n"

def _tikz_code(body: str) -> str:
    """TikZ 片段 → 完整可编译的 LaTeX 文档。"""
    with open(_TIKZ_HEADER, encoding="utf-8") as fh:
        head = fh.read().rstrip()
    return head + "\n\n" + body.strip() + "\n\n\\end{document}\n"


def src_of(fn) -> str:
    """函数源码 + 可运行头部（import/配色/助手），保证复制走能直接跑。"""
    fw_hdr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code_header_fw.py")
    with open(fw_hdr, encoding="utf-8") as fh:
        header = fh.read().rstrip()
    body = inspect.getsource(fn).strip()
    return header + "\n\n\n" + body + "\n\n\nif __name__ == \"__main__\":\n    " \
        + fn.__name__ + "()\n"


def main() -> int:
    items = []
    for slug, fn, title, desc, figtype, venues, domain in replicas.REPLICAS:
        png = os.path.join(common.OUT_FIG, "rep-" + slug + ".png")
        webp = os.path.join(common.OUT_FIG, "rep-" + slug + ".webp")
        # 只要 PNG 比 WebP 新就重转，否则改了代码看不到效果
        need = os.path.exists(png) and (
            not os.path.exists(webp)
            or os.path.getmtime(png) > os.path.getmtime(webp))
        if need:
            common._png_to_webp(png, webp, 1500)
        if not os.path.exists(webp):
            print("  ! missing", slug)
            continue
        items.append({
            "id": "rep-" + slug,
            "group": "replicas",
            "category": "figure",
            "figType": figtype,
            "kind": "chart",
            "title": title,
            "caption": desc,
            "domain": domain,
            "venues": venues,
            "styles": ["matplotlib"],
            "code": src_of(fn),
            "codeLang": "python",
            "render": "renders-fig/rep-%s.webp" % slug,
            "palette": [],
            "source": {"repo": None, "repoUrl": None,
                       "license": "本项目原创复刻", "stars": 0, "path": None},
        })

    # 框架图（05 架构 / 06 机制）：matplotlib 版，线条用 FancyArrowPatch 严格正交
    for slug, fn, title, desc, figtype, venues, domain in FRAMEWORK_REPLICAS:
        png = fn()
        webp = os.path.join(common.OUT_FIG, "rep-" + slug + ".webp")
        common._png_to_webp(png, webp, 1600)
        items.append({
            "id": "rep-" + slug,
            "group": "replicas",
            "category": "figure",
            "figType": figtype,
            "kind": "diagram",
            "title": title,
            "caption": desc,
            "domain": domain,
            "venues": venues,
            "styles": ["matplotlib", "framework"],
            "code": _mpl_code(fn),
            "codeLang": "python",
            "render": "renders-fig/rep-%s.webp" % slug,
            "palette": [],
            "source": {"repo": None, "repoUrl": None,
                       "license": "本项目原创复刻", "stars": 0, "path": None},
        })

    common.emit(items, "raw-replicas.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
