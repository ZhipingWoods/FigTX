<div align="center">

# FigTX

**论文图表 LaTeX 样式库 · 看得见的表格与图**

[![Pages](https://img.shields.io/badge/demo-GitHub%20Pages-b91c1c)](https://zhipingwoods.github.io/FigTX/)
[![Release](https://img.shields.io/github/v/release/ZhipingWoods/FigTX?color=b91c1c)](https://github.com/ZhipingWoods/FigTX/releases)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

macOS · Windows · Linux · Web

</div>

---

## 这是什么

写论文时最耗时的不是想清楚结果，而是把表格调到"能看"。三线表、跨列表头、
分组底色、加粗最优值、箭头标注……每种都要试半天。

**FigTX 把这些一次收集齐**，每个样式都带：

- **真实渲染图** —— 用 `tectonic` 把源码重新编译成图片，所见即所得
- **完整 LaTeX 源码** —— 一键复制 / 下载 `.tex`
- **配色板** —— 自动抽取样式里用到的十六进制颜色
- **元信息** —— 会议、caption、行数、来源笔记

打开就能浏览、搜索、筛选，选中样式直接复制进自己的论文。

## 快速开始

### 桌面版（推荐）

到 [Releases](https://github.com/ZhipingWoods/FigTX/releases) 下载对应平台安装包：

| 平台 | 文件 |
|---|---|
| macOS (Apple Silicon) | `FigTX-<version>-arm64.dmg` |
| macOS (Intel) | `FigTX-<version>-x64.dmg` |
| Windows | `FigTX-Setup-<version>-x64.exe` |
| Linux | `FigTX-<version>-x86_64.AppImage` / `.deb` |

### 网页版

直接访问 **https://zhipingwoods.github.io/FigTX/**

### 本地开发

```bash
git clone git@github.com:ZhipingWoods/FigTX.git
cd FigTX
npm install
npm run dev          # 浏览器 http://localhost:5173
npm run electron:dev # 桌面窗口
```

## 打包

```bash
npm run dist:mac     # .dmg + .zip (arm64 & x64)
npm run dist:win     # NSIS 安装包 + 便携版
npm run dist:linux   # AppImage + deb
```

产物输出到 `release/`。CI 也会在三平台自动构建，见 `.github/workflows/release.yml`。

## 数据是怎么来的

```
小红书笔记 ──► docx 附件 ──► LaTeX 源码 ──► tectonic 编译 ──► 预览图
                  │                                            │
                  └──────────► 笔记配图 ────────────────────────┘
```

| 脚本 | 作用 |
|---|---|
| `tools/extract_docx.py` | 从 `.docx` 抽取 LaTeX、识别表格/图、抽配色 |
| `tools/render_tex.py` | tectonic 编译 + 自动修复片段 + 转 WebP |
| `tools/fetch_images.py` | 下载原笔记配图作为兜底预览 |
| `tools/build-data.mjs` | 汇总成 `src/data/items.json` |

```bash
python3 tools/extract_docx.py --docx-dir <docx目录> --notes <notes.json> --out .
python3 tools/render_tex.py --items data/raw-items.json --out public/renders
python3 tools/fetch_images.py --items data/raw-items.json --out public/note-images
node tools/build-data.mjs
```

> 渲染依赖：[tectonic](https://tectonic-typesetting.github.io/)（必装）、
> poppler / cwebp（可选；macOS 会自动退回系统 `qlmanage`）。

## 扩展新的数据源

`data/raw-items.json` 是唯一的数据契约，任何来源只要转成这个结构即可合并：

```json
{
  "id": "table-276",
  "kind": "table",
  "title": "overleaf 中顶会顶刊 latex 表格绘制-（276）",
  "caption": "Main Results on CoPHEME Dataset.",
  "latex": "\\begin{table*}...",
  "latexFile": "data/latex/table-276.tex",
  "palette": ["#EEF2F5", "#F7F3E8"],
  "venues": ["ACL"],
  "year": 2026,
  "images": ["https://.../note-cover.webp"],
  "noteId": "6b04e12c000000002500be5c",
  "docId": "7711535982676015286"
}
```

计划支持的来源见 [Roadmap](docs/wiki/Roadmap.md)。

## 目录结构

```
FigTX/
├── src/                 # React 前端（Vite）
│   ├── App.tsx
│   ├── styles.css
│   └── data/items.json  # 构建产物，不要手改
├── electron/            # 桌面端外壳
├── tools/               # 数据管线
├── data/
│   ├── raw-items.json   # 中间产物
│   └── latex/*.tex      # 抽取出的源码
├── public/
│   ├── renders/         # tectonic 渲染图 (webp)
│   └── note-images/     # 原笔记配图
├── docs/wiki/           # Wiki 源文件
└── .github/workflows/   # CI：Pages + 三平台 release
```

## 数据来源与许可

样式来源于公开分享的论文 LaTeX 片段，本项目只做**收集、索引与展示**，
用于学习与写作参考。单个样式的版权归属原作者 / 原论文。

代码以 [Apache-2.0](LICENSE) 发布。

## 相关文档

- [使用手册](docs/wiki/使用手册.md)
- [样式分类](docs/wiki/样式分类.md)
- [贡献指南](docs/wiki/贡献指南.md)
- [数据管线](docs/wiki/数据管线.md)
