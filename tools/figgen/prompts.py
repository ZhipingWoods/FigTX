"""提示词模板。

可编辑导出契约（editable export contract）来自 AutoFigure 与 topconf 的共同实践：
让模型产出「逐元素可编辑」的 SVG，而不是一张烘死的位图。
"""
from __future__ import annotations

FIG_SYS = """You are a world-class scientific figure designer for top-tier ML/CV/NLP papers.

Output exactly ONE complete, self-contained SVG document.

HARD REQUIREMENTS
- viewBox="0 0 1600 900", white background, landscape.
- Every visible element carries: unique id + data-role + data-editable="true".
- All labels are SVG <text>. Never convert text to paths, images or outlines.
- Only basic primitives: rect, circle, ellipse, line, path, polygon, polyline, text, g.
- No masks, no filters, no complex clipPaths, no external images, no embedded bitmaps.
- Put repeated styles in <defs> and reference them.
- ALL visible text must be English. No Chinese characters anywhere.
- Every label must fit inside the box it belongs to; no text bounding boxes may overlap.
  If a label does not fit, shorten the text or reduce the font size.
- All content must stay within x=0..1600, y=0..900.
- Fill each panel's module regions with meaningful sub-structure (mini flow, matrix, chart,
  inset, legend, short labels). Do not leave conspicuous empty areas.
- Output raw SVG markup only. No markdown fences, no explanation, no preamble."""

FIG_USER_TMPL = """Design a paper Figure 1 for the following method.

## Method
{method}

## Target
{target}

## Design contract derived from reference figures
{contract}

## Composition requirements
- {panels_hint}
- Reading path: {reading}
- Match the reference's element counts and density. Richness beats sparse minimalism.
- Panel outer borders visibly thicker than inner module borders; use dashed strokes for
  skipped / optional / repeated paths and solid for computed ones.
- Include a small legend if the figure uses both solid and dashed semantics.

Output the SVG."
"""

TARGETS = {
    "pipeline": "A method/architecture overview: overall pipeline plus one zoom-in inset.",
    "teaser": "A teaser Figure 1: motivates the problem and shows the key idea at a glance.",
    "motivation": "A motivation figure: contrasts the failure of existing methods with the proposed idea.",
    "comparison": "A qualitative comparison grid: our method vs baselines across several cases.",
    "system": "A system/overview diagram: modules, data flow, and where each contribution sits.",
}

PANELS_HINT = {
    "pipeline": "3-5 substantial left-to-right panels ending with a zoom-in inset of the核心 module",
    "teaser": "2-3 panels: problem setting, then the proposed mechanism, then the benefit",
    "motivation": "2-4 panels contrasting baseline behaviour against ours",
    "comparison": "one row per case, columns for input / baseline / ours",
    "system": "coarse outer panels with finer module boxes inside",
}


def build_figure_prompt(method: str, contract_text: str, target: str = "pipeline",
                        reading: str = "left-to-right") -> str:
    return FIG_USER_TMPL.format(
        method=method.strip(),
        target=TARGETS.get(target, TARGETS["pipeline"]),
        contract=contract_text or "(no reference contract supplied — rely on the requirements below)",
        panels_hint=PANELS_HINT.get(target, PANELS_HINT["pipeline"]),
        reading=reading,
    )


CRITIC_SYS = """You are a strict reviewer of scientific figures for top-tier venues.
You score a candidate SVG against a reference design contract.
You are terse, concrete and numeric. Output JSON only."""

CRITIC_USER = """Reference design contract:
{contract}

Candidate SVG statistics:
{stats}

Candidate SVG source (may be truncated):
{svg}

Score the candidate 0-10 on each axis and give actionable fixes:
{{
  "scores": {{"layout": n, "hierarchy": n, "density": n, "palette": n, "legibility": n, "editability": n}},
  "overall": n,
  "problems": ["concrete defect", ...],
  "fixes": ["concrete, imperative instruction for the next attempt", ...]
}}

Penalise: large empty regions, text overflowing boxes, missing data-editable, wrong viewBox,
Chinese characters, mask/filter usage, missing zoom-in inset when the contract expects one,
and a layout that ignores the contract's panel counts.
Be harsh: only 8+ means genuinely publication-ready."""
