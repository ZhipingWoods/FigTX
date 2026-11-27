---
name: figtx-find-figure
description: |
  在 FigTX 图库（顶会顶刊论文的框架图、实验图、LaTeX 表格）里按领域和研究问题找参考图，列出候选让用户挑，再交给复刻或绘图 skill。
  Use when the user asks "find a reference figure", "找参考图", "有没有类似的框架图", "想看看别人怎么画 X", "推荐几张 pipeline 图/实验图/表格样式".
---

# 在 FigTX 里找参考图

**前置条件**：需要 `figtx` 命令。不在 PATH 上时先装：
`uv tool install "git+https://github.com/ZhipingWoods/FigTX#subdirectory=packages/figtx-forge"`

## 流程

1. **问清楚要找什么**（用户没说时问一句即可）：要画的是框架图、实验图还是表格？研究领域和问题是什么（如「长上下文推理」「新视角合成」）？

2. **检索**。用英文关键词效果最好，领域词和问题词各试一次：
   - 框架图：`figtx search "diffusion video generation" --category figure --type framework --limit 10`
   - 实验图：`figtx search "ablation bar" --category figure --type quantitative`
   - 表格：`figtx search "main results" --category table`
   - 已知编号直接查：`figtx search F012`
   - 需要结构化结果时加 `--json`（含 `previewUrl`、`paper`）。
   默认读线上索引（缓存 24 小时）；在 FigTX 仓库里开发时可用 `--index public/index.json`。

3. **给用户挑**：列 5–10 个候选，每个一行：编号、类型、会议/年份、标题、预览链接。按与用户问题的相关度排，说一句为什么推荐前两个。没结果就换同义词、放宽类型再搜一次，仍然没有就如实说。

4. **用户选定后**：
   - 下载预览图到工作目录（`curl -L -o figtx-ref/<编号>.webp <previewUrl>`，需要时转成 PNG）。
   - 想要这张图的可编辑版 → 交给 `figtx-redraw-figure`。
   - 想照它的版式画自己的方法 → 交给 `figtx-framework-figure`。
   - 实验图 → `figtx-plot`；表格 → 条目里就有 LaTeX 源码，打开 FigTX 网站对应编号（`https://zhipingwoods.github.io/FigTX/#T042`）复制，或交给 `figtx-table-from-screenshot`。

## 注意

- 图的版权归原论文作者；给用户的结果里保留标题、会议和论文链接。
- 不要编造编号或链接——只用 `figtx search` 返回的内容。
