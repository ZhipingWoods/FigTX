/** 图库筛选：分区 + 多维筛选（同一维度内 OR，不同维度间 AND）+ 关键词搜索；计数按「其余已选条件」计算。 */
import type { Lite } from './data';
import { SECTIONS, numOf } from './meta';
import type { Filters, Page } from './route';

export type FacetKey = 'd' | 'p' | 'v' | 'y' | 'ft';
type Section = 'figures' | 'experiments' | 'tables';

const keyCache = new WeakMap<Lite, string>();
function searchKey(it: Lite): string {
  let k = keyCache.get(it);
  if (k === undefined) {
    k = [it.no, it.t, (it.v || []).join(' '), (it.p || []).join(' '), it.ft, it.y].join(' ').toLowerCase();
    keyCache.set(it, k);
  }
  return k;
}

const valuesOf = (it: Lite, key: FacetKey): (string | number)[] =>
  key === 'y' ? (it.y ? [it.y] : []) : key === 'ft' ? (it.ft ? [it.ft] : []) : (it[key] || []);

function matches(it: Lite, f: Filters, skip?: FacetKey): boolean {
  for (const key of ['d', 'p', 'v', 'y', 'ft'] as FacetKey[]) {
    if (key === skip) continue;
    const want = f[key] as (string | number)[] | undefined;
    if (want?.length && !valuesOf(it, key).some((v) => want.includes(v as never))) return false;
  }
  if (f.ed && it.ed === 'none') return false;
  if (f.top && !it.aw) return false;
  if (f.q) {
    const q = f.q.trim().toLowerCase();
    if (/^[tf]\d{3,}$/.test(q)) return (it.no || '').toLowerCase() === q;
    const key = searchKey(it);
    if (!q.split(/\s+/).every((tok) => key.includes(tok))) return false;
  }
  return true;
}

function inSection(items: Lite[], section: Section) {
  const s = SECTIONS.find((x) => x.page === section)!;
  return items.filter(s.match);
}

export function applyFilters(items: Lite[], section: Page, f: Filters): Lite[] {
  const out = inSection(items, section as Section).filter((it) => matches(it, f));
  if (section === 'figures') return out.sort((a, b) => (b.y || 0) - (a.y || 0) || numOf(a.no) - numOf(b.no));
  return out.sort((a, b) => numOf(a.no) - numOf(b.no));
}

export function facetCounts(items: Lite[], section: Page, f: Filters, key: FacetKey): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const it of inSection(items, section as Section)) {
    if (!matches(it, f, key)) continue;
    for (const v of valuesOf(it, key)) counts[v] = (counts[v] || 0) + 1;
  }
  return counts;
}
