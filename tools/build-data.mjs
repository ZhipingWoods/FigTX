#!/usr/bin/env node
/**
 * 汇总 raw-items.json + 渲染图 + 笔记配图 → src/data/items.json
 *
 *   node tools/build-data.mjs
 */
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const RAW = path.join(ROOT, 'data/raw-items.json');
const RENDERS = path.join(ROOT, 'public/renders');
const NOTE_IMGS = path.join(ROOT, 'public/note-images');
const OUT = path.join(ROOT, 'src/data/items.json');

const raw = JSON.parse(fs.readFileSync(RAW, 'utf8'));
const renderFiles = new Set(fs.existsSync(RENDERS) ? fs.readdirSync(RENDERS) : []);
const noteFiles = new Set(fs.existsSync(NOTE_IMGS) ? fs.readdirSync(NOTE_IMGS) : []);

function findRender(id) {
  for (const ext of ['.webp', '.png']) {
    if (renderFiles.has(id + ext)) return 'renders/' + id + ext;
  }
  return null;
}

function findNoteImages(id) {
  return [...noteFiles]
    .filter((f) => f.startsWith(id + '-'))
    .sort((a, b) => {
      const na = Number(a.match(/-(\d+)\./)?.[1] ?? 0);
      const nb = Number(b.match(/-(\d+)\./)?.[1] ?? 0);
      return na - nb;
    })
    .map((f) => 'note-images/' + f);
}

const items = raw.map((it) => {
  const render = findRender(it.id);
  const noteImages = findNoteImages(it.id);
  const publishedAt = it.publishedAt ? new Date(it.publishedAt * 1000).toISOString().slice(0, 10) : null;
  return {
    id: it.id,
    kind: it.kind,
    title: it.title || '',
    caption: it.caption || '',
    venues: it.venues || [],
    year: it.year || null,
    tags: (it.tags || []).filter((t) => !/^#?latex表格$/.test(t)).slice(0, 6),
    number: it.number ?? null,
    palette: (it.palette || []).slice(0, 6),
    latexFile: it.latexFile,
    render,
    noteImages,
    publishedAt,
    source: {
      platform: 'xiaohongshu',
      author: '爱芝芝爱科研',
      noteId: it.noteId,
      docId: it.docId,
      noteUrl: it.noteId ? 'https://www.xiaohongshu.com/explore/' + it.noteId : null,
    },
  };
});

items.sort((a, b) => (b.number ?? -1) - (a.number ?? -1));

const stats = {
  total: items.length,
  withRender: items.filter((i) => i.render).length,
  withImages: items.filter((i) => i.noteImages.length).length,
  kinds: items.reduce((acc, i) => ((acc[i.kind] = (acc[i.kind] || 0) + 1), acc), {}),
  venues: items.reduce((acc, i) => {
    for (const v of i.venues) acc[v] = (acc[v] || 0) + 1;
    return acc;
  }, {}),
  generatedAt: new Date().toISOString(),
};

// 把 LaTeX 正文一并内联，前端无需额外请求（Electron file:// 也能用）
for (const it of items) {
  const p = path.join(ROOT, it.latexFile);
  it.latex = fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : '';
}

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify({ stats, items }, null, 0));

const bytes = fs.statSync(OUT).size;
console.log(
  'items=' + stats.total + ' render=' + stats.withRender + ' images=' + stats.withImages +
  ' -> ' + path.relative(ROOT, OUT) + ' (' + (bytes / 1024).toFixed(1) + ' KB)',
);
console.log('venues:', Object.entries(stats.venues).sort((a, b) => b[1] - a[1]).slice(0, 10));
