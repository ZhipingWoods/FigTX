# FigTX 图库整合与「拿来即用」设计

日期：2026-11-27
状态：草案，待确认

## 1. 意图

FigTX 会作为开源项目，服务科研工作者。用户打开它，可以看到顶会、顶刊论文里的**图和表**。参考对象包括 CVPR、NeurIPS、ICLR 这类会议，以后还会加入 Nature、Science、Cell 正刊和 NMI 等子刊。用户的目的不是欣赏，而是**照着用**：把看中的图或表复制走，换成自己的数据和内容。

已有项目各自只做了一半：

| 项目 | 做到了 | 缺什么 |
|---|---|---|
| topconf-paper-figure-gallery | 3449 张顶会 Figure 1 / Teaser，可以浏览和筛选 | 只能看。可编辑导出要在网页里自己配置 key，而且不保证质量 |
| PaperGallery | 约 256 张框架图和 68 张主图，元数据比较全（标签、代码、项目页、bibtex） | 只能看 |
| AutoFigure | 能根据文字生成图，用「生成 → 评审 → 修改」循环提升质量 | 不能基于某张具体的参考图 |
| paper-plot-skills | 在 Claude Code / Codex 里调用 skill，就能画出相近的实验图，作者本人一直在用 | 只覆盖实验图 |
| FigTX 现状 | 188 张 LaTeX 表格（有真实渲染图）、35 张实验/样式图、10 张论文复刻图、一个「生成」页签 | 框架图很少；生成功能不够好；没有收藏 |

FigTX 要把这些整合起来：**能看，也能用**。

## 2. 用户与使用路径

作者本人的典型使用流程，也就是目标用户的流程：

1. **画框架图**：打开 FigTX，先**按领域、按研究问题**浏览好看的框架图，挑出几张喜欢的。点「重画成可编辑版」，把**这张图本身一比一重画**成可编辑的 SVG / PPTX。下载后，把内容改成自己的方法。
2. **画实验图**：回来找实验图，拿走 matplotlib 代码，换上自己的数据。
3. **做表格**：回来找 LaTeX 表格，复制源码。
4. **收藏**：随时把喜欢的图或表加进「我的收藏」。
5. **截图转换**：用户手里有一张截图（论文里的表或图），上传后转成 LaTeX 表格，或者转成可编辑的图。
6. **贡献**：重画或转换出来的结果，可以贡献回公共库。经过自动检查和人工审核、质量过关后才合并；合并后，下一个人就能直接下载现成的可编辑版。

## 3. 目标、非目标、反目标

**目标**
- G1：把 topconf（3449 张）和 PaperGallery（框架图约 256 张、主图约 68 张）的图和元数据并入 FigTX，与现有的表格和实验图放在同一个网站里浏览。
- G2：可以按**领域**、**研究问题**、会议/期刊、年份、图类型、「是否已有可编辑版」来筛选和搜索。
- G3：首页重新设计，参考两个参考站点的观感，但不照抄。首页要让人一眼看到三条入口：框架图、实验图、表格。
- G4：「我的收藏」功能，存在本地，不需要登录。
- G5：「重画成可编辑版」：把原图一比一重建成可编辑的 SVG 和 PPTX；在可行的情况下，也导出 draw.io 格式。
- G6：截图转换：表格截图转成 LaTeX，并编译验证；实验图截图转成 matplotlib 代码；框架图截图走 G5 的流程。
- G7：生成功能支持多家模型：OpenAI（GPT / Codex 系列模型）、Anthropic Claude、Google Gemini、xAI Grok，以及任何 OpenAI 兼容的接口（如 DeepSeek）。
- G8：提供一组 **skills**，放进 Claude Code 或 Codex 就能直接用，能力和 G5、G6、框架图生成一致。这些 skill 由三个参考项目和 paper-plot-skills 的作图经验总结而来。
- G9：贡献流程：有一份贡献指南、一个固定的贡献包格式、一个自动质量检查脚本（贡献者本地能跑，PR 上也会自动跑），由维护者人工审核后合并。
- G10：更新脚本。上游来源（topconf、PaperGallery，以后还有期刊）更新后，一条命令就能增量同步：新条目进库，旧条目的编号不变。

