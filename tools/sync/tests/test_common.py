import json

from PIL import Image, ImageDraw

from tools.sync.common import (ROOT, arxiv_id, canon_venue, dhash, dump_json, hamming, load_json,
                               norm_title, slug)


def test_slug_stable_and_safe():
    assert slug("Deng_VPGS SLAM_2025") == "deng-vpgs-slam-2025"
    assert slug("中文 Name!") == "name"
    assert slug("x" * 200) == "x" * 80


def test_norm_title():
    assert norm_title("BPipe:  Memory-Balanced  Pipeline") == norm_title("bpipe memory balanced pipeline")


def test_arxiv_id():
    assert arxiv_id("https://arxiv.org/pdf/2312.00112v2.pdf") == "2312.00112"
    assert arxiv_id("https://arxiv.org/abs/2312.00112") == "2312.00112"
    assert arxiv_id("https://openreview.net/x") is None
    assert arxiv_id(None) is None


def test_canon_venue():
    assert [canon_venue(v) for v in ["neurips", "arxiv", "Foo", "", "mm"]] == ["NeurIPS", "arXiv", "FOO", "Unknown", "ACM MM"]


def _draw(path, size, seed):
    im = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(im)
    w, h = size
    if seed == 0:
        d.rectangle((w * 0.1, h * 0.2, w * 0.4, h * 0.8), fill="#3366cc")
        d.ellipse((w * 0.55, h * 0.1, w * 0.9, h * 0.6), fill="#cc3333")
    else:
        d.rectangle((w * 0.5, h * 0.5, w * 0.95, h * 0.95), fill="#222222")
        d.line((0, 0, w, h * 0.3), fill="#22aa22", width=max(2, w // 40))
    im.save(path)
    return path


def test_dhash_same_image_resized(tmp_path):
    a = dhash(_draw(tmp_path / "a.png", (800, 400), 0))
    b = dhash(_draw(tmp_path / "b.png", (400, 200), 0))
    c = dhash(_draw(tmp_path / "c.png", (800, 400), 1))
    assert len(a) == 16
    assert hamming(a, b) <= 4
    assert hamming(a, c) > 12


def test_dump_json_stable(tmp_path):
    obj = {"b": 1, "a": ["中文", 2]}
    p = tmp_path / "x.json"
    dump_json(p, obj)
    first = p.read_bytes()
    dump_json(p, obj)
    assert p.read_bytes() == first and first.endswith(b"\n")
    assert load_json(p, None) == obj
    assert load_json(tmp_path / "missing.json", []) == []


def test_taxonomy_shape():
    tax = json.loads((ROOT / "data" / "taxonomy.json").read_text(encoding="utf-8"))
    keys = [d["key"] for d in tax["domains"]]
    assert len(keys) == 16 and len(set(keys)) == 16
    assert all(d["zh"] and d["en"] for d in tax["domains"])
    assert tax["figTypeGroups"] and all(tax["figTypeGroups"].values())
