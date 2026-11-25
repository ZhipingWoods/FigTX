#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 LaTeX 编译失败的表生成「占位预览」——避免卡片一片空白。

背景：216 张表里有 31 张的 LaTeX 源码是残缺片段（从 docx 抽取时被截断，
实测 table-262 有 tabular 套 tabular、table-75 环境不配平），
无论怎么修都编不过。与其让卡片看不见，不如明确告诉用户原因。

用法：python3 tools/make_placeholder.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "renders")
FAIL = "/tmp/rtest7/_failures.json"


def _font(size):
    for fp in ("/System/Library/Fonts/Hiragino Sans GB.ttc",
               "/System/Library/Fonts/Supplemental/Songti.ttc",
               "/Library/Fonts/Arial Unicode.ttf"):
        try:
            return ImageFont.truetype(fp, size, index=0)
        except Exception:
            continue
    return ImageFont.load_default()


def main() -> int:
    items = {i["id"]: i for i in json.load(open(os.path.join(ROOT, "data/raw-items.json"),
                                                encoding="utf-8"))}
    fails = []
    if os.path.exists(FAIL):
        fails = json.load(open(FAIL, encoding="utf-8"))
    if not fails:
        # 没有失败清单就从 items.json 里找无渲染的
        cur = json.load(open(os.path.join(ROOT, "src/data/items.json"), encoding="utf-8"))
        fails = [{"id": i["id"], "error": ""} for i in cur["items"]
                 if i["category"] == "table" and not i.get("render")]
    f_t = _font(30)
    f_s = _font(19)
    f_m = _font(15)
    made = 0
    for f in fails:
        tid = f["id"]
        it = items.get(tid, {})
        m = re.search(r"main\.tex:(\d+): ([^;]+)", f.get("error", ""))
        err = (m.group(2).strip() if m else f.get("error", ""))[:110] or "未知编译错误"
        W, H = 1200, 420
        im = Image.new("RGB", (W, H), "#FBF7F5")
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, W - 1, H - 1], outline="#E0C8C0", width=3)
        # 顶部色带
        d.rectangle([0, 0, W, 76], fill="#F5E4DE")
        d.text((36, 24), "⚠ 这张表的 LaTeX 源码残缺，无法编译出图", font=f_t, fill="#8C2D18")
        y = 108
        title = (it.get("title") or "")[:54]
        d.text((36, y), "表格：" + title, font=f_s, fill="#241A17")
        y += 38
        d.text((36, y), "编号：" + tid, font=f_m, fill="#6B5A55")
        y += 32
        d.text((36, y), "编译错误：", font=f_m, fill="#6B5A55")
        y += 26
        # 错误信息换行
        line = ""
        for ch in err:
            if d.textlength(line + ch, font=f_m) > W - 90:
                d.text((54, y), line, font=f_m, fill="#8C2D18"); y += 24; line = ch
            else:
                line += ch
        if line:
            d.text((54, y), line, font=f_m, fill="#8C2D18")
        y += 44
        for t in ("源码来自原作者分享的 docx，抽取时被截断（环境不配平 / 命令未定义）。",
                  "该表的 LaTeX 仍可在卡片里完整复制——需要时自行补全后再编译。"):
            d.text((36, y), t, font=f_m, fill="#4A3B37")
            y += 28
        png = os.path.join(OUT, tid + ".png")
        im.save(png)
        # 转 webp，和正常表一致
        try:
            subprocess.run(["cwebp", "-quiet", "-q", "90", "-resize", "1500", "0",
                            png, "-o", os.path.join(OUT, tid + ".webp")],
                           check=True, capture_output=True)
        except Exception:
            pass
        made += 1
    print("生成占位预览:", made, "张")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
