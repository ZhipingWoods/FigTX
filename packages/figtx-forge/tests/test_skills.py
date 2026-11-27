import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from figtx_forge.cli import SUBCOMMANDS, build_parser, main
from figtx_forge.skills_install import SKILLS_DIR, install_skills, list_skills

EXPECTED = {"figtx-find-figure", "figtx-redraw-figure", "figtx-framework-figure",
            "figtx-table-from-screenshot", "figtx-plot"}
PKG = Path(__file__).resolve().parents[1]


def _frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "missing frontmatter"
    fm, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^[a-z_]+:", line):
            key, _, val = line.partition(":")
            fm[key] = val.strip()
        elif key:
            fm[key] += " " + line.strip()
    return fm


def test_expected_skills_present():
    assert set(list_skills()) == EXPECTED


def test_all_skills_have_frontmatter():
    for name in EXPECTED:
        fm = _frontmatter((SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8"))
        assert fm["name"] == name
        desc = fm["description"].strip("|> ")
        assert 50 <= len(desc) <= 1024, (name, len(desc))


def test_skill_body_length():
    for name in EXPECTED:
        assert len((SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8").splitlines()) <= 200


def test_skill_commands_exist():
    build_parser()  # 加载全部子命令
    for md in SKILLS_DIR.rglob("*.md"):
        for sub in re.findall(r"figtx ([a-z][a-z-]*)", md.read_text(encoding="utf-8")):
            assert sub in SUBCOMMANDS or sub == "forge", (md.name, sub)


def test_install_copy(tmp_path):
    paths = install_skills(tmp_path, "both", link=False)
    assert len(paths) == 10
    assert (tmp_path / ".claude/skills/figtx-redraw-figure/SKILL.md").exists()
    assert (tmp_path / ".claude/skills/figtx-redraw-figure/references/scene-schema.md").exists()
    assert (tmp_path / ".codex/skills/figtx-plot/SKILL.md").exists()


def test_install_link(tmp_path):
    install_skills(tmp_path, "claude", link=True)
    assert (tmp_path / ".claude/skills/figtx-plot").is_symlink()
    assert not (tmp_path / ".codex").exists()


def test_install_overwrites(tmp_path):
    target = tmp_path / ".claude/skills/figtx-plot"
    target.mkdir(parents=True)
    (target / "old.txt").write_text("x")
    install_skills(tmp_path, "claude", link=False)
    assert not (target / "old.txt").exists() and (target / "SKILL.md").exists()


def test_cli_skills_list_and_install(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert main(["skills", "list"]) == 0
    assert set(capsys.readouterr().out.split()) >= EXPECTED
    assert main(["skills", "install", "--target", "codex"]) == 0
    assert (tmp_path / ".codex/skills/figtx-find-figure/SKILL.md").exists()


@pytest.mark.skipif(not shutil.which("uv"), reason="no uv")
def test_skills_in_wheel(tmp_path):
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(tmp_path), str(PKG)], check=True, capture_output=True)
    names = zipfile.ZipFile(next(tmp_path.glob("*.whl"))).namelist()
    assert "figtx_forge/skills/figtx-redraw-figure/SKILL.md" in names
