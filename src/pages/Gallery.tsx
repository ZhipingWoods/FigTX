import { useEffect, useMemo, useRef, useState } from 'react';
import Card from '../components/Card';
import FilterBar from '../components/FilterBar';
import type { Index, Lite } from '../lib/data';
import { useFavs } from '../lib/favs';
import { applyFilters } from '../lib/filter';
import { FIGTYPE_LABEL, SECTIONS, domainLabel } from '../lib/meta';
import type { Filters, Route } from '../lib/route';
import { buildHash } from '../lib/route';

const PAGE = 60;

function Chips({ idx, f, onChange }: { idx: Index; f: Filters; onChange: (f: Filters) => void }) {
  const chips: { label: string; next: Filters }[] = [];
  const drop = (key: keyof Filters, v?: string | number) => {
    const next: Filters = { ...f };
    const cur = f[key];
    if (Array.isArray(cur) && v !== undefined) {
      const rest = (cur as (string | number)[]).filter((x) => x !== v);
      if (rest.length) (next as Record<string, unknown>)[key] = rest;
      else delete next[key];
    } else delete next[key];
    return next;
  };
  for (const d of f.d || []) chips.push({ label: domainLabel(idx, d), next: drop('d', d) });
  for (const p of f.p || []) chips.push({ label: p, next: drop('p', p) });
  for (const v of f.v || []) chips.push({ label: v, next: drop('v', v) });
  for (const y of f.y || []) chips.push({ label: String(y), next: drop('y', y) });
  for (const t of f.ft || []) chips.push({ label: FIGTYPE_LABEL[t] || t, next: drop('ft', t) });
  if (f.q) chips.push({ label: `“${f.q}”`, next: drop('q') });
  if (!chips.length) return null;
  return (
    <div className="chips">
      {chips.map((c) => <button key={c.label} type="button" onClick={() => onChange(c.next)}>{c.label}</button>)}
    </div>
  );
}

export default function Gallery({ idx, route, onOpen }: {
  idx: Index; route: Route; onOpen: (it: Lite, list: Lite[]) => void;
}) {
  const section = SECTIONS.find((s) => s.page === route.page)!;
  const f = route.f;
  const list = useMemo(() => applyFilters(idx.items, route.page, f), [idx, route.page, f]);
  const favs = useFavs();
  const [shown, setShown] = useState(PAGE);
  const moreRef = useRef<HTMLDivElement>(null);

  useEffect(() => setShown(PAGE), [list]);
  useEffect(() => {
    const el = moreRef.current;
    if (!el) return;
    const io = new IntersectionObserver((es) => es.some((e) => e.isIntersecting) && setShown((n) => n + PAGE),
      { rootMargin: '1200px' });
    io.observe(el);
    return () => io.disconnect();
  }, [shown, list]);

  const go = (next: Filters) => { location.hash = buildHash({ page: route.page, f: next }); };
  const visible = list.slice(0, shown);

  return (
    <div className="wrap">
      <div className="page-head">
        <h1>{section.label}</h1>
        <p>{section.desc}</p>
      </div>
      <section style={{ paddingTop: 28 }}>
        <FilterBar idx={idx} section={route.page} f={f} count={list.length} onChange={go} />
        <Chips idx={idx} f={f} onChange={go} />
        {list.length === 0 ? (
          <div className="empty">
            没有符合条件的{section.label}。
            <button type="button" onClick={() => go({})}>清除筛选</button>
          </div>
        ) : (
          <>
            <div className={'masonry' + (route.page === 'tables' ? ' wide' : '')}>
              {visible.map((it) => (
                <Card key={it.id} it={it} fav={(it.no || it.id) in favs} onOpen={() => onOpen(it, list)} />
              ))}
            </div>
            {shown < list.length && (
              <div ref={moreRef} className="load-more">加载更多…（{shown.toLocaleString()} / {list.length.toLocaleString()}）</div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
