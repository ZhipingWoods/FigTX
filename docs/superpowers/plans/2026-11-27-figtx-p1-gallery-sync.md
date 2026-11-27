# FigTX P1 图库整合（topconf + PaperGallery）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 topconf-paper-figure-gallery（3449 张）和 PaperGallery（框架图约 256 张、主图约 68 张）的图和论文元数据并入 FigTX，合并去重。高清原图放 Hugging Face，缩略图放进 git，用一条命令 `npm run sync` 增量更新，每周自动开 PR；网站先用现有界面就能浏览全部图（新界面在 P2 做）。

**Architecture:** 新建 `tools/sync/`（Python）。每个来源一个适配器，输出统一格式的「来源记录」到 `data/sources/<source>.json`。然后依次执行：合并去重（论文键 + 图片 dHash）得到 `data/raw-gallery.json`、生成缩略图、领域打标（有缓存）、上传原图到 HF。`tools/build-data.mjs` 读取 raw-gallery 和 tags，生成前端条目和 `index.json`；`assign_numbers.py` 增量编号。上游仓库缓存在 `.cache/upstream/`（不入库）。

**Tech Stack:** Python ≥3.10，依赖 pillow、numpy、pyyaml、huggingface_hub，测试用 pytest，全部通过 `uv run --with ...` 运行，不改动现有 `.venv-fig`；Node 侧涉及 build-data.mjs 和 React（只做最小改动）；CI 是 GitHub Actions，开 PR 用 peter-evans/create-pull-request@v7。

**Spec:** `docs/superpowers/specs/2026-11-27-figtx-gallery-integration-design.md`（§5.1–§5.4、§9；P2 的界面另写计划）

## Global Constraints

- 已有编号（T001–T188、F001–F035）和 `#T042` 直达链接不能改变；新图从 F036 开始增量分配，**sync 不删除已有编号**。
- 每条外部数据都要保留署名：论文标题、作者、会议、年份、论文链接、来源项目（topconf / PaperGallery）、上游地址。
- PaperGallery 只取事实性元数据（title、authors、year、conference、tags、paper、code、project、bibtex）和图片，**不取 md 正文（摘要）**，不复制它的网站代码。
- 缩略图格式：webp，最长边 800px，quality 80，存放在 `public/thumbs/<id>.webp`，入库。
- 原图放在 HF 数据集 `OliverThompson/figtx-assets`（公开），路径为 `originals/<id>.<ext>`，访问 URL 为 `https://huggingface.co/datasets/OliverThompson/figtx-assets/resolve/main/originals/<id>.<ext>`。原图**不入 git**。
- 领域只能从 `data/taxonomy.json` 里选；人工修正过（`"manual": true`）的打标永远不被覆盖。
- 密钥只从 `.env` 和环境变量读取（`FIGTX_LLM_*`、`HF_TOKEN`），不打印，不写入任何文件。
- 单个文件不超过 500 行；改动后运行 `npm run build`。
- 用户在工作区里有一处未提交的修改 `tools/figgen/prompts.py`，不要碰它；每次提交都用明确的路径。
- 分支：`feat/gallery-sync`。`main` 有 ruleset 保护，通过 PR 合并。
- 测试命令：`uv run --with pytest --with pillow --with numpy --with pyyaml --with huggingface_hub pytest tools/sync/tests -q`（下文记作 `$SYNCTEST`）。

## Review Focus

1. **上游拉取失败**（断网、仓库改名）：该来源的 `data/sources/<src>.json` 保持上次的内容不变，sync 继续处理其他来源，最后的报告里写明失败；已有条目一个都不能丢。→ Task 9 `test_run_keeps_previous_source_on_fetch_failure`
2. **PaperGallery frontmatter 的 YAML 写坏了**（bibtex 里有未转义的引号、花括号或冒号）：退回正则解析，拿到 title、year 等核心字段即可；实在解析不了的条目计入报告，不能让整个 sync 崩溃。→ Task 3 `test_parse_broken_yaml_falls_back`
3. **文件名带空格、中文或大小写混杂**（如 `Deng_VPGS SLAM_2025.jpg`）：生成的 id 是安全的 slug，路径能正常读写，同一个文件每次生成的 id 都一样。→ Task 1 `test_slug_stable_and_safe`
4. **图片是 CMYK、带透明通道的 PNG、调色板模式或已损坏**：缩略图都转成白底 RGB；损坏的图跳过并计入报告，不让 sync 崩溃。→ Task 5 `test_thumb_handles_modes_and_corrupt`
5. **上游没有变化时再跑一次 sync**：不产生任何文件改动（`git status` 干净），编号不变，HF 不重复上传。→ Task 9 `test_run_is_idempotent`

