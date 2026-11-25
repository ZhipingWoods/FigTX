#!/usr/bin/env node
// 构建后处理：把 <script type="module"> 改成经典 defer 脚本。
//
// 为什么必须做：浏览器对 file:// 协议下的 module 脚本一律按 CORS 拦掉，
// 双击 dist/index.html 打开就是空白页。
// rollup 输出已改为 iife（经典脚本），去掉 type="module" 即可离线双击使用。
import fs from 'node:fs';
import path from 'node:path';

const DIST = path.join(process.cwd(), 'dist');
const HTML = path.join(DIST, 'index.html');

if (!fs.existsSync(HTML)) {
  console.error('[fix-html] 找不到 dist/index.html，先跑 vite build');
  process.exit(1);
}

let html = fs.readFileSync(HTML, 'utf8');

// 1) module 脚本 -> 经典 defer 脚本（保留 src 与样式表）
html = html.replace(
  /<script[^>]*type="module"[^>]*><\/script>/g,
  (tag) => {
    const m = tag.match(/src="([^"]+)"/);
    return m ? '<script defer src="' + m[1] + '"></script>' : '';
  },
);

// 2) 只删 modulepreload，绝不碰 stylesheet
html = html.replace(/<link[^>]*rel="modulepreload"[^>]*>/g, '');

// 3) crossorigin 在 file:// 下无意义，去掉
html = html.replace(/\s+crossorigin(?==|\s|>)/g, '');

// 4) script 挪到 </body> 前（defer 语义）
const sm = html.match(/<script defer src="[^"]+"><\/script>/);
if (sm) {
  html = html.replace(sm[0], '');
  html = html.replace('</body>', '  ' + sm[0] + '\n  </body>');
}

fs.writeFileSync(HTML, html);

if (/type="module"/.test(html)) {
  console.error('[fix-html] 警告：仍存在 type="module"');
  process.exit(1);
}
// 注意：iife 打包时 Vite 会把 CSS 内联进 JS（不产出独立 .css），
// 这是好事 —— 离线只需要 index.js 一个文件。
// 只有在既没有 <link rel=stylesheet> 也没有内联 CSS 时才报错。
const hasInlineCss = fs
  .readdirSync(path.join(DIST, 'assets'))
  .some((f) => f.endsWith('.js') && /\.no-badge|card-preview/.test(fs.readFileSync(path.join(DIST, 'assets', f), 'utf8')));
if (!/rel="stylesheet"/.test(html) && !hasInlineCss) {
  console.error('[fix-html] 警告：样式丢失（既无 link 也无内联）');
  process.exit(1);
}
console.log('[fix-html] OK: 经典脚本（CSS 已内联，file:// 可直接双击打开）');
