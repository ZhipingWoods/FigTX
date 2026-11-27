---
name: figtx-redraw-figure
description: |
  把一张论文图（框架图 / pipeline / teaser / 主图）一比一复刻成可编辑的 SVG 和 PPTX：位置、大小、线条、文字都与原图一致，照片类元素先抠出来再原位放回。
  Use when the user wants to "redraw this figure", "make this figure editable", "一比一复刻", "重画成可编辑版", "转成 PPT/SVG", or picks a figure from FigTX and asks for the editable file.
---

# 一比一复刻论文图（FigTX）

**前置条件**：需要 `figtx` 命令。不在 PATH 上时先装：
`uv tool install "git+https://github.com/ZhipingWoods/FigTX#subdirectory=packages/figtx-forge"`

**分工**：你负责「看」和「写」——读原图、写场景 JSON。`figtx` 负责所有可度量的事——渲染、和原图逐像素比对、导出。场景 JSON 是唯一真源，SVG/PPTX 都从它导出，**不要手写 SVG**。

**交付标准（硬门槛，`figtx redraw-check` 会逐项判定）**：
- composite ≥ 0.98，dark_recall ≥ 0.98，local_recall ≥ 0.97，edge_f1 ≥ 0.97，color_similarity ≥ 0.98
- 原图中的每一行文字都在场景里，内容完全一致（`--texts`）
- 位图对象面积 ≤ 40%（原图以照片为主时加 `--allow-photo-heavy`，上限 0.85，并在交付说明里写明）
- 不允许整页贴图冒充可编辑；不允许出现原图里没有的内容

## 工作目录

在当前项目下建 `figtx-redraw/<图名>/`，放：`original.png`（原图，PNG）、`texts.txt`、`regions.json`、`crops/`、`scene.json`、`out/`。

## 流程

1. **准备原图**。用户给的若是 jpg/webp，转成 PNG 存为 `original.png`，记下宽高（场景画布必须等于原图像素尺寸）。

2. **抄文字**。逐行把原图里所有可见文字抄进 `texts.txt`，一个文字框一行，大小写、标点、上下标（用 Unicode：xᵢ、x′、ℒ）都照原样。这是之后核对「文字完全一致」的依据。位于抠图区域内的文字（如图标上的 "GPU"）随位图保留，不写进 `texts.txt`。

3. **决定哪些元素抠图**。只有矢量画不出来的才抠：照片、渲染结果、热力图/特征图、复杂插画、3D 截图、Logo。框、线、箭头、文字、色块、简单图标、公式一律矢量重建。把要抠的区域写进 `regions.json`：
   `[{"id": "photo-1", "x": 412, "y": 36, "w": 180, "h": 120}, ...]`（原图像素坐标，宁可贴边紧一点），然后：
   `figtx crop original.png regions.json -o crops`

4. **写场景 JSON**（格式见 `references/scene-schema.md`）。顺序：
   - 先写底层大结构：面板背景、分组框、主要容器——量准 x/y/w/h、圆角、描边粗细和颜色。
   - 再写连线和箭头：起止点落在容器边上。
   - 再写文字：每个文字框一个 text 节点，x/y/w/h 框住原图中那段文字，字号按原图字高估（字号 ≈ 大写字母高度 × 1.4）。
   - 最后放 image 节点（href 指向 `crops/<id>.png`，位置大小与 regions.json 一致）。
   - 颜色用取色得到的精确 hex，不要凭感觉。

5. **校验**：
   `figtx redraw-check original.png scene.json -o out --texts texts.txt`
   读终端输出的各项分数、`worst tile`、`missing_texts`、lint 问题，然后**打开 `out/heatmap.png` 看**：红色 = 原图有但你漏画/画偏了；蓝色 = 你多画了。对照 `out/render.png` 和原图找差异。

6. **修正**，回到第 5 步。每轮优先修：缺失文字 → 红色大块（漏画的结构）→ 位置偏移（整体红蓝成对出现说明偏了几像素）→ 颜色 → 细节线条。按 `references/redraw-checklist.md` 逐项过。**最多 8 轮**。

7. **导出**：`figtx export scene.json -o out`，得到 `out/scene.svg` 和 `out/scene.pptx`。

8. **交付说明**（告诉用户）：
   - 最终各项分数、迭代轮数、位图占比；
   - 达标 → 说明「已一比一复刻，SVG/PPTX 可直接编辑」；
   - 未达标 → 必须明确写「**需检查**」，列出未达标的指标和 heatmap 里还红着的区域，仍然交付文件，不要说成合格品；
   - 用了 `--allow-photo-heavy` 要写明。

## 常见坑

- **图层顺序**：原图里虚线、箭头常常压在色块上面。heatmap 上沿着色块边缘出现一条红线时，多半是把线画在了色块下面——把线条节点挪到数组后面。
- **点线相位**：点线的点距对了但起点不对，heatmap 会出现一串红蓝交替的点。量原图第一个点的 x，把线的起点设到那里。
- 圆点虚线用 `dash: [1.5, 5]` 这类「短实长空」；导出 PPTX 时会映射到最接近的预设线型（sysDot / dot / dash / lgDash / sysDash），间距是近似的。

- 画布尺寸写成 1600×900 之类的「标准尺寸」——错，必须等于原图像素。
- 文字框太窄导致 lint 报 `text-overflow`：放宽 w，不要缩字号去凑。
- 箭头用 polyline 画三角——用 line/path 的 `arrowEnd: true`，这样 PPTX 里也是原生箭头。
- 把整个面板抠成图片来「提分」——违反交付标准，redraw-check 的位图占比会拦住。
- 不确定一段文字内容时宁可放大原图再看，不要猜。