**非目标**
- 不提供托管的生成服务，不替用户付模型费用。生成一律在用户自己的机器上、用用户自己的 key 或自己的 agent 来跑。
- 不做账号系统和云端收藏。
- 不预先把 3800 张图全部重画一遍。只在有人需要时重画，重画过的结果通过贡献慢慢沉淀进库。
- 第一期不接入 Nature / Science / Cell / NMI 的真实数据，只把数据结构和导入脚本预留好。

**反目标**（即使功能能跑，出现以下情况也算失败）
- 把整张位图塞进 SVG 或 PPTX，冒充「可编辑」。
- 重画出来的图里混进了别的论文的内容。现有 figgen 的评审环节已经把这一点当作首要错误来扣分。
- 仓库被大文件撑爆，clone 慢到没人愿意贡献；或者因为下载量太大，触发 GitHub 的流量配额，导致仓库被锁。
- 首页加载 3800 张图时卡顿。
- 用户的 API key 被写进仓库或日志，或者被发送到所选模型服务商之外的任何地方。
- 照搬 PaperGallery 的网站源码。它的源码声明「仅限学术、禁止二次分发」。我们只收它的图片和论文元数据。

**关于图片转载（作者已决定）**：作者确认可以把论文图片复制进仓库，理由是论文都已公开。需要注意，topconf 的 `IMAGES_POLICY.md` 写明它的 MIT 许可不覆盖图片，并承诺「不作为素材包分发」；PaperGallery 没有声明图片和元数据的许可。我们的做法如下：
- 每条数据保留完整署名，包括原论文信息和来源项目（topconf / PaperGallery）。
- 设立下架通道。
- PaperGallery 只取事实性元数据（标题、作者、年份、会议、各类链接、bibtex）和图片，不取它写的摘要正文；需要摘要时，从 arXiv 取。（我的判断）

## 4. 已有资产与事实

- **FigTX**：React 18 + Vite 6 + Electron 33。数据由 `tools/build-data.mjs` 汇总 `data/raw-*.json`，生成 `src/data/items.json`（构建产物，不入库）。稳定编号存放在 `data/catalog.json`（T001…/F001…，只增量分配）。GitHub Pages 通过 `.github/workflows/pages.yml` 在 push main 后构建。生成模块在 `tools/figgen/`（Python），包括 `llm_client.py`（OpenAI 兼容）、`contract.py`（设计契约）、`generate.py`（生成→评审→修改）、`server.py`（本地 8780 端口，提供 `/api/health`、`/api/contracts`、`/api/generate`），前端对应 `src/Forge.tsx`。
- **topconf**：`data/figures.json` 共 3449 条，字段有 id、venue、year、title、authors、pattern、image、paper、pdf_source、score、tier、award、w、h。pattern 的分布：teaser 1560、architecture 513、conceptual 439、pipeline 396、framework 283、taxonomy 247，其余很少。图片 334MB，中位数每张约 87KB（jpg）。代码采用 MIT 许可；`forge/` 里有完整的「位图 → 可编辑场景 JSON → SVG/PPTX/VSDX/draw.io」实现（`editable-native.mjs` 等），以及验证文档 `EDITABLE_EXPORT.md` 和 `RECONSTRUCTION-VALIDATION.md`。上游仓库：github.com/qwdwqfwq/topconf-paper-figure-gallery。
- **PaperGallery**：数据在 `web` 分支。`src/content/images/{pipeline,header}/paper/*.md` 是 frontmatter 格式，字段有 title、authors、year、conference、tags、image、paper、code、project、bibtex，正文是摘要。图片在 `public/images/{pipeline,header}/`。另有 `project_page/`（项目主页示例和模板）和 `tools/`（配色、图标、资源库链接）。源码许可：仅限学术，禁止二次分发。
- **AutoFigure**：MIT 许可。核心机制「生成 → 评审 → 修改」已经在 figgen 里实现。
- **paper-plot-skills**：本地路径 `/Users/zhipingwu/CodeHome/VizPlugin/paper-plot-skills`，上游是 github.com/Trae1ounG/paper-plot-skills。包含 `plot-from-data` 和 `plot-from-image` 两个 skill。**本地副本里没有找到 LICENSE 文件。**
- **GitHub 的限制**：Git LFS 在免费账号下每月有 10 GiB 存储和 10 GiB 下载流量；任何人 clone 或 Actions checkout 拉取 LFS 文件，都算在仓库所有者的流量里；超出后，在下个月之前 LFS 会被停用。按我的理解（尚未核实），直接从分支部署的 GitHub Pages 不会解析 LFS 文件，必须在 Actions 里用 `lfs: true` 做 checkout。

