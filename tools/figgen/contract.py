"""设计契约（design contract）：从参考图提取精确可量化的视觉参数。

设计动机来自 topconf-paper-figure-gallery 的实践：
  写「配色克制、层次清晰」这种形容词，等于把所有具体决策都丢给生成模型，
  风格漂移就是这么来的。只有精确数值才能钉住风格。
  （原文注释：Prose like "restrained palette, clear hierarchy" leaves every
   concrete decision to the generator, which is where style drift comes from;
   exact values pin it down.）

所以这里让视觉模型输出**可校验的结构化 JSON**，而不是散文描述。
"""
from __future__ import annotations

import json
import re

from . import llm_client as L

ANALYZE_SYS = """You are a design analyst for scientific figures. You inspect ONE reference figure and output a machine-checkable design contract as strict JSON.

Rules:
- Measure, do not editorialize. Every field must be a concrete value (hex color, px size, integer count), not an adjective.
- Never write words like "clean", "modern", "restrained". Those are not measurable.
- If a field is genuinely not present in the figure, omit it rather than inventing it.
- Output JSON only, no markdown fences, no commentary."""

ANALYZE_USER = """Analyse the attached reference figure and return this JSON shape:

{
  "canvas": {"aspect": "16:9 | 4:3 | other", "orientation": "landscape | portrait | square"},
  "pattern": "pipeline | teaser | motivation | comparison | system-overview | result-grid | other",
  "palette": {"background": "#hex", "primary": "#hex", "accent": "#hex", "neutral": "#hex", "others": ["#hex"]},
  "typography": {"title_px": int, "panel_header_px": int, "label_px": int, "note_px": int,
                 "family": "sans | serif | mixed"},
  "strokes": {"box_px": number, "arrow_px": number, "connector_px": number,
              "panel_border_heavier_than_module": true},
  "density": {"panels": int, "containers": int, "modules_per_panel": int,
              "solid_borders": int, "dashed_borders": int, "connectors": int,
              "fill_percent": int},
  "layout": {"reading_direction": "left-to-right | top-to-bottom | other",
             "panel_division": "short description of how the canvas is split"},
  "topology": {"anchor": "where the eye starts", "flow": "how information moves",
               "spacing": "gutters and grouping rhythm"},
  "style_fingerprint": {"panel_shape": "rounded | sharp | mixed",
                        "module_shape": "...", "arrow_style": "...",
                        "icon_style": "...", "text_treatment": "..."},
  "panels": [{"name": "...", "role": "...", "x_pct": int, "y_pct": int, "w_pct": int, "h_pct": int}],
  "elements": ["recurring element types you actually see"],
  "reusable_rules": ["3-6 short, imperative, measurable rules another designer could follow"]
}

All *_pct values are integers 0-100 relative to the canvas. Be exact about counts.
"""


def _strip_fences(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"^\`\`\`(?:json)?\s*", "", t, flags=re.I)
    t = re.sub(r"\s*\`\`\`$", "", t)
    return t


