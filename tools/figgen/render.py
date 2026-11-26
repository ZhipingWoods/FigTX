"""把生成的 SVG 渲染成 PNG / WebP 预览图。

用 playwright 的 Chromium 做无头渲染 —— 保证和浏览器里看到的一致
（字体、圆角、虚线、透明度都不会失真）。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 本机可能装过 playwright，优先复用
# 需要的是 playwright-core 的模块目录（require 用）
_CANDIDATES = [
    os.path.join(ROOT, "node_modules", "playwright-core"),
]

_NODE_SCRIPT = """
const { chromium } = require(process.argv[2]);
const fs = require('fs');
(async () => {
  const svgPath = process.argv[3];
  const outPath = process.argv[4];
  const w = parseInt(process.argv[5] || '1600', 10);
  const h = parseInt(process.argv[6] || '900', 10);
  const scale = parseFloat(process.argv[7] || '2');
  const svg = fs.readFileSync(svgPath, 'utf8');
  const b = await chromium.launch({
    executablePath: process.argv[8] || undefined,
    headless: true,
  });
  const p = await (await b.newContext({
    viewport: { width: w, height: h },
    deviceScaleFactor: scale,
  })).newPage();
  const tmp = svgPath + '.view.html';
  fs.writeFileSync(tmp, '<html><body style="margin:0;background:#fff">' + svg + '</body></html>');
  await p.goto('file://' + tmp, { waitUntil: 'load' });
  await p.waitForTimeout(400);
  await p.screenshot({ path: outPath });
  fs.unlinkSync(tmp);
  await b.close();
  console.log('ok');
})();
"""

_CHROME_HINTS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Users/zhipingwu/Library/Caches/ms-playwright/chromium-1248/chrome-mac-arm64/"
    "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
]


def _node_modules_dir() -> str | None:
    """返回 playwright-core 模块目录（直接给 require 用）。"""
    for c in _CANDIDATES:
        if os.path.isdir(c):
            return c
    return None


def _chrome() -> str | None:
    for c in _CHROME_HINTS:
        if os.path.exists(c):
            return c
    return None


def svg_to_png(svg_path: str, png_path: str, width: int = 1600, height: int = 900,
               scale: float = 2.0, quiet: bool = True) -> bool:
    """渲染 SVG 为 PNG。失败时（quiet=False）打印真实原因，便于排查。"""
    nm = _node_modules_dir()
    if not nm:
        if not quiet:
            print("[render] 找不到 playwright-core，先跑 npm i -D playwright-core")
        return False
    script = os.path.join(tempfile.gettempdir(), "_figtx_render.js")
    with open(script, "w", encoding="utf-8") as f:
        f.write(_NODE_SCRIPT)
    cmd = ["node", script, nm, os.path.abspath(svg_path), os.path.abspath(png_path),
           str(width), str(height), str(scale), _chrome() or ""]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except Exception as e:
        if not quiet:
            print("[render] 调用 node 失败: %s" % e)
        return False
    ok = os.path.exists(png_path) and os.path.getsize(png_path) > 0
    if not ok and not quiet:
        print("[render] node 退出码 %s" % r.returncode)
        print("[render] stderr:", (r.stderr or "").strip()[:600])
        print("[render] stdout:", (r.stdout or "").strip()[:300])
    return ok


def png_to_webp(png_path: str, webp_path: str, max_px: int = 3000) -> bool:
    """PNG -> WebP，顺便把过宽的图缩到 max_px 以内。"""
    cwebp = shutil.which("cwebp")
    if not cwebp:
        return False
    from PIL import Image
    im = Image.open(png_path)
    w, h = im.size
    if w > max_px or h > max_px:
        ratio = max_px / float(max(w, h))
        im = im.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        im.save(png_path)
    try:
        subprocess.run([cwebp, "-q", "90", "-m", "6", png_path, "-o", webp_path],
                       capture_output=True, timeout=120)
        return os.path.exists(webp_path)
    except Exception:
        return False
