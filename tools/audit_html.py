#!/usr/bin/env python3
r"""生成逐项核对页 audit/index.html（缩略图 + 状态 + 源码入口）。

用法: python3 tools/audit_html.py
"""
from __future__ import annotations

import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audit", "index.html")

TEMPLATE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>FigTX 逐项核对</title>
<style>
  :root { --line:#e7e5e4; --ink:#1a1a18; --ink3:#8a8580; }
  * { box-sizing:border-box }
  body { margin:0; font:14px/1.5 -apple-system,"PingFang SC","Segoe UI",sans-serif;
         background:#fafaf9; color:var(--ink) }
  header { position:sticky; top:0; background:#fff; border-bottom:1px solid var(--line);
           padding:14px 20px; display:flex; gap:14px; align-items:center; flex-wrap:wrap; z-index:5 }
  h1 { font-size:16px; margin:0 }
  .stat { font-size:13px; color:var(--ink3) }
  .stat b { color:var(--ink) }
  .filters { display:flex; gap:8px; margin-left:auto }
  .filters button { padding:5px 12px; border-radius:999px; border:1px solid var(--line);
                    background:#fff; font-size:12px; cursor:pointer }
  .filters button[data-on="1"] { background:var(--ink); color:#fff; border-color:var(--ink) }
  main { padding:18px 20px 60px; display:grid; gap:14px;
         grid-template-columns:repeat(auto-fill,minmax(240px,1fr)) }
  figure.card { margin:0; background:#fff; border:1px solid var(--line); border-radius:10px;
                overflow:hidden; display:flex; flex-direction:column }
  .shot { height:260px; display:flex; align-items:flex-start; justify-content:center;
          background:#fff; border-bottom:1px solid var(--line); overflow:hidden; padding:6px }
  .shot img { max-width:100%; max-height:520px; width:auto; height:auto; display:block }
  figcaption { padding:8px 10px 10px; display:flex; flex-direction:column; gap:5px }
  .id { font:11px/1 ui-monospace,monospace; color:var(--ink3) }
  .cap { font-size:12px; line-height:1.35; display:-webkit-box; -webkit-line-clamp:2;
         -webkit-box-orient:vertical; overflow:hidden; min-height:32px }
  .badges { display:flex; gap:4px; flex-wrap:wrap }
  .b { font-size:10px; padding:1px 6px; border-radius:4px; border:1px solid var(--line) }
  .b-render { background:#ecfdf5; border-color:#a7f3d0; color:#065f46 }
  .b-photo { background:#fffbeb; border-color:#fde68a; color:#92400e }
  .b-warn { background:#fefce8; border-color:#fde68a; color:#854d0e }
  .b-fail { background:#fef2f2; border-color:#fecaca; color:#991b1b }
  figure.card[data-status="warn"] { border-color:#fde68a }
  body[data-f="ok"] figure.card:not([data-status="ok"]) { display:none }
  body[data-f="warn"] figure.card[data-status="ok"] { display:none }
</style></head><body data-f="all">
<header>
  <h1>FigTX 逐项核对</h1>
  <span class="stat">共 <b>__TOTAL__</b> 项 · 正常 <b>__OK__</b> · 待确认 <b>__WARN__</b> · 有问题 <b>__FAIL__</b></span>
  <div class="filters">
    <button data-f="all" data-on="1">全部</button>
    <button data-f="ok">仅正常</button>
    <button data-f="warn">仅待确认</button>
  </div>
</header>
<main>__CARDS__</main>
<script>
document.querySelectorAll('.filters button').forEach(function (b) {
  b.onclick = function () {
    document.querySelectorAll('.filters button').forEach(function (x) { x.dataset.on = '0'; });
    b.dataset.on = '1';
    document.body.dataset.f = b.dataset.f;
  };
});
</script>
</body></html>"""


def main() -> int:
    data = json.load(open(os.path.join(ROOT, "src/data/items.json"), encoding="utf-8"))
    items = data["items"]
    report = {
        r["id"]: r
        for r in json.load(open(os.path.join(ROOT, "audit/report.json"), encoding="utf-8"))
    }

    cards = []
    for it in items:
        r = report.get(it["id"], {})
        status = r.get("status", "unknown")
        issues = r.get("issues") or []
        notes = [n for n in (r.get("notes") or []) if n != "无渲染(用原图兜底)"]
        img = it.get("render") or (it.get("noteImages") or [None])[0]
        src = "../public/" + img if img else ""
        badges = []
        badges.append(
            '<span class="b b-photo">原图</span>'
            if not it.get("render")
            else '<span class="b b-render">渲染</span>'
        )
        for i in issues:
            badges.append('<span class="b b-fail">%s</span>' % html.escape(i))
        for n in notes:
            badges.append('<span class="b b-warn">%s</span>' % html.escape(n))

        cap = it.get("caption") or it.get("title") or "（无标题）"
        cards.append(
            '<figure class="card" data-status="%s">'
            '<a class="shot" href="%s" target="_blank"><img loading="lazy" src="%s" alt=""></a>'
            '<figcaption><div class="id">%s</div><div class="cap">%s</div>'
            '<div class="badges">%s</div></figcaption></figure>'
            % (status, src, src, html.escape(it["id"]), html.escape(cap[:90]), "".join(badges))
        )

    ok = sum(1 for r in report.values() if r["status"] == "ok")
    warn = sum(1 for r in report.values() if r["status"] == "warn")
    fail = sum(1 for r in report.values() if r["status"] == "fail")

    doc = (
        TEMPLATE.replace("__TOTAL__", str(len(items)))
        .replace("__OK__", str(ok))
        .replace("__WARN__", str(warn))
        .replace("__FAIL__", str(fail))
        .replace("__CARDS__", "\n".join(cards))
    )

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print("written %s (%.1f KB)" % (OUT, len(doc) / 1024))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
