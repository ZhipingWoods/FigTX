"""P1 全分支评审发现的问题的回归测试。"""
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

from tools.sync.merge import merge, rec_key, seed_id_map
from tools.sync.push_assets import push
from tools.sync.run import run
from tools.sync.sync_journal import parse as parse_journal
from tools.sync.sync_papergallery import parse as parse_pg

FIX = Path(__file__).parent / "fixtures"
REPO = Path(__file__).resolve().parents[3]


def _img(root, rel, variant=0, size=(400, 300)):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(im)
    if variant == 0:
        d.rectangle((40, 60, 160, 240), fill="#3366cc")
        d.ellipse((220, 30, 360, 180), fill="#cc3333")
    else:
        d.rectangle((200, 150, 380, 290), fill="#222222")
        d.line((0, 0, 400, 90), fill="#22aa22", width=10)
    im.save(p)
    return rel


def _rec(source, uid, kind, image, title="Shared Paper About Gaussian Splatting", **kw):
    r = {"source": source, "upstreamId": uid, "kind": kind, "title": title, "authors": ["A"], "venue": "CVPR",
         "year": 2025, "tier": None, "award": None, "tags": [], "paper": None, "pdf": None, "code": None,
         "project": None, "bibtex": None, "image": image, "w": 400, "h": 300}
    r.update(kw)
    return r


def test_ids_stable_when_topconf_joins_pg_only(tmp_path):
    roots = {"topconf": tmp_path, "papergallery": tmp_path}
    pg = _rec("papergallery", "X_Paper_2025", "pipeline", _img(tmp_path, "pg.jpg"))
    id_map = {}
    first, _ = merge([pg], roots, id_map=id_map)
    assert first[0]["id"] == "pg-pipeline-x-paper-2025"
    tc = _rec("topconf", "cvpr2025-1", "architecture", _img(tmp_path, "tc.jpg"))
    second, _ = merge([pg, tc], roots, id_map=id_map)
    assert [i["id"] for i in second] == ["pg-pipeline-x-paper-2025"] and len(second[0]["sources"]) == 2


def test_ids_stable_when_header_deleted(tmp_path):
    roots = {"papergallery": tmp_path}
    img = _img(tmp_path, "x.jpg")
    head = _rec("papergallery", "X_Paper_2025", "header", img)
    pipe = _rec("papergallery", "X_Paper_2025", "pipeline", img)
    id_map = {}
    first, _ = merge([head, pipe], roots, id_map=id_map)
    second, _ = merge([head], roots, id_map=id_map)
    assert first[0]["id"] == second[0]["id"]


def test_pipeline_preferred_over_header(tmp_path):
    img = _img(tmp_path, "x.jpg")
    items, _ = merge([_rec("papergallery", "X_Paper_2025", "header", img),
                      _rec("papergallery", "X_Paper_2025", "pipeline", img)], {"papergallery": tmp_path})
    assert items[0]["figType"] == "pipeline"
    assert sorted(s["kind"] for s in items[0]["sources"]) == ["header", "pipeline"]


def test_seed_id_map_keeps_existing_ids(tmp_path):
    prev = [{"id": "pg-header-x-paper-2025", "sources": [
        {"platform": "papergallery", "upstreamId": "X_Paper_2025", "repo": None},
        {"platform": "papergallery", "upstreamId": "X_Paper_2025", "repo": None}]}]
    id_map = seed_id_map(prev)
    img = _img(tmp_path, "x.jpg")
    items, _ = merge([_rec("papergallery", "X_Paper_2025", "header", img),
                      _rec("papergallery", "X_Paper_2025", "pipeline", img)], {"papergallery": tmp_path}, id_map=id_map)
    assert items[0]["id"] == "pg-header-x-paper-2025" and items[0]["figType"] == "pipeline"
    assert rec_key({"source": "papergallery", "kind": "header", "upstreamId": "X"}) == "papergallery:header:X"


def test_corrupt_image_skipped_not_crash(tmp_path):
    (tmp_path / "bad.jpg").write_bytes(b"not an image")
    good = _rec("topconf", "ok", "pipeline", _img(tmp_path, "ok.jpg"), title="Fine Paper With A Long Title")
    bad = _rec("topconf", "bad", "pipeline", "bad.jpg", title="Broken Paper With A Long Title")
    items, rep = merge([good, bad], {"topconf": tmp_path})
    assert [i["id"] for i in items] == ["tc-ok"] and rep["bad_records"] == ["topconf:bad"]


def test_papergallery_corrupt_image_counted(tmp_path):
    root = tmp_path / "pg"
    shutil.copytree(FIX / "papergallery", root)
    (root / "public/images/pipeline/Agelos_DynMF_2024.jpg").write_bytes(b"broken")
    recs, st = parse_pg(root)
    assert st["bad_image"] == 1 and "Agelos_DynMF_2024" not in {r["upstreamId"] for r in recs}


def test_url_scheme_sanitized(tmp_path):
    r = _rec("topconf", "x", "pipeline", _img(tmp_path, "x.jpg"), code="javascript:alert(1)",
             paper="https://ok.example/p", project="ftp://x")
    items, _ = merge([r], {"topconf": tmp_path})
    p = items[0]["paper"]
    assert p["code"] is None and p["project"] is None and p["url"] == "https://ok.example/p"


