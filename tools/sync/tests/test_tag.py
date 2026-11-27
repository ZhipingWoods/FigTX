import json

from tools.sync.tag import tag


def _items(n):
    return [{"id": f"i{k}", "title": f"Paper {k}", "figType": "pipeline", "paper": {"venue": "ICML", "year": 2024}}
            for k in range(n)]


class FakeChat:
    def __init__(self, reply=None):
        self.prompts, self.reply = [], reply

    def __call__(self, messages, **kw):
        self.prompts.append(messages[-1]["content"])
        if self.reply is not None:
            return self.reply
        ids = [x["id"] for x in json.loads(messages[-1]["content"].split("ITEMS:\n", 1)[1])]
        return "```json\n" + json.dumps({i: {"domains": ["cv", "bogus"], "problems": ["Novel View Synthesis " * 5]}
                                         for i in ids}) + "\n```"


def test_tag_writes_valid_domains(tmp_path):
    p = tmp_path / "tags.json"
    rep = tag(_items(2), p, chat_fn=FakeChat())
    t = json.loads(p.read_text())
    assert rep == {"tagged": 2, "failed": 0}
    assert t["i0"]["domains"] == ["cv"] and len(t["i0"]["problems"][0]) <= 60
    assert t["i0"]["problems"][0] == t["i0"]["problems"][0].lower()


def test_tag_skips_cached_and_manual(tmp_path):
    p = tmp_path / "tags.json"
    p.write_text(json.dumps({"i0": {"domains": ["nlp"], "problems": [], "manual": True}}))
    fake = FakeChat()
    tag(_items(2), p, chat_fn=fake)
    assert '"i0"' not in fake.prompts[0] and json.loads(p.read_text())["i0"]["domains"] == ["nlp"]


def test_tag_batches(tmp_path):
    fake = FakeChat()
    rep = tag(_items(85), tmp_path / "tags.json", chat_fn=fake)
    assert len(fake.prompts) == 3 and rep["tagged"] == 85


def test_tag_bad_json_counts_failed(tmp_path):
    rep = tag(_items(40), tmp_path / "tags.json", chat_fn=FakeChat(reply="sorry, no json"))
    assert rep == {"tagged": 0, "failed": 40}


def test_tag_no_key(tmp_path, monkeypatch):
    monkeypatch.delenv("FIGTX_LLM_KEY", raising=False)
    assert tag(_items(3), tmp_path / "tags.json") == {"tagged": 0, "skipped": "no-key"}


def test_prompt_has_no_abstract(tmp_path):
    items = _items(1)
    items[0]["abstract"] = "SECRET-ABSTRACT"
    fake = FakeChat()
    tag(items, tmp_path / "tags.json", chat_fn=fake)
    assert "SECRET-ABSTRACT" not in fake.prompts[0]


def test_tag_parallel_same_result(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    tag(_items(130), a, chat_fn=FakeChat(), workers=1)
    rep = tag(_items(130), b, chat_fn=FakeChat(), workers=6)
    assert rep == {"tagged": 130, "failed": 0} and a.read_bytes() == b.read_bytes()
