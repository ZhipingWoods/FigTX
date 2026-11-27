#!/usr/bin/env node
/**
 * 汇总 raw-items.json（表格）+ raw-figures.json（图）+ 渲染图 → src/data/items.json
 *
 *   node tools/build-data.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { SHARDS, shardOf, pad } from './shard.mjs';

const ROOT = process.cwd();
const RAW_TABLES = path.join(ROOT, 'data/raw-items.json');
const RAW_FIGURES = path.join(ROOT, 'data/raw-figures.json');
const RAW_RECIPES = path.join(ROOT, 'data/raw-recipes.json');
const RAW_FIGS2 = path.join(ROOT, 'data/raw-figs2.json');
const RAW_REPLICAS = path.join(ROOT, 'data/raw-replicas.json');
const RAW_GALLERY = path.join(ROOT, 'data/raw-gallery.json');
const TAGS_FILE = path.join(ROOT, 'data/tags.json');
const ASSET_MANIFEST = path.join(ROOT, 'data/sources/assets-manifest.json');
const THUMBS = path.join(ROOT, 'public/thumbs');
// 与 tools/sync/push_assets.py 的 REPO_ID 保持一致
const HF_ORIGINALS = 'https://huggingface.co/datasets/OliverThompson/figtx-assets/resolve/main/originals/';
const REPAIRED_FILE = path.join(ROOT, 'data/table-repaired.json');
const CATALOG_FILE = path.join(ROOT, 'data/catalog.json');

// 稳定编号：T001-T999 表格 / F001-F999 图（存在 catalog.json 里，增删不重排）
const CATALOG = (() => {
  try { return JSON.parse(fs.readFileSync(CATALOG_FILE, 'utf8')); }
  catch { return {}; }
})();
const catalogNo = (id) => (CATALOG[id] && CATALOG[id].no) || null;

// 自动修复渲染的表：源码是残缺片段，渲染时走了降级策略（卡片上标注出来）
const REPAIRED = (() => {
  try {
    const rows = JSON.parse(fs.readFileSync(REPAIRED_FILE, 'utf8'));
    const LABEL = {
      'tabular-only': '已自动修复 · 只渲染表格本体',
      'plain-cells': '已自动修复 · 剥离自定义宏后渲染',
      'plain-cells-forced': '已自动修复 · 文档级冲突，改用纯文本单元格',
    };
    const map = {};
    for (const r of rows) map[r.id] = LABEL[r.stage] || '已自动修复';
    return map;
  } catch {
    return {};
  }
})();
const RENDERS = path.join(ROOT, 'public/renders');
const RENDERS_FIG = path.join(ROOT, 'public/renders-fig');
const OUT = path.join(ROOT, 'src/data/items.json');

const readJson = (p, fallback) => (fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : fallback);
const listDir = (p) => (fs.existsSync(p) ? new Set(fs.readdirSync(p)) : new Set());

const rawTables = readJson(RAW_TABLES, []);
const rawFigures = readJson(RAW_FIGURES, [])
  .concat(readJson(RAW_RECIPES, []))
  .concat(readJson(RAW_FIGS2, []))
  .concat(readJson(RAW_REPLICAS, []));
const renderFiles = listDir(RENDERS);
const figFiles = listDir(RENDERS_FIG);

function findIn(dirSet, prefix, id) {
  for (const ext of ['.webp', '.png']) {
    if (dirSet.has(id + ext)) return prefix + id + ext;
  }
  return null;
}

/** 归一化：压掉空白差异，用于识别「同一段代码的两份拷贝」 */
const fingerprint = (code) => crypto.createHash('sha1').update(code.replace(/\s+/g, ' ').trim()).digest('hex');

/* ---------------------------------------------------------------- 表格 */

const seen = new Map();
const tables = [];
let dropped = 0;

