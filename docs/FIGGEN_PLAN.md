# FigTX 图生成能力整合方案

## 已验证的事实（本轮实测）
- 内网 API 可用：https://llm-center.modelbest.co/v1/chat/completions
- 多模态可用（能读懂我们的渲染图，描述准确）
- **SVG 生成可用**：GPT_svn19r 直接产出可用的论文 Figure 1
  - 35 个 <text>、84 个 data-editable、0 mask/filter、viewBox 正确、0 中文
  - 质量：完整 A/B 双面板 + 图例 + 放大 inset + 专业配色
- 推理模型（deepseek-v4.1-flash-mb）会把 token 全花在 reasoning 上，不适合长 SVG 输出
- 部分模型会截断输出（GEMINI 只画 3 个面板、GROK 右侧溢出）

## 三个项目可吸收的点

### 1. AutoFigure (ICLR 2026, ResearAI)
- **Review-Refine 双 agent 循环** ← 核心机制
  Generate → Evaluate(打分 0-10 + 具体反馈) → Refine → 直到达标
- FigureBench 3300 对数据（HuggingFace WestlakeNLP/FigureBench）
- 输出 SVG + mxGraph XML（draw.io 兼容）
- 关键提示词：editable export contract（id/data-role/data-editable）
- **我们的适配**：provider 抽象层要支持自定义 base_url（它只支持 openrouter/gemini/bianxie）

### 2. topconf-paper-figure-gallery
- **设计契约（design contract）提取** ← 最值得学
  - 不写"简洁优雅"，而是精确测量：palette 色值、typography 字号层级、
    strokes 线宽、density（容器数/模块数/箭头数/填充率）、
    topology（anchor/zones/flow/spacing）、layoutBlueprint（zone 的 x/y/w/h）
  - 注释原话："Prose like 'restrained palette, clear hierarchy' leaves every
    concrete decision to the generator, which is where style drift comes from"
- 3452 张真实顶会主图库，按 venue/year/pattern 筛选
- 输出 SVG/PPTX/VSDX/draw.io 四格式

### 3. PaperGallery (LongHZ140516)
- 分类方式：images/header（teaser）vs images/pipeline（框架图）← 值得借鉴的划分
- tools/colors 配色工具、tools/icons 图标库
- tools/repository 资源库
- project/examples + project/templates

## 实施路线

### Phase A：生成内核（不依赖前端）
tools/figgen/
  - llm_client.py      OpenAI 兼容客户端（读 .env 里的 key，不硬编码）
  - contract.py        设计契约：从参考图提取精确参数
  - generate.py        Generate → Evaluate → Refine 循环
  - prompts.py         提示词模板（editable export contract）
  - render.py          SVG → PNG（playwright）
  
### Phase B：参考图库
- 从现有 10 张论文复刻图提取设计契约
- 分类参照 PaperGallery：header / pipeline / result / motivation
- 每张图配 contract JSON

### Phase C：接入 FigTX
- 新增「生成」页签
- 选参考图 → 自动带出设计契约 → 调 LLM 生成 → 预览 → 下载 SVG
- key 从本地配置读，不入库

## 安全
- API key 放 .env（已在 .gitignore）
- 前端不硬编码 key
