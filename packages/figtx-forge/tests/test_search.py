import json

from figtx_forge.cli import main
from figtx_forge.search import load_index, search
from helpers import FIXTURE

IDX_PATH = FIXTURE.parent / "index.json"
IDX = json.loads(IDX_PATH.read_text())


def test_search_title_beats_tag():
    r = search(IDX, "diffusion")
    assert [x["id"] for x in r] == ["title-hit", "tag-hit", "caption-hit"]


def test_search_number_exact():
    assert [x["no"] for x in search(IDX, "T042")] == ["T042"]
    assert [x["no"] for x in search(IDX, "f011")] == ["F011"]


def test_search_filter_type():
    r = search(IDX, "model", fig_type="framework")
    assert r and all(x["figType"] == "framework" for x in r)


def test_search_filter_category():
    assert [x["id"] for x in search(IDX, "model", category="table")] == ["table-042"]


def test_search_no_hits():
    assert search(IDX, "zzzz") == []


def test_load_index_path():
    assert load_index(str(IDX_PATH))["v"] == 1


def test_load_index_env(monkeypatch):
    monkeypatch.setenv("FIGTX_INDEX", str(IDX_PATH))
    assert len(load_index(None)["items"]) == 4


def test_cli_search_text_and_json(capsys):
    assert main(["search", "diffusion", "--index", str(IDX_PATH), "--limit", "1"]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1 and out[0].startswith("F011") and "https://zhipingwoods.github.io/FigTX/renders-fig/b.webp" in out[0]
    assert main(["search", "diffusion", "--index", str(IDX_PATH), "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 3