## 5. 设计

### 5.1 统一的条目模型

所有条目（表、实验图、框架图、主图……）都使用同一个结构。现有 `items.json` 的字段保留，在此基础上新增以下字段：

```
category      'table' | 'figure'
figType       framework | teaser | pipeline | architecture | conceptual | taxonomy
              | motivation | quantitative | qualitative | style | ...（沿用现有值，再并入 topconf 的 pattern）
source        { platform: 'topconf' | 'papergallery' | 'figtx' | 'contrib' | 'journal', upstreamId, upstreamUrl }
paper         { title, authors[], venue, year, tier?, award?, url, pdf?, code?, project?, bibtex? }
domains[]     固定领域表里的取值（见 5.3）
problems[]    研究问题关键词（自由文本，归一化为小写英文短语）
assets        { preview: 'thumbs/…webp', original: <大文件位置>, editable: { svg?, pptx?, drawio?, tex?, py? } }
editableStatus 'original-only' | 'editable' | 'native-code'
               （表格和实验图本身就有源码，属于 native-code）
```

编号：已有的 T/F 编号保持不变。新并入的图继续使用 F 序号，由 `assign_numbers.py` 增量分配。

**去重合并（作者要求）**：不同来源之间有重复的论文和图，必须合并。
- 判断同一篇论文：标题归一化（小写、去掉标点和空白）+ 年份；有 arXiv id 或 DOI 时，优先用它们判断。
- 判断同一张图：感知哈希（pHash），汉明距离小于阈值即视为同一张。分辨率或裁边不同也能识别。
- 同一张图合并为**一个条目**，`source` 改为数组，记录所有来源，保留各来源的署名。图片取分辨率更高的那张；元数据按字段合并，PaperGallery 的 code / project / bibtex 字段补进 topconf 的条目。
- 同一篇论文的不同图，各自是独立条目，在详情页里互相链接。
- 每次同步都会输出合并报告，列出疑似重复但没有自动合并的条目，供人工确认。

### 5.2 数据来源与更新脚本

新建 `tools/sync/` 目录，每个来源一个适配器，全部输出到 `data/sources/<source>.json`，格式统一：

- `sync_topconf.py`：浅克隆或拉取上游仓库到 `.cache/upstream/topconf`（不入库），读取 `data/figures.json`。
- `sync_papergallery.py`：浅克隆 `web` 分支到 `.cache/upstream/papergallery`，解析 frontmatter。只取 header 和 pipeline 两类。项目主页示例、配色、图标、资源库不在本期范围内。
- `sync_journal.py`：预留给 Nature / Science / Cell / NMI。输入是手工整理的清单（DOI、图号），脚本负责抓取元数据。本期只定义输入格式，并写一个空跑测试。

总入口是一条命令：`npm run sync`。它依次执行：各来源同步 → 去重合并 → 生成缩略图 → 领域/问题打标（有缓存，只处理新条目）→ 增量编号 → `build-data`。运行结束后打印一份报告：新增多少条、更新多少条、上游删了多少条（上游删除的条目只标记，不自动删）、打标失败多少条。