---

## File Structure

```
tools/sync/__init__.py
tools/sync/common.py          slug、标题归一化、arXiv id 提取、venue 规范化、dHash、来源记录的数据类
tools/sync/sync_topconf.py    拉取上游并解析 figures.json → data/sources/topconf.json
tools/sync/sync_papergallery.py 拉取 web 分支（稀疏检出）并解析 frontmatter → data/sources/papergallery.json
tools/sync/merge.py           来源记录 → data/raw-gallery.json + 疑似重复报告
tools/sync/assets.py          缩略图、原图暂存、资产清单（sha256）
tools/sync/push_assets.py     原图增量上传到 HF
tools/sync/tag.py             用 LLM 做领域/研究问题打标，带缓存（data/tags.json）
tools/sync/run.py             总入口：sync 各来源 → merge → assets → tag → push → 报告
tools/sync/tests/test_*.py, tools/sync/tests/fixtures/
data/taxonomy.json            领域表（中英文名称）+ figType 分组
data/sources/*.json           各来源的标准化记录（入库）
data/raw-gallery.json         合并后的图库条目（入库）
data/tags.json                打标缓存（入库）
data/sources/assets-manifest.json  id → {sha256, ext, w, h, uploaded}（入库）
public/thumbs/<id>.webp       缩略图（入库）
tools/build-data.mjs          修改：并入 gallery 条目
tools/assign_numbers.py       修改：增加 --keep-missing 参数，gallery 条目的排序
src/App.tsx, src/labels.ts    最小改动：新 figType 的标签、详情页的论文信息块
.github/workflows/sync.yml    每周 sync 并开 PR
IMAGES_POLICY.md              图片来源、署名、下架流程
package.json                  新增 "sync" 脚本
.gitignore                    新增 .cache/
```

## 统一数据格式（Task 1 定义）

**来源记录**（`data/sources/<src>.json` 是这种记录的数组）：
```json
{"source": "topconf", "upstreamId": "icml2023-0064", "kind": "pipeline",
 "title": "BPipe: ...", "authors": ["..."], "venue": "ICML", "year": 2023,
 "tier": "oral", "award": null, "tags": [],
 "paper": "https://...", "pdf": "https://...", "code": null, "project": null, "bibtex": null,
 "image": "images/icml/final/icml2023-0064.jpg", "w": 450, "h": 288}
```
`image` 是相对上游仓库根目录的路径。上游根目录：topconf 为 `.cache/upstream/topconf`，PaperGallery 为 `.cache/upstream/papergallery`。

**图库条目**（`data/raw-gallery.json` 是这种条目的数组）：
```json
{"id": "tc-icml2023-0064", "figType": "pipeline", "title": "...",
 "paper": {"title": "...", "authors": [], "venue": "ICML", "year": 2023, "url": "...", "pdf": "...",
           "code": null, "project": null, "bibtex": null, "tier": "oral", "award": null},
 "tags": [], "sources": [{"platform": "topconf", "upstreamId": "icml2023-0064",
                          "repo": "https://github.com/qwdwqfwq/topconf-paper-figure-gallery"}],
 "image": {"source": "topconf", "path": "images/icml/final/icml2023-0064.jpg", "w": 450, "h": 288},
 "dhash": "f0e1d2c3b4a59687"}
```
id 规则：topconf 为 `tc-<upstreamId>`；PaperGallery 为 `pg-<kind>-<slug(stem)>`。两边重复合并时，保留 topconf 的 id。

---

### Task 1: 公共工具与领域表

**Files:**
- Create: `tools/sync/__init__.py`、`tools/sync/common.py`、`data/taxonomy.json`
- Test: `tools/sync/tests/test_common.py`