def _first_json(text: str):
    """从模型输出里抓第一个平衡的 JSON 对象。"""
    t = _strip_fences(text)
    start = t.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(t)):
        ch = t[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(t[start:i + 1])
                except Exception:
                    return None
    return None


def extract(image_path: str, model: str | None = None) -> dict | None:
    """分析一张参考图，返回设计契约 dict（失败返回 None）。"""
    msg = [
        {"role": "system", "content": ANALYZE_SYS},
        {"role": "user", "content": [
            {"type": "text", "text": ANALYZE_USER},
            L.image_part(image_path),
        ]},
    ]
    raw = L.chat(msg, model=model, max_tokens=4000, temperature=0.1)
    return _first_json(raw)


# 参考图里的具体实体名、标注、具体数值都会诱导模型照抄内容，
# 契约只该传递"视觉语法"（几何/密度/配色/层级），不该传递"讲什么"。
# 只去掉「内容标注」，保留几何数值（x/y/w/h、px、间距都是要用的）。
_CONTENT_NOISE = re.compile(
    r"\((?:a|b|c|d|e|f)\)|"                        # 面板标注 (a)(b)(c)
    r"\b(?:fig(?:ure)?|tab(?:le)?)\.?\s*\d+\b",   # Figure 3 / Table 2
    re.I,
)


def _structure_only(text: str) -> str:
    """从契约描述里剥掉参考图的具体内容，只留可迁移的结构信息。"""
    t = _CONTENT_NOISE.sub(" ", text or "")
    t = re.sub(r"\s{2,}", " ", t).strip(" ;,.")
    return t[:180]


def to_prompt(contract: dict) -> str:
    """把契约渲染成提示词里的硬约束段落（与 topconf 的 designContractText 同思路）。"""
    if not contract:
        return ""
    rows: list[str] = []
    c = contract

    pal = c.get("palette") or {}
    used = [k + " " + str(pal[k]) for k in ("background", "primary", "accent", "neutral")
            if isinstance(pal, dict) and pal.get(k)]
    extras = pal.get("others") if isinstance(pal, dict) else None
    if used or extras:
        rows.append("- palette: " + ", ".join(used + (list(extras) if extras else [])))

    ty = c.get("typography") or {}
    scale = [k.replace("_px", "") + " " + str(ty[k]) + "px"
             for k in ("title_px", "panel_header_px", "label_px", "note_px") if ty.get(k)]
    if scale:
        rows.append("- type scale: " + ", ".join(scale) +
                    " (keep this hierarchy: title > panel header > label > note)")

    st = c.get("strokes") or {}
    w = [k.replace("_px", "") + " " + str(st[k]) + "px"
         for k in ("box_px", "arrow_px", "connector_px") if st.get(k)]
    if w:
        rows.append("- stroke weights: " + ", ".join(w))
    if st.get("panel_border_heavier_than_module"):
        rows.append("- panel outer borders thicker than inner module borders")

    dn = c.get("density") or {}
    bits = []
    for k, label in (("panels", "panels"), ("containers", "container boxes"),
                     ("modules_per_panel", "modules per panel"),
                     ("connectors", "separate arrows/connectors"),
                     ("solid_borders", "solid borders"),
                     ("dashed_borders", "dashed borders")):
        if dn.get(k) is not None:
            bits.append("%s %s" % (dn[k], label))
    if dn.get("fill_percent") is not None:
        bits.append("canvas about %s%% filled" % dn["fill_percent"])
    if bits:
        rows.append("- counted in the reference: " + ", ".join(bits) + " — match these counts")

    lay = c.get("layout") or {}
    if lay.get("reading_direction"):
        rows.append("- reading direction: " + str(lay["reading_direction"]))
    # panel_division 常含参考图的具体标注（如 "(a) xxx"），只保留结构词
    pd = lay.get("panel_division")
    if pd:
        rows.append("- panel division: " + _structure_only(str(pd)))

    topo = c.get("topology") or {}
    tp = []
    if topo.get("anchor"):
        tp.append("anchor: " + _structure_only(str(topo["anchor"])))
    if topo.get("spacing"):
        tp.append("spacing: " + _structure_only(str(topo["spacing"])))
    # 故意丢弃 topology.flow —— 它总是描述参考图的具体内容走向，
    # 模型会把其中的实体名照搬进新图（实测：生成了参考图的 SANA-Video/Linear DiT）
    if tp:
        rows.append("- topology: " + "; ".join(tp))

    sf = c.get("style_fingerprint") or {}
    sfs = [k + ": " + str(v) for k, v in sf.items() if v]
    if sfs:
        rows.append("- style fingerprint: " + "; ".join(sfs))

    panels = c.get("panels") or []
    if panels:
        names = []
        for p in panels[:8]:
            nm = " — ".join([x for x in (p.get("name"), p.get("role")) if x])
            geo = ""
            if all(p.get(k) is not None for k in ("x_pct", "y_pct", "w_pct", "h_pct")):
                geo = " @ %s%%,%s%% size %s%%x%s%%" % (
                    p["x_pct"], p["y_pct"], p["w_pct"], p["h_pct"])
            if nm or geo:
                names.append(nm + geo)
        if names:
            rows.append("- panels: " + " | ".join(names))

    if c.get("elements"):
        el = c["elements"]
        rows.append("- recurring elements: " + (", ".join(el) if isinstance(el, list) else str(el)))

    for rule in (c.get("reusable_rules") or [])[:8]:
        rows.append("- rule: " + str(rule))

    return "\n".join(rows)
