"""运行 matplotlib 绘图脚本，收集它生成的图片。"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OUTPUT_EXT = {".png", ".pdf", ".svg"}


def run_plot(script_path, out_dir, timeout: int = 120, python: str | None = None) -> dict:
    """在临时工作目录里用 MPLBACKEND=Agg 运行脚本，把新生成的 png/pdf/svg 复制到 out_dir。"""
    script = Path(script_path).resolve()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, MPLBACKEND="Agg")
    with tempfile.TemporaryDirectory() as tmp:
        try:
            proc = subprocess.run([python or sys.executable, str(script)], cwd=tmp, env=env,
                                  capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"ok": False, "files": [], "stderr_tail": f"timeout after {timeout}s"}
        files = []
        for p in sorted(Path(tmp).rglob("*")):
            if p.suffix.lower() in OUTPUT_EXT and p.is_file():
                dst = out / p.name
                shutil.copy2(p, dst)
                files.append(str(dst))
    return {"ok": proc.returncode == 0, "files": files, "stderr_tail": proc.stderr[-2000:]}