**Interfaces:**
- Produces:
  - `slug(s: str) -> str`：转小写；非 `[a-z0-9]` 的字符序列替换为 `-`；去掉首尾的 `-`；最长 80 个字符。
  - `norm_title(s: str) -> str`：转小写，NFKC 归一化，去掉标点和多余空白。
  - `arxiv_id(url: str | None) -> str | None`：识别 `arxiv.org/(abs|pdf)/XXXX.XXXXX`，去掉版本号和 `.pdf` 后缀。
  - `canon_venue(s: str) -> str`：映射关系为 neurips→NeurIPS、iclr→ICLR、icml→ICML、cvpr→CVPR、iccv→ICCV、eccv→ECCV、acl→ACL、emnlp→EMNLP、naacl→NAACL、aaai→AAAI、ijcai→IJCAI、siggraph→SIGGRAPH、tpami→TPAMI、ijcv→IJCV、arxiv→arXiv、mm→ACM MM、kdd→KDD、icra→ICRA、iros→IROS、rss→RSS、wacv→WACV、tog→TOG；不在表里的转大写；空字符串映射为 `"Unknown"`。
  - `dhash(path_or_image) -> str`：64 位差值哈希，以 16 位十六进制字符串表示（灰度后缩放到 9×8，比较相邻像素）。
  - `hamming(a: str, b: str) -> int`
  - `load_json(path, default)`、`dump_json(path, obj)`：dump 时 `ensure_ascii=False, indent=1`，键序稳定，并以换行结尾，保证 sync 幂等。
- `data/taxonomy.json`：
  - `{"domains": [{"key":"cv","zh":"计算机视觉","en":"Computer Vision"}, ...], "figTypeGroups": {...}}`
  - 领域 key：cv、3d、gen、nlp、mm、rl、robot、theory、graph、sys、safety、sci、med、audio、rec、agent，共 16 个，中英文名称取自 spec §5.3。
  - `figTypeGroups`：framework 组为 [framework, architecture, pipeline, mechanism]；teaser 组为 [teaser, conceptual, taxonomy]；experiment 组为 [quantitative, qualitative, results, comparison, efficiency, tradeoff, motivation, style]。

- [ ] **Step 1: 写失败测试**
```python
def test_slug_stable_and_safe(): assert slug("Deng_VPGS SLAM_2025") == "deng-vpgs-slam-2025" and slug("中文 Name!") == "name" and slug("中文 Name!") == slug("中文 Name!")
def test_norm_title(): assert norm_title("BPipe:  Memory-Balanced  Pipeline") == norm_title("bpipe memory balanced pipeline")
def test_arxiv_id(): assert arxiv_id("https://arxiv.org/pdf/2312.00112v2.pdf") == "2312.00112" and arxiv_id("https://openreview.net/x") is None
def test_canon_venue(): assert [canon_venue(v) for v in ["neurips","arxiv","Foo",""]] == ["NeurIPS","arXiv","FOO","Unknown"]
def test_dhash_same_image_resized(tmp_path): # 同一张图分别存成 800px 宽和 400px 宽 → hamming ≤ 4；与另一张不同的图 → hamming > 12
def test_dump_json_stable(tmp_path): # 同一个对象 dump 两次，得到的字节完全相同，并以 "\n" 结尾
def test_taxonomy_shape(): # domains 共 16 个，key 不重复；每个 figTypeGroups 的值都是非空列表
```
- [ ] **Step 2: 运行 `$SYNCTEST`，确认失败（ModuleNotFoundError）。**
- [ ] **Step 3: 实现。**
- [ ] **Step 4: 运行 `$SYNCTEST`，确认通过。**
- [ ] **Step 5: 提交** `git checkout -b feat/gallery-sync && git add tools/sync data/taxonomy.json && git commit -m "feat(sync): 公共工具与领域表"`

### Task 2: topconf 适配器

**Files:**
- Create: `tools/sync/sync_topconf.py`、`tools/sync/tests/fixtures/topconf/`（迷你上游仓库：`data/figures.json` 中 3 条记录，`images/` 下 3 张小图）
- Test: `tools/sync/tests/test_topconf.py`

**Interfaces:**
- Consumes: `canon_venue`、`dump_json`
- Produces:
  - `fetch(cache_dir: Path, local: Path | None = None) -> Path`：local 不为空时直接返回 local；否则 `git clone --depth 1 https://github.com/qwdwqfwq/topconf-paper-figure-gallery <cache>/topconf`，已存在则执行 `git -C ... pull --ff-only`。返回上游根目录。失败时抛出 `FetchError`。
  - `parse(root: Path) -> list[dict]`：读取 `data/figures.json` 并转换成来源记录。`kind` 取 pattern 的值；`paper` 取 `paper` 字段，`pdf` 取 `pdf_source` 字段；`tier` 和 `award` 原样保留；图片文件不存在的记录跳过并计数。
  - `main(argv) -> int`：参数 `--local PATH` 和 `--out data/sources/topconf.json`。