for (const it of rawTables) {
  const fp = fingerprint(it.latex || '');
  const render = findIn(renderFiles, 'renders/', it.id);
  if (seen.has(fp)) {
    const prev = seen.get(fp);
    // 保留元数据更完整 / 有渲染图的那一份
    const better = (render && !prev.render) || (!render && prev.render === null && (it.title || '').length > (prev.title || '').length);
    if (!better) { dropped++; continue; }
    tables.splice(tables.findIndex((t) => t.id === prev.id), 1);
    dropped++;
  }
  const item = {
    id: it.id,
    category: 'table',
    no: catalogNo(it.id),
    // 源码残缺、渲染时走了降级策略的表，在卡片上标注
    repaired: Object.prototype.hasOwnProperty.call(REPAIRED, it.id)
      ? REPAIRED[it.id]
      : null,
    kind: it.kind === 'table' || it.kind === 'mixed' ? 'table' : it.kind,
    title: it.title || '',
    caption: it.caption || '',
    venues: it.venues || [],
    year: it.year || null,
    tags: (it.tags || []).filter((t) => !/^#?latex表格$/.test(t)).slice(0, 6),
    number: it.number ?? null,
    palette: (it.palette || []).slice(0, 6),
    code: it.latex || '',
    codeLang: 'latex',
    render,
    noteImages: [],
    publishedAt: it.publishedAt ? new Date(it.publishedAt * 1000).toISOString().slice(0, 10) : null,
    source: { platform: 'paper', author: '', repo: null, repoUrl: null, license: null },
  };
  seen.set(fp, item);
  tables.push(item);
}

/* ---------------------------------------------------------------- 图 */

const figures = rawFigures.map((it) => ({
  id: it.id,
  category: 'figure',
  no: catalogNo(it.id),
  // 图的二级分类：framework / motivation / quantitative / qualitative
  figType: it.figType || 'style',
  group: it.group || null,
  kind: it.kind || 'chart',
  title: it.title || '',
  caption: it.caption || '',
  domain: it.domain || [],
  venues: it.venues || [],
  year: null,
  tags: (it.styles || []).filter((s) => s !== 'no-latex'),
  number: null,
  palette: (it.palette || []).slice(0, 6),
  code: it.code || '',
  codeLang: it.codeLang || 'python',
  render: findIn(figFiles, 'renders-fig/', it.id) || it.render || null,
  repaired: Object.prototype.hasOwnProperty.call(REPAIRED, it.id)
    ? REPAIRED[it.id]
    : null,
  editFiles: it.editFiles || [],
  noteImages: [],
  publishedAt: null,
  source: {
    platform: it.source?.repo ? 'github' : 'origin',
    author: it.source?.repo || '',
    repo: it.source?.repo || null,
    repoUrl: it.source?.repoUrl || null,
    license: it.source?.license || null,
    stars: it.source?.stars || 0,
    path: it.source?.path || null,
  },
}));

tables.sort((a, b) => (b.number ?? -1) - (a.number ?? -1));
// 图：论文复刻（replicas）排前面，其余按原顺序
const FIG_ORDER = ['efficiency', 'architecture', 'mechanism', 'tradeoff', 'results',
                   'motivation', 'quantitative', 'qualitative', 'framework', 'style'];
figures.sort((a, b) => {
  const ia = a.group === 'replicas' ? -1 : FIG_ORDER.indexOf(a.figType);
  const ib = b.group === 'replicas' ? -1 : FIG_ORDER.indexOf(b.figType);
  return ia - ib;
});
/* ---------------------------------------------------------------- 图库（topconf / PaperGallery 等，由 npm run sync 生成） */

const SOURCE_NAME = { topconf: 'topconf-paper-figure-gallery', papergallery: 'PaperGallery', journal: '期刊' };
const TAGS = readJson(TAGS_FILE, {});
const MANIFEST = readJson(ASSET_MANIFEST, {});
const thumbFiles = listDir(THUMBS);
const gallery = readJson(RAW_GALLERY, [])
  .filter((g) => thumbFiles.has(g.id + '.webp'))
  .map((g) => {
    const tag = TAGS[g.id] || {};
    const asset = MANIFEST[g.id];
    const first = g.sources[0] || {};
    return {
      id: g.id,
      category: 'figure',
      no: catalogNo(g.id),
      figType: g.figType,
      group: 'gallery',
      kind: 'diagram',
      title: g.title || '',
      caption: '',
      domain: [],
      domains: tag.domains || [],
      problems: tag.problems || [],
      venues: g.paper.venue && g.paper.venue !== 'Unknown' ? [g.paper.venue] : [],
      year: g.paper.year || null,
      tags: g.tags || [],
      number: null,
      palette: [],
      code: '',
      codeLang: null,
      render: 'thumbs/' + g.id + '.webp',
      original: asset && asset.uploaded ? HF_ORIGINALS + g.id + '.' + asset.ext : null,
      editableStatus: 'original-only',
      paper: g.paper,
      sources: g.sources,
      repaired: null,
      editFiles: [],
      noteImages: [],
      publishedAt: null,
      source: { platform: first.platform || 'gallery', author: '', repo: SOURCE_NAME[first.platform] || first.platform || null, repoUrl: first.repo || null, license: null },
    };
  })
  .sort((a, b) => (b.year || 0) - (a.year || 0) || a.id.localeCompare(b.id));

const items = [...tables, ...figures, ...gallery];

const stats = {
  total: items.length,
  tables: tables.length,
  figures: figures.length + gallery.length,
  gallery: gallery.length,
  sources: gallery.reduce((a, i) => { for (const src of i.sources) a[src.platform] = (a[src.platform] || 0) + 1; return a; }, {}),
  tableRender: tables.filter((i) => i.render).length,
  figureRender: figures.filter((i) => i.render).length + gallery.length,
  kinds: items.reduce((a, i) => ((a[i.kind] = (a[i.kind] || 0) + 1), a), {}),
  venues: items.reduce((a, i) => { for (const v of i.venues) a[v] = (a[v] || 0) + 1; return a; }, {}),
  repos: figures.reduce((a, i) => { if (i.source.repo) a[i.source.repo] = (a[i.source.repo] || 0) + 1; return a; }, {}),
  figTypes: [...figures, ...gallery].reduce((a, i) => ((a[i.figType] = (a[i.figType] || 0) + 1), a), {}),
  domains: figures.reduce((a, i) => { for (const d of i.domain || []) a[d] = (a[d] || 0) + 1; return a; }, {}),
  generatedAt: new Date().toISOString(),
};

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify({ stats, items }));
const bytes = fs.statSync(OUT).size;
console.log(
  'items=' + items.length + ' (表格 ' + tables.length + ' / 图 ' + figures.length + ')' +
  ' 去重丢弃 ' + dropped + ' -> ' + path.relative(ROOT, OUT) + ' (' + (bytes / 1024).toFixed(1) + ' KB)',
);
console.log('表格已渲染:', stats.tableRender, '/', tables.length, ' 图已渲染:', stats.figureRender, '/', figures.length);

