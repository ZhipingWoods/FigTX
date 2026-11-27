import json
from pathlib import Path

from tools.sync.sync_papergallery import fetch, parse, parse_frontmatter

FIX = Path(__file__).parent / "fixtures" / "papergallery"


def _by_id():
    recs, _ = parse(FIX)
    return {r["upstreamId"]: r for r in recs}


def test_parse_ok():
    r = _by_id()["Agelos_DynMF_2024"]
    assert r["source"] == "papergallery" and r["kind"] == "pipeline"
    assert r["venue"] == "ECCV" and r["year"] == 2024 and r["tags"] == ["3DGS", "Real-time", "Motion"]
    assert r["code"] == "https://github.com/agelosk/dynmf" and r["project"].startswith("https://agelosk")
    assert r["bibtex"].startswith("@inproceedings") and r["paper"].startswith("https://arxiv.org")
    assert r["image"] == "public/images/pipeline/Agelos_DynMF_2024.jpg" and (r["w"], r["h"]) == (400, 240)


def test_parse_broken_yaml_falls_back():
    recs, st = parse(FIX)
    r = _by_id()["Broken_Yaml_2025"]
    assert st["fallback"] == 1 and r["venue"] == "arXiv" and r["bibtex"] is None and r["code"] is None


def test_space_in_filename():
    r = _by_id()["Deng_VPGS SLAM_2025"]
    assert (FIX / r["image"]).is_file() and r["venue"] == "Unknown" and r["paper"] is None


def test_header_kind_and_missing_image():
    recs, st = parse(FIX)
    assert _by_id()["Chen_AerialMind_2026"]["kind"] == "header"
    assert st["missing_image"] == 1 and "No_Image_2025" not in _by_id()
    assert st["parsed"] == 4


def test_body_never_kept():
    recs, _ = parse(FIX)
    assert "ABSTRACT-SENTINEL" not in json.dumps(recs)


def test_frontmatter_none_without_title_and_image():
    assert parse_frontmatter("---\nfoo: 1\n---\nbody") is None


def test_fetch_local_passthrough(tmp_path):
    assert fetch(tmp_path, local=FIX) == FIX
