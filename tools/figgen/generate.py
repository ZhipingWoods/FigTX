"""生成器：Generate -> Evaluate -> Refine 循环。

机制来自 AutoFigure（ICLR 2026）的 Review-Refine 双 agent 设计：
  1. Generate：按方法描述 + 设计契约产出候选 SVG
  2. Evaluate：评审 agent 打分（0-10）并给出具体修改指令
  3. Refine：带着问题清单重写，直到达标或轮数用尽

保守策略（针对实测遇到的问题）：
  - 部分模型会截断输出 —— 检测 </svg> 缺失，直接重试
  - 空白度过高（内容占比过低）视为失败
  - 出现中文 / mask / 缺 data-editable 直接扣分并要求重写
"""
from __future__ import annotations

import json
import os
import re

from . import contract as C
from . import llm_client as L
from . import prompts as P

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "figgen-out")


def _score_of(reply: str) -> tuple[float, list]:
    """从评审回复里取 overall 分和 fixes。"""
    t = (reply or "").strip()
    start = t.find("{")
    if start >= 0:
        depth = 0
        for i in range(start, len(t)):
            if t[i] == "{":
                depth += 1
            elif t[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        d = json.loads(t[start:i + 1])
                        ov = d.get("overall")
                        fixes = d.get("fixes") or []
                        return (float(ov) if ov is not None else 0.0,
                                [str(x) for x in fixes][:10])
                    except Exception:
                        break
    m = re.search(r'"overall"\s*:\s*([0-9.]+)', t)
    return (float(m.group(1)) if m else 0.0, [])


def quality_gate(svg: str, min_fill: float = 0.0) -> tuple[bool, list]:
    """硬性合格检查。返回 (是否合格, 问题列表)。"""
    s = L.svg_stats(svg)
    problems = []
    if not s["closed"]:
        problems.append("SVG 被截断：没有以 </svg> 结束")
    if not s["viewbox"]:
        problems.append("缺少 viewBox")
    if s["texts"] < 8:
        problems.append("文字元素太少（%d），布局可能过于稀疏" % s["texts"])
    if s["editable"] < 10:
        problems.append("data-editable 标记过少（%d），不可编辑" % s["editable"])
    if s["masks_filters"] > 0:
        problems.append("使用了 mask/filter（%d 处），破坏可编辑性" % s["masks_filters"])
    if s["chinese_chars"] > 0:
        problems.append("含 %d 个中文字符" % s["chinese_chars"])
    return (len(problems) == 0, problems)


def generate(
    method: str,
    reference_image: str | None = None,
    contract_prompt: str | None = None,   # 直接用已缓存的设计契约，跳过视觉分析
    target: str = "pipeline",
    max_rounds: int = 3,
    model: str | None = None,
    critic_model: str | None = None,
    save_dir: str | None = None,
    verbose: bool = True,
    score_threshold: float = 8.0,
) -> dict:
    """跑完整的生成循环，返回结果 dict。"""
    out_dir = save_dir or OUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    contract = None
    contract_text = contract_prompt or ""
    if contract_text and verbose:
        print("[contract] 使用缓存的设计契约（跳过视觉分析）", flush=True)
    elif reference_image and os.path.exists(reference_image):
        if verbose:
            print("[contract] 分析参考图 ...", flush=True)
        contract = C.extract(reference_image, model=model)
        contract_text = C.to_prompt(contract)
        if verbose and contract:
            print("[contract] 提取到 %d 条约束" % contract_text.count("\n"), flush=True)

    base_prompt = P.build_figure_prompt(method, contract_text, target)
    messages = [
        {"role": "system", "content": P.FIG_SYS},
        {"role": "user", "content": base_prompt},
    ]

    history = []
    best = None
    pending: list = []          # 累积的评审意见 [(类别, [条目])]

    for rnd in range(1, max_rounds + 1):
        if verbose:
            print("[gen] 第 %d/%d 轮 ..." % (rnd, max_rounds), flush=True)
        try:
            reply = L.chat(messages, model=model, max_tokens=8000, temperature=0.3)
        except L.LLMError as e:
            history.append({"round": rnd, "error": str(e)})
            continue

        svg = L.extract_svg(reply)
        if not svg:
            history.append({"round": rnd, "error": "模型输出里没有找到 <svg>"})
            if verbose:
                print("      无 SVG，重试", flush=True)
            messages.append({"role": "assistant", "content": reply[:2000]})
            messages.append({"role": "user",
                             "content": "You did not output an SVG. Output ONLY the raw <svg>...</svg> markup now."})
            continue

        ok, problems = quality_gate(svg)
        stats = L.svg_stats(svg)

        score = 0.0
        fixes: list[str] = []
        if ok:
            if verbose:
                print("      硬性检查通过，送评审 ...", flush=True)
            try:
                critic_msg = [
                    {"role": "system", "content": P.CRITIC_SYS},
                    {"role": "user", "content": P.CRITIC_USER.format(
                        method=method.strip()[:4000],
                        contract=contract_text or "(none)",
                        stats=json.dumps(stats, ensure_ascii=False),
                        svg=svg[:24000],
                    )},
                ]
                score, fixes = _score_of(L.chat(critic_msg, model=critic_model or model,
                                                max_tokens=1500, temperature=0.1))
            except L.LLMError as e:
                fixes = ["评审失败：%s" % e]

        record = {"round": rnd, "score": score, "stats": stats,
                  "problems": problems, "fixes": fixes, "svg": svg}
        history.append(record)
        if verbose:
            print("      得分 %.1f/10 | 问题 %d 条" % (score, len(problems)), flush=True)

        if ok and (best is None or score > best["score"]):
            best = record

        if ok and score >= score_threshold:
            if verbose:
                print("      达标（>= %.1f），停止" % score_threshold, flush=True)
            break

        # 累积所有轮次的评审意见 —— 只给最新一轮会让模型反复踩同一个坑
        if problems:
            pending.append(("硬性违规", problems))
        if fixes:
            pending.append(("评审要求", fixes))

        fb = []
        for label, items in pending:
            fb.append("%s（必须全部修复）：" % label)
            fb += ["- " + x for x in items]
        if not fb:
            fb.append("上一版仍不够好：提高信息密度，填补空白区域，加强层级区分。")
        fb.append("")
        fb.append("在上一版基础上修改，不要从零重写。输出修改后的完整 SVG，只输出 SVG。")

        # 关键：保留 assistant 上一版 SVG，让模型在它基础上改（in-context refinement）
        messages = [
            {"role": "system", "content": P.FIG_SYS},
            {"role": "user", "content": base_prompt},
            {"role": "assistant", "content": svg},
            {"role": "user", "content": "\n".join(fb)},
        ]

    result = {
        "method": method,
        "target": target,
        "contract": contract,
        "contract_text": contract_text,
        "rounds": len(history),
        "best_score": best["score"] if best else 0.0,
        "best_svg": best["svg"] if best else None,
        "best_stats": best["stats"] if best else None,
        "history": [{k: v for k, v in h.items() if k != "svg"} for h in history],
    }
    if best and best["svg"]:
        base = re.sub(r"[^a-zA-Z0-9_-]+", "-", (method or "figure"))[:40].strip("-")
        path = os.path.join(out_dir, "fig-%s.svg" % base)
        with open(path, "w", encoding="utf-8") as f:
            f.write(best["svg"])
        result["svg_path"] = path
        if verbose:
            print("[saved] %s (score %.1f)" % (path, best["score"]), flush=True)
    return result