- [ ] **Step 1: 写失败测试**
```python
def test_parse_fixture(): recs = parse(FIX); assert len(recs) == 3 and recs[0]["venue"] == "ICML" and recs[0]["source"] == "topconf"
def test_parse_skips_missing_image(tmp_path): # 把 fixture 复制到 tmp_path，删掉一张图 → 只解析出 2 条记录
def test_fetch_local_passthrough(tmp_path): assert fetch(tmp_path, local=FIX) == FIX
def test_fetch_failure_raises(tmp_path, monkeypatch): # 把 git 命令换成一个会失败的命令 → 抛出 FetchError
```
- [ ] **Step 2–4: 先确认测试失败，再实现，最后确认通过。**
- [ ] **Step 5: 提交** `feat(sync): topconf 适配器`

### Task 3: PaperGallery 适配器

**Files:**
- Create: `tools/sync/sync_papergallery.py`、`tools/sync/tests/fixtures/papergallery/`（迷你 web 分支结构：一份正常的 md、一份带有坏 YAML 的 md、一份带空格文件名的 md，以及对应的图片）
- Test: `tools/sync/tests/test_papergallery.py`

**Interfaces:**
- Produces:
  - `fetch(cache_dir, local=None) -> Path`：不使用 local 时，执行 `git clone --depth 1 --branch web --filter=blob:none --sparse https://github.com/LongHZ140516/PaperGallery <cache>/papergallery`，然后 `git sparse-checkout set src/content/images public/images`；已存在则执行 `pull --ff-only`。
  - `parse_frontmatter(text: str) -> dict | None`：先用 `yaml.safe_load` 解析 `---` 之间的内容；解析失败时退回到逐行正则，取 `key: "value"` 和 `key: ["a", "b"]` 两种形式。bibtex 在回退模式下取到的值不可靠，直接置为 None。title 和 image 都缺失时返回 None。
  - `parse(root) -> tuple[list[dict], dict]`：分别遍历 `src/content/images/{pipeline,header}/paper/*.md`；kind 为 `pipeline` 或 `header`，其中 header 对应 figType `teaser`（在 merge 阶段映射）；图片路径为 `public/images/<kind>/<image>`；year 转成 int。**md 正文一律丢弃。** 第二个返回值是统计信息 `{"parsed": n, "fallback": n, "failed": n, "missing_image": n}`。
  - `main(argv) -> int`

- [ ] **Step 1: 写失败测试**
```python
def test_parse_ok(): recs, st = parse(FIX); r = [x for x in recs if x["upstreamId"] == "Agelos_DynMF_2024"][0]; assert r["venue"] == "ECCV" and r["code"].startswith("https://github.com") and "abstract" not in r
def test_parse_broken_yaml_falls_back(): recs, st = parse(FIX); assert st["fallback"] == 1 and any(x["upstreamId"] == "Broken_Yaml_2025" for x in recs)
def test_space_in_filename(): # 文件名为 "Deng_VPGS SLAM_2025.jpg" 的条目被解析出来，且图片路径存在
def test_body_never_kept(): # 所有记录序列化成 JSON 后，都不包含 fixture 里摘要正文中的那句话
```
- [ ] **Step 2–4: 先确认测试失败，再实现，最后确认通过。**
- [ ] **Step 5: 提交** `feat(sync): PaperGallery 适配器（只取元数据和图片）`

### Task 4: 合并去重

**Files:**
- Create: `tools/sync/merge.py`
- Test: `tools/sync/tests/test_merge.py`

