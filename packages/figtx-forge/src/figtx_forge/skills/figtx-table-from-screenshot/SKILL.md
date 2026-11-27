---
name: figtx-table-from-screenshot
description: |
  把论文表格截图转成可编译的 LaTeX（booktabs 三线表风格），用 tectonic 编译出预览并与截图逐格核对，保证行列、合并单元格、数字、加粗/下划线/底色都一致。
  Use when the user gives a table screenshot and asks "convert to LaTeX", "截图转表格", "把这个表转成 latex", "照这个表的样式做一个".
---

# 表格截图 → LaTeX

**前置条件**：需要 `figtx` 命令（安装：`uv tool install "git+https://github.com/ZhipingWoods/FigTX#subdirectory=packages/figtx-forge"`）和 tectonic（`brew install tectonic`，或见 https://tectonic-typesetting.github.io）。`figtx tex` 退出码 2 表示没装 tectonic。

## 流程

1. **读结构**：数清楚行数、列数、表头层级、`\multicolumn` / `\multirow` 的位置、竖线有无、分组横线（`\cmidrule`）位置。写下来：`rows=?, cols=?`（rows 按 `\\` 计，即每一行内容一个）。

2. **写 LaTeX**（`table.tex`，只写 tabular 本体即可，`figtx tex` 会自动包成独立文档；也可以带 `\begin{table}` 和 `\caption`，会被自动剥掉再编译）：
   - 三线表用 `\toprule` / `\midrule` / `\bottomrule`，不要用 `\hline` 冒充。
   - 加粗最优 `\textbf{}`、次优 `\underline{}`，照截图标注；整行/单元格底色用 `\rowcolor` / `\cellcolor`（xcolor[table] 已加载），颜色用 `\definecolor{name}{HTML}{RRGGBB}` 取截图里的色值。
   - 符号：✓ ✗ 用 `\ding{51}` / `\ding{55}`（pifont 已加载），± 用 `$\pm$`。
   - 可用宏包：booktabs、multirow、makecell、array、tabularx、graphicx、amsmath、amssymb、pifont、xcolor[table]。需要别的宏包时写完整文档（含 `\documentclass`）。

3. **编译并核对**：
   `figtx tex table.tex -o preview.png --compare screenshot.png`
   - 第一行输出 `rows=… cols=… multicolumn=… multirow=…`，必须与第 1 步数的一致。
   - **打开 preview.png 与截图并排逐格核对数字**——这是最重要的一步，OCR 式错误（0/O、1/l、小数点）只能靠逐格看。
   - `--compare` 的像素分数仅供参考（字体不同分数天然偏低），不作为通过标准。截图里带有表题（caption）时分数会更低——要参考分数，先把截图裁到只剩表格本体。
   - 对齐方式也要核对：某列的 `-` 或短数字居中而不是靠右，说明那一列是 `c` 而不是 `r`。

4. **修正**，回到第 3 步，直到结构一致、每个数字一致、强调样式一致。

5. **交付**：`table.tex` 源码 + `preview.png`。提醒用户：数字已逐格核对；若截图模糊无法确认某格，明确指出是哪一格。
