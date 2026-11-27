# 图片来源与版权（Images Policy）

FigTX 是一个**非商业、教育与研究用途**的论文图表索引。图库中的论文图（框架图、Teaser 主图等）来自已公开发表或公开预印的论文，**版权归原论文作者与出版方所有**，FigTX 不对图片本身主张任何版权。代码的许可（见 [LICENSE](LICENSE)）**不覆盖**这些图片。

## 来源

| 来源 | 说明 |
|---|---|
| [topconf-paper-figure-gallery](https://github.com/qwdwqfwq/topconf-paper-figure-gallery) | ICLR / ICML / NeurIPS / CVPR / ACL / AAAI 2023–2026 论文的 Figure 1 / Teaser |
| [PaperGallery](https://github.com/LongHZ140516/PaperGallery) | 框架图（pipeline）与主图（header）；FigTX 只收录图片与论文的事实性信息（标题、作者、会议、链接、BibTeX），不复制其网站代码与摘要文字 |
| FigTX 自有 | 渲染的 LaTeX 表格、实验图、论文图复刻 |
| 期刊（`data/journals.json`） | 维护者手工整理的 Nature / Science / Cell 等期刊论文图 |

## 署名

每张图在网站详情页和 `data/raw-gallery.json` 中都标注了论文标题、作者、会议/期刊、年份、论文链接，以及收录它的来源项目。高清原图存放在 Hugging Face 数据集 [OliverThompson/figtx-assets](https://huggingface.co/datasets/OliverThompson/figtx-assets)，同样附带来源说明。

## 下架

如果你是某张图的版权方，希望将其移除，请在 [GitHub Issues](https://github.com/ZhipingWoods/FigTX/issues) 中注明论文标题和 FigTX 编号（如 `F1234`）。维护者核实后会在 **72 小时内**删除该图及其缩略图、原图和所有引用。

## 给使用者的提示

复用某张图（包括 FigTX 生成的可编辑重画版）时，请以原论文和出版方的许可为准，并保留原始署名。
