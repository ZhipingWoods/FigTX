# FigTX P2「看图墙」首页与浏览 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把网站换成作者选定的 mockup C「看图墙」视觉。内容包括：首页（倾斜图片墙首屏、领域胶囊、拼贴入口卡、两条大图横带）、图库（吸顶筛选条加瀑布流，按领域、研究问题、会议、年份、图类型、可编辑、Oral/Best 筛选）、深色灯箱详情、本地收藏（可导入导出）。数据改为「精简索引 + 按需加载详情」，首屏不再打包 7.5 MB 的 JSON。

**Architecture:**
- **数据：** `build-data.mjs` 额外生成 `public/data/index.js`（`window.__FIGTX_INDEX__ = {...}`，全部条目的精简字段）和 64 个详情分片 `public/data/detail-NN.js`（`window.__figtxDetail(NN, {...})`）。用 `<script>` 注入加载，`file://`、Pages、Electron 下都能用。
- **前端：** 按页面和组件拆分文件，用 hash 路由（`#/`、`#/figures`、`#/experiments`、`#/tables`、`#/favorites`、`#/forge`；`#F036`、`#T042` 直达灯箱，兼容旧链接）。
- **样式：** 按 mockup C 移植到 `src/theme.css`，工作台的样式抽到 `src/forge.css`。

**Tech Stack:** React 18、Vite 6、TypeScript；新增 vitest 测纯逻辑；Python pytest（现有 `tools/sync/tests` 框架）测 build-data 的输出；浏览器验证用 Claude Browser preview 和 playwright-core。

**Spec:** `docs/superpowers/specs/2026-11-27-figtx-gallery-integration-design.md` §5.5、§5.6。视觉参考稿：`figgen-out/mockups/c.html`（不入库）。

## Global Constraints

- 视觉照 C：底色白与 `--mist #EEF1F5`，文字 `--ink #1B1D22`，强调色 `--pink #FF4F7B`；标题用霞鹜文楷（`LXGW WenKai`，CDN 加载，离线时回退到楷体），界面用 Figtree 和 PingFang。
- 已有编号和直达链接 `#T042`、`#F036` 必须继续可用。
- 离线可用：`dist/index.html` 双击打开（`file://`）和 Electron 下都要能用，不能依赖 `fetch` 本地 JSON。
- 首屏只加载精简索引（目标 ≤ 1.5 MB 未压缩），详情按需加载。
- 单文件不超过 500 行。
- 不改动用户在工作区里未提交的修改 `tools/figgen/prompts.py`。
- 分支 `feat/p2-wall`，通过 PR 合并（main 有 ruleset）。

## Review Focus

1. **从 `file://` 打开 `dist/index.html`**：首页、图库、灯箱都能用（数据经 `<script>` 加载）。→ Task 6 的 playwright 用 file:// 跑一遍。
2. **旧链接 `#T042` 和刚上线的 `#F036`**：打开后直接显示对应条目的灯箱，背景切到所属分区。→ Task 4 的浏览器检查。
3. **筛选组合后为空**：显示空状态和「清除筛选」，不白屏。→ Task 3 的 `filter.test.ts` 加浏览器检查。
4. **收藏导入时 JSON 损坏或版本不对**：给出提示，不覆盖已有收藏。→ Task 5 的 `favs.test.ts`。
5. **详情分片加载失败（断网）**：灯箱显示「详情加载失败，重试」，卡片信息照常显示。→ Task 4 的 `data.test.ts`。

---

### Task 1: 数据拆分（精简索引 + 详情分片）与加载器
**Files:** Create `tools/shard.mjs`（`shardOf(id) -> 0..63`，djb2 哈希；build 和前端共用）、`src/lib/data.ts`；Modify `tools/build-data.mjs`、`.gitignore`（忽略 `public/data/`）、`package.json`（新增 vitest 和 `test:web` 脚本）；Test `tools/sync/tests/test_build.py`（新增用例）、`src/lib/data.test.ts`。
- **索引条目字段：**
  - `id`、`no`、`cat`（`figure` 或 `table`）、`ft`（figType）、`grp`（framework、teaser 或 experiment，表格为 table）、`t`（标题，表格取 caption 或 title）、`v`（会议列表）、`y`（年份）、`d`（领域 key）、`p`（研究问题）、`r`（缩略图路径）、`ar`（宽高比，有尺寸时才有）、`ed`（`editable`、`code` 或 `none`）、`aw`（award 或 tier，可空）、`src`（来源平台）、`k`（搜索用的小写拼接串：标题、会议、标签、问题）。
  - 索引里另外附带 `stats`、`taxonomy`（领域中文名）和 `generatedAt`。
