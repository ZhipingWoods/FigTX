# FigTX Skills（P4）+ figtx-forge 工具包 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提供 5 个可以在 Claude Code / Codex 中直接加载的 FigTX skill，以及它们共用的命令行工具包 `figtx-forge`（命令名 `figtx`）。工具包负责：渲染、一比一比对、抠图、导出 SVG/PPTX、编译 LaTeX 表格、运行绘图脚本、检索 FigTX 索引。

**Architecture:** agent 负责「看」和「写」：识别原图，写出场景 JSON、LaTeX 或 matplotlib 脚本。`figtx` 命令负责所有可以确定性完成、可以测试的工作：渲染、打分、导出。场景 JSON 是唯一真源，SVG 和 PPTX 都从它生成。这个包放在 `packages/figtx-forge/`，skills 以包数据的形式随包分发。P3 的本地服务（`figtx serve`）以后也放进同一个包，复用这里的模块。

**Tech Stack:** Python ≥3.10，依赖 pillow、numpy、resvg-py（不需要浏览器即可渲染 SVG）、python-pptx、pypdfium2，测试用 pytest，构建和安装用 uv / hatchling；LaTeX 编译依赖外部的 tectonic；FigTX 侧涉及 Node（`tools/build-data.mjs`）。

**Spec:** `docs/superpowers/specs/2026-11-27-figtx-gallery-integration-design.md`（主要对应 §5.7、§5.8、§5.9 中质量指标的部分、§7）

**与 spec 的一处偏差（我的判断）：** spec §5.8 写的是在仓库根目录建 `skills/`。本计划把 skills 放到 `packages/figtx-forge/src/figtx_forge/skills/`，这样不 clone 仓库、只用 `uv tool install git+...#subdirectory=...` 安装的用户也能拿到 skills（构建 subdirectory 时，无法引用子目录之外的文件）。

## Global Constraints

- 单个文件不超过 500 行（来自 CLAUDE.md）。
- 不提交密钥。`figtx` 本身不调用任何模型 API，也不读取任何 key。
- 一比一复刻的判定门槛（spec §5.7，原样照抄）：综合分数和深色笔画召回率 ≥ 0.98；局部召回率和边缘 F1 ≥ 0.97；颜色相似度 ≥ 0.98；文字内容完全一致；位图对象面积占比默认低于 40%。原图以照片为主时可以放宽，但必须在结果中注明。
- 禁止用整页位图冒充可编辑结果（spec 反目标）。
- 场景 JSON 是唯一真源。PPTX、SVG 都由它导出（spec §5.9）。
- skill 的 frontmatter `name` 必须和目录名一致，统一以 `figtx-` 开头。
- paper-plot-skills 只引用，不复制它的任何脚本（spec §7）。
- 用户在 FigTX 现有工作区里有一处未提交的修改 `tools/figgen/prompts.py`，执行本计划时不要碰它。
- 所有工作在分支 `feat/skills` 上进行，最后提交 PR 到 `ZhipingWoods/FigTX`。
- 测试命令统一为：`uv run --project packages/figtx-forge pytest packages/figtx-forge/tests -q`（下文记作 `$PYTEST`）。

## Review Focus

1. **原图和渲染图尺寸不一致**（比如 agent 把画布写成 1600×900，而原图是 1092×599）：比对前必须先缩放到原图尺寸再打分，不能直接崩溃，也不能给出虚高的分数。→ Task 3 `test_compare_resizes_render`
2. **场景里的图片节点引用的裁片文件不存在，或路径逃出了场景目录**（例如 `../../etc/x.png`）：校验时要报出明确错误，不能静默生成一张空图，也不能读取场景目录以外的文件。→ Task 1 `test_validate_image_href_outside_dir`
3. **文字里含有 `&`、`<`、引号、中文或 emoji**：导出的 SVG 必须仍然是合法 XML，PPTX 里的文字必须原样保留。→ Task 2 `test_svg_escapes_text`，Task 5 `test_pptx_keeps_special_text`
4. **几乎全白、深色像素很少的原图**（比如浅色线稿）：各项召回率不能除以零；没有墨迹的区块不参与「局部召回率」的计算。→ Task 3 `test_compare_blank_original`
5. **tectonic 没有安装**：`figtx tex` 要给出安装提示，并以退出码 2 结束，不能抛出 Python 堆栈。→ Task 6 `test_tex_missing_tectonic`

---

## File Structure

