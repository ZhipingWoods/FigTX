#!/usr/bin/env python3
r"""下载笔记配图（创作者原图），作为渲染失败时的兜底预览。

用法:
    python3 tools/fetch_images.py --items data/raw-items.json --out public/note-images
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36")


def ext_of(url: str) -> str:
    low = url.lower()
    for e in ("webp", "jpg", "jpeg", "png"):
        if e in low:
            return "jpg" if e == "jpeg" else e
    return "webp"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default="data/raw-items.json")
    ap.add_argument("--out", default="public/note-images")
    args = ap.parse_args()

    items = json.load(open(args.items, encoding="utf-8"))
    os.makedirs(args.out, exist_ok=True)
    ok = fail = 0
    for it in items:
        for idx, url in enumerate(it.get("images") or []):
            name = "%s-%d.%s" % (it["id"], idx, ext_of(url))
            dest = os.path.join(args.out, name)
            if os.path.exists(dest) and os.path.getsize(dest) > 1024:
                ok += 1
                continue
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read()
                if len(data) < 512:
                    raise ValueError("too small")
                with open(dest, "wb") as fh:
                    fh.write(data)
                ok += 1
            except Exception as e:
                fail += 1
                print("  ! %s: %s" % (name, e), file=sys.stderr)
    print("images ok=%d fail=%d -> %s" % (ok, fail, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