- **详情：** 即完整条目（现在 `items.json` 中一条的全部内容）。
- `items.json` 和 `public/index.json` 继续生成：`assign_numbers.py` 和 `figtx search` 要用。
- **`data.ts` 的接口：**
  - `loadIndex(): Promise<Index>`
  - `loadDetail(id): Promise<Detail>`：按分片缓存；失败时 reject，下次调用重试。
  - `loadScript(url)`：可注入实现，供测试替换。
- [ ] **测试：**
  - pytest：`test_lite_index_and_shards`。index.js 能解析出条目数等于 items 数；一条图库条目的 `grp` 为 framework，`ar` 约等于 w/h；分片总条目数等于总数，且每条都在 `shardOf(id)` 号分片里。
  - vitest：`loadDetail` 只为同一分片注入一次脚本；脚本 onerror 时 reject，下次调用重试。
- [ ] 确认测试失败，实现，确认通过；运行 `npm run build`，确认 index.js ≤ 1.5 MB；提交。

### Task 2: 主题、外壳、路由、首页
**Files:** Create `src/theme.css`（移植 C）、`src/forge.css`（把 styles.css 中的 `.forge*` 规则和它们依赖的变量抽出来）、`src/lib/route.ts`（`parseHash`、`buildHash`）、`src/components/Header.tsx`、`src/pages/Home.tsx`；Modify `src/App.tsx`（改为外壳，加载索引后按路由渲染页面）、`src/main.tsx`（样式引入）、`index.html`（字体 link，title 改为「FigTX · 顶会顶刊的图和表」）；Delete：旧 App 中被页面取代的部分，旧 `styles.css` 中工作台之外的规则。
- **首页内容：**
  - **图片墙：** 取 `aw` 非空或年份最新的框架/主图约 40 张，分 4 行，倾斜 -4°。
  - **大标题**「顶会顶刊的图和表 / 拿来就能改」。
  - **一句话统计：** 来自 `stats`，例如「收录了 3,768 张框架图与主图、35 张实验图、188 个 LaTeX 表格」。
  - **胶囊搜索框：** 回车后跳到 `#/figures?q=`。
  - **常搜词：** 3 个领域加 1 个编号示例。
  - **领域胶囊行：** 显示各领域的条目数，点击跳到 `#/figures?d=key`。
  - **三张入口卡：** 每张拼贴 4 张真实缩略图，并显示条数。
  - **两条大图横带：**「最近新增」按编号倒序取 12 张图库条目；「有源码可直接改」取实验图和表格中 `ed !== 'none'` 的 12 条。
  - **页脚：** 版权说明，链接到 IMAGES_POLICY。
- `route.ts` 的路由：`#/`、`#/figures?d=&p=&v=&y=&ft=&ed=1&top=1&q=`、`#/experiments`、`#/tables`、`#/favorites`、`#/forge`；`#F036`、`#T042` 解析为 `{open: 'F036'}`。
- [ ] **测试：** vitest `route.test.ts` 覆盖解析与生成往返、旧链接 `#T042`、未知 hash 回落到首页。
- [ ] 实现，然后在浏览器检查首页并截图，和 c.png 对照：首屏墙、标题、搜索、胶囊、入口卡、横带都在；提交。

### Task 3: 图库页（筛选条 + 瀑布流）
**Files:** Create `src/lib/filter.ts`（`applyFilters(index, route) -> Item[]`、`facetCounts(items, key)`）、`src/components/FilterBar.tsx`、`src/components/Card.tsx`、`src/pages/Gallery.tsx`。
- **三个分区共用一个组件：**
  - 框架图：`cat=figure` 且 `grp` 为 framework 或 teaser。
  - 实验图：`grp=experiment`。
  - 表格：`cat=table`。表格卡片的图是宽图，用两列布局。
- **筛选条：**
  - 下拉：领域、研究问题（出现次数最多的 40 个，加搜索框）、会议、年份、图类型。
  - 开关：「有可编辑版或源码」「Oral / Best」。
  - 右侧显示计数。
- 筛选条件全部写进 hash，便于分享链接和返回。
- 瀑布流用 CSS columns；有 `ar` 时预留图片框高度，避免跳动。每页 60 张，滚动加载下一页（沿用 P1 的分页思路）。
- **卡片：** 缩略图、粉色「可编辑」贴纸、会议+年份、Best/Oral 标签、标题、悬停出现的收藏心形。
- 没有结果时显示空状态和「清除筛选」。
- [ ] **测试：** vitest `filter.test.ts`：
  - 多条件组合；q 能匹配标题、问题和编号（含 `F036` 精确匹配）。
  - `facetCounts` 的计数按其余已选条件计算。
  - 没有结果时返回 `[]`。
- [ ] 实现，然后在浏览器检查：领域加会议组合筛选、计数正确、hash 同步、返回键恢复筛选、空状态；提交。

