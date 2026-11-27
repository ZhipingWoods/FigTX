#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给每个条目分配稳定编号，写入 data/catalog.json。

设计原则（做 1 步想 10 步）：
  1. **稳定**：编号一旦分配就固定，增删条目不会重排。
     否则归档、引用、分享链接全部失效。
  2. **可读**：表格 T001-T999，图 F001-F999。
  3. **有序**：表格按源文件编号升序（自然的归档顺序）；
     图按「复刻 → 期刊样式 → 动机 → 定量 → 定性」排，复刻最重要排前面。
  4. **可恢复**：catalog.json 是唯一真相源，删了能重建（但重建会重排）。

用法:
  python3 tools/assign_numbers.py           # 分配新编号（已有编号不动）
  python3 tools/assign_numbers.py --renumber # 强制重排（慎用）
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "data", "catalog.json")


def _src_no(item: dict) -> int:
    """从 id 或标题里取源文件编号，用于排序。"""
    iid = item["id"]
    m = re.match(r"table-(\d+)", iid)
    if m:
        return int(m.group(1))
    if iid == "file1":
        return 6
    if iid == "file-table7-latex":
        return 7
    m = re.search(r"（(\d+)）", item.get("title") or "")
    if m:
        return int(m.group(1))
    return 9999


# 图的排序权重：复刻 > 期刊样式 > 动机 > 定量 > 定性 > 其他
_FIG_ORDER = {
    "architecture": 0, "mechanism": 0,          # 论文复刻
    "style": 1,
    "framework": 2, "motivation": 3,
    "quantitative": 4, "efficiency": 5, "tradeoff": 6, "results": 7,
    "qualitative": 8,
}


def _fig_key(item: dict):
    # 图库条目（topconf / PaperGallery 等，带 paper 字段）排在 FigTX 自有图之后：年份新的在前
    if item.get("paper"):
        return (2, 0, -(item.get("year") or 0), item["id"])
    ft = item.get("figType") or "style"
    is_rep = item["id"].startswith("rep-")
    return (0 if is_rep else 1, _FIG_ORDER.get(ft, 9), 0, item["id"])


def main() -> int:
    renumber = "--renumber" in sys.argv
    # 同步时用：上游暂时缺失的条目也保留编号（编号一旦分配永不回收）
    keep_missing = "--keep-missing" in sys.argv
    items = json.load(open(os.path.join(ROOT, "src", "data", "items.json"),
                          encoding="utf-8"))["items"]

    catalog: dict = {}
    if os.path.exists(CATALOG) and not renumber:
        try:
            catalog = json.load(open(CATALOG, encoding="utf-8"))
        except Exception:
            catalog = {}

    tables = sorted([i for i in items if i["category"] == "table"], key=_src_no)
    figures = sorted([i for i in items if i["category"] == "figure"], key=_fig_key)

    # 已用编号（避免冲突）
    used = {v["no"] for v in catalog.values() if "no" in v}

    def _assign(group, prefix):
        n = 1
        for it in group:
            cur = catalog.get(it["id"], {}).get("no")
            if cur and not renumber:
                continue
            while ("%s%03d" % (prefix, n)) in used:
                n += 1
            no = "%s%03d" % (prefix, n)
            catalog[it["id"]] = {"no": no, "kind": prefix,
                                 "title": it["title"][:60]}
            used.add(no)
            n += 1

    _assign(tables, "T")
    _assign(figures, "F")

    # 清理已删除条目
    if not keep_missing:
        alive = {i["id"] for i in items}
        catalog = {k: v for k, v in catalog.items() if k in alive}

    json.dump(catalog, open(CATALOG, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("catalog: %d 条（表格 %d / 图 %d）" %
          (len(catalog), len(tables), len(figures)))
    tn = sorted(v["no"] for k, v in catalog.items() if v["kind"] == "T")
    fn = sorted(v["no"] for k, v in catalog.items() if v["kind"] == "F")
    if tn:
        print("  表格编号: %s … %s" % (tn[0], tn[-1]))
    if fn:
        print("  图编号:   %s … %s" % (fn[0], fn[-1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
