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
- Output raw SVG markup only. No markdown fences, no explanation, no preamble.

ANTI-COPY RULE (critical): reference figures are supplied only to transfer visual grammar.
Never reproduce their text, module names, entity names, captions or logical structure.
Every label in your output must come from the METHOD description below, not from a reference."""

FIG_USER_TMPL = """Design a paper Figure 1 for the following method.

## Method
{method}

## Target
{target}

## Design contract derived from reference figures
{contract}

IMPORTANT — the contract above describes VISUAL GRAMMAR only (geometry, density, palette,
stroke language, hierarchy). It is NOT the content you must draw. The reference figure is a
different paper about a different method. You MUST invent panels, labels and internal structure
that describe the method below. Never reuse the reference's entity names, module names, section
titles or panel captions. If the contract mentions specific numbers of panels or boxes, keep the
same COUNT and RHYTHM, but fill them with completely new, method-specific content.

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

CRITIC_USER = """The method this figure is supposed to illustrate:
{method}

Judge CONTENT CORRECTNESS first: does the figure actually depict this method's
components and data flow? A visually clean figure that illustrates the wrong method
scores 0 on content. Only then judge visual quality against the contract.

Reference design contract:
{contract}

Candidate SVG statistics:
{stats}

Candidate SVG source (may be truncated):
{svg}

Score the candidate 0-10 on each axis and give actionable fixes:
{{
  "scores": {{"content": n, "layout": n, "hierarchy": n, "density": n, "palette": n, "legibility": n, "editability": n}},
  "overall": n,
  "wrong_content": ["any element that does NOT belong to this method", ...],
  "problems": ["concrete defect", ...],
  "fixes": ["concrete, imperative instruction for the next attempt", ...]
}}

Penalise hard: entities, module names or captions that belong to some OTHER paper
(this is the most common failure — the model copies the reference figure's content),
large empty regions, text overflowing boxes, missing data-editable, wrong viewBox,
Chinese characters, mask/filter usage, and a layout ignoring the contract's panel counts.
If the figure illustrates a different method than the one given, overall must be <= 3.
Be harsh: only 8+ means genuinely publication-ready."""
