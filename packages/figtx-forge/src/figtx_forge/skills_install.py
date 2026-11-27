"""把随包分发的 FigTX skills 安装到 Claude Code（~/.claude/skills）和 Codex（~/.codex/skills）。"""
from __future__ import annotations

import shutil
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"
TARGETS = {"claude": ".claude/skills", "codex": ".codex/skills"}


def list_skills() -> list[str]:
    return sorted(p.name for p in SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file())


def install_skills(home: Path, target: str = "both", link: bool = False) -> list[Path]:
    """复制（或符号链接）每个 skill 目录到目标位置；已存在的同名目录会被替换。"""
    keys = list(TARGETS) if target == "both" else [target]
    installed = []
    for key in keys:
        root = Path(home) / TARGETS[key]
        root.mkdir(parents=True, exist_ok=True)
        for name in list_skills():
            dst = root / name
            if dst.is_symlink() or dst.is_file():
                dst.unlink()
            elif dst.exists():
                shutil.rmtree(dst)
            if link:
                dst.symlink_to(SKILLS_DIR / name, target_is_directory=True)
            else:
                shutil.copytree(SKILLS_DIR / name, dst)
            installed.append(dst)
    return installed