另外提供一个定时的 GitHub Action（每周一次），自动跑 `npm run sync`，有变化就开一个 PR，由维护者合并。打标需要调用模型，Action 里只有在配置了 key 的情况下才会打标；没有 key 时，新条目标记为「待打标」，仍然入库。

### 5.3 领域与研究问题

topconf 的条目没有领域标签。PaperGallery 有自由标签，但有错别字，也不统一。

- **领域**：使用一张固定的表（约 15–20 个），例如：计算机视觉、3D 与图形学、生成模型、NLP 与 LLM、多模态、强化学习与决策、机器人与具身智能、机器学习理论与优化、图学习、高效推理与系统、安全与对齐、AI for Science、医学影像、语音与音频、推荐与检索、Agent。这张表写在 `data/taxonomy.json` 里，并显示中文标签。
- **研究问题**：每条 1–3 个短语，例如 "long-context reasoning"、"novel view synthesis"。
- **打标脚本** `tools/sync/tag.py`：用标题加摘要（有摘要时）调用模型打标，结果缓存在 `data/tags.json` 里，入库后可以人工修正。人工修正过的条目不会被自动打标覆盖。

### 5.4 存储布局（已确认：大文件放 Hugging Face，使用作者本人账户）

推荐方案：

| 内容 | 位置 | 原因 |
|---|---|---|
| 代码、元数据 JSON、SVG、LaTeX、Python 源码 | 普通 git | 都是文本、体积小，在 PR 里能看到改动、方便审核 |
| 浏览用缩略图（最长边约 800px 的 webp，每张约 30–60KB） | 普通 git | 网站和桌面版必须能直接显示；3800 张合计约 150–200MB |
| 高清原图、PPTX、draw.io | 作者本人账户下的 Hugging Face 公开数据集仓库（名称暂定 `<作者HF用户名>/figtx-assets`） | 免费，公开下载不按流量计费，专门用来放大文件；网站通过 `resolve/main/...` URL 直接引用，桌面版按需下载 |

- 上传：`tools/sync/push_assets.py` 用 `huggingface_hub` 增量上传，只传新增或变更的文件。本地运行时用 `hf auth login`；在 Actions 里运行时，用仓库 secret `HF_TOKEN`（需要作者在 HF 创建一个 write token，填到 GitHub 仓库设置里，这一步只能由作者本人完成）。
- 缩略图放进普通 git（作者没有反对，我的判断）。

不推荐用 Git LFS 放这些文件：每次有人 clone 或 fork、每次 Pages 构建，都会消耗仓库所有者 10 GiB/月的流量。开源后很容易用超，用超之后整个仓库的 LFS 都会被锁住。

GitHub Release 附件可以作为备选（没有流量配额），但不方便按单个文件引用。

### 5.5 首页与浏览

视觉风格在实现前先做 2–3 版 mockup，由作者挑选。以下只确定结构：

- **首页**：
  - 首屏写清楚定位（「顶会顶刊的图和表，拿来就能改」），附实时统计（多少张框架图、实验图、表格、可编辑版）。
  - 三张大入口卡片：框架图、实验图、表格。
  - 一个全局搜索框，可以搜标题、领域、研究问题、编号。
  - 「最近新增」和「已有可编辑版」两条精选横带。
  - 一条按领域快速进入的导航。
- **图库页**：框架图用瀑布流（图片高低不一）；表格和实验图保留现在的网格。左侧或顶部放筛选：领域、研究问题、会议/期刊、年份、图类型、是否有可编辑版、Oral / Best 等。
- **详情页**：
  - 大图。
  - 论文信息：标题、作者、会议、论文链接、代码和项目页链接、bibtex 一键复制。
  - 可编辑文件下载区：没有可编辑版时显示「重画成可编辑版」按钮。
  - 收藏按钮。
  - 同领域推荐。
