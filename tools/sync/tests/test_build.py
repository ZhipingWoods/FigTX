"""build-data.mjs 与 assign_numbers.py 并入图库条目的集成测试（在临时迷你仓库里跑真脚本）。"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]


def _gallery(i, year):
    return {"id": f"tc-x{i}", "figType": "pipeline", "title": f"Paper {i}", "tags": ["T"],
            "paper": {"title": f"Paper {i}", "authors": ["A"], "venue": "ICML", "year": year,
                      "url": f"https://arxiv.org/abs/2401.0000{i}", "pdf": None, "code": None, "project": None,
                      "bibtex": None, "tier": None, "award": None},
            "sources": [{"platform": "topconf", "upstreamId": f"x{i}", "repo": "https://github.com/q/t"}],
            "image": {"source": "topconf", "path": "a.jpg", "w": 10, "h": 10}, "dhash": "0" * 16}


@pytest.fixture
def tmp_repo(tmp_path):
    r = tmp_path / "repo"
    (r / "tools").mkdir(parents=True)
    for f in ("build-data.mjs", "assign_numbers.py"):
        shutil.copy(REPO / "tools" / f, r / "tools" / f)
    (r / "data" / "sources").mkdir(parents=True)
    (r / "public" / "thumbs").mkdir(parents=True)
    (r / "data" / "raw-figures.json").write_text(json.dumps([{"id": "fig-old", "figType": "style", "title": "Old"}]))
    (r / "data" / "catalog.json").write_text(json.dumps({"fig-old": {"no": "F035", "kind": "F", "title": "Old"},
                                                         "gone": {"no": "F034", "kind": "F", "title": "Gone"}}))
    (r / "data" / "raw-gallery.json").write_text(json.dumps([_gallery(1, 2023), _gallery(2, 2025)]))
    (r / "data" / "tags.json").write_text(json.dumps({"tc-x1": {"domains": ["cv"], "problems": ["p"], "model": "m"}}))
    (r / "data" / "sources" / "assets-manifest.json").write_text(json.dumps(
        {"tc-x1": {"sha256": "s", "ext": "jpg", "w": 10, "h": 10, "uploaded": True},
         "tc-x2": {"sha256": "s", "ext": "png", "w": 10, "h": 10, "uploaded": False}}))
    for i in (1, 2):
        (r / "public" / "thumbs" / f"tc-x{i}.webp").write_bytes(b"x")
    return r


def _build(r):
    subprocess.run(["node", "tools/build-data.mjs"], cwd=r, check=True, capture_output=True)
    return {i["id"]: i for i in json.loads((r / "src/data/items.json").read_text())["items"]}


def test_build_includes_gallery(tmp_repo):
    items = _build(tmp_repo)
    g = items["tc-x1"]
    assert g["category"] == "figure" and g["render"] == "thumbs/tc-x1.webp" and g["domains"] == ["cv"]
    assert g["paper"]["venue"] == "ICML" and g["venues"] == ["ICML"] and g["year"] == 2023
    assert g["editableStatus"] == "original-only" and g["code"] == "" and g["source"]["repo"] == "topconf-paper-figure-gallery"
    assert g["original"] == "https://huggingface.co/datasets/OliverThompson/figtx-assets/resolve/main/originals/tc-x1.jpg"
    assert items["tc-x2"]["original"] is None and items["tc-x2"]["domains"] == []
    stats = json.loads((tmp_repo / "src/data/items.json").read_text())["stats"]
    assert stats["gallery"] == 2 and stats["sources"] == {"topconf": 2}


def test_index_has_domains(tmp_repo):
    _build(tmp_repo)
    idx = {i["id"]: i for i in json.loads((tmp_repo / "public/index.json").read_text())["items"]}
    assert idx["tc-x1"]["domains"] == ["cv"] and idx["tc-x1"]["problems"] == ["p"]
    assert idx["tc-x1"]["paper"] == "https://arxiv.org/abs/2401.00001"


def test_numbers_keep_existing_and_extend(tmp_repo):
    _build(tmp_repo)
    subprocess.run(["python3", "tools/assign_numbers.py", "--keep-missing"], cwd=tmp_repo, check=True, capture_output=True)
    cat = json.loads((tmp_repo / "data/catalog.json").read_text())
    assert cat["fig-old"]["no"] == "F035" and cat["gone"]["no"] == "F034"
    assert cat["tc-x2"]["no"] == "F001" and cat["tc-x1"]["no"] == "F002"
    items = _build(tmp_repo)
    assert items["tc-x2"]["no"] == "F001"


def test_numbers_new_start_after_existing_when_low_numbers_taken(tmp_repo):
    cat = {f"f{k}": {"no": "F%03d" % k, "kind": "F", "title": ""} for k in range(1, 36)}
    (tmp_repo / "data/catalog.json").write_text(json.dumps(cat))
    _build(tmp_repo)
    subprocess.run(["python3", "tools/assign_numbers.py", "--keep-missing"], cwd=tmp_repo, check=True, capture_output=True)
    cat = json.loads((tmp_repo / "data/catalog.json").read_text())
    assert cat["fig-old"]["no"] == "F036" and cat["tc-x2"]["no"] == "F037" and cat["tc-x1"]["no"] == "F038"
