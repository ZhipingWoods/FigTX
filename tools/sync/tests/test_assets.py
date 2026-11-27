import pytest
from PIL import Image

from tools.sync.assets import BadImage, make_thumb, sync_assets


def _save(path, size, mode="RGB", color=(200, 30, 30)):
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", size, color)
    if mode != "RGB":
        im = im.convert(mode)
    im.save(path)
    return path


def test_thumb_size_and_format(tmp_path):
    src = _save(tmp_path / "a.jpg", (2000, 1000))
    assert make_thumb(src, tmp_path / "t.webp") == (800, 400)
    im = Image.open(tmp_path / "t.webp")
    assert im.format == "WEBP" and im.size == (800, 400)


def test_thumb_no_upscale(tmp_path):
    src = _save(tmp_path / "a.png", (300, 200))
    assert make_thumb(src, tmp_path / "t.webp") == (300, 200)


def test_thumb_handles_modes_and_corrupt(tmp_path):
    for mode, ext in (("CMYK", "jpg"), ("P", "png"), ("L", "png")):
        make_thumb(_save(tmp_path / f"m.{ext}", (100, 80), mode), tmp_path / f"{mode}.webp")
        assert Image.open(tmp_path / f"{mode}.webp").mode == "RGB"
    rgba = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    rgba.save(tmp_path / "alpha.png")
    make_thumb(tmp_path / "alpha.png", tmp_path / "alpha.webp")
    assert Image.open(tmp_path / "alpha.webp").convert("RGB").getpixel((25, 25)) == (255, 255, 255)
    good = _save(tmp_path / "full.jpg", (400, 400))
    (tmp_path / "trunc.jpg").write_bytes(good.read_bytes()[:300])
    with pytest.raises(BadImage):
        make_thumb(tmp_path / "trunc.jpg", tmp_path / "x.webp")


def _items(root):
    _save(root / "a.jpeg", (1000, 500))
    _save(root / "b.png", (200, 100), color=(10, 10, 200))
    return [{"id": "tc-a", "image": {"source": "topconf", "path": "a.jpeg"}},
            {"id": "pg-b", "image": {"source": "papergallery", "path": "b.png"}}]


def test_sync_assets_writes_everything(tmp_path):
    root = tmp_path / "up"
    items = _items(root)
    roots = {"topconf": root, "papergallery": root}
    rep = sync_assets(items, roots, tmp_path / "thumbs", tmp_path / "orig", tmp_path / "m.json")
    assert rep == {"thumbs_new": 2, "skipped": 0, "bad": []}
    assert (tmp_path / "thumbs/tc-a.webp").exists() and (tmp_path / "orig/tc-a.jpg").exists()
    assert (tmp_path / "orig/pg-b.png").exists()


def test_sync_assets_idempotent(tmp_path):
    root = tmp_path / "up"
    items = _items(root)
    roots = {"topconf": root, "papergallery": root}
    sync_assets(items, roots, tmp_path / "thumbs", tmp_path / "orig", tmp_path / "m.json")
    before = (tmp_path / "m.json").read_bytes()
    rep = sync_assets(items, roots, tmp_path / "thumbs", tmp_path / "orig", tmp_path / "m.json")
    assert rep["thumbs_new"] == 0 and rep["skipped"] == 2 and (tmp_path / "m.json").read_bytes() == before


def test_sync_assets_resets_uploaded_on_change(tmp_path):
    import json

    root = tmp_path / "up"
    items = _items(root)
    roots = {"topconf": root, "papergallery": root}
    m = tmp_path / "m.json"
    sync_assets(items, roots, tmp_path / "thumbs", tmp_path / "orig", m)
    data = json.loads(m.read_text())
    for v in data.values():
        v["uploaded"] = True
    m.write_text(json.dumps(data))
    _save(root / "a.jpeg", (1000, 500), color=(0, 200, 0))
    sync_assets(items, roots, tmp_path / "thumbs", tmp_path / "orig", m)
    data = json.loads(m.read_text())
    assert data["tc-a"]["uploaded"] is False and data["pg-b"]["uploaded"] is True


def test_sync_assets_bad_image_reported(tmp_path):
    root = tmp_path / "up"
    items = _items(root)
    (root / "b.png").write_bytes(b"not an image")
    rep = sync_assets(items, {"topconf": root, "papergallery": root}, tmp_path / "t", tmp_path / "o", tmp_path / "m.json")
    assert rep["bad"] == ["pg-b"] and rep["thumbs_new"] == 1