- **性能**：条目会到 3800 张以上。列表只加载精简索引，例如 `index.json` 里放 id、缩略图、标题、标签，并尽量压到 1MB 以内；详情按需加载。网格做虚拟滚动或分页加载，缩略图懒加载。
- 现有的 T/F 编号直达（`#T042`）、正序/倒序、桌面版离线浏览全部保留。桌面版内置缩略图，高清原图在线时再按需获取。

### 5.6 我的收藏

- 存储：浏览器里用 IndexedDB（桌面版同样适用），不需要登录。
- 收藏的单位是条目，可以加备注、建分组。
- 用户自己转换或重画的结果也存进收藏，标记为「我的」，带上文件。
- 支持导出和导入 JSON，方便换电脑或备份。
- 收藏里的条目可以一键进入贡献流程（见 5.9）。

### 5.7 重画与转换（生成模块重做）

**模型接入层**：重写 `tools/figgen/llm_client.py`，改为 provider 抽象：

- `openai`：OpenAI 官方，包括 GPT 和 Codex 系列模型。
- `openai_compatible`：任意 base_url，可接 xAI Grok、DeepSeek、Gemini 的 OpenAI 兼容端点，以及内网网关。
- `anthropic`：原生 Messages API。
- `gemini`：原生 API，可选；如果兼容端点已经够用，这一项可以不做。

每个 provider 声明自己的能力：是否支持视觉输入、最大输出长度、是否是推理模型（推理模型的已知问题是 token 全部花在 reasoning 上）。配置来源：`.env`，或者用户在界面里填写（只存在本机）。

**Codex 和 Claude Code 本身不走 API 接入，而是通过 5.8 的 skill 来使用。**

**三条流程**（都在本地 figgen 服务里跑，网页版和桌面版共用）：

1. **框架图 / 主图重画** `redraw`：原图 → 分块视觉识别，得到场景 JSON（文字、容器、连线、箭头、图标、照片区域各自是独立对象）→ 渲染 → 与原图比对（像素和结构指标）→ 把误差大的区域发回模型修正（AutoFigure 的评审-修改循环，加上 topconf 的修正门槛）→ 导出 SVG、PPTX，以及 draw.io（能做就做）。达不到质量门槛的结果标为「需检查」，不会被当作合格品交付，也不允许整页位图兜底。

   **质量标准（作者要求）：一比一复刻。** 每个元素的位置、大小、线条（粗细、颜色、虚实、箭头样式）、文字（内容、字号、粗细、颜色）都要与原图一致。
   - 照片、渲染结果、复杂插画、3D 截图这类元素，**先从原图里抠出来**，作为独立的位图对象，按原位置原尺寸放回去。
   - 其余部分（框、线、箭头、文字、色块、简单图标、公式）全部用矢量对象一比一重建。
   - 照片较多的 teaser 图也在重画范围内，同样遵守「抠图 + 矢量重建」。
   - 判定指标（与 topconf 的门槛对齐）：综合分数和深色笔画召回率 ≥ 0.98，局部召回率和边缘 F1 ≥ 0.97，颜色相似度 ≥ 0.98，文字内容完全一致。
   - 位图对象的面积占比必须低于一个上限，默认 40%，防止用大块位图偷懒；如果原图本身以照片为主，可以放宽，并在结果里注明。
   - 贡献 PR 的合并门槛使用同一组指标。topconf `forge/` 中场景 → 四种格式的导出代码是 MIT 许可，可以移植或复用，需注明出处。
2. **表格截图 → LaTeX** `table`：视觉识别 → LaTeX（booktabs 风格）→ 用 tectonic 编译 → 把渲染图和截图比对 → 修正 → 输出 `.tex` 和预览图。
3. **实验图截图 → 代码** `plot`：用 plot-from-image 的思路，截图 → matplotlib 脚本 → 运行 → 比对 → 修正 → 输出 `.py`、PNG、PDF。

