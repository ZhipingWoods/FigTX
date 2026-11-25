#!/usr/bin/env node
// 生成离线 Web 包：dist/ + 使用说明，打包成 zip。
// 给不想装桌面端、也不想联网的人：解压后双击 index.html 即可。
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const ROOT = process.cwd();
const DIST = path.join(ROOT, 'dist');
const OUT = path.join(ROOT, 'release-web');
const STAGE = path.join(OUT, 'FigTX-offline');

if (!fs.existsSync(path.join(DIST, 'index.html'))) {
  console.error('先跑 npm run build');
  process.exit(1);
}

fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(STAGE, { recursive: true });
fs.cpSync(DIST, STAGE, { recursive: true });

fs.writeFileSync(
  path.join(STAGE, '使用说明.txt'),
  [
    'FigTX 离线版',
    '============',
    '',
    '双击 index.html 即可在浏览器中打开，无需联网、无需安装任何软件。',
    '',
    '包含内容：',
    '  - LaTeX 表格样式（全部有真实渲染预览）',
    '  - 图样式（期刊样式 / 动机图 / 实验图 / 论文复刻）',
    '  - 每个条目有编号 T001+ / F001+，可在搜索框直接输入编号定位',
    '',
    '使用方式：',
    '  1. 双击 index.html',
    '  2. 搜索框输入编号（如 T042）可直接定位',
    '  3. 点开卡片可查看渲染细节、复制 LaTeX 源码',
    '',
    '离线说明：本目录所有资源都在本地，不会发起任何网络请求。',
    '',
  ].join('\n'),
  'utf8',
);

const zip = path.join(OUT, 'FigTX-offline-web.zip');
execFileSync('zip', ['-qr', zip, 'FigTX-offline'], { cwd: OUT });

const mb = (fs.statSync(zip).size / 1048576).toFixed(0);
console.log('[offline] ' + path.relative(ROOT, zip) + '  ' + mb + ' MB');
