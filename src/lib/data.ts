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
// 缓存失效：index.js 带构建号，详情分片带索引的生成时间，避免新旧数据混用
declare const __BUILD_ID__: string | undefined;
const BUILD = typeof __BUILD_ID__ !== 'undefined' ? __BUILD_ID__ : '';
let dataVersion = '';
const withV = (url: string, v: string) => (v ? url + '?v=' + encodeURIComponent(v) : url);

function domLoader(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = url;
    s.async = true;
    // 动态插入的脚本默认是低优先级，会排在几十张缩略图后面（实测线上要等 20 秒）；数据脚本要优先
    (s as HTMLScriptElement & { fetchPriority?: string }).fetchPriority = 'high';
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
  dataVersion = '';
  shards.clear();
  pending.clear();
  if (typeof window !== 'undefined') delete (window as any).__FIGTX_INDEX__;
  installHook();
}

export function loadIndex(): Promise<Index> {
  if (!indexP) {
    indexP = loader(withV(BASE + 'index.js', BUILD))
      .then(() => {
        const idx = (window as any).__FIGTX_INDEX__ as Index | undefined;
        if (!idx) throw new Error('索引格式不对');
        dataVersion = idx.generatedAt || '';
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
      pending.set(n, loader(withV(BASE + 'detail-' + pad(n) + '.js', dataVersion)).finally(() => pending.delete(n)));
    }
    await pending.get(n);
  }
  const d = shards.get(n)?.[id];
  if (!d) throw new Error('not found: ' + id);
  return d;
}

export const thumbOf = (it: Pick<Lite, 'id' | 'r'>) => it.r || `thumbs/${it.id}.webp`;

/** 预取详情（鼠标移到卡片上时调用），失败静默，点开时会再试一次。 */
export function prefetchDetail(id: string): void {
  loadDetail(id).catch(() => {});
}
