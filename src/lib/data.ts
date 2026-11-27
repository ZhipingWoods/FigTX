/**
 * 前端数据：首屏只加载精简索引（public/data/index.js），详情按 64 个分片按需加载（detail-NN.js）。
 * 用 <script> 注入而不是 fetch：file:// 双击打开、GitHub Pages、Electron 下都能用。
 */
import { pad, shardOf } from '../../tools/shard.mjs';

export type Lite = {
  id: string;
  no: string | null;
  cat: 'figure' | 'table';
  ft: string | null;
  grp: 'framework' | 'teaser' | 'experiment' | 'table';
  t: string;
  v?: string[];
  y: number | null;
  d?: string[];
  p?: string[];
  r?: string;
  ar?: number;
  ed: 'editable' | 'code' | 'none';
  aw?: string;
  src: string;
};

export type Domain = { key: string; zh: string; en: string };

export type Index = {
  v: number;
  generatedAt: string;
  stats: Record<string, any>;
  taxonomy: Domain[];
  items: Lite[];
};

export type Detail = Record<string, any> & { id: string };

type Loader = (url: string) => Promise<void>;

const BASE = './data/';

function domLoader(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = url;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => {
      s.remove();
      reject(new Error('加载失败：' + url));
    };
    document.head.appendChild(s);
  });
}

let loader: Loader = domLoader;
let indexP: Promise<Index> | null = null;
const shards = new Map<number, Record<string, Detail>>();
const pending = new Map<number, Promise<void>>();

function installHook() {
  if (typeof window !== 'undefined') {
    (window as any).__figtxDetail = (n: number, obj: Record<string, Detail>) => shards.set(n, obj);
  }
}
installHook();

/** 测试用：替换脚本加载方式。 */
export function setScriptLoader(fn: Loader) {
  loader = fn;
}

/** 测试用：清空缓存。 */
export function _reset() {
  indexP = null;
  shards.clear();
  pending.clear();
  if (typeof window !== 'undefined') delete (window as any).__FIGTX_INDEX__;
  installHook();
}

export function loadIndex(): Promise<Index> {
  if (!indexP) {
    indexP = loader(BASE + 'index.js')
      .then(() => {
        const idx = (window as any).__FIGTX_INDEX__ as Index | undefined;
        if (!idx) throw new Error('索引格式不对');
        return idx;
      })
      .catch((e) => {
        indexP = null;
        throw e;
      });
  }
  return indexP;
}

export async function loadDetail(id: string): Promise<Detail> {
  const n = shardOf(id);
  if (!shards.has(n)) {
    if (!pending.has(n)) {
      pending.set(n, loader(BASE + 'detail-' + pad(n) + '.js').finally(() => pending.delete(n)));
    }
    await pending.get(n);
  }
  const d = shards.get(n)?.[id];
  if (!d) throw new Error('not found: ' + id);
  return d;
}

export const thumbOf = (it: Pick<Lite, 'id' | 'r'>) => it.r || `thumbs/${it.id}.webp`;