```
packages/figtx-forge/
  pyproject.toml                       包定义，console script: figtx = figtx_forge.cli:main
  src/figtx_forge/__init__.py          __version__ = "0.1.0"
  src/figtx_forge/cli.py               argparse 子命令分发（只做参数解析和调用）
  src/figtx_forge/scene.py             场景 JSON 的加载和校验
  src/figtx_forge/geometry.py          SVG path d 解析与采样、bbox 计算
  src/figtx_forge/svg_export.py        场景 → SVG 字符串
  src/figtx_forge/render.py            SVG → PIL.Image（resvg-py）
  src/figtx_forge/metrics.py           原图与渲染图比对、热力图
  src/figtx_forge/redraw.py            抠图、lint、redraw-check 流程
  src/figtx_forge/pptx_export.py       场景 → 原生 PPTX 形状
  src/figtx_forge/tex.py               LaTeX 表格编译与表格结构统计
  src/figtx_forge/plot.py              运行 matplotlib 脚本并收集输出
  src/figtx_forge/search.py            加载 FigTX index.json 并检索
  src/figtx_forge/skills_install.py    把随包分发的 skills 安装到 ~/.claude/skills 和 ~/.codex/skills
  src/figtx_forge/skills/figtx-*/SKILL.md (+ references/*.md)
  tests/test_*.py, tests/fixtures/
scripts/install-skills.sh              从 clone 下来的仓库安装（uv tool install --editable + figtx skills install --link）
tools/build-data.mjs                   修改：额外输出 public/index.json
package.json                           修改：新增 "skills:install" 脚本；license 字段改为 Apache-2.0
.gitignore                             修改：忽略 public/index.json
README.md                              修改：新增「在 Claude Code / Codex 里用 FigTX」一节
```

## 场景 JSON（Task 1 定义，后续任务共用）

```json
{
  "version": 1,
  "canvas": {"width": 1092, "height": 599, "background": "#FFFFFF"},
  "source": {"image": "original.png", "figtxId": "F123"},
  "nodes": [
    {"id": "n1", "type": "rect", "x": 10, "y": 10, "w": 200, "h": 80, "rx": 8,
     "fill": "#77AADA", "stroke": "#222222", "strokeWidth": 1.5, "dash": [4, 2], "opacity": 1},
    {"id": "n2", "type": "ellipse", "cx": 300, "cy": 50, "rx": 40, "ry": 30, "fill": "#FFF"},
    {"id": "n3", "type": "line", "x1": 210, "y1": 50, "x2": 260, "y2": 50,
     "stroke": "#333", "strokeWidth": 2, "arrowEnd": true, "arrowStart": false},
    {"id": "n4", "type": "polyline", "points": [[0,0],[10,0],[10,10]], "closed": true, "fill": "#EEE"},
    {"id": "n5", "type": "path", "d": "M 10 10 C 40 0 60 0 90 10", "stroke": "#333", "fill": "none"},
    {"id": "n6", "type": "text", "x": 20, "y": 30, "w": 180, "h": 24, "text": "Encoder",
     "fontSize": 18, "fontWeight": "bold", "fontStyle": "normal", "fontFamily": "Arial",
     "fill": "#111", "align": "center", "valign": "middle"},
    {"id": "n7", "type": "image", "x": 400, "y": 20, "w": 160, "h": 120, "href": "crops/photo1.png"}
  ]
}
```

坐标单位是原图像素。`text` 的 `x, y, w, h` 指文字框，不是基线。`image.href` 必须是场景文件所在目录下的相对路径。颜色接受 `#RGB` 或 `#RRGGBB`，以及 `"none"`。

---

### Task 1: 包骨架与场景校验

**Files:**
- Create: `packages/figtx-forge/pyproject.toml`、`src/figtx_forge/__init__.py`、`src/figtx_forge/cli.py`、`src/figtx_forge/scene.py`
- Test: `packages/figtx-forge/tests/test_scene.py`、`tests/test_cli.py`

**Interfaces:**
- Produces: `load_scene(path: str | Path) -> dict`（读取 JSON，把 `base_dir` 记到 `scene["_base_dir"]` 中）；`validate_scene(scene: dict) -> list[str]`（返回错误列表，空列表表示合法）；`NODE_TYPES = {"rect","ellipse","line","polyline","path","text","image"}`；`cli.main(argv: list[str] | None = None) -> int`；`cli.SUBCOMMANDS: dict[str, Callable]`，用于注册子命令，后续任务往里面加。

- [ ] **Step 1: 写失败测试**

```python
def test_validate_ok(tmp_path): # 用上文示例场景（去掉 n7）写入 tmp_path/scene.json
    assert validate_scene(load_scene(p)) == []
def test_validate_unknown_type(): assert any("unknown type" in e for e in validate_scene({"version":1,"canvas":{"width":10,"height":10},"nodes":[{"id":"a","type":"star"}]}))
def test_validate_missing_canvas(): assert any("canvas" in e for e in validate_scene({"version":1,"nodes":[]}))
def test_validate_duplicate_id(): ...  # 两个 id="a" → 错误里包含 "duplicate id a"
def test_validate_image_href_outside_dir(tmp_path): # href="../../etc/x.png" → 错误包含 "outside scene dir"；href="crops/missing.png" → 错误包含 "not found"
def test_cli_version(capsys): assert main(["--version"]) == 0 and "0.1.0" in capsys.readouterr().out
```

