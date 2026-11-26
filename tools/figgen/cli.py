#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FigTX 框架图生成 CLI。

用法：
  # 从方法描述生成（可带参考图）
  python3 tools/figgen/cli.py \
      --method-file paper_method.txt \
      --reference public/renders-fig/rep-05-architecture.webp \
      --target pipeline --rounds 3 --preview

  # 只用描述、不要参考图
  python3 tools/figgen/cli.py --method "..." --target teaser

  # 分析一张参考图、只导出设计契约（不生成）
  python3 tools/figgen/cli.py --analyse-only public/renders-fig/rep-05-architecture.webp
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from figgen import contract as C
from figgen import generate as G
from figgen import render as R


def main() -> int:
    ap = argparse.ArgumentParser(description="FigTX 论文框架图生成器")
    ap.add_argument("--method", help="方法描述文本")
    ap.add_argument("--method-file", help="从文件读方法描述")
    ap.add_argument("--reference", help="参考图路径（提取设计契约）")
    ap.add_argument("--target", default="pipeline",
                    choices=["pipeline", "teaser", "motivation", "comparison", "system"])
    ap.add_argument("--rounds", type=int, default=3, help="最多生成轮数")
    ap.add_argument("--model", help="覆盖默认模型")
    ap.add_argument("--out", help="输出目录")
    ap.add_argument("--preview", action="store_true", help="额外渲染 PNG/WebP 预览")
    ap.add_argument("--analyse-only", metavar="IMAGE",
                    help="只分析参考图并打印设计契约")
    args = ap.parse_args()

    if args.analyse_only:
        c = C.extract(args.analyse_only, model=args.model)
        if not c:
            print("提取失败", file=sys.stderr)
            return 2
        print(json.dumps(c, ensure_ascii=False, indent=1))
        print()
        print("=== 渲染成提示词 ===")
        print(C.to_prompt(c))
        return 0

    method = args.method
    if args.method_file:
        method = open(args.method_file, encoding="utf-8").read()
    if not method:
        ap.error("需要 --method 或 --method-file")

    res = G.generate(
        method=method,
        reference_image=args.reference,
        target=args.target,
        max_rounds=args.rounds,
        model=args.model,
        save_dir=args.out,
        verbose=True,
    )

    print()
    print("轮数: %d | 最佳分: %.1f/10" % (res["rounds"], res["best_score"]))
    if res.get("svg_path"):
        print("SVG: " + res["svg_path"])
        if args.preview:
            png = res["svg_path"].replace(".svg", ".png")
            if R.svg_to_png(res["svg_path"], png):
                print("PNG: " + png)
                webp = res["svg_path"].replace(".svg", ".webp")
                if R.png_to_webp(png, webp):
                    print("WebP: " + webp)
            else:
                print("（预览渲染失败，可只用 SVG）")
    else:
        print("未产出合格 SVG")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
