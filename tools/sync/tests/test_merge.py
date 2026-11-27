from PIL import Image, ImageDraw

from tools.sync.merge import merge, paper_key

T = "Shared Paper: Something Great"


def _img(root, rel, size, variant):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(im)
    w, h = size
    if variant == 0:
        d.rectangle((w * .1, h * .2, w * .4, h * .8), fill="#3366cc")
        d.ellipse((w * .55, h * .1, w * .9, h * .6), fill="#cc3333")
    elif variant == 1:
        d.rectangle((w * .5, h * .5, w * .95, h * .95), fill="#222222")
        d.line((0, 0, w, h * .3), fill="#22aa22", width=max(2, w // 40))
    else:
        d.ellipse((w * .05, h * .05, w * .3, h * .9), fill="#aa22aa")
        d.rectangle((w * .6, h * .05, w * .95, h * .4), fill="#cccc22")
    im.save(p)
    return rel


def _rec(source, uid, title, year, image, size, **kw):
    r = {"source": source, "upstreamId": uid, "kind": kw.pop("kind", "pipeline"), "title": title, "authors": ["A"],
         "venue": kw.pop("venue", "ICML"), "year": year, "tier": None, "award": None, "tags": kw.pop("tags", []),
         "paper": kw.pop("paper", None), "pdf": kw.pop("pdf", None), "code": kw.pop("code", None),
         "project": None, "bibtex": None, "image": image, "w": size[0], "h": size[1]}
    r.update(kw)
    return r


def _setup(tmp_path):
    tc, pg = tmp_path / "tc", tmp_path / "pg"
    recs = [
        _rec("topconf", "icml2024-1", T, 2024, _img(tc, "a.jpg", (450, 300), 0), (450, 300), tier="oral"),
        _rec("papergallery", "Smith_Shared_2024", T, 2024, _img(pg, "a.jpg", (900, 600), 0), (900, 600),
             code="https://github.com/x/y", tags=["Diffusion"], venue="Unknown"),
        _rec("topconf", "icml2024-2", "Two Figures Paper", 2024, _img(tc, "b.jpg", (400, 300), 1), (400, 300)),
        _rec("papergallery", "Lee_Two_2024", "Two Figures Paper", 2024, _img(pg, "c.jpg", (400, 300), 2), (400, 300)),
        _rec("topconf", "cvpr2023-9", "Arxiv Keyed Papr", 2023, _img(tc, "d.jpg", (400, 300), 2), (400, 300),
             paper="https://arxiv.org/abs/2301.00001"),
        _rec("papergallery", "Kim_Arxiv_2023", "Arxiv Keyed Paper", 2023, _img(pg, "d.jpg", (800, 600), 2), (800, 600),
             paper="https://arxiv.org/pdf/2301.00001v2.pdf", kind="header"),
        _rec("papergallery", "Old_Same_2022", "Two Figures Paper", 2022, _img(pg, "e.jpg", (400, 300), 1), (400, 300)),
    ]
    return recs, {"topconf": tc, "papergallery": pg}


def _by_id(items):
    return {i["id"]: i for i in items}


def test_same_figure_two_sources_merges(tmp_path):
    recs, roots = _setup(tmp_path)
    items, rep = merge(recs, roots)
    it = _by_id(items)["tc-icml2024-1"]
    assert [s["platform"] for s in it["sources"]] == ["papergallery", "topconf"]
    assert it["paper"]["code"] == "https://github.com/x/y" and it["paper"]["venue"] == "ICML"
    assert it["paper"]["tier"] == "oral" and it["tags"] == ["Diffusion"]
    assert it["image"] == {"source": "papergallery", "path": "a.jpg", "w": 900, "h": 600}
    assert "pg-pipeline-smith-shared-2024" not in _by_id(items)


def test_two_figures_same_paper_stay_separate(tmp_path):
    recs, roots = _setup(tmp_path)
    items, _ = merge(recs, roots)
    two = [i for i in items if i["paper"]["title"] == "Two Figures Paper" and i["paper"]["year"] == 2024]
    assert sorted(i["id"] for i in two) == ["pg-pipeline-lee-two-2024", "tc-icml2024-2"]


def test_arxiv_key_beats_title_typo(tmp_path):
    recs, roots = _setup(tmp_path)
    items, rep = merge(recs, roots)
    it = _by_id(items)["tc-cvpr2023-9"]
    assert len(it["sources"]) == 2 and it["figType"] == "pipeline"
    assert paper_key(recs[4]) == paper_key(recs[5]) == "arxiv:2301.00001"


def test_header_maps_to_teaser(tmp_path):
    recs, roots = _setup(tmp_path)
    only_pg = [dict(recs[5], upstreamId="Solo_2023", paper=None, title="Solo")]
    items, _ = merge(only_pg, roots)
    assert items[0]["figType"] == "teaser" and items[0]["id"] == "pg-header-solo-2023"


def test_same_title_diff_year_same_image_merges(tmp_path):
    recs, roots = _setup(tmp_path)
    items, rep = merge(recs, roots)
    it = _by_id(items)["tc-icml2024-2"]
    assert [s["upstreamId"] for s in it["sources"]] == ["Old_Same_2022", "icml2024-2"]
    assert rep["items"] == 4 and rep["merged"] == 3


def test_title_variants_are_one_paper(tmp_path):
    tc, pg = tmp_path / "tc", tmp_path / "pg"
    recs = [
        _rec("topconf", "acl-1", "Towards Economical Inference: Enabling D eep S eek\u2019s Multi-Head Latent Attention",
             2025, _img(tc, "x.jpg", (400, 300), 0), (400, 300)),
        _rec("papergallery", "Ji_MHA2MLA_2025", "Towards Economical Inference: Enabling DeepSeek's Multi-Head Latent "
             "Attention in Any Transformer-based LLMs", 2025, _img(pg, "x.jpg", (800, 600), 0), (800, 600)),
        _rec("papergallery", "Bian_DynamicCity_2025", "Dynamiccity: Large-scale 4d occupancy generation", 2025,
             _img(pg, "y.jpg", (400, 300), 1), (400, 300)),
        _rec("topconf", "iclr-2", "DynamicCity: Large-Scale 4D Occupancy Generation", 2025,
             _img(tc, "y.jpg", (400, 300), 1), (400, 300)),
    ]
    items, rep = merge(recs, {"topconf": tc, "papergallery": pg})
    assert sorted(i["id"] for i in items) == ["tc-acl-1", "tc-iclr-2"]


def test_arxiv_links_records_with_and_without_id(tmp_path):
    tc, pg = tmp_path / "tc", tmp_path / "pg"
    recs = [
        _rec("topconf", "a", "Completely Different Wording", 2024, _img(tc, "a.jpg", (400, 300), 2), (400, 300),
             paper="https://arxiv.org/abs/2402.00002"),
        _rec("papergallery", "B_Paper_2024", "Another Title Entirely", 2024, _img(pg, "a.jpg", (400, 300), 2), (400, 300),
             paper="https://arxiv.org/pdf/2402.00002.pdf"),
    ]
    items, _ = merge(recs, {"topconf": tc, "papergallery": pg})
    assert len(items) == 1


def test_suspects_only_close_images_across_papers(tmp_path):
    from tools.sync.merge import SUSPECT_IMAGE

    assert SUSPECT_IMAGE == 8
    recs, roots = _setup(tmp_path)
    _, rep = merge(recs, roots)
    assert all(s["reason"].startswith("dhash") and int(s["reason"].split()[1]) <= 8 for s in rep["suspects"])


def test_merge_deterministic(tmp_path):
    recs, roots = _setup(tmp_path)
    assert merge(recs, roots) == merge(list(reversed(recs)), roots)


def test_hash_cache_used(tmp_path):
    recs, roots = _setup(tmp_path)
    cache = {}
    merge(recs, roots, hashes=cache)
    assert len(cache) == len(recs)
    for p in (tmp_path / "tc").glob("*.jpg"):
        p.unlink()
    items, _ = merge(recs, roots, hashes=cache)
    assert len(items) == 4