### Task 4: 深色灯箱详情
**Files:** Create `src/components/Lightbox.tsx`、`src/lib/highlight.tsx`（从旧 App 中移出 LaTeX 和 Python 高亮）。
- **布局：** 左侧白底大图舞台，下方有「上一张 / 下一张」和同领域缩略条。右侧白色信息卡：
  - 标题、作者、会议与年份、领域和问题标签。
  - 链接：论文、PDF、代码、项目页、高清原图。
  - BibTeX 复制。
  - **可编辑区：**
    - 有 `editFiles` 时提供下载。
    - 表格和实验图有源码时，提供复制和下载（.tex/.py）按钮，并有可折叠的源码视图。
    - 两者都没有的图库条目，显示「重画成可编辑版」，说明可以用 `figtx-redraw-figure` skill，并给出命令和 README 链接。
  - 收藏按钮。
- **交互：** Esc 关闭，← → 翻页；打开时把 hash 设为 `#<no>`，关闭时恢复所在页面的路由。
- 详情加载中显示骨架屏；加载失败显示「详情加载失败，重试」。
- 删除旧组件残留的空「★」星标显示（P1 遗留的小问题）。
- [ ] **测试：** vitest 测试可编辑区三种分支的选择逻辑（抽成纯函数 `editableMode(detail)`）。
- [ ] 浏览器检查：`#F036` 直达，`#T042` 直达并显示源码和复制，← → 翻页，断网时（拦截 detail 请求）显示重试；提交。

### Task 5: 收藏
**Files:** Create `src/lib/favs.ts`（localStorage 键 `figtx:favs:v1`，内容 `{v: 1, items: {id: {addedAt, note}}}`；接口 `toggle`、`list`、`exportJson`、`importJson(text) -> {added, skipped} | throws`）、`src/pages/Favorites.tsx`（复用卡片和瀑布流；可编辑备注；导出和导入按钮）。
- 收藏在页头导航中显示计数徽标，各页通过 storage 事件同步。
- [ ] **测试：** vitest `favs.test.ts`：toggle 的往返；导出后再导入，结果一致；导入损坏的 JSON 或 `v ≠ 1` 时报错，且不改动已有收藏；导入时按 id 合并，跳过重复项。
- [ ] 实现，浏览器检查后提交。

### Task 6: 工作台、离线与清理
- 工作台（`#/forge`）沿用现有的 `Forge.tsx`，套进新外壳，样式来自 `forge.css`。
- 删除不再使用的代码：旧 App 的卡片、Modal、旧筛选逻辑；`src/data/items.json` 不再被前端 import。
- `make-offline.mjs` 和 `fix-html.mjs` 的流程保持可用。
- [ ] 运行 playwright：用 `file://` 打开 `dist/index.html`，检查首页、`#/figures`、打开灯箱，0 个页面错误；用 Pages 的路径（本地 preview 子路径）再跑一次；提交。

### Task 7: 验证、评审、PR
- [ ] 运行 `npm run test:web`、`npm run sync:test`、figtx-forge 的测试、`npx tsc --noEmit`、`npm run build`，全部通过。
- [ ] 在浏览器走一遍：首页 → 点领域胶囊 → 组合筛选 → 打开灯箱 → 收藏 → 收藏页 → 导出。在 1440、1024、390 三种宽度下截图，与 c.png 对照。
- [ ] 测量性能：首屏传输量（index.js 加主 JS）、切换分区的耗时（用 MutationObserver 测量）。
- [ ] 派一个全新的评审员评审整个分支，修复 Critical 和 Important 级别的问题（先写测试）。
- [ ] 推送并开 PR。CI 通过后合并（作者已授权：CI 通过即合并），然后确认 Pages 上线。

### Task 8: README 重写
- 在线上站点用 1440 宽度截 4 张图，存为 `docs/assets/` 下的 webp：首页首屏、图库筛选、灯箱详情、表格详情。
- **README 结构：**
  1. 顶部居中的 logo、一句定位、三个按钮（在线浏览、下载桌面版、在 Claude Code / Codex 里用），以及一张首屏大图。
  2. 数字条：框架图与主图、实验图、表格、可编辑版的数量。
  3. 「能做什么」：三栏，看图、拿走源码、一比一重画，各配一张截图。
  4. 快速开始。
  5. 在 Claude Code / Codex 里用（保留 P4 的内容并精简）。
  6. 图库同步与更新（`npm run sync`、每周 PR、下架方式）。
  7. 数据来源与致谢（topconf、PaperGallery、paper-plot-skills、AutoFigure），链接到 IMAGES_POLICY。
  8. 贡献、License。
- 删去过时的「编号与定位」长段落和旧截图引用；仍被用到的旧截图保留，不再用的删除。
- [ ] 在 GitHub 上预览渲染效果（推送后看 PR 的文件视图），提交。
