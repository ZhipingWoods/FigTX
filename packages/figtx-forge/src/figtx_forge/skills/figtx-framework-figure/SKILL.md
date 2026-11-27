---
name: figtx-framework-figure
description: |
  根据用户的方法描述和一张参考图，画一张新的论文框架图 / Figure 1（沿用参考图的版式、配色、线条语言，内容全部换成用户的方法），导出可编辑 SVG 和 PPTX。
  Use when the user says "draw a framework figure / pipeline figure / Figure 1 for my method", "照这张图的风格画我的方法", "帮我画方法总览图", "画 teaser".
---

# 画新的框架图（AutoFigure 式生成-评审-修改）

**前置条件**：需要 `figtx` 命令。不在 PATH 上时先装：
`uv tool install "git+https://github.com/ZhipingWoods/FigTX#subdirectory=packages/figtx-forge"`

**输入**：① 方法描述（模块、数据流、关键创新点；不够就向用户要）；② 一张参考图（用户给，或先用 `figtx-find-figure` 找）。

**最重要的规则**：参考图只提供**视觉语法**（几何、密度、配色、线条、层级），**不提供内容**。参考图里的模块名、实体名、面板标题、说明文字一个都不能出现在新图里。这是最常见的失败。

## 流程

1. **测量设计契约**。看参考图，按 `references/design-contract.md` 的字段逐项写出**具体数值**（hex 颜色、px 字号、线宽、面板数、每面板模块数、箭头数、面板相对位置百分比）。不写「简洁」「优雅」这种词——只有数值能防止风格漂移。存为 `contract.json`。

2. **规划内容**。把用户的方法拆成与契约**相同数量和节奏**的面板/模块，每个标签都来自方法描述。写一个简短提纲给自己：面板 → 模块 → 连线 → 放大细节。

3. **写场景 JSON**（格式同 `figtx-redraw-figure` 的 `references/scene-schema.md`；画布默认 1600×900，或与参考图同比例）。
   - 面板外框比模块框更粗；可选/跳过的路径用虚线（`dash`），计算路径用实线；同时用到两种时加小图例。
   - 每个面板里填有意义的子结构（迷你流程、矩阵、小图表、放大框），不要留大块空白。
   - 全英文；数学符号用 Unicode 上下标（xᵢ、ℒ、x′），不要丢掉下标。
   - 标题与副标题分两行，间距 ≥ 12px。

4. **自查**：
   - `figtx lint scene.json --english-only` —— 必须无 text-overflow / out-of-canvas / cjk。
   - `figtx render scene.json -o render.png`，**打开 render.png 看**，按下面的评审表给自己打分。

5. **评审表**（0–10 分，先判内容再判视觉）：
   - content：是否真的画的是用户的方法？出现任何参考图的内容 → content 记 0，必须重做。
   - layout / hierarchy / density / palette：是否符合契约的面板数、模块密度、配色、线宽层级？
   - legibility：文字无重叠、无溢出，最小字号 ≥ 契约的 note 字号。
   - 总分 ≥ 8 才算可投稿。不到 8 → 列出具体问题和修法，改场景，回到第 4 步。**最多 3 轮**。

6. **导出**：`figtx export scene.json -o out` → `out/scene.svg`、`out/scene.pptx`。交付时附上最终评分和仍存在的不足。
