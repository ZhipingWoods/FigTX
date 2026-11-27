---
name: figtx-plot
description: |
  画论文实验图（柱状、折线、散点、雷达、热力图等）：有数据时套用顶会风格出图；有截图时用 matplotlib 复刻并与截图比对。风格可从 FigTX 实验图库挑选，也可配合 paper-plot-skills 使用。
  Use when the user says "plot my results", "画实验图", "用这个风格画我的数据", "复刻这张实验图", "make a bar/line/radar chart for the paper".
---

# 论文实验图

**前置条件**：需要 `figtx` 命令（安装：`uv tool install "git+https://github.com/ZhipingWoods/FigTX#subdirectory=packages/figtx-forge"`）和一个装有 matplotlib 的 Python。`figtx plot-run` 默认用 figtx 自己的解释器（通常没有 matplotlib），所以一般要加 `--python $(which python3)` 指向用户环境。

## 情况 A：用户有数据，想要好看的论文风格

1. **先看 paper-plot-skills 是否已安装**（`ls ~/.claude/skills ~/.codex/skills` 中有 `plot-from-data` / `plot-from-image`）。已安装 → 直接用它的 `plot-from-data`，它有现成的顶会风格模板。
2. 没安装 → 告诉用户可以安装 https://github.com/Trae1ounG/paper-plot-skills（作者另行维护，FigTX 不内置它的代码），同时可以直接用 FigTX 实验图库：
   - `figtx search "bar ablation" --category figure --type quantitative --json`，挑一个风格；
   - 打开 FigTX 网站对应编号复制它的 matplotlib 代码，把数据换成用户的；
3. 写成 `plot.py`，运行：`figtx plot-run plot.py -o out --python $(which python3)`，打开生成的图检查：字号在单栏宽度下可读（≥ 8pt）、配色色盲友好、图例不遮挡数据、坐标轴有单位。
4. 交付 `plot.py` + PNG/PDF（论文里用 PDF 矢量版）。

## 情况 B：用户有一张实验图截图，想复刻

1. 读截图：图类型、子图布局、坐标范围和刻度、每个系列的颜色/线型/marker、图例位置、字体（衬线/无衬线）、网格样式。数据看不清时用估计值并告诉用户。
2. 写 `plot.py`（`plt.savefig('figure.png', dpi=300)`，画布尺寸按截图宽高比设置）。
3. `figtx plot-run plot.py -o out --python $(which python3) --compare screenshot.png`，打开 `out/figure.png` 与截图并排对比，按差异修改。比对分数仅供参考（字体、抗锯齿会拉低分数）。
4. 迭代到视觉上一致（最多 5 轮），交付 `plot.py` + 图片，并说明哪些数值是估计的。

## 注意

- 不复制 paper-plot-skills 的脚本进项目；需要它的能力时让用户自己安装。
- 不确定的数据不要编造成「精确值」。
