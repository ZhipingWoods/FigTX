"""OpenAI 兼容的 LLM 客户端。

只用标准库 urllib，避免额外依赖。从 .env 读取配置，绝不硬编码密钥。
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request

# tools/figgen/llm_client.py -> 仓库根（三层）
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_env() -> None:
    """把仓库根目录的 .env 读进 os.environ（不覆盖已有变量）。"""
    p = os.path.join(ROOT, ".env")
    if not os.path.exists(p):
        return
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


_load_env()

BASE = os.environ.get("FIGTX_LLM_BASE", "https://llm-center.modelbest.co/v1").rstrip("/")
KEY = os.environ.get("FIGTX_LLM_KEY", "")
MODEL = os.environ.get("FIGTX_LLM_MODEL", "GPT_svn19r")


class LLMError(RuntimeError):
    pass


def chat(
    messages: list,
    model: str | None = None,
    max_tokens: int = 8000,
    temperature: float = 0.2,
    timeout: int = 240,
    retries: int = 2,
) -> str:
    """发一次 chat/completions，返回 message.content。失败会重试。"""
    if not KEY:
        raise LLMError("缺少 FIGTX_LLM_KEY，请在仓库根目录 .env 里配置")

    body = {
        "model": model or MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    data = json.dumps(body).encode("utf-8")
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            BASE + "/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + KEY,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            choice = (payload.get("choices") or [{}])[0]
            return (choice.get("message") or {}).get("content") or ""
        except urllib.error.HTTPError as e:
            last = "HTTP %s: %s" % (e.code, e.read()[:200].decode("utf-8", "replace"))
        except Exception as e:  # 超时/连接错误
            last = "%s: %s" % (type(e).__name__, e)
        if attempt < retries:
            time.sleep(2 * (attempt + 1))
    raise LLMError("LLM 调用失败 —— %s" % last)


def image_part(path: str) -> dict:
    """把一个本地图片文件变成 OpenAI 兼容的 image_url part。"""
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png",
            "webp": "webp", "gif": "gif"}.get(ext, "png")
    b64 = base64.b64encode(open(path, "rb").read()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": "data:image/%s;base64,%s" % (mime, b64)},
    }


SVG_RE = re.compile(r"<svg[\s\S]*?</svg>", re.I)


def extract_svg(text: str) -> str | None:
    """从模型输出里抓出第一个完整 <svg>...</svg>（去掉 markdown 围栏）。"""
    if not text:
        return None
    text = re.sub(r"^```(?:svg|xml)?\s*", "", text.strip(), flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    m = SVG_RE.search(text)
    return m.group(0) if m else None


def svg_stats(svg: str) -> dict:
    """可编辑性统计 —— 用来判断生成结果是否达标。"""
    return {
        "bytes": len(svg.encode("utf-8")),
        "texts": svg.count("<text"),
        "editable": svg.count("data-editable"),
        "roles": svg.count("data-role"),
        "rects": svg.count("<rect"),
        "paths": svg.count("<path"),
        "masks_filters": svg.count("<mask") + svg.count("<filter"),
        "viewbox": (re.search(r'viewBox="([^"]+)"', svg) or [None, None])[1],
        "chinese_chars": len(re.findall(r"[\u4e00-\u9fff]", svg)),
        "closed": svg.rstrip().endswith("</svg>"),
    }