**Interfaces:**
- Consumes: `norm_title`、`arxiv_id`、`slug`、`dhash`、`hamming`
- Produces:
  - `paper_key(rec) -> str`：优先用 `arxiv:<id>`（从 paper 或 pdf 链接里提取）；否则用 `title:<norm_title>:<year>`。
  - `merge(records: list[dict], roots: dict[str, Path], hashes: dict | None = None) -> tuple[list[dict], dict]`：
    1. 按 paper_key 分组。
    2. 组内按 dHash 聚类：hamming ≤ 6 视为同一张图。
    3. 每个聚类生成一个条目：图片取 w×h 最大的那张；id 优先用 topconf 的。
    4. 元数据按字段合并：非空值优先，topconf 优先；code、project、bibtex 从 PaperGallery 补充；tags 取并集。
    5. sources 列出所有来源。
    6. figType 规则：PaperGallery 的 header 映射为 teaser，pipeline 保持 pipeline；topconf 的 pattern 原样保留。
    7. 输出按 id 排序。
    8. `hashes` 是 dHash 缓存，键为 `"<source>:<upstreamId>"`，命中则不重新计算。
  - 第二个返回值是报告：`{"items": n, "merged": n, "suspects": [{"a": id, "b": id, "reason": "same-title-diff-year" | "dhash 7-12"}]}`

- [ ] **Step 1: 写失败测试**（用 Task 2、Task 3 的 fixture 构造：一篇论文同时出现在两个来源，图相同但分辨率不同；另一篇论文有两张不同的图）
```python
def test_same_figure_two_sources_merges(): items, rep = merge(...); it = by_id(items)["tc-x"]; assert len(it["sources"]) == 2 and it["paper"]["code"] and it["image"]["w"] == 900
def test_two_figures_same_paper_stay_separate(): assert len([i for i in items if i["paper"]["title"] == T]) == 2
def test_arxiv_key_beats_title_typo(): # 标题有一处拼写差异，但 arXiv id 相同 → 合并为一个条目
def test_suspect_same_title_diff_year(): assert rep["suspects"][0]["reason"] == "same-title-diff-year"
def test_merge_deterministic(): assert merge(recs, roots) == merge(list(reversed(recs)), roots)
```
- [ ] **Step 2–4: 先确认测试失败，再实现，最后确认通过。**
- [ ] **Step 5: 提交** `feat(sync): 跨来源合并去重`

### Task 5: 缩略图与原图暂存

**Files:**
- Create: `tools/sync/assets.py`
- Test: `tools/sync/tests/test_assets.py`

**Interfaces:**
- Produces:
  - `make_thumb(src: Path, dst: Path, max_px=800, quality=80) -> tuple[int, int]`：处理 EXIF 方向；CMYK、P、LA、RGBA 模式统一铺到白底后转为 RGB；最长边缩放到 max_px，不放大；保存为 webp。图片损坏时抛出 `BadImage`。
  - `sync_assets(items, roots, thumbs_dir, originals_dir, manifest_path) -> dict`：对每个条目计算原图的 sha256。sha 与 manifest 一致且缩略图存在时跳过；否则生成缩略图，并把原图复制为 `originals_dir/<id>.<ext>`（ext 取小写，jpeg 统一写成 jpg）。manifest 的条目格式为 `{sha256, ext, w, h, uploaded: bool}`；sha 发生变化时，把 uploaded 重置为 false。返回 `{"thumbs_new": n, "skipped": n, "bad": [ids]}`。
  - 坏图对应的条目从 raw-gallery 中剔除：由 run.py 根据 bad 列表过滤。

- [ ] **Step 1: 写失败测试**
```python
def test_thumb_size_and_format(tmp_path): # 输入 2000×1000 → 输出 webp，尺寸为 800×400
def test_thumb_no_upscale(tmp_path): # 输入 300×200 → 输出仍为 300×200
def test_thumb_handles_modes_and_corrupt(tmp_path): # CMYK jpg、RGBA png、P 模式 png 都能生成白底缩略图；截断的 jpg → 抛出 BadImage
def test_sync_assets_idempotent(tmp_path): # 运行两次，第二次 thumbs_new == 0，manifest 的字节内容不变
def test_sync_assets_resets_uploaded_on_change(tmp_path): # 修改原图后 uploaded 变回 False
```
- [ ] **Step 2–4: 先确认测试失败，再实现，最后确认通过。**
- [ ] **Step 5: 提交** `feat(sync): 缩略图与原图暂存`

### Task 6: 原图上传到 Hugging Face

**Files:**
- Create: `tools/sync/push_assets.py`、`tools/sync/hf_readme.md`（数据集卡片：来源、署名、版权归原作者、下架联系方式）
- Test: `tools/sync/tests/test_push.py`