class FakeApi:
    def __init__(self, fail_upload=None):
        self.calls, self.fail_upload = [], fail_upload

    def create_repo(self, *a, **k):
        self.calls.append("create_repo")

    def upload_folder(self, **k):
        if self.fail_upload:
            raise self.fail_upload
        self.calls.append("upload_folder")

    def upload_file(self, **k):
        self.calls.append("upload_file")

    def delete_files(self, **k):
        self.calls.append(("delete_files", tuple(k["delete_patterns"])))


def _manifest(tmp_path):
    d = tmp_path / "orig"
    d.mkdir()
    (d / "a.jpg").write_bytes(b"x")
    m = tmp_path / "m.json"
    m.write_text(json.dumps({"a": {"sha256": "s", "ext": "jpg", "w": 1, "h": 1, "uploaded": False}}))
    return d, m


def test_push_http_error_reported(tmp_path):
    from huggingface_hub.errors import HfHubHTTPError

    d, m = _manifest(tmp_path)
    class FakeHttpError(HfHubHTTPError):  # 构造真实异常需要 HTTP 响应对象，这里只要类型对
        def __init__(self, msg):
            Exception.__init__(self, msg)

    rep = push(d, m, api=FakeApi(fail_upload=FakeHttpError("401 Unauthorized")))
    assert rep["uploaded"] == 0 and "401" in rep["error"]
    assert json.loads(m.read_text())["a"]["uploaded"] is False


def test_push_deletes_taken_down(tmp_path):
    d, m = _manifest(tmp_path)
    data = json.loads(m.read_text())
    data["a"]["uploaded"] = True
    data["gone"] = {"sha256": "s", "ext": "jpg", "w": 1, "h": 1, "uploaded": True, "takedown": True}
    m.write_text(json.dumps(data))
    fake = FakeApi()
    rep = push(d, m, api=fake)
    assert ("delete_files", ("originals/gone.jpg",)) in fake.calls and rep["deleted"] == 1
    assert "gone" not in json.loads(m.read_text())


def test_journal_relative_path(tmp_path):
    (tmp_path / "data").mkdir()
    Image.new("RGB", (20, 10), "white").save(tmp_path / "data" / "fig.png")
    p = tmp_path / "data" / "journals.json"
    p.write_text(json.dumps([{"doi": "10.1/x", "figure": "Fig. 1", "venue": "Nature", "year": 2024, "title": "T",
                              "image": "data/fig.png"}, {"doi": "10.1/y", "image": "ht!tp://bad url"}]))
    recs, st = parse_journal(p, tmp_path)
    assert recs[0]["image"] == "data/fig.png" and st["skipped"] == 1


# ---------- run 级 ----------
def _repo(tmp_path):
    r = tmp_path / "repo"
    (r / "tools").mkdir(parents=True)
    for f in ("build-data.mjs", "assign_numbers.py", "shard.mjs"):
        shutil.copy(REPO / "tools" / f, r / "tools" / f)
    (r / "data").mkdir()
    (r / "data" / "catalog.json").write_text("{}")
    return r


def test_upstream_missing_items_kept_and_marked(tmp_path):
    r = _repo(tmp_path)
    tc = tmp_path / "tc"
    shutil.copytree(FIX / "topconf", tc)
    local = {"topconf": tc, "papergallery": FIX / "papergallery"}
    run(local=local, no_tag=True, no_push=True, root=r)
    (tc / "images/cvpr/final/cvpr2024-0001.jpg").unlink()
    rep = run(local=local, no_tag=True, no_push=True, root=r)
    g = {i["id"]: i for i in json.loads((r / "data/raw-gallery.json").read_text())}
    assert g["tc-cvpr2024-0001"]["upstreamMissing"] is True and rep["missing"] == 1
    assert (r / "public/thumbs/tc-cvpr2024-0001.webp").exists() and rep["items"] == 7


def test_takedown_removes_and_blocks(tmp_path):
    r = _repo(tmp_path)
    local = {"topconf": FIX / "topconf", "papergallery": FIX / "papergallery"}
    run(local=local, no_tag=True, no_push=True, root=r)
    (r / "data/takedown.json").write_text(json.dumps([{"id": "tc-icml2023-0064", "reason": "author request",
                                                        "date": "2026-11-27"}]))
    rep = run(local=local, no_tag=True, no_push=True, root=r)
    ids = {i["id"] for i in json.loads((r / "data/raw-gallery.json").read_text())}
    assert "tc-icml2023-0064" not in ids and rep["removed"] == ["tc-icml2023-0064"]
    assert not (r / "public/thumbs/tc-icml2023-0064.webp").exists()
    assert "tc-icml2023-0064" not in json.loads((r / "data/sources/assets-manifest.json").read_text())
    rep2 = run(local=local, no_tag=True, no_push=True, root=r)
    assert "tc-icml2023-0064" not in {i["id"] for i in json.loads((r / "data/raw-gallery.json").read_text())}
    assert rep2["items"] == 6


def test_report_counts_new(tmp_path):
    r = _repo(tmp_path)
    local = {"topconf": FIX / "topconf", "papergallery": FIX / "papergallery"}
    rep = run(local=local, no_tag=True, no_push=True, root=r)
    assert rep["new"] == 7 and rep["missing"] == 0
    rep2 = run(local=local, no_tag=True, no_push=True, root=r)
    assert rep2["new"] == 0
