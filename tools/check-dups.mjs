#!/usr/bin/env node
/**
 * 检查渲染图是否重复（感知哈希 dHash）。
 *
 * 背景：表格能按 LaTeX 源码哈希判重，但图没有源码可比。
 * SciencePlots 那 16 个样式变体渲染出来 dHash 距离 0-4，属实质重复，
 * 之前没有任何环节能发现——16 张几乎一样的卡片在库里挂了两周。
 *
 * 用法：node tools/check-dups.mjs [阈值，默认 4]
 * 退出码：0 = 无重复，1 = 有重复组
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const THRESH = Number(process.argv[2] || 4);
const ITEMS = path.join(ROOT, 'src', 'data', 'items.json');

const data = JSON.parse(fs.readFileSync(ITEMS, 'utf8'));
const figs = data.items.filter((i) => i.category === 'figure' && i.render);
if (!figs.length) { console.log('没有可检查的图'); process.exit(0); }

const PY = [
  'import json,sys',
  'from PIL import Image',
  'import numpy as np',
  'def dh(p,s=8):',
  '    im=Image.open(p).convert("L").resize((s+1,s),Image.LANCZOS)',
  '    a=np.asarray(im,dtype=np.int16)',
  '    return [int(b) for b in (a[:,1:]>a[:,:-1]).flatten()]',
  'data=json.loads(sys.stdin.read())',
  'out={}',
  'for k,v in data.items():',
  '    try: out[k]=dh(v)',
  '    except Exception: out[k]=None',
  'print(json.dumps(out))',
].join('\n');

const input = JSON.stringify(Object.fromEntries(
  figs.map((i) => [i.id, path.join(ROOT, 'public', i.render)])));

const py = path.join(ROOT, '.venv-fig', 'bin', 'python');
let hashes;
try {
  hashes = JSON.parse(execFileSync(py, ['-c', PY], {
    input, encoding: 'utf8', maxBuffer: 16 << 20, cwd: ROOT,
  }));
} catch (e) {
  console.error('哈希计算失败（需要 .venv-fig 里有 PIL/numpy）:', String(e.message).slice(0, 120));
  process.exit(2);
}

const ids = Object.keys(hashes).filter((k) => hashes[k]);
const used = new Set();
const groups = [];
for (let a = 0; a < ids.length; a++) {
  if (used.has(ids[a])) continue;
  const grp = [ids[a]];
  for (let b = a + 1; b < ids.length; b++) {
    if (used.has(ids[b])) continue;
    let hd = 0;
    for (let i = 0; i < 64; i++) if (hashes[ids[a]][i] !== hashes[ids[b]][i]) hd++;
    if (hd <= THRESH) { grp.push(ids[b]); used.add(ids[b]); }
  }
  if (grp.length > 1) { used.add(ids[a]); groups.push(grp); }
}

console.log('检查 ' + ids.length + ' 张图，阈值 dHash<=' + THRESH);
if (!groups.length) { console.log('✓ 没有近乎重复的图'); process.exit(0); }
console.log('⚠ 发现 ' + groups.length + ' 组近乎重复：');
for (const g of groups) console.log('   ' + g.join(' ≈ '));
console.log('\n建议：合并成一张对比图/画廊，或删掉多余的。');
process.exit(1);