- [ ] **Step 2: 运行 `$PYTEST tests/test_scene.py tests/test_cli.py`，确认失败（ModuleNotFoundError）。**
- [ ] **Step 3: 实现。** pyproject 使用 hatchling，`requires-python=">=3.10"`，dependencies：`pillow>=10`、`numpy>=1.24`、`resvg-py>=0.5`、`python-pptx>=1.0`、`pypdfium2>=4`；dev 组加 `pytest>=8`；`[tool.hatch.build.targets.wheel] packages=["src/figtx_forge"]`，并且要把 `skills/**` 打进包里。`validate_scene` 需要检查：`canvas.width/height` 为正数；每个节点有 `id`，且 id 不重复；类型合法；每种类型的必填字段齐全；颜色格式正确；`image.href` 解析后仍在 `_base_dir` 之内，并且文件存在。
- [ ] **Step 4: 运行 `$PYTEST`，确认通过。**
- [ ] **Step 5: 提交** `git checkout -b feat/skills && git add packages/figtx-forge && git commit -m "feat(forge): figtx-forge 包骨架与场景 JSON 校验"`

### Task 2: 场景导出为 SVG，再渲染成图片

**Files:**
- Create: `src/figtx_forge/geometry.py`、`svg_export.py`、`render.py`
- Test: `tests/test_svg_render.py`

**Interfaces:**
- Consumes: `load_scene`、`validate_scene`
- Produces: `path_to_polylines(d: str, samples: int = 16) -> list[list[tuple[float, float]]]`（支持 M/L/H/V/C/S/Q/T/Z 命令，大小写都要处理；A 命令按直线近似）；`node_bbox(node: dict) -> tuple[x, y, w, h]`；`scene_to_svg(scene: dict, embed_images: bool = True) -> str`；`render_svg(svg: str, width: int, height: int) -> PIL.Image.Image`（RGB，白色背景）；`render_scene(scene) -> PIL.Image.Image`；CLI 子命令 `figtx render scene.json -o out.png`。

- [ ] **Step 1: 写失败测试**

```python
def test_rect_fill_rendered(): img = render_scene(scene_with_rect(fill="#FF0000")); assert img.getpixel((50,30)) == (255,0,0)
def test_svg_has_viewbox(): assert 'viewBox="0 0 1092 599"' in scene_to_svg(s)
def test_svg_escapes_text(): s = scene_with_text('A & B <x> "q" 中文 🚀'); ET.fromstring(scene_to_svg(s))  # 不抛异常；解析后 <text> 内容与原文相同
def test_text_rendered_dark_pixels(): # 黑色 text 节点所在框内，深色像素（<128）数量 > 50
def test_arrow_end_has_marker(): assert "marker-end" in scene_to_svg(scene_with_line(arrowEnd=True))
def test_path_curve_samples(): pts = path_to_polylines("M 0 0 C 0 10 10 10 10 0")[0]; assert len(pts) == 17 and pts[-1] == (10.0, 0.0)
def test_image_embedded_base64(tmp_path): # 场景引用了一张 10x10 的 crops/a.png → svg 中包含 "data:image/png;base64,"
```

- [ ] **Step 2: 运行，确认失败。**
- [ ] **Step 3: 实现。** 文字的对齐方式：`align` 映射到 `text-anchor`（left→start，center→middle，right→end），`valign` 用 `dominant-baseline`（top→hanging，middle→central，bottom→text-after-edge）计算 y。`dash` 映射为 `stroke-dasharray`。箭头在 `<defs>` 里定义一个共享的 marker，颜色取线条颜色，按颜色分别生成 marker。`render_svg` 调用 `resvg_py.svg_to_bytes(svg_string=svg, width=w, height=h, background="#ffffff")`。
- [ ] **Step 4: 运行，确认通过。**
- [ ] **Step 5: 提交** `feat(forge): 场景导出 SVG 与 resvg 渲染`

### Task 3: 一比一比对指标

**Files:**
- Create: `src/figtx_forge/metrics.py`
- Test: `tests/test_metrics.py`

**Interfaces:**
- Produces: `THRESHOLDS = {"composite":0.98,"dark_recall":0.98,"local_recall":0.97,"edge_f1":0.97,"color_similarity":0.98}`；`compare(original: Image, rendered: Image) -> dict`，返回的字段包括上述 5 项、`dark_precision`、`passed: bool`、`failed: list[str]`、`worst_tiles: list[{"x","y","w","h","recall"}]`（最差的 5 块）；`diff_heatmap(original, rendered) -> Image`；CLI `figtx compare orig.png render.png [--json out.json] [--heatmap out.png]`，通过时退出码 0，否则 1。

