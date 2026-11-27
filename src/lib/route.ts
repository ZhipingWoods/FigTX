/** hash 路由：#/、#/figures?d=cv&v=CVPR…、#/experiments、#/tables、#/favorites、#/forge；#F036 / #T042 直达条目。 */
export type Page = 'home' | 'figures' | 'experiments' | 'tables' | 'favorites' | 'forge';

export type Filters = {
  q?: string;
  d?: string[];
  p?: string[];
  v?: string[];
  y?: number[];
  ft?: string[];
  ed?: boolean;
  top?: boolean;
};

export type Route = { page: Page; f: Filters; open?: string };

const PAGES: Page[] = ['home', 'figures', 'experiments', 'tables', 'favorites', 'forge'];
const LIST_KEYS = ['d', 'p', 'v', 'ft'] as const;

function safeDecode(s: string): string {
  try {
    return decodeURIComponent(s);
  } catch {
    return s; // 链接里有不合法的 % 时原样保留，不让页面崩溃
  }
}

export function parseHash(hash: string): Route {
  const h = (hash || '').replace(/^#/, '');
  const num = h.match(/^([TFtf]\d{3,})$/);
  if (num) return { page: 'home', f: {}, open: num[1].toUpperCase() };
  const m = h.match(/^\/([a-z]*)(?:\?(.*))?$/);
  const page = (m && (m[1] || 'home')) as Page;
  if (!m || !PAGES.includes(page)) return { page: 'home', f: {} };
  // 自己解析查询串：列表值里「未编码的逗号」是分隔符，值本身的逗号在生成时编码成 %2C
  const raw: Record<string, string> = {};
  for (const pair of (m[2] || '').split('&')) {
    if (!pair) continue;
    const i = pair.indexOf('=');
    if (i > 0) raw[pair.slice(0, i)] = pair.slice(i + 1);
  }
  const f: Filters = {};
  for (const k of LIST_KEYS) {
    if (raw[k]) {
      const vals = raw[k].split(',').map(safeDecode).filter(Boolean);
      if (vals.length) f[k] = vals;
    }
  }
  const years = (raw.y || '').split(',').map(Number).filter((n) => Number.isInteger(n) && n > 1900);
  if (years.length) f.y = years;
  if (raw.ed === '1') f.ed = true;
  if (raw.top === '1') f.top = true;
  if (raw.q) f.q = safeDecode(raw.q);
  return { page, f };
}

export function buildHash(r: Route): string {
  if (r.open) return '#' + r.open;
  if (r.page === 'home') return '#/';
  const qs: string[] = [];
  const f = r.f || {};
  for (const k of LIST_KEYS) if (f[k]?.length) qs.push(k + '=' + f[k]!.map(encodeURIComponent).join(','));
  if (f.y?.length) qs.push('y=' + f.y.join(','));
  if (f.ed) qs.push('ed=1');
  if (f.top) qs.push('top=1');
  if (f.q) qs.push('q=' + encodeURIComponent(f.q));
  return '#/' + r.page + (qs.length ? '?' + qs.join('&') : '');
}
