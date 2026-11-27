import hashlib
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from tools.sync.run import run
from tools.sync.sync_journal import parse as parse_journal

REPO = Path(__file__).resolve().parents[3]
FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_repo(tmp_path):
    r = tmp_path / "repo"
    (r / "tools").mkdir(parents=True)
    for f in ("build-data.mjs", "assign_numbers.py"):
        shutil.copy(REPO / "tools" / f, r / "tools" / f)
    (r / "data").mkdir()
    (r / "data" / "catalog.json").write_text("{}")
    return r


LOCAL = {"topconf": FIX / "topconf", "papergallery": FIX / "papergallery"}


def _snapshot(r):
    out = {}
    for p in sorted(list((r / "data").rglob("*")) + list((r / "public" / "thumbs").rglob("*"))):
        if p.is_file():
            out[str(p.relative_to(r))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_run_end_to_end_fixture(tmp_repo):
    rep = run(local=LOCAL, no_tag=True, no_push=True, root=tmp_repo)
    assert rep["sources"]["topconf"] == 3 and rep["sources"]["papergallery"] == 4
    assert rep["items"] == 7 and rep["errors"] == {}
    assert len(list((tmp_repo / "public/thumbs").glob("*.webp"))) == 7
    items = json.loads((tmp_repo / "src/data/items.json").read_text())["items"]
    assert sum(1 for i in items if i.get("group") == "gallery") == 7
    cat = json.loads((tmp_repo / "data/catalog.json").read_text())
    assert all(cat[i]["no"].startswith("F") for i in cat)


def test_run_is_idempotent(tmp_repo):
    run(local=LOCAL, no_tag=True, no_push=True, root=tmp_repo)
    before = _snapshot(tmp_repo)
    run(local=LOCAL, no_tag=True, no_push=True, root=tmp_repo)
    assert _snapshot(tmp_repo) == before


def test_run_keeps_previous_source_on_fetch_failure(tmp_repo):
    run(local=LOCAL, no_tag=True, no_push=True, root=tmp_repo)
    src = (tmp_repo / "data/sources/topconf.json").read_bytes()
    broken = dict(LOCAL, topconf=tmp_repo / "does-not-exist")
    rep = run(local=broken, no_tag=True, no_push=True, root=tmp_repo)
    assert "topconf" in rep["errors"]
    assert (tmp_repo / "data/sources/topconf.json").read_bytes() == src
    assert rep["items"] == 7
    items = json.loads((tmp_repo / "src/data/items.json").read_text())["items"]
    assert sum(1 for i in items if i.get("group") == "gallery") == 7


def test_journal_empty_and_one(tmp_path):
    p = tmp_path / "journals.json"
    p.write_text("[]")
    assert parse_journal(p, tmp_path)[0] == []
    img = tmp_path / "fig.png"
    Image.new("RGB", (40, 30), "white").save(img)
    p.write_text(json.dumps([
        {"doi": "10.1038/s41586-024-00001-1", "figure": "Fig. 1", "venue": "Nature", "year": 2024,
         "title": "A Nature Paper", "authors": ["N"], "image": str(img)},
        {"figure": "Fig. 2", "venue": "Science", "year": 2024, "title": "No DOI", "image": str(img)},
    ]))
    recs, st = parse_journal(p, tmp_path)
    assert len(recs) == 1 and recs[0]["source"] == "journal" and recs[0]["venue"] == "Nature"
    assert recs[0]["paper"] == "https://doi.org/10.1038/s41586-024-00001-1" and recs[0]["kind"] == "framework"
    assert st["skipped"] == 1


def test_run_only_keeps_other_sources(tmp_repo):
    run(local=LOCAL, no_tag=True, no_push=True, root=tmp_repo)
    rep = run(sources=("topconf",), local=LOCAL, no_tag=True, no_push=True, root=tmp_repo)
    assert rep["items"] == 7 and rep["sources"]["papergallery"] == 4


def test_run_prunes_orphan_thumbs(tmp_repo):
    run(local=LOCAL, no_tag=True, no_push=True, root=tmp_repo)
    orphan = tmp_repo / "public/thumbs/tc-merged-away.webp"
    orphan.write_bytes(b"x")
    man = json.loads((tmp_repo / "data/sources/assets-manifest.json").read_text())
    man["tc-merged-away"] = {"sha256": "s", "ext": "jpg", "w": 1, "h": 1, "uploaded": True}
    (tmp_repo / "data/sources/assets-manifest.json").write_text(json.dumps(man))
    rep = run(local=LOCAL, no_tag=True, no_push=True, root=tmp_repo)
    assert not orphan.exists() and rep["pruned"] == 1
    assert "tc-merged-away" not in json.loads((tmp_repo / "data/sources/assets-manifest.json").read_text())