算法如下（先固定下来，以后再标定）：
1. 把 rendered 用 LANCZOS 缩放到 original 的尺寸，两张都转为 RGB，透明部分铺白底。
2. 深色掩码：亮度 `0.299R+0.587G+0.114B < 160`。容差：用 `MaxFilter(5)` 对掩码做膨胀，相当于半径 2px。
3. `dark_recall = |O ∩ dilate(R)| / |O|`，`dark_precision = |R ∩ dilate(O)| / |R|`。分母为 0 时，该项记为 1.0。
4. 边缘：对灰度图做 Sobel，幅值 > 40 视为边缘。在 2px 容差下分别算精确率和召回率，再算 F1。
5. 局部召回：把图切成 8×8 网格。只统计深色像素数量 ≥ 0.2% 区块面积的区块，计算每块的 dark_recall，取最小值。没有任何合格区块时，记为 1.0。
6. 颜色：在原图非近白像素上（任一通道 < 235）比较。两张图先做 `GaussianBlur(2)`，再从 sRGB 转换到 Lab（用 numpy 实现公式，D65 白点），计算 ΔE76 的均值。`color_similarity = clip(1 - meanΔE/100, 0, 1)`。
7. `composite = mean(dark_recall, dark_precision, edge_f1, color_similarity)`。
8. 热力图：在原图的 35% 灰度版本上，把漏画的像素（O 有、R 没有）标红，把多画的像素（R 有、O 没有）标蓝。

- [ ] **Step 1: 写失败测试**

```python
def test_identical_passes(): m = compare(img, img.copy()); assert m["passed"] and min(m[k] for k in THRESHOLDS) >= 0.999
def test_shift_fails(): m = compare(img, ImageChops.offset(img, 8, 0)); assert not m["passed"] and "dark_recall" in m["failed"]
def test_color_change_fails(): # 把同一个场景的矩形填充色从 #77AADA 换成 #DA7777 → "color_similarity" in m["failed"]
def test_missing_label_hits_local(): # 去掉一个小的 text 节点 → m["local_recall"] < 0.97，同时 m["dark_recall"] > 0.95
def test_compare_resizes_render(): # 渲染图是原图的 2 倍尺寸、内容相同 → passed
def test_compare_blank_original(): # 原图全白，渲染图全白 → 所有指标都是 1.0，不出现 ZeroDivisionError
def test_heatmap_marks_missing_red(): # 漏画区域内的像素满足 R>200、G<80
```

测试用图由 Task 2 的 `render_scene` 根据一个固定的 fixture 场景生成：`tests/fixtures/pipeline_scene.json`。场景画布为 1092×599，包含 3 个框（填充色 #77AADA、#F2C14E、#9BD08B）、2 支带箭头的线，以及 4 个标签："Input"、"Encoder"、"Decoder"、"Output"。之后的任务都复用这个场景。

- [ ] **Step 2: 运行，确认失败。**
- [ ] **Step 3: 按上面的算法实现。**
- [ ] **Step 4: 运行，确认通过。**如果 `test_identical_passes` 或 `test_shift_fails` 中有一个无法通过，只允许调整第 2 步的亮度阈值或 Sobel 阈值，`THRESHOLDS` 不能改。
- [ ] **Step 5: 提交** `feat(forge): 一比一比对指标与差异热力图`

### Task 4: 抠图、lint 与 redraw-check

**Files:**
- Create: `src/figtx_forge/redraw.py`
- Test: `tests/test_redraw.py`