**Interfaces:**
- Produces:
  - `REPO_ID = "OliverThompson/figtx-assets"`
  - `original_url(id: str, ext: str) -> str`
  - `push(originals_dir, manifest_path, api=None, dry_run=False) -> dict`：
    - api 默认是 `HfApi()`，认证用环境变量 `HF_TOKEN` 或本机 `hf auth login` 的凭据。
    - 先调用 `create_repo(REPO_ID, repo_type="dataset", exist_ok=True, private=False)`。
    - 只上传 manifest 中 `uploaded=false` 的文件：调用一次 `upload_folder(repo_id, repo_type="dataset", folder_path=originals_dir, path_in_repo="originals", allow_patterns=[...这些文件...], commit_message=...)`，同时上传 README.md（即数据集卡片）。
    - 成功后把这些条目标记为 `uploaded=true`。
    - 没有需要上传的文件时，不调用 api。
    - 返回 `{"uploaded": n}`。
  - 没有凭据时，打印「跳过上传：未登录 HF」，返回 `{"uploaded": 0, "skipped": "no-auth"}`，不抛异常。

- [ ] **Step 1: 写失败测试**（用一个记录调用参数的假 api 对象）
```python
def test_push_only_pending(tmp_path): r = push(d, m, api=fake); assert r["uploaded"] == 2 and fake.calls[-1]["allow_patterns"] == ["a.jpg", "b.png"]
def test_push_noop_when_nothing_pending(tmp_path): assert push(d, m_all_uploaded, api=fake) == {"uploaded": 0} and fake.calls == []
def test_push_marks_uploaded(tmp_path): # push 之后，manifest 中所有条目都是 uploaded=true
def test_original_url(): assert original_url("tc-x", "jpg") == "https://huggingface.co/datasets/OliverThompson/figtx-assets/resolve/main/originals/tc-x.jpg"
def test_push_no_auth(tmp_path): # 假 api 的 create_repo 抛出 LocalTokenNotFoundError → 返回 skipped no-auth
```
- [ ] **Step 2–4: 先确认测试失败，再实现，最后确认通过。**
- [ ] **Step 5: 提交** `feat(sync): 原图增量上传 Hugging Face`

### Task 7: 领域 / 研究问题打标

**Files:**
- Create: `tools/sync/tag.py`
- Test: `tools/sync/tests/test_tag.py`

**Interfaces:**
- Consumes: `data/taxonomy.json`；`tools/figgen/llm_client.chat`，被注入为 `chat_fn`
- Produces:
  - `tag(items, tags_path, chat_fn=None, batch=40) -> dict`：
    1. 跳过已经在 tags.json 中的 id（包括 manual 的条目）。
    2. 剩余条目每 40 条打包发送一次，prompt 中只包含 id、标题、会议、年份和 figType，**不发送摘要**。
    3. 要求模型返回 JSON：`{"<id>": {"domains": ["cv", ...（1–3 个 taxonomy key）], "problems": ["novel view synthesis", ...（1–3 个英文短语，小写）]}}`。
    4. 校验返回结果：丢弃不在 taxonomy 里的 key，problems 截断到 60 字符。
    5. 写入 `{"domains", "problems", "model"}`。
    6. 某一批解析失败时记入 `failed` 并继续处理下一批。
    7. `chat_fn` 为 None 且 `FIGTX_LLM_KEY` 未设置时，打印提示并返回 `{"tagged": 0, "skipped": "no-key"}`。
  - 返回 `{"tagged": n, "failed": n}`

- [ ] **Step 1: 写失败测试**（用假的 chat_fn）
```python
def test_tag_writes_valid_domains(tmp_path): # 假模型返回 {"a": {"domains": ["cv", "bogus"], "problems": ["X"]}} → tags["a"]["domains"] == ["cv"]，problems == ["x"]
def test_tag_skips_cached_and_manual(tmp_path): # 已经存在 manual 条目 → chat_fn 收到的 prompt 中不包含该 id
def test_tag_batches(tmp_path): # 85 个条目 → chat_fn 被调用 3 次
def test_tag_bad_json_counts_failed(tmp_path): # 假模型返回非 JSON → failed == 40，且不抛异常
def test_tag_no_key(tmp_path, monkeypatch): # 删除 FIGTX_LLM_KEY 环境变量 → 返回 skipped no-key
```
- [ ] **Step 2–4: 先确认测试失败，再实现，最后确认通过。**
- [ ] **Step 5: 提交** `feat(sync): 领域与研究问题打标（带缓存）`

