"""领域 / 研究问题打标：只用标题、会议、年份、图类型（不发摘要），结果缓存在 data/tags.json。

人工修正过的条目（"manual": true）和已经打过标的条目都不会再发给模型。
"""
from __future__ import annotations

import json
import os
import re

from .common import ROOT, dump_json, load_json

BATCH = 40
MAX_PROBLEM = 60

SYSTEM = ("You classify research papers into a fixed set of domains and name the concrete research problems they "
          "address, using only the title, venue, year and figure type. Output strict JSON only.")


def _taxonomy() -> list[dict]:
    return load_json(ROOT / "data" / "taxonomy.json", {})["domains"]


def _prompt(batch: list[dict], domains: list[dict]) -> str:
    keys = "\n".join(f"- {d['key']}: {d['en']}" for d in domains)
    items = [{"id": it["id"], "title": it.get("title", ""), "venue": (it.get("paper") or {}).get("venue"),
              "year": (it.get("paper") or {}).get("year"), "figType": it.get("figType")} for it in batch]
    return ("Domains (use 1-3 keys per paper, most specific first):\n" + keys +
            "\n\nFor every item return {\"<id>\": {\"domains\": [keys], \"problems\": [1-3 short lowercase English "
            "phrases naming the research problem, e.g. \"novel view synthesis\"]}}. Return one JSON object covering "
            "all ids.\n\nITEMS:\n" + json.dumps(items, ensure_ascii=False))


def _parse(reply: str) -> dict | None:
    m = re.search(r"\{.*\}", reply or "", re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _clean(entry, valid: set[str]) -> dict | None:
    if not isinstance(entry, dict):
        return None
    doms = [d for d in entry.get("domains") or [] if d in valid][:3]
    probs = [str(p).strip().lower()[:MAX_PROBLEM].strip() for p in entry.get("problems") or [] if str(p).strip()][:3]
    return {"domains": doms, "problems": probs} if doms or probs else None


def tag(items: list[dict], tags_path, chat_fn=None, batch: int = BATCH, workers: int = 6) -> dict:
    tags = load_json(tags_path, {})
    todo = [it for it in items if it["id"] not in tags]
    if not todo:
        return {"tagged": 0, "failed": 0}
    if chat_fn is None:
        if not os.environ.get("FIGTX_LLM_KEY"):
            print("跳过打标：未设置 FIGTX_LLM_KEY（新条目先不打标，之后本地补打）")
            return {"tagged": 0, "skipped": "no-key"}
        from tools.figgen import llm_client

        chat_fn = llm_client.chat
    domains = _taxonomy()
    valid = {d["key"] for d in domains}
    model = os.environ.get("FIGTX_LLM_MODEL", "default")
    chunks = [todo[i:i + batch] for i in range(0, len(todo), batch)]

    def ask(k_chunk):
        k, chunk = k_chunk
        try:
            return chat_fn([{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": _prompt(chunk, domains)}], max_tokens=8000, temperature=0)
        except Exception as e:  # 单批失败不影响其他批
            print(f"打标失败（第 {k + 1} 批）：{type(e).__name__}: {e}")
            return ""

    rep = {"tagged": 0, "failed": 0}
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for chunk, reply in zip(chunks, pool.map(ask, enumerate(chunks))):
            data = _parse(reply) or {}
            for it in chunk:
                entry = _clean(data.get(it["id"]), valid)
                if entry is None:
                    rep["failed"] += 1
                    continue
                tags[it["id"]] = dict(entry, model=model)
                rep["tagged"] += 1
            dump_json(tags_path, tags)  # 每批落盘：中途中断也不丢已打的标
    return rep