**Interfaces:**
- Consumes: `load_scene`、`validate_scene`、`render_scene`、`scene_to_svg`、`compare`、`diff_heatmap`、`node_bbox`
- Produces:
  - `crop_regions(image_path, regions: list[dict], out_dir) -> list[str]`：regions 的每一项是 `{"id","x","y","w","h"}`，输出文件为 `out_dir/<id>.png`，裁剪框越界时截到图像范围内。
  - `bitmap_area_ratio(scene) -> float`：所有 image 节点面积之和除以画布面积，结果最大为 1。
  - `lint_scene(scene, english_only: bool = False) -> list[dict]`：每项是 `{"id","rule","msg"}`。规则包括：
    - `text-overflow`：估算宽度 `len(text) * fontSize * 0.55` 大于 `w * 1.05`；中日韩字符按 1.0 倍字宽计算。
    - `text-overlap`：两个文字框的交集面积超过较小框面积的 15%。
    - `out-of-canvas`：任何节点的 bbox 超出画布 2px 以上。
    - `cjk`：仅在 `english_only=True` 时检查，文字中含有中日韩字符。
  - `redraw_check(original_path, scene_path, out_dir, texts_path: str | None = None, allow_photo_heavy: bool = False) -> dict`：依次生成 `out_dir/render.png`、`heatmap.png`、`scene.svg`、`report.json`。报告内容是 compare 的结果，加上 `bitmap_ratio`、`bitmap_limit`（0.40；`allow_photo_heavy=True` 时为 0.85，并加上 `"note":"photo-heavy"`）、`missing_texts`、`lint`。`passed` 的条件是：compare 通过、位图占比不超过上限、`missing_texts` 为空、`lint` 中没有 `text-overflow` 和 `out-of-canvas`。
  - 文字核对：`texts.txt` 中每一行，在空白归一化后，必须完全等于场景中某个 text 节点的文字。
  - CLI：`figtx crop`、`figtx lint`、`figtx redraw-check orig.png scene.json -o out/ [--texts texts.txt] [--allow-photo-heavy]`，通过时退出码 0，否则 1。

- [ ] **Step 1: 写失败测试**

```python
def test_crop_clamps(tmp_path): # 区域 x=-5, w 超出原图 → 输出图尺寸被截到原图范围内
def test_bitmap_ratio_full_page_fails(tmp_path): # 场景里只有一个铺满画布的 image 节点 → report["passed"] is False, report["bitmap_ratio"] == 1.0
def test_photo_heavy_flag(tmp_path): # 位图占比为 0.6；不加 flag → 不通过；加上 allow_photo_heavy → bitmap_limit == 0.85，note 为 "photo-heavy"
def test_missing_text_reported(tmp_path): # texts.txt 中包含 "Classifier"，fixture 场景中没有这段文字 → report["missing_texts"] == ["Classifier"]
def test_lint_overflow(): assert lint_scene(scene_with_text("A very long label", w=40, fontSize=18))[0]["rule"] == "text-overflow"
def test_redraw_check_self_passes(tmp_path): # 用 fixture 场景渲染出原图 → 用同一个场景做 redraw-check → passed，且 out/ 下的 4 个文件都存在
```

- [ ] **Step 2: 运行，确认失败。**
- [ ] **Step 3: 实现。**
- [ ] **Step 4: 运行，确认通过。**
- [ ] **Step 5: 提交** `feat(forge): 抠图、场景 lint 与 redraw-check`

### Task 5: 导出原生 PPTX

**Files:**
- Create: `src/figtx_forge/pptx_export.py`
- Test: `tests/test_pptx.py`

**Interfaces:**
- Consumes: `load_scene`、`path_to_polylines`、`scene_to_svg`
- Produces: `scene_to_pptx(scene, out_path) -> None`；CLI `figtx export scene.json -o outdir [--svg] [--pptx]`。不指定格式时，两种都导出，文件名分别为 `outdir/<scene文件名>.svg` 和 `.pptx`。

映射规则：
- 尺寸：1px 对应 9525 EMU，幻灯片尺寸等于画布尺寸。
- rect：圆角半径 `rx > 0` 时用 `ROUNDED_RECTANGLE`，并把 adjustments[0] 设为 `rx / min(w, h)`；否则用 `RECTANGLE`。
- ellipse：用 `OVAL`。
- line：用直线 connector；`arrowEnd` / `arrowStart` 通过 lxml 写入 `a:tailEnd type="triangle"` / `a:headEnd`。
- polyline 和 path：采样后用 `build_freeform` 生成，闭合的路径要设置 `close`。
- text：文本框，内边距设为 0，关闭自动换行和自动适配。字号以 pt 为单位，等于 fontSize × 0.75。粗体、斜体、颜色、对齐方式都要映射。
- image：用 `add_picture`。
- 虚线：设置 `line.dash_style`（有 dash 时统一用 `MSO_LINE.DASH`）。
- opacity：通过 lxml 写入 `a:alpha`。

- [ ] **Step 1: 写失败测试**

```python
def test_pptx_shape_count(tmp_path): # fixture 场景（3 个框、2 支箭头、4 个标签）→ Presentation 中第一张幻灯片的 shapes 数量为 9
def test_pptx_text_preserved(tmp_path): assert {"Encoder","Decoder"} <= {s.text_frame.text for s in shapes if s.has_text_frame}
def test_pptx_keeps_special_text(tmp_path): # 'A & B <x> 中文' 原样保留
def test_pptx_slide_size(tmp_path): assert prs.slide_width == 1092*9525
def test_pptx_arrow_xml(tmp_path): # 对应箭头的 connector XML 中含有 'tailEnd'，且 type="triangle"
def test_pptx_picture_count(tmp_path): # 场景有 1 个 image 节点 → 恰好 1 个 MSO_SHAPE_TYPE.PICTURE
```

