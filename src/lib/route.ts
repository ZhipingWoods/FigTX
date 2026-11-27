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

export function parseHash(hash: string): Route {
  const h = decodeURIComponent((hash || '').replace(/^#/, ''));
  const num = h.match(/^([TFtf]\d{3,})$/);
  if (num) return { page: 'home', f: {}, open: num[1].toUpperCase() };
  const m = h.match(/^\/([a-z]*)(?:\?(.*))?$/);
  const page = (m && (m[1] || 'home')) as Page;
  if (!m || !PAGES.includes(page)) return { page: 'home', f: {} };
  const f: Filters = {};
  const qs = new URLSearchParams(m[2] || '');
  for (const k of LIST_KEYS) {
    const v = qs.get(k);
    if (v) f[k] = v.split(',').filter(Boolean);
  }
  const years = (qs.get('y') || '').split(',').map(Number).filter((n) => Number.isInteger(n) && n > 1900);
  if (years.length) f.y = years;
  if (qs.get('ed') === '1') f.ed = true;
  if (qs.get('top') === '1') f.top = true;
  const q = qs.get('q');
  if (q) f.q = q;
  return { page, f };
}

export function buildHash(r: Route): string {
  if (r.open) return '#' + r.open;
  if (r.page === 'home') return '#/';
  const qs: string[] = [];
  const f = r.f || {};
  for (const k of LIST_KEYS) if (f[k]?.length) qs.push(k + '=' + encodeURIComponent(f[k]!.join(',')));
  if (f.y?.length) qs.push('y=' + f.y.join(','));
  if (f.ed) qs.push('ed=1');
  if (f.top) qs.push('top=1');
  if (f.q) qs.push('q=' + encodeURIComponent(f.q));
  return '#/' + r.page + (qs.length ? '?' + qs.join('&') : '');
}