// 精简索引：给 figtx search / skills / 首页检索用（不含代码，体积小）
const INDEX_OUT = path.join(ROOT, 'public/index.json');
const index = {
  v: 1,
  generatedAt: stats.generatedAt,
  base: 'https://zhipingwoods.github.io/FigTX/',
  items: items.map((it) => ({
    id: it.id,
    no: it.no || null,
    category: it.category,
    figType: it.figType || null,
    kind: it.kind || null,
    title: it.title || '',
    caption: (it.caption || '').slice(0, 200),
    venues: it.venues || [],
    year: it.year || null,
    domains: it.domains || it.domain || [],
    problems: it.problems || [],
    tags: it.tags || [],
    preview: it.render || null,
    paper: (it.paper && it.paper.url) || it.source?.repoUrl || null,
  })),
};
fs.writeFileSync(INDEX_OUT, JSON.stringify(index));
console.log('index.json:', index.items.length, '条 ->', path.relative(ROOT, INDEX_OUT), '(' + (fs.statSync(INDEX_OUT).size / 1024).toFixed(1) + ' KB)');

// ---------------------------------------------------------------- 前端用：精简索引 + 详情分片
// 用 <script> 加载（不是 fetch），所以 file:// 双击打开、Pages、Electron 都能用。
const TAXONOMY = readJson(path.join(ROOT, 'data/taxonomy.json'), { domains: [], figTypeGroups: {} });
const GROUP_OF = {};
for (const [g, types] of Object.entries(TAXONOMY.figTypeGroups || {})) for (const t of types) GROUP_OF[t] = g;
const groupOf = (it) => (it.category === 'table' ? 'table' : GROUP_OF[it.figType] || 'experiment');
const editableOf = (it) =>
  it.editableStatus === 'editable' || (it.editFiles && it.editFiles.length) ? 'editable' : it.code ? 'code' : 'none';

const lite = items.map((it) => {
  const asset = MANIFEST[it.id];
  const title = it.category === 'table' ? it.caption || it.title : it.title || it.caption;
  const row = {
    id: it.id, no: it.no || null, cat: it.category, ft: it.figType || null, grp: groupOf(it),
    t: (title || '').slice(0, 220), v: it.venues || [], y: it.year || null,
    d: it.domains || [], p: it.problems || [], r: it.render || null, ed: editableOf(it),
    aw: (it.paper && (it.paper.award || it.paper.tier)) || null,
    src: (it.sources && it.sources[0] && it.sources[0].platform) || 'figtx',
  };
  if (asset && asset.w && asset.h) row.ar = asset.w / asset.h;
  // 缩略图路径是 thumbs/<id>.webp 时省略（前端按 id 还原），给首屏索引减重
  if (row.r === 'thumbs/' + it.id + '.webp') delete row.r;
  if (!row.d.length) delete row.d;
  if (!row.p.length) delete row.p;
  if (!row.v.length) delete row.v;
  if (!row.aw) delete row.aw;
  return row;
});

const DATA_DIR = path.join(ROOT, 'public/data');
fs.rmSync(DATA_DIR, { recursive: true, force: true });
fs.mkdirSync(DATA_DIR, { recursive: true });
const liteIndex = {
  v: 1, generatedAt: stats.generatedAt, stats,
  taxonomy: TAXONOMY.domains || [], items: lite,
};
fs.writeFileSync(path.join(DATA_DIR, 'index.js'), 'window.__FIGTX_INDEX__=' + JSON.stringify(liteIndex) + ';\n');
const shards = Array.from({ length: SHARDS }, () => ({}));
for (const it of items) shards[shardOf(it.id)][it.id] = it;
shards.forEach((obj, n) => {
  fs.writeFileSync(path.join(DATA_DIR, 'detail-' + pad(n) + '.js'), 'window.__figtxDetail(' + n + ',' + JSON.stringify(obj) + ');\n');
});
console.log('data/index.js:', lite.length, '条 (' + (fs.statSync(path.join(DATA_DIR, 'index.js')).size / 1024).toFixed(1) + ' KB) + ' + SHARDS + ' 个详情分片');
