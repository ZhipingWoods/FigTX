import { useEffect, useMemo, useRef, useState } from 'react';
import type { Index } from '../lib/data';
import type { FacetKey } from '../lib/filter';
import { facetCounts } from '../lib/filter';
import { FIGTYPE_LABEL, domainLabel } from '../lib/meta';
import type { Filters, Page } from '../lib/route';

const FACETS: { key: FacetKey; label: string; top?: number; find?: boolean }[] = [
  { key: 'd', label: '领域' }, { key: 'p', label: '研究问题', top: 60, find: true },
  { key: 'v', label: '会议 / 期刊', top: 40 }, { key: 'y', label: '年份' }, { key: 'ft', label: '图类型' },
];

function Pill({ idx, section, f, facet, open, setOpen, onChange }: {
  idx: Index; section: Page; f: Filters; facet: (typeof FACETS)[number]; open: boolean;
  setOpen: (k: string | null) => void; onChange: (f: Filters) => void;
}) {
  const [find, setFind] = useState('');
  const counts = useMemo(() => (open ? facetCounts(idx.items, section, f, facet.key) : {}), [open, idx, section, f, facet.key]);
  const selected = ((f[facet.key] as (string | number)[]) || []).map(String);
  let opts = Object.entries(counts).sort((a, b) => (facet.key === 'y' ? Number(b[0]) - Number(a[0]) : b[1] - a[1]));
  if (find) opts = opts.filter(([k]) => k.toLowerCase().includes(find.toLowerCase()));
  if (facet.top) opts = opts.slice(0, facet.top);
  const label = (k: string) => (facet.key === 'd' ? domainLabel(idx, k) : facet.key === 'ft' ? FIGTYPE_LABEL[k] || k : k);
  const set = (vals: string[]) => {
    const next = { ...f, [facet.key]: facet.key === 'y' ? vals.map(Number) : vals };
    if (!vals.length) delete (next as Record<string, unknown>)[facet.key];
    onChange(next);
  };
  return (
    <div className={'pill' + (open ? ' open' : '')} onClick={(e) => e.stopPropagation()}>
      <button type="button" className={selected.length ? 'act' : ''} onClick={() => setOpen(open ? null : facet.key)}>
        {facet.label}{selected.length ? ` · ${selected.length}` : ''}
      </button>
      {open && (
        <div className="pop">
          {facet.find && <input className="find" placeholder="筛选…" value={find} onChange={(e) => setFind(e.target.value)} />}
          {opts.map(([k, n]) => (
            <label key={k}>
              <input type="checkbox" checked={selected.includes(k)}
                     onChange={(e) => set(e.target.checked ? [...selected, k] : selected.filter((s) => s !== k))} />
              {label(k)}<em>{n}</em>
            </label>
          ))}
          {!opts.length && <div className="clear">没有可选项</div>}
          {selected.length > 0 && <button type="button" className="clear" onClick={() => set([])}>清除</button>}
        </div>
      )}
    </div>
  );
}

export default function FilterBar({ idx, section, f, count, onChange }: {
  idx: Index; section: Page; f: Filters; count: number; onChange: (f: Filters) => void;
}) {
  const [open, setOpen] = useState<string | null>(null);
  const [q, setQ] = useState(f.q || '');
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => setQ(f.q || ''), [f.q]);
  useEffect(() => {
    const close = () => setOpen(null);
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, []);
  const facets = section === 'tables' ? FACETS.filter((x) => x.key === 'v' || x.key === 'y') : FACETS;
  return (
    <div className="fbar" ref={ref}>
      <form className="search-mini" onSubmit={(e) => { e.preventDefault(); onChange({ ...f, q: q.trim() || undefined }); }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="搜索标题、问题、编号" />
      </form>
      {facets.map((facet) => (
        <Pill key={facet.key} idx={idx} section={section} f={f} facet={facet} open={open === facet.key}
              setOpen={setOpen} onChange={onChange} />
      ))}
      <button type="button" className={'tg' + (f.ed ? ' on' : '')} onClick={() => onChange({ ...f, ed: !f.ed || undefined })}>
        {section === 'figures' ? '有可编辑版' : '有源码'}
      </button>
      {section === 'figures' && (
        <button type="button" className={'tg' + (f.top ? ' on' : '')} onClick={() => onChange({ ...f, top: !f.top || undefined })}>
          Oral / Best
        </button>
      )}
      <span className="cnt"><b>{count.toLocaleString()}</b> {section === 'tables' ? '个' : '张'}</span>
    </div>
  );
}
