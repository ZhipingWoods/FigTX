#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地生成服务：给 FigTX 前端提供图生成 API。

设计取舍：
  - 不把 API key 放进前端（浏览器里任何 key 都等于公开）
  - 前端只调本地 localhost 服务，服务端从 .env 读 key
  - 用标准库 http.server，不引入 web 框架依赖

端点：
  GET  /api/contracts          列出已缓存的设计契约
  POST /api/generate           {method, reference, target, rounds} -> 生成
  GET  /api/health             健康检查
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from figgen import contract as C
from figgen import generate as G
from figgen import llm_client as L
from figgen import render as R

CONTRACTS = os.path.join(ROOT, "data", "fig-contracts.json")
OUT_DIR = os.path.join(ROOT, "figgen-out")
PORT = int(os.environ.get("FIGTX_GEN_PORT", "8770"))

_lock = threading.Lock()


def load_contracts() -> dict:
    if not os.path.exists(CONTRACTS):
        return {}
    try:
        return json.load(open(CONTRACTS, encoding="utf-8"))
    except Exception:
        return {}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # 静音访问日志

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/health"):
            try:
                ok = bool(L.KEY)
            except Exception:
                ok = False
            self._json(200, {"ok": True, "llm_configured": ok, "model": L.MODEL})
            return
        if self.path.startswith("/api/contracts"):
            data = load_contracts()
            brief = [
                {"id": k, "no": v.get("no"), "figType": v.get("figType"),
                 "title": v.get("title"), "image": v.get("image")}
                for k, v in data.items()
            ]
            brief.sort(key=lambda x: x.get("no") or "")
            self._json(200, {"contracts": brief})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if not self.path.startswith("/api/generate"):
            self._json(404, {"error": "not found"})
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            req = json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception as e:
            self._json(400, {"error": "bad json: %s" % e})
            return

        method = (req.get("method") or "").strip()
        if not method:
            self._json(400, {"error": "method 不能为空"})
            return

        ref_id = req.get("reference") or ""
        target = req.get("target") or "pipeline"
        rounds = int(req.get("rounds") or 3)
        model = req.get("model") or None

        ref_image = None
        cached_prompt = ""
        if ref_id:
            c = load_contracts().get(ref_id)
            if c:
                ref_image = os.path.join(ROOT, "public", c["image"])
                cached_prompt = c.get("prompt") or C.to_prompt(c.get("contract") or {})

        if not os.environ.get("FIGTX_LLM_KEY"):
            self._json(400, {"error": "未配置 FIGTX_LLM_KEY（见 .env）"})
            return

        with _lock:  # 串行化，避免并发把 API 打爆
            try:
                res = G.generate(
                    method=method,
                    reference_image=ref_image,
                    contract_prompt=cached_prompt or None,
                    target=target,
                    max_rounds=max(1, min(rounds, 5)),
                    model=model,
                    save_dir=OUT_DIR,
                    verbose=False,
                )
            except Exception as e:
                self._json(500, {"error": "%s: %s" % (type(e).__name__, e)})
                return

        out = {
            "rounds": res["rounds"],
            "best_score": res["best_score"],
            "history": [{k: v for k, v in h.items() if k != "svg"}
                        for h in res["history"]],
        }
        if res.get("best_svg"):
            svg_path = res["svg_path"]
            base = os.path.splitext(os.path.basename(svg_path))[0]
            png_path = os.path.join(OUT_DIR, base + ".png")
            webp_path = os.path.join(OUT_DIR, base + ".webp")
            R.svg_to_png(svg_path, png_path)
            R.png_to_webp(png_path, webp_path)
            out["svg"] = res["best_svg"]
            out["svg_file"] = os.path.basename(svg_path)
            if os.path.exists(png_path):
                out["png_file"] = os.path.basename(png_path)
            if os.path.exists(webp_path):
                out["webp_file"] = os.path.basename(webp_path)
        self._json(200, out)


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("FigTX 生成服务: http://127.0.0.1:%d" % PORT)
    print("  GET  /api/health")
    print("  GET  /api/contracts")
    print("  POST /api/generate")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
