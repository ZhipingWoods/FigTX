import { useMemo, useState } from 'react';
import type { Index, Lite } from '../lib/data';
import { thumbOf } from '../lib/data';
import { buildHash } from '../lib/route';
import { SECTIONS, domainLabel, numOf, venueLine } from '../lib/meta';

const TRIES = ['diffusion', '3D Gaussian', 'agent', 'T042'];

function pickWall(items: Lite[]) {
  const pool = items.filter((it) => it.grp === 'framework' || it.grp === 'teaser');
  const award = pool.filter((it) => it.aw);
  const recent = pool.filter((it) => !it.aw).sort((a, b) => (b.y || 0) - (a.y || 0) || numOf(b.no) - numOf(a.no));
  const picked = [...award, ...recent].slice(0, 40);
  return [0, 1, 2, 3].map((r) => picked.slice(r * 10, r * 10 + 10));
}

function Rail({ items, onOpen }: { items: Lite[]; onOpen: (it: Lite, list: Lite[]) => void }) {
  return (
    <div className="rail">
      {items.map((it) => (
        <figure key={it.id} onClick={() => onOpen(it, items)} role="button" tabIndex={0} aria-label={it.t}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), onOpen(it, items))}>
          {it.ed !== 'none' && <span className="sticker">{it.ed === 'editable' ? '可编辑' : '有源码'}</span>}
          <div className="im"><img src={thumbOf(it)} alt={it.t} loading="lazy" /></div>
          <figcaption>
            {it.t}
            <small>{[it.no, venueLine(it)].filter(Boolean).join(' · ')}</small>
          </figcaption>
        </figure>
      ))}
    </div>
  );
}

export default function Home({ idx, onOpen }: { idx: Index; onOpen: (it: Lite, list: Lite[]) => void }) {
  const [q, setQ] = useState('');
  const items = idx.items;
  const wall = useMemo(() => pickWall(items), [items]);
  const counts = useMemo(() => {
    const c = { framework: 0, experiment: 0, table: 0, editable: 0 };
    for (const it of items) {
      if (it.grp === 'framework' || it.grp === 'teaser') c.framework++;
      else if (it.grp === 'experiment') c.experiment++;
      else c.table++;
      if (it.ed !== 'none') c.editable++;
    }
    return c;
  }, [items]);
  const domains = useMemo(() => {
    const n: Record<string, number> = {};
    for (const it of items) for (const d of it.d || []) n[d] = (n[d] || 0) + 1;
    return idx.taxonomy.map((d) => ({ ...d, n: n[d.key] || 0 })).filter((d) => d.n).sort((a, b) => b.n - a.n);
  }, [items, idx.taxonomy]);
  const entries = useMemo(
    () => SECTIONS.map((s) => {
      const list = items.filter(s.match);
      const pics = (s.page === 'figures' ? list.filter((it) => it.aw) : list).slice(0, s.page === 'tables' ? 2 : 4);
      return { ...s, n: list.length, pics };
    }),
    [items],
  );
  const recent = useMemo(
    () => items.filter((it) => it.src !== 'figtx').sort((a, b) => numOf(b.no) - numOf(a.no)).slice(0, 12),
    [items],
  );
  const withCode = useMemo(() => {
    const exp = items.filter((it) => it.grp === 'experiment' && it.ed !== 'none');
    const tab = items.filter((it) => it.cat === 'table' && it.ed !== 'none');
    return [...exp.slice(0, 7), ...tab.slice(0, 5)];
  }, [items]);

  const search = (text: string) => {
    const t = text.trim();
    if (!t) return;
    location.hash = /^[TFtf]\d{3,}$/.test(t) ? '#' + t.toUpperCase() : buildHash({ page: 'figures', f: { q: t } });
  };

  return (
    <>
      <div className="hero">
        <div className="wall" aria-hidden="true">
          {wall.map((row, i) => (
            <div className="r" key={i}>
              {row.map((it) => <img key={it.id} src={thumbOf(it)} alt="" decoding="async" />)}
            </div>
          ))}
        </div>
        <div className="pitch">
          <h1>顶会顶刊的图和表<br />拿来就能改</h1>
          <p>
            现在收了 <b>{counts.framework.toLocaleString()}</b> 张框架图与主图、<b>{counts.experiment}</b> 张实验图和{' '}
            <b>{counts.table}</b> 个 LaTeX 表格，其中 <b>{counts.editable}</b> 个带可编辑源码，下载就能换成你的内容。
          </p>
          <form className="search" onSubmit={(e) => { e.preventDefault(); search(q); }}>
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="搜标题、领域、研究问题，或直接输入编号 F1477、T042" />
            <button type="submit">搜索</button>
          </form>
          <div className="tries">
            常搜 {TRIES.map((t) => <button key={t} type="button" onClick={() => search(t)}>{t}</button>)}
          </div>
        </div>
      </div>

      <div className="domrow">
        <button className="on" type="button" onClick={() => (location.hash = '#/figures')}>
          全部<em>{counts.framework.toLocaleString()}</em>
        </button>
        {domains.map((d) => (
          <button key={d.key} type="button" onClick={() => (location.hash = buildHash({ page: 'figures', f: { d: [d.key] } }))}>
            {domainLabel(idx, d.key)}<em>{d.n}</em>
          </button>
        ))}
      </div>

      <div className="wrap">
        <section>
          <div className="sh"><h2>想找哪一种</h2></div>
          <div className="entries">
            {entries.map((e) => (
              <a key={e.page} className="entry" href={'#/' + e.page}>
                <div className="pics" style={{ gridTemplateColumns: e.pics.length > 2 ? '1fr 1fr' : '1fr' }}>
                  {e.pics.map((it) => <img key={it.id} src={thumbOf(it)} alt="" loading="lazy" />)}
                </div>
                <div className="lab">
                  <h3>{e.label}</h3>
                  <span><b>{e.n.toLocaleString()} {e.page === 'tables' ? '个' : '张'}</b>{e.desc}</span>
                </div>
              </a>
            ))}
          </div>
        </section>

        <section>
          <div className="sh">
            <div><h2>最近新增</h2><p>来自 topconf-paper-figure-gallery 与 PaperGallery，每周自动同步</p></div>
            <a href="#/figures">看全部</a>
          </div>
          <Rail items={recent} onOpen={onOpen} />
        </section>

        <section>
          <div className="sh">
            <div><h2>有源码，直接改</h2><p>实验图附 matplotlib 脚本，表格附 LaTeX 源码，复制换数据就能用</p></div>
            <a href="#/experiments">看实验图</a>
          </div>
          <Rail items={withCode} onOpen={onOpen} />
        </section>
      </div>
    </>
  );
}