- [ ] **Step 2: 运行，确认失败。**
- [ ] **Step 3: 实现。**
- [ ] **Step 4: 运行，确认通过。**然后手动检查一次：把 `figtx export tests/fixtures/pipeline_scene.json -o /tmp/x` 导出的 pptx 用 Keynote 或 PowerPoint 打开（`open /tmp/x/pipeline_scene.pptx`），截图确认框、箭头、文字都在，并且每个都能单独选中。
- [ ] **Step 5: 提交** `feat(forge): 场景导出原生 PPTX 形状`

### Task 6: LaTeX 表格编译与绘图脚本运行

**Files:**
- Create: `src/figtx_forge/tex.py`、`src/figtx_forge/plot.py`
- Test: `tests/test_tex_plot.py`

**Interfaces:**
- Consumes: `compare`
- Produces:
  - `table_shape(tex: str) -> dict`：返回 `{"rows": int, "cols": int, "multicolumn": int, "multirow": int}`。只统计第一个 tabular / tabularx / tblr 环境：rows 是 `\\` 的个数（排除 `\hline` 单独占的行），cols 等于列格式串中 l/c/r/p/X/m/b 的个数。
  - `compile_table(tex_path, out_png, dpi=300) -> dict`：返回 `{"ok": bool, "log_tail": str, "png": str | None}`。输入如果已经有 `\documentclass`，原样编译；否则包装进 `standalone` 文档，preamble 加载 booktabs、multirow、makecell、array、tabularx、graphicx、amsmath、amssymb、pifont 和 `xcolor[table]`。编译命令为 `tectonic --outdir tmp file.tex`，用 pypdfium2 渲染第一页。
  - `run_plot(script_path, out_dir, timeout=120) -> dict`：在临时工作目录中，设置环境变量 `MPLBACKEND=Agg`，用当前 Python 运行脚本，收集新生成的 png/pdf/svg，复制到 out_dir。返回 `{"ok", "files", "stderr_tail"}`。
  - CLI：`figtx tex table.tex -o out.png [--compare shot.png]`，输出结构统计，并在提供截图时输出比对报告（仅供参考，不影响退出码）。编译失败时退出码为 1；找不到 tectonic 时打印 `brew install tectonic` 或 https://tectonic-typesetting.github.io 的安装提示，退出码为 2。`figtx plot-run script.py -o out/ [--compare shot.png]`。

- [ ] **Step 1: 写失败测试**

```python
def test_table_shape(): assert table_shape(r"\begin{tabular}{lcc}\toprule A&B&C\\ \midrule 1&2&3\\ \bottomrule\end{tabular}") == {"rows":2,"cols":3,"multicolumn":0,"multirow":0}
@pytest.mark.skipif(not shutil.which("tectonic"), reason="no tectonic")
def test_compile_booktabs(tmp_path): r = compile_table(p, tmp_path/"t.png"); assert r["ok"] and Image.open(r["png"]).width > 100
def test_tex_missing_tectonic(monkeypatch, capsys): monkeypatch.setattr(shutil, "which", lambda n: None); assert main(["tex", str(p), "-o", "x.png"]) == 2 and "tectonic" in capsys.readouterr().err
def test_run_plot_collects_png(tmp_path): # 脚本内容为 plt.plot([1,2]); plt.savefig("a.png") → r["files"] 中有 a.png
def test_run_plot_error(tmp_path): # 脚本 raise ValueError → r["ok"] is False，且 "ValueError" 出现在 stderr_tail 中
```

- [ ] **Step 2: 运行，确认失败（Python 依赖里没有 matplotlib 时，test_run_plot 需要用 `uv run --with matplotlib` 跑；在 pyproject 的 dev 依赖组里加上 `matplotlib>=3.7`）。**
- [ ] **Step 3: 实现。**
- [ ] **Step 4: 运行，确认通过。**
- [ ] **Step 5: 提交** `feat(forge): LaTeX 表格编译与绘图脚本运行`

### Task 7: FigTX 索引与 `figtx search`

**Files:**
- Modify: `tools/build-data.mjs`（在写完 items.json 之后，追加生成 index.json 的逻辑）、`.gitignore`
- Create: `src/figtx_forge/search.py`、`tests/fixtures/index.json`
- Test: `tests/test_search.py`