### Task 8: 并入前端数据与编号

**Files:**
- Modify: `tools/build-data.mjs`（读取 `data/raw-gallery.json`、`data/tags.json`、`data/sources/assets-manifest.json`，生成 gallery 条目）
- Modify: `tools/assign_numbers.py`（新增 `--keep-missing` 参数；gallery 条目排在现有图之后，按 `(year desc, id)` 排序）
- Modify: `src/labels.ts`、`src/App.tsx`（`FIGTYPE_LABEL` 补全新的 figType；`Modal` 在条目带有 `paper` 字段时显示论文信息块，并隐藏没有代码时的复制和下载按钮）
- Test: 用 Node 运行一个校验脚本 `tools/sync/tests/check_build.py`，作为 pytest 测试，内部用 subprocess 调用 `node tools/build-data.mjs`

**Interfaces:**
- gallery 条目在 items.json 中的形态：在现有 figure 条目的字段之外，增加：
  - `paper`、`sources`
  - `domains`、`problems`：没有打标时为 `[]`
  - `render: "thumbs/<id>.webp"`
  - `original`：manifest 中 uploaded 为 true 时取 `original_url`，否则为 null
  - `editableStatus: "original-only"`
  - `code: ""`、`codeLang: null`、`noteImages: []`
  - `venues: [paper.venue]`、`year`
  
  `index.json` 自动包含这些新条目，domains 和 problems 字段也会带上。
- `stats` 增加 `gallery`（gallery 条目总数）和 `sources: {topconf, papergallery}`。
- `assign_numbers.py --keep-missing`：不删除 catalog 中当前不存在的 id。`run.py` 始终带这个参数。

- [ ] **Step 1: 写失败测试**
```python
def test_build_includes_gallery(tmp_repo): # 准备 2 条 gallery 条目和对应的缩略图 → 运行 build-data → items.json 中有这 2 条，render 指向 thumbs/，domains 来自 tags.json
def test_index_has_domains(tmp_repo): # index.json 中对应条目的 domains 等于 tags 里的值
def test_numbers_keep_existing_and_extend(tmp_repo): # catalog 中已有 F035 → 新条目从 F036 开始；带 --keep-missing 时，被移除的 id 仍保留在 catalog 中
```
- [ ] **Step 2–4: 先确认测试失败，再实现，最后确认通过。**额外运行 `npx tsc --noEmit` 和 `npm run build`，都要通过。
- [ ] **Step 5: 提交** `feat(gallery): 图库条目并入前端数据与编号`

### Task 9: 总入口、每周同步、图片政策

**Files:**
- Create: `tools/sync/run.py`、`tools/sync/sync_journal.py`、`data/journals.json`（初始为 `[]`）、`.github/workflows/sync.yml`、`IMAGES_POLICY.md`
- Modify: `package.json`（新增 `"sync": "uv run --with pillow --with numpy --with pyyaml --with huggingface_hub python -m tools.sync.run"`）、`.gitignore`（新增 `.cache/`）
- Test: `tools/sync/tests/test_run.py`

**Interfaces:**
- `run(sources=("topconf", "papergallery", "journal"), local: dict | None = None, no_tag=False, no_push=False, root=REPO) -> dict`，依次执行：
  1. 每个来源先 fetch 再 parse，写入 `data/sources/<src>.json`。fetch 失败时保留旧文件，并记入 `report["errors"]`。
  2. 读取所有来源文件，执行 merge，写入 `data/raw-gallery.json`。
  3. 执行 sync_assets，并剔除坏图。
  4. 执行 tag，除非 `no_tag`。
  5. 执行 push，除非 `no_push`。
  6. 运行 `python3 tools/assign_numbers.py --keep-missing`。注意它依赖 items.json，所以先跑一次 `node tools/build-data.mjs`，再跑编号，最后再跑一次 build-data。
  7. 打印报告：各来源的条目数、新增、合并、疑似重复、坏图、打标、上传、错误；同时写入 `.cache/sync-report.json`。
