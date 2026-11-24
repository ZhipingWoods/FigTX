#!/usr/bin/env node
/**
 * 汇总 raw-items.json（表格）+ raw-figures.json（图）+ 渲染图 → src/data/items.json
 *
 *   node tools/build-data.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const ROOT = process.cwd();
const RAW_TABLES = path.join(ROOT, 'data/raw-items.json');
const RAW_FIGURES = path.join(ROOT, 'data/raw-figures.json');
const RAW_RECIPES = path.join(ROOT, 'data/raw-recipes.json');
const RAW_FIGS2 = path.join(ROOT, 'data/raw-figs2.json');
const RAW_REPLICAS = path.join(ROOT, 'data/raw-replicas.json');
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
const items = [...tables, ...figures];

const stats = {
  total: items.length,
  tables: tables.length,
  figures: figures.length,
  tableRender: tables.filter((i) => i.render).length,
  figureRender: figures.filter((i) => i.render).length,
  kinds: items.reduce((a, i) => ((a[i.kind] = (a[i.kind] || 0) + 1), a), {}),
  venues: items.reduce((a, i) => { for (const v of i.venues) a[v] = (a[v] || 0) + 1; return a; }, {}),
  repos: figures.reduce((a, i) => { if (i.source.repo) a[i.source.repo] = (a[i.source.repo] || 0) + 1; return a; }, {}),
  figTypes: figures.reduce((a, i) => ((a[i.figType] = (a[i.figType] || 0) + 1), a), {}),
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