**Interfaces:**
- Produces:
  - `public/index.json`：`{"v": 1, "generatedAt": ISO 时间, "base": "https://zhipingwoods.github.io/FigTX/", "items": [{"id","no","category","figType","kind","title","caption","venues","year","domains","problems","tags","preview","paper"}]}`。其中 caption 截断到 200 字；domains 和 problems 在 P1 之前允许是空数组；preview 是相对 base 的路径；paper 取自 `source.repoUrl` 或论文链接，没有时为 null。
  - `load_index(src: str | None) -> dict`：src 可以是路径或 URL；为 None 时依次尝试环境变量 `FIGTX_INDEX`，再尝试 `base + "index.json"`。下载结果缓存到 `~/.cache/figtx/index.json`，缓存有效期 24 小时。
  - `search(index, query, category=None, fig_type=None, limit=20) -> list[dict]`：查询词按空白切分并转小写。打分规则：每个词在 title 中命中得 3 分，在 domains、problems、tags、venues 中命中得 2 分，在 caption 中命中得 1 分；查询词是编号形式（如 `F012`、`T042`）时直接精确匹配。只返回得分大于 0 的条目，同分按 year 降序排列。
  - CLI：`figtx search "query" [--category figure|table] [--type framework] [--limit 20] [--index PATH|URL] [--json]`。文本输出每行一条：`no  figType  venues year  title  <base+preview>`。

- [ ] **Step 1: 写失败测试**

```python
def test_search_title_beats_tag(): r = search(IDX, "diffusion"); assert r[0]["id"] == "title-hit"
def test_search_number_exact(): assert [x["no"] for x in search(IDX, "T042")] == ["T042"]
def test_search_filter_type(): assert all(x["figType"] == "framework" for x in search(IDX, "model", fig_type="framework"))
def test_search_no_hits(): assert search(IDX, "zzzz") == []
def test_load_index_path(tmp_path): assert load_index(str(fixture))["v"] == 1
```

- [ ] **Step 2: 运行，确认失败。**
- [ ] **Step 3: 实现 search.py，并修改 build-data.mjs。**
- [ ] **Step 4: 运行 `$PYTEST`，确认通过。**再运行 `node tools/build-data.mjs && python3 -c "import json;d=json.load(open('public/index.json'));assert d['v']==1 and len(d['items'])==223;print('ok')"`，期望输出 `ok`。条目数应等于 `src/data/items.json` 中 `stats.total` 的值，目前是 223。
- [ ] **Step 5: 提交** `feat(forge): FigTX 精简索引与 figtx search`

### Task 8: 五个 skill 与安装

**Files:**
- Create: `src/figtx_forge/skills/figtx-find-figure/SKILL.md`
- Create: `src/figtx_forge/skills/figtx-redraw-figure/SKILL.md` + `references/scene-schema.md` + `references/redraw-checklist.md`
- Create: `src/figtx_forge/skills/figtx-framework-figure/SKILL.md` + `references/design-contract.md`
- Create: `src/figtx_forge/skills/figtx-table-from-screenshot/SKILL.md`
- Create: `src/figtx_forge/skills/figtx-plot/SKILL.md`
- Create: `src/figtx_forge/skills_install.py`、`scripts/install-skills.sh`
- Modify: `package.json`（新增 `"skills:install": "bash scripts/install-skills.sh"`；`license` 改为 `"Apache-2.0"`）
- Test: `tests/test_skills.py`

**Interfaces:**
- Consumes: 前面所有任务注册的 CLI 子命令。
- Produces:
  - `figtx skills list`
  - `figtx skills install [--target claude|codex|both] [--link]`：默认 both。复制到 `~/.claude/skills/<name>` 和 `~/.codex/skills/<name>`；指定 `--link` 时改为建立符号链接，这样仓库更新后能立即生效。目标已存在时直接覆盖，并打印提示。
  - `install_skills(home: Path, target: str, link: bool) -> list[Path]`

各 skill 的内容要求（都用中文写，frontmatter 的 description 要中英文触发词兼有）：
- **figtx-find-figure**：根据领域和研究问题调用 `figtx search`，列出 5–10 个候选，附预览链接，请用户挑选；用户选中后，下载原图到工作目录，交给 redraw 或 framework skill 继续处理。
- **figtx-redraw-figure**：一比一复刻的完整流程：
  1. 把原图中全部文字逐行抄进 `texts.txt`。
  2. 确定需要抠出的位图区域，用 `figtx crop` 裁出来。
  3. 写场景 JSON，先写大结构，再写细节。
  4. 运行 `figtx redraw-check`，查看 `heatmap.png` 和 `worst_tiles`，修改场景。
  5. 最多迭代 8 轮。达标后运行 `figtx export`；不达标时，交付结果并明确写出「需检查」和未达标的指标。
  
  `references/` 中包含：场景格式说明（与上文一致）、门槛数值，以及反目标清单（整页位图、混入别的论文的内容、文字溢出）。
