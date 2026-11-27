import json

from huggingface_hub.errors import LocalTokenNotFoundError

from tools.sync.push_assets import REPO_ID, original_url, push


class FakeApi:
    def __init__(self, fail_auth=False):
        self.calls, self.fail_auth = [], fail_auth

    def create_repo(self, repo_id, **kw):
        if self.fail_auth:
            raise LocalTokenNotFoundError("no token")
        self.calls.append({"op": "create_repo", "repo_id": repo_id, **kw})

    def upload_folder(self, **kw):
        self.calls.append({"op": "upload_folder", **kw})

    def upload_file(self, **kw):
        self.calls.append({"op": "upload_file", **kw})


def _setup(tmp_path, uploaded=(False, False, True)):
    d = tmp_path / "orig"
    d.mkdir()
    man = {}
    for (name, ext), up in zip((("a", "jpg"), ("b", "png"), ("c", "jpg")), uploaded):
        (d / f"{name}.{ext}").write_bytes(b"x")
        man[name] = {"sha256": "s", "ext": ext, "w": 1, "h": 1, "uploaded": up}
    m = tmp_path / "m.json"
    m.write_text(json.dumps(man))
    return d, m


def test_push_only_pending(tmp_path):
    d, m = _setup(tmp_path)
    fake = FakeApi()
    assert push(d, m, api=fake) == {"uploaded": 2}
    up = [c for c in fake.calls if c["op"] == "upload_folder"][0]
    assert up["allow_patterns"] == ["a.jpg", "b.png"] and up["path_in_repo"] == "originals"
    assert up["repo_id"] == REPO_ID and up["repo_type"] == "dataset"
    assert any(c["op"] == "upload_file" and c["path_in_repo"] == "README.md" for c in fake.calls)


def test_push_marks_uploaded(tmp_path):
    d, m = _setup(tmp_path)
    push(d, m, api=FakeApi())
    assert all(v["uploaded"] for v in json.loads(m.read_text()).values())


def test_push_noop_when_nothing_pending(tmp_path):
    d, m = _setup(tmp_path, uploaded=(True, True, True))
    fake = FakeApi()
    assert push(d, m, api=fake) == {"uploaded": 0} and fake.calls == []


def test_push_skips_missing_local_files(tmp_path):
    d, m = _setup(tmp_path)
    (d / "b.png").unlink()
    fake = FakeApi()
    assert push(d, m, api=fake) == {"uploaded": 1}
    assert json.loads(m.read_text())["b"]["uploaded"] is False


def test_push_dry_run(tmp_path):
    d, m = _setup(tmp_path)
    fake = FakeApi()
    assert push(d, m, api=fake, dry_run=True) == {"uploaded": 0, "pending": 2} and fake.calls == []


def test_original_url():
    assert original_url("tc-x", "jpg") == \
        "https://huggingface.co/datasets/OliverThompson/figtx-assets/resolve/main/originals/tc-x.jpg"


def test_push_no_auth(tmp_path):
    d, m = _setup(tmp_path)
    assert push(d, m, api=FakeApi(fail_auth=True)) == {"uploaded": 0, "skipped": "no-auth"}
