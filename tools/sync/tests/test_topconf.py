import shutil
import subprocess
from pathlib import Path

import pytest

from tools.sync.sync_topconf import FetchError, fetch, parse

FIX = Path(__file__).parent / "fixtures" / "topconf"


def test_parse_fixture():
    recs = parse(FIX)
    assert len(recs) == 3
    r = {x["upstreamId"]: x for x in recs}["icml2023-0064"]
    assert r["source"] == "topconf" and r["venue"] == "ICML" and r["year"] == 2023
    assert r["kind"] == "pipeline" and r["tier"] == "oral"
    assert r["paper"].startswith("https://proceedings") and r["pdf"].startswith("https://arxiv.org")
    assert r["image"] == "images/icml/final/icml2023-0064.jpg" and (r["w"], r["h"]) == (900, 576)
    assert r["code"] is None and r["bibtex"] is None


def test_parse_empty_pdf_is_none():
    r = {x["upstreamId"]: x for x in parse(FIX)}["icml2025-0100"]
    assert r["pdf"] is None and r["award"] == "best paper"


def test_parse_skips_missing_image(tmp_path):
    root = tmp_path / "tc"
    shutil.copytree(FIX, root)
    (root / "images/cvpr/final/cvpr2024-0001.jpg").unlink()
    assert len(parse(root)) == 2


def test_fetch_local_passthrough(tmp_path):
    assert fetch(tmp_path, local=FIX) == FIX


def test_fetch_failure_raises(tmp_path, monkeypatch):
    def fail(*a, **k):
        raise subprocess.CalledProcessError(128, a[0])

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(FetchError):
        fetch(tmp_path)