- **figtx-framework-figure**：根据「方法描述 + 参考图」画新的框架图：
  1. 先测出参考图的设计契约。字段列表照搬 `tools/figgen/contract.py` 中的 ANALYZE_USER 结构，翻译成要测量的项目。
  2. 再写场景 JSON。
  3. 运行 `figtx render` 和 `figtx lint --english-only`。
  4. 按 `tools/figgen/prompts.py` 中的评审标准自评（最重要的一条：不能出现参考论文的实体名称），最多 3 轮。
  5. 运行 `figtx export`。
- **figtx-table-from-screenshot**：识别表格 → 写 booktabs 风格的 LaTeX → `figtx tex --compare` → 核对 rows/cols 和截图是否一致，逐格核对数字 → 修正 → 交付 `.tex` 和预览图。
- **figtx-plot**：
  - 有数据、要套用风格时：先检查是否已安装 paper-plot-skills（`~/.claude/skills/plot-from-data` 等）。已安装就交给它处理；未安装就给出安装地址 https://github.com/Trae1ounG/paper-plot-skills，并说明可以从 FigTX 实验图库中挑选风格（`figtx search --type quantitative`），拿条目里的代码改数据。
  - 有截图、要复刻时：写 matplotlib 脚本，用 `figtx plot-run --compare` 迭代。
  - 不复制 paper-plot-skills 的任何代码。

- [ ] **Step 1: 写失败测试**

```python
def test_all_skills_have_frontmatter(): # 每个 skills/*/SKILL.md 的 frontmatter 中，name 等于目录名，description 长度在 50 到 1024 之间
def test_skill_commands_exist(): # 正则提取 SKILL.md 中所有 `figtx <sub>`，sub 都必须在 cli.SUBCOMMANDS 中
def test_install_copy(tmp_path): paths = install_skills(tmp_path, "both", link=False); assert (tmp_path/".claude/skills/figtx-redraw-figure/SKILL.md").exists() and (tmp_path/".codex/skills/figtx-plot/SKILL.md").exists()
def test_install_link(tmp_path): install_skills(tmp_path, "claude", link=True); assert (tmp_path/".claude/skills/figtx-plot").is_symlink()
def test_skills_in_wheel(tmp_path): # uv build --wheel 之后，wheel 的 namelist 中包含 figtx_forge/skills/figtx-redraw-figure/SKILL.md
```

- [ ] **Step 2: 运行，确认失败。**
- [ ] **Step 3: 写 skills_install.py 和 5 个 SKILL.md 及其 references。** 每个 SKILL.md 正文不超过 200 行。正文第一段写明前置条件：`figtx` 不在 PATH 上时，先运行 `uv tool install "git+https://github.com/ZhipingWoods/FigTX#subdirectory=packages/figtx-forge"`。`scripts/install-skills.sh` 依次执行 `uv tool install --editable packages/figtx-forge --force` 和 `figtx skills install --link`。
- [ ] **Step 4: 运行 `$PYTEST`，确认通过；再运行 `npm run skills:install && ls ~/.claude/skills | grep figtx-`，期望列出 5 个 skill。**
- [ ] **Step 5: 提交** `feat(skills): 五个 FigTX skill 与安装命令`

### Task 9: 用真实图走一遍流程、写文档、提交 PR

**Files:**
- Modify: `README.md`：在「它能做什么」之后新增「在 Claude Code / Codex 里用 FigTX」一节，包含安装命令、5 个 skill 各一句说明，以及一个示例对话。
- Create: 无（试跑产物放在 `figgen-out/skill-trial/`，这个目录已被 gitignore）

- [ ] **Step 1: 试跑 redraw。** 从 topconf 本地仓库挑一张 architecture 类的图：`/Users/zhipingwu/CodeHome/topconf-paper-figure-gallery/images/` 中 `pattern=architecture` 的第一张；挑一张不含照片、以框和线为主的。在当前会话中按 `figtx-redraw-figure` 的流程完整执行一遍，记下最终的 report.json 指标、迭代轮数，以及哪些指标没有达标。
- [ ] **Step 2: 试跑 table。** 取 `public/renders/` 中一张表格的渲染图当作截图，按 `figtx-table-from-screenshot` 的流程跑一遍，确认编译成功、rows/cols 一致。
- [ ] **Step 3: 根据试跑中发现的流程问题修改 SKILL.md。** 只改说明文字和顺序。如果发现指标的算法有问题，记进 PR 描述，留给 P3 去标定，不在本计划里改门槛。
- [ ] **Step 4: 写 README 的新章节。运行 `npm run build`，确认成功。运行 `$PYTEST`，确认全部通过。**
- [ ] **Step 5: 提交并开 PR。** `git push -u origin feat/skills`，然后用 `gh pr create`（需要先登录 gh；如果没有登录，改用 GitHub 网页链接，并告诉用户）。PR 描述中写明：试跑指标、未达标的项、门槛是否需要在 P3 标定。