保留现有的「根据方法描述 + 参考图设计契约生成新图」功能（`generate`），作为第四个入口。

前端「生成」页签改成「工作台」，四个入口：重画、表格截图、实验图截图、按描述生成。详情页的「重画成可编辑版」按钮会带着原图直接跳到工作台。

如果本地服务没有启动，工作台要明确提示怎么启动（一条命令），或者引导用户改用 skill。

**分发方式（已确认）**：生成能力不内置进桌面安装包。用户有两种用法：
- 一条命令装好本地服务。打包成 Python 包 `figtx-forge`，用 `uvx figtx-forge` 或 `pipx run figtx-forge` 启动。依赖 tectonic 和渲染器，首次运行时检测，缺什么就提示安装。
- 在 Claude Code / Codex 里使用 skills。

### 5.8 Skills

在仓库根目录新建 `skills/`，每个 skill 一个目录，使用标准的 `SKILL.md` 格式，Claude Code 和 Codex 都能直接加载：

| skill | 做什么 |
|---|---|
| `figtx-find-figure` | 根据用户的领域和研究问题，在 FigTX 索引里检索参考图（读取打包好的 `index.json`，或直接访问线上地址） |
| `figtx-redraw-figure` | 把一张图一比一重画成可编辑的 SVG/PPTX（总结 5.7-1 的流程和检查清单；agent 自己写 SVG，再用附带的脚本渲染和比对） |
| `figtx-framework-figure` | 根据方法描述 + 参考图，画新的框架图（AutoFigure 的循环 + 设计契约 + 反目标清单） |
| `figtx-table-from-screenshot` | 表格截图 → LaTeX，并编译验证 |
| `figtx-plot` | 实验图：选风格并填入数据，或者从截图复刻。基于 paper-plot-skills ⚠️ 许可待确认（见 §9 Q2） |

skill 里附带的脚本复用 `tools/figgen` 的渲染和比对代码，不重复实现。另提供 `npm run skills:install`，把 skills 链接到 `~/.claude/skills` 和 `~/.codex/skills`。

### 5.9 贡献与质量审核

- **贡献包格式**：`contrib/<条目id或new-xxx>/`，包含：
  - `meta.json`：对应的原条目 id、论文信息、使用的模型和流程、贡献者。
  - 可编辑文件。
  - `preview.webp`。
- **唯一真源（我的判断）**：PR 里只提交文本格式的可编辑文件，包括场景 JSON + SVG（图）、`.tex`（表）、`.py`（实验图），不提交 PPTX 等二进制文件。合并后，由 CI 从场景 JSON 重新生成 PPTX / draw.io，再上传到 5.4 规定的大文件位置。这样 git 历史里不会出现二进制文件，审核时也能看到改动。
- **自动检查脚本** `tools/check_contribution.py`：
  - 结构检查：必填字段、文件存在、大小上限。
  - SVG 检查：能渲染；不含整页位图；文字没有溢出容器、没有互相重叠；`viewBox` 正确；没有 `mask` 或 `filter`（会影响 PPT 转换）。
  - LaTeX 检查：能编译通过。
  - 与原图比对：相似度超过阈值。
  - 去重检查。
  - 输出一份 Markdown 报告。
- **PR 上的 GitHub Action**：自动运行检查脚本，并把报告评论到 PR 上。没通过就不能合并。
- **人工审核**：维护者看过之后合并。合并后会触发同步：条目的状态变为「已有可编辑版」，大文件上传到 5.4 规定的位置。
- **桌面版和网页版的「贡献」按钮**：把收藏里的结果打包成贡献包 zip，然后引导用户去 GitHub 提 PR。网页上会给出图文步骤。
- **贡献指南**：重写现有的 `docs/wiki/贡献指南.md`，并在根目录放 `CONTRIBUTING.md`，说明可以贡献什么、格式要求、质量标准、本地自查命令、审核流程。
- **图片政策与下架**：新增 `IMAGES_POLICY.md`，说明来源、署名、合理使用，以及收到下架请求后的处理流程。