- CLI 参数：`--local-topconf PATH`、`--local-papergallery PATH`、`--no-tag`、`--no-push`、`--only topconf|papergallery`
- `sync.yml`：
  - 触发条件：`schedule: cron "17 3 * * 1"` 加上 `workflow_dispatch`。
  - 依次执行 setup-node、npm ci、setup-uv，然后运行 `npm run sync -- --no-tag`。打标需要的内网模型在 Actions 里访问不到；新条目先不打标，由维护者在本地补打。
  - 存在 `HF_TOKEN` secret 时上传原图，否则加 `--no-push`。
  - 最后用 `peter-evans/create-pull-request@v7` 开 PR，分支名为 `sync/weekly`，标题为「chore(sync): 每周同步上游图库」，正文附上报告。
  - permissions：`contents: write`、`pull-requests: write`。
- `sync_journal.py`（spec §5.2，本期只定义格式）：
  - `data/journals.json` 是手工维护的清单，每项为 `{"doi", "figure": "Fig. 1", "venue": "Nature" | "Science" | "Cell" | "NMI" | ..., "year", "title", "authors", "image": "本地路径或图片 URL"}`。
  - `parse(path) -> list[dict]`：把清单转换成来源记录，`source` 为 `"journal"`，`kind` 为 `"framework"`，`paper` 为 `https://doi.org/<doi>`；缺少 doi 或 image 的项计入报告后跳过。
  - run 默认的来源列表加入 journal；清单为空时，生成 0 条记录。
- `IMAGES_POLICY.md`：
  - 说明图片来源：顶会论文、topconf 和 PaperGallery 收集的图。
  - 署名方式：每张图都带论文信息和来源项目。
  - 版权归原作者，本仓库为非商业、教育用途。
  - 下架方式：提 issue，或联系仓库维护者，收到后 72 小时内处理。
  - 不在文件里写任何个人邮箱，只写 GitHub issue 地址。

- [ ] **Step 1: 写失败测试**（用 Task 2、Task 3 的 fixture 作为两个 local 上游，tag 和 push 都换成假实现）
```python
def test_run_end_to_end_fixture(tmp_repo): rep = run(local=..., no_tag=True, no_push=True, root=tmp_repo); assert rep["items"] == N and (tmp_repo/"public/thumbs").glob("*.webp")
def test_run_is_idempotent(tmp_repo): # 运行两次，两次之间所有被跟踪文件的哈希都相同
def test_journal_empty_and_one(tmp_path): # 空清单 → []；一条合法项 → 一条 source=journal 的记录，paper 以 https://doi.org/ 开头；缺少 doi 的项 → 被跳过并计数
def test_run_keeps_previous_source_on_fetch_failure(tmp_repo): # 第二次运行时 topconf 的 fetch 抛错 → data/sources/topconf.json 不变，report["errors"] 中包含 topconf，gallery 条目数不变
```
- [ ] **Step 2–4: 先确认测试失败，再实现，最后确认通过。**
- [ ] **Step 5: 提交** `feat(sync): npm run sync 总入口、每周同步 Action、图片政策`

### Task 10: 真实同步、上线

- [ ] **Step 1: 真实同步。** 运行 `npm run sync -- --local-topconf /Users/zhipingwu/CodeHome/topconf-paper-figure-gallery`。PaperGallery 走线上 clone，可能需要几分钟，放到后台运行。完成后核对报告：
  - topconf 约 3449 条，PaperGallery 约 324 条。
  - 打印合并数和疑似重复数。抽查 5 个疑似重复，并打开对应的缩略图看一眼。
  - 坏图数为 0，或者都列明了原因。
  - 打标覆盖率 ≥ 95%。如果 `.env` 中没有 key，就记下来，留给用户处理。
  - HF 上传数等于条目数。
- [ ] **Step 2: 抽查 HF。** 用 `curl -sI` 请求 3 个 `original_url`，期望返回 200 或 302。
- [ ] **Step 3: 本地预览。** 运行 `npm run build` 和 `npm run preview`。在浏览器中检查：图的总数约 3800+；按会议筛选可用；打开一张 topconf 图的详情，能看到论文标题、作者和链接；`#F036` 能直达对应条目。
- [ ] **Step 4: 再运行一次 `npm run sync -- --no-tag --no-push`，确认 `git status` 只剩用户原有的修改（幂等性）。**
- [ ] **Step 5: 提交数据并推送。** 提交 `data/` 与 `public/thumbs/`。推送 `feat/gallery-sync`，开 PR（如果 gh 无法使用，就给出浏览器链接）。CI 通过后，由用户确认是否合并。
