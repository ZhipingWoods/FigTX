#!/usr/bin/env python3
r"""逐项审计已入库的样式：渲染图质量 + 源码完整性 + 元数据。

用法:
    python3 tools/audit.py            # 输出汇总 + docs/audit.md + audit/index.html
    python3 tools/audit.py --verbose
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_ppm(path: str):
    """读取 dwebp 输出的 PPM(P6)，返回 (w, h, samples)。"""
    with open(path, "rb") as f:
        data = f.read()
    if not data.startswith(b"P6"):
        return None
    # 解析头部：P6 \n w h \n 255 \n
    idx = 2
    fields = []
    while len(fields) < 3:
        while idx < len(data) and data[idx : idx + 1].isspace():
            idx += 1
        if data[idx : idx + 1] == b"#":
            while data[idx : idx + 1] not in (b"\n", b""):
                idx += 1
            continue
        start = idx
        while idx < len(data) and not data[idx : idx + 1].isspace():
            idx += 1
        fields.append(int(data[start:idx]))
    idx += 1
    w, h, _maxval = fields
    return w, h, data[idx:]


def analyze_image(webp_path: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        ppm = os.path.join(tmp, "a.ppm")
        r = subprocess.run(
            ["dwebp", "-quiet", webp_path, "-ppm", "-o", ppm],
            capture_output=True,
        )
        if r.returncode != 0 or not os.path.exists(ppm):
            return {"ok": False, "error": "dwebp failed"}
        parsed = read_ppm(ppm)
    if not parsed:
        return {"ok": False, "error": "bad ppm"}
    w, h, px = parsed
    total = w * h
    if total == 0:
        return {"ok": False, "error": "empty"}

    # 采样统计（步长自适应，控制在 ~200k 像素内）
    step = max(1, int((total / 200000) ** 0.5))
    ink = 0
    counted = 0
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(0, h, step):
        base = y * w * 3
        for x in range(0, w, step):
            i = base + x * 3
            r_, g_, b_ = px[i], px[i + 1], px[i + 2]
            counted += 1
            # 非白判定：任一通道 < 240
            if r_ < 240 or g_ < 240 or b_ < 240:
                ink += 1
                if x < minx: minx = x
                if y < miny: miny = y
                if x > maxx: maxx = x
                if y > maxy: maxy = y

    ink_ratio = ink / counted if counted else 0
    if ink == 0:
        return {"ok": False, "error": "blank", "w": w, "h": h, "ink": 0}

    touch = {
        "left": minx <= step,
        "top": miny <= step,
        "right": maxx >= w - 1 - step,
        "bottom": maxy >= h - 1 - step,
    }
    # 最后 3 行里，非白像素占比最多的一条
    bottom_ink = 0.0
    for yy in range(max(0, h - 3), h):
        row = 0
        cnt = 0
        base = yy * w * 3
        for x in range(0, w, step):
            i = base + x * 3
            cnt += 1
            if px[i] < 240 or px[i + 1] < 240 or px[i + 2] < 240:
                row += 1
        if cnt:
            bottom_ink = max(bottom_ink, row / cnt)

    return {
        "ok": True,
        "w": w, "h": h,
        "ink_ratio": round(ink_ratio, 4),
        "bbox": [minx, miny, maxx, maxy],
        "touch": touch,
        "aspect": round(w / h, 2),
        "bottom_ink": round(bottom_ink, 3),
    }


BRACE_LINE = re.compile(r"^\s*(%|$)")


def audit_item(it: dict) -> dict:
    issues: list[str] = []
    notes: list[str] = []

    # 图条目：只检查渲染图与源码，不做 LaTeX 结构检查
    if it.get("category") == "figure":
        code = it.get("code") or ""
        if len(code.strip()) < 30:
            issues.append("源码过短")
        render_rel = it.get("render")
        img = None
        if not render_rel:
            issues.append("预览图缺失")
        else:
            pth = os.path.join(ROOT, "public", render_rel)
            if not os.path.exists(pth):
                issues.append("预览图文件不存在")
            else:
                img = analyze_image(pth)
                if not img.get("ok"):
                    issues.append("预览图异常:" + str(img.get("error")))
                elif img["ink_ratio"] < 0.005:
                    issues.append("预览图几乎空白")
        status = "fail" if issues else ("warn" if notes else "ok")
        return {"id": it["id"], "status": status, "issues": issues, "notes": notes, "image": img}

    latex = it.get("code") or ""
    if len(latex.strip()) < 30:
        issues.append("源码过短")
    if "CDATA" in latex:
        issues.append("含 CDATA 残留")
    # 括号配平（忽略转义与注释）
    clean = re.sub(r"(?<!\\)%.*", "", latex)
    clean = clean.replace(r"\{", "").replace(r"\}", "")
    if clean.count("{") != clean.count("}"):
        notes.append("花括号不配平")
    if r"\begin{tabular" not in latex and r"\begin{tikzpicture" not in latex:
        notes.append("无 tabular/tikz")

    if not it.get("caption"):
        notes.append("无 caption")

    render_rel = it.get("render")
    img = None
    if render_rel:
        p = os.path.join(ROOT, "public", render_rel.replace("renders/", "renders/"))
        if not os.path.exists(p):
            issues.append("渲染图缺失")
        else:
            img = analyze_image(p)
            if not img.get("ok"):
                issues.append("渲染图异常:" + str(img.get("error")))
            else:
                if img["ink_ratio"] < 0.01:
                    issues.append("渲染图几乎空白")
                if img["ink_ratio"] > 0.85:
                    notes.append("渲染图过密")
                # 真正的截断：最后一行有很宽的墨迹（整行表格被切），
                # 而不是零星的边缘噪点。
                if img["touch"]["bottom"] and img.get("bottom_ink", 0) > 0.5:
                    notes.append("可能被截断(底部整行贴边)")
    else:
        notes.append("无渲染预览")

    status = "fail" if issues else ("warn" if notes else "ok")
    return {"id": it["id"], "status": status, "issues": issues, "notes": notes, "image": img}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "audit"))
    args = ap.parse_args()

    data = json.load(open(os.path.join(ROOT, "src/data/items.json"), encoding="utf-8"))
    items = data["items"]

    results = []
    for idx, it in enumerate(items, 1):
        r = audit_item(it)
        r["title"] = it.get("caption") or it.get("title") or it["id"]
        r["number"] = it.get("number")
        r["venues"] = it.get("venues") or []
        r["render"] = it.get("render")
        r["noteImages"] = it.get("noteImages") or []
        r["kind"] = it.get("kind")
        results.append(r)
        if args.verbose and r["status"] != "ok":
            print("[%3d/%d] %-16s %s %s" % (idx, len(items), r["id"], r["status"], r["issues"] or r["notes"]))

    ok = sum(1 for r in results if r["status"] == "ok")
    warn = sum(1 for r in results if r["status"] == "warn")
    fail = sum(1 for r in results if r["status"] == "fail")

    print("总计 %d 项：正常 %d / 待确认 %d / 有问题 %d" % (len(results), ok, warn, fail))

    # 汇总问题类型
    from collections import Counter
    c = Counter()
    for r in results:
        for i in r["issues"]:
            c[i] += 1
        for n in r["notes"]:
            c["· " + n] += 1
    for k, v in c.most_common(12):
        print("  %3d  %s" % (v, k))

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1)
    print("报告: %s/report.json" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