## 6. 分期（每期都能单独上线）

1. **P1 数据整合**：统一条目模型、sync 脚本、领域打标、缩略图、存储布局、`npm run sync`、定时 Action。完成后，网站能用现有界面浏览全部约 3800 张图。
2. **P2 首页与浏览**：先出 mockup，作者选定后再实现首页、图库页、详情页、筛选、性能优化，以及我的收藏。
3. **P3 工作台**：provider 抽象、重画、表格截图、实验图截图，以及按描述生成的改进。
4. **P4 Skills**：五个 skill 和安装脚本。
5. **P5 贡献流程**：贡献包、检查脚本、PR Action、贡献指南、图片政策。
6. **P6 发布（作者要求）**：所有功能完成后，打版本 tag（如 `v1.0.0`），由 `release.yml` 构建 macOS / Windows / Linux 桌面安装包并上传到 GitHub Releases；同时把 `figtx-forge` 发布到 PyPI（需要作者提供 PyPI token），把 skills 打成 zip 附在 Release 里。README 同步更新截图和安装说明。

P1 和 P3 之间没有依赖，可以并行。P2 依赖 P1 的数据。P4 复用 P3 的脚本。P5 依赖 P3 的输出格式。P6 放在最后。

## 7. 约束

- 根目录的 CLAUDE.md 规定：单个文件不超过 500 行；不提交密钥；改动后要跑 `npm run build`。
- 用户的 key 只放在 `.env`（已在 .gitignore 里）或本机配置里，前端不硬编码。
- 网页版是纯静态站点（GitHub Pages），生成功能依赖本地服务或 skill。
- 现有 T/F 编号和 `#T042` 直达链接不能失效。
- 每条来自外部的数据都要保留完整署名：论文标题、作者、链接、来源项目。
- **许可（我的判断）**：仓库的 `LICENSE` 文件是 Apache-2.0，但 `package.json` 写的是 MIT。以 `LICENSE` 文件为准，把 `package.json` 改为 Apache-2.0。移植 topconf `forge/` 中的 MIT 代码时，在文件头和 `NOTICE` 里注明出处。贡献的可编辑文件采用和代码相同的许可，同时说明「图的内容设计归原论文作者所有」。PR 模板里放一个确认勾选框，不要求签 DCO/CLA。
- **paper-plot-skills（我的判断）**：上游仓库没有 LICENSE 文件，按「保留所有权利」处理。`figtx-plot` 只引用它，让用户另行安装，不复制它的脚本。如果作者以后拿到授权，可以改为内置。

## 8. 留给实现者决定（标注为我的判断）

- 缩略图的具体尺寸和压缩质量；虚拟滚动用哪种实现方式。
- 领域表的最终版本（在 5.3 的基础上可以增删）。
- 打标和重画默认用哪家模型。
- draw.io 导出是否在 P3 完成，还是推迟。
- 首页的视觉风格：给出 mockup 后由作者选择。

## 9. 作者的决定（2026-11-27）

1. 大文件放 Hugging Face，使用作者本人账户（作者的 GitHub 已关联 HF）。
2. 生成功能通过命令或 skill 使用，不内置进桌面版。所有功能完成后，打 tag 并上传发布包。
3. 重画标准是一比一复刻：位置、大小、线条都要一致；复杂元素可以先抠出来，再按原样放回。不同来源之间重复的论文和图要合并。
4. 允许把论文图片复制进仓库。
5. 需要贡献功能：先审核，质量过关后再合并；同时提供自动检查脚本和贡献说明。

**仍需作者本人操作的事项（不影响开工）**：
- 告诉我 HF 用户名，或者在本机执行 `hf auth login`。
- 在 HF 创建 write token，并填入 GitHub 仓库的 secret `HF_TOKEN`。
- P6 发布时提供 PyPI token。
