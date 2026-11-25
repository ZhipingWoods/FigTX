import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import data from './data/items.json';

type Category = 'table' | 'figure';

type Item = {
  id: string;
  category: Category;
  figType?: string;
  group?: string | null;
  kind: string;
  domain?: string[];
  title: string;
  caption: string;
  venues: string[];
  year: number | null;
  tags: string[];
  number: number | null;
  palette: string[];
  code: string;
  codeLang: string;
  render: string | null;
  no?: string | null;          // 稳定编号 T001-T999 / F001-F999
  repaired?: string | null;
  editFiles?: { ext: string; label: string; path: string }[];
  noteImages: string[];
  publishedAt: string | null;
  source: {
    platform: string;
    author: string;
    repo: string | null;
    repoUrl: string | null;
    license: string | null;
    stars?: number;
    path?: string | null;
  };
};

type Stats = {
  total: number;
  tables: number;
  figures: number;
  tableRender: number;
  figureRender: number;
  kinds: Record<string, number>;
  venues: Record<string, number>;
  repos: Record<string, number>;
  figTypes: Record<string, number>;
  domains: Record<string, number>;
  generatedAt: string;
};

const ALL = data as unknown as { items: Item[]; stats: Stats };
const ITEMS = ALL.items;
const STATS = ALL.stats;

const KIND_LABEL: Record<string, string> = {
  table: '表格',
  figure: '图',
  chart: '数据图',
  diagram: '示意图',
  mixed: '表+图',
  snippet: '片段',
};

const LANG_LABEL: Record<string, string> = {
  latex: 'LaTeX',
  python: 'Python',
  r: 'R',
  julia: 'Julia',
};

const CATEGORY_LABEL: Record<Category, string> = { table: '表格', figure: '图' };

const FIGTYPE_LABEL: Record<string, string> = {
  // 论文图复刻（按参考图的用途分）
  efficiency: '效率分析',
  architecture: '架构图',
  mechanism: '机制示意',
  tradeoff: '权衡曲线',
  results: '结果对比',
  // 通用模板
  framework: '框架图',
  motivation: '动机图',
  quantitative: '实验·定量',
  qualitative: '实验·定性',
  style: '绘图样式',
};

const REPLICA_TYPES = ['efficiency', 'architecture', 'mechanism', 'tradeoff', 'results'];

function highlightLatex(code: string) {
  return code.split('\n').map((line, i) => {
    let commentAt = -1;
    let esc = false;
    for (let k = 0; k < line.length; k++) {
      if (line[k] === '\\') { esc = !esc; continue; }
      if (line[k] === '%' && !esc) { commentAt = k; break; }
      esc = false;
    }
    const body = commentAt >= 0 ? line.slice(0, commentAt) : line;
    const comment = commentAt >= 0 ? line.slice(commentAt) : '';
    const parts: React.ReactNode[] = [];
    const re = /\\[a-zA-Z@]+\*?|[{}]/g;
    let last = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(body))) {
      if (m.index > last) parts.push(body.slice(last, m.index));
      const tok = m[0];
      parts.push(
        <span key={i + ':' + m.index} className={tok === '{' || tok === '}' ? 'tok-brace' : 'tok-cmd'}>
          {tok}
        </span>,
      );
      last = m.index + tok.length;
    }
    if (last < body.length) parts.push(body.slice(last));
    return (
      <div key={i}>
        {parts}
        {comment && <span className="tok-comment">{comment}</span>}
        {'\n'}
      </div>
    );
  });
}

function highlightPython(code: string) {
  const KW = /\b(import|from|as|def|return|for|in|if|else|elif|with|class|lambda|None|True|False)\b/g;
  return code.split('\n').map((line, i) => {
    const hash = line.indexOf('#');
    const body = hash >= 0 ? line.slice(0, hash) : line;
    const comment = hash >= 0 ? line.slice(hash) : '';
    const parts: React.ReactNode[] = [];
    let last = 0;
    let m: RegExpExecArray | null;
    KW.lastIndex = 0;
    while ((m = KW.exec(body))) {
      if (m.index > last) parts.push(body.slice(last, m.index));
      parts.push(<span key={i + ':k' + m.index} className="tok-cmd">{m[0]}</span>);
      last = m.index + m[0].length;
    }
    const tail = body.slice(last);
    const strParts = tail.split(/('[^']*'|"[^"]*")/g).map((s, j) =>
      /^['"]/.test(s) ? <span key={i + ':s' + j} className="tok-brace">{s}</span> : s,
    );
    parts.push(...strParts);
    return (
      <div key={i}>
        {parts}
        {comment && <span className="tok-comment">{comment}</span>}
        {'\n'}
      </div>
    );
  });
}

export default function App() {
  const [category, setCategory] = useState<Category>('table');
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState<string>('all');
  const [figType, setFigType] = useState<string>('all');
  const [domain, setDomain] = useState<string>('all');
  const [replicaOnly, setReplicaOnly] = useState(false);
  const [venue, setVenue] = useState<string>('all');
  const [onlyRendered, setOnlyRendered] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);
  // 排序方向：asc = 编号正序（T001→T199），desc = 倒序（T199→T001）
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(() => {
    try {
      const v = localStorage.getItem('figtx.sortDir');
      return v === 'desc' ? 'desc' : 'asc';
    } catch {
      return 'asc';
    }
  });
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    try {
      localStorage.setItem('figtx.sortDir', sortDir);
    } catch {
      /* 忽略隐私模式下的写入失败 */
    }
  }, [sortDir]);

  const scoped = useMemo(() => ITEMS.filter((i) => i.category === category), [category]);

  const kindsInScope = useMemo(() => {
    const acc: Record<string, number> = {};
    for (const i of scoped) acc[i.kind] = (acc[i.kind] || 0) + 1;
    return acc;
  }, [scoped]);

  const venuesInScope = useMemo(() => {
    const acc: Record<string, number> = {};
    for (const i of scoped) for (const v of i.venues) acc[v] = (acc[v] || 0) + 1;
    return Object.entries(acc).sort((a, b) => b[1] - a[1]).slice(0, 12);
  }, [scoped]);

  const figTypesInScope = useMemo(() => {
    const acc: Record<string, number> = {};
    for (const i of scoped) {
      const k = i.figType || 'style';
      acc[k] = (acc[k] || 0) + 1;
    }
    return acc;
  }, [scoped]);

  const domainsInScope = useMemo(() => {
    const acc: Record<string, number> = {};
    for (const i of scoped) for (const d of i.domain || []) acc[d] = (acc[d] || 0) + 1;
    return Object.entries(acc).sort((a, b) => b[1] - a[1]).slice(0, 14);
  }, [scoped]);

  // 先按筛选条件过滤（不含排序）
  const base = useMemo(() => {
    const q = query.trim().toLowerCase();
    return scoped.filter((it) => {
      if (category === 'figure' && replicaOnly && it.group !== 'replicas') return false;
      if (category === 'figure' && figType !== 'all' && (it.figType || 'style') !== figType) return false;
      if (category === 'figure' && domain !== 'all' && !(it.domain || []).includes(domain)) return false;
      if (category === 'table' && kind !== 'all' && it.kind !== kind) return false;
      if (venue !== 'all' && !it.venues.includes(venue)) return false;
      if (onlyRendered && !it.render) return false;
      if (!q) return true;
      const hay = [
        it.no || '',
        it.id,
        it.title,
        it.caption,
        it.code.slice(0, 3000),
        it.venues.join(' '),
        it.tags.join(' '),
        it.source.repo || '',
      ]
        .join(' ')
        .toLowerCase();
      return hay.includes(q);
    });
  }, [scoped, category, query, kind, figType, domain, venue, onlyRendered, replicaOnly]);

  // 再按稳定编号排序（正序/倒序）
  const filtered = useMemo(() => {
    const list = base.filter((i) => !!i);
    const sign = sortDir === 'asc' ? 1 : -1;
    // 按稳定编号排序；无编号的排最后
    return [...list].sort((a, b) => {
      const na = a.no || '~';
      const nb = b.no || '~';
      if (na === nb) return 0;
      return na < nb ? -sign : sign;
    });
  }, [base, sortDir]);

  // URL hash 直达：#T042 / #F007 或 #<item-id>
  useEffect(() => {
    const applyHash = () => {
      const raw = decodeURIComponent(window.location.hash.replace(/^#/, '')).trim();
      if (!raw) return;
      const up = raw.toUpperCase();
      const hit =
        ITEMS.find((i) => (i.no || '').toUpperCase() === up) ||
        ITEMS.find((i) => i.id === raw);
      if (hit) {
        setCategory(hit.category);
        setKind('all');
        setFigType('all');
        setDomain('all');
        setVenue('all');
        setQuery('');
        setReplicaOnly(false);
        setOnlyRendered(false);
        setOpenId(hit.id);
      } else {
        // 编号失效（条目已删除）时不能停留在上一条 —— 否则链接指向错的条目
        setOpenId(null);
      }
    };
    applyHash();
    window.addEventListener('hashchange', applyHash);
    return () => window.removeEventListener('hashchange', applyHash);
  }, []);

  // 打开条目时把编号写进 hash，方便复制链接直接定位
  useEffect(() => {
    const cur = ITEMS.find((i) => i.id === openId);
    const want = cur && cur.no ? '#' + cur.no : '';
    if (want && window.location.hash !== want) {
      history.replaceState(null, '', want);
    } else if (!openId && window.location.hash) {
      history.replaceState(null, '', window.location.pathname + window.location.search);
    }
  }, [openId]);

  const openIndex = filtered.findIndex((i) => i.id === openId);
  const open = openIndex >= 0 ? filtered[openIndex] : null;

  const move = useCallback(
    (delta: number) => {
      if (!filtered.length) return;
      const next = Math.min(Math.max(openIndex + delta, 0), filtered.length - 1);
      setOpenId(openIndex < 0 ? filtered[0].id : filtered[next].id);
    },
    [filtered, openIndex],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === '/' && document.activeElement !== searchRef.current) {
        e.preventDefault();
        searchRef.current?.focus();
        return;
      }
      if (e.key === 'Escape') { setOpenId(null); return; }
      if (!open) return;
      if (e.key === 'ArrowRight' || e.key === 'j') move(1);
      if (e.key === 'ArrowLeft' || e.key === 'k') move(-1);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, move]);

  const switchCategory = (c: Category) => {
    setCategory(c);
    setKind('all');
    setFigType('all');
    setDomain('all');
    setReplicaOnly(false);
    setVenue('all');
    setOpenId(null);
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">TeX</div>
          <div className="brand-text">
            <div className="brand-title">FigTX</div>
            <div className="brand-sub">论文表格与图 · 样式库</div>
          </div>
        </div>

        <label className="search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" strokeLinecap="round" />
          </svg>
          <input
            ref={searchRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={category === 'table' ? '搜索 caption、会议、LaTeX 命令…' : '搜索图样式、配色、依赖包…'}
            spellCheck={false}
          />
          <kbd>/</kbd>
        </label>

        <div className="spacer" />
        <button
          className="sortbtn"
          onClick={() => setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))}
          title={sortDir === 'asc' ? '当前：编号正序 —— 点击切换为倒序' : '当前：编号倒序 —— 点击切换为正序'}
          aria-label={sortDir === 'asc' ? '切换为倒序' : '切换为正序'}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
            {sortDir === 'asc' ? (
              <>
                <path d="M7 4v16" />
                <path d="m4 17 3 3 3-3" />
                <path d="M13 6h7" />
                <path d="M13 12h5" />
                <path d="M13 18h3" />
              </>
            ) : (
              <>
                <path d="M7 20V4" />
                <path d="m4 7 3-3 3 3" />
                <path d="M13 6h3" />
                <path d="M13 12h5" />
                <path d="M13 18h7" />
              </>
            )}
          </svg>
          {sortDir === 'asc' ? '正序' : '倒序'}
        </button>
        <div className="count">
          <b>{filtered.length}</b> / {scoped.length} 个{CATEGORY_LABEL[category]}
        </div>
      </header>

      <nav className="tabs">
        <button className="tab" data-active={category === 'table'} onClick={() => switchCategory('table')}>
          表格 <span className="n">{STATS.tables}</span>
        </button>
        <button className="tab" data-active={category === 'figure'} onClick={() => switchCategory('figure')}>
          图 <span className="n">{STATS.figures}</span>
        </button>
      </nav>

      <div className="filters">
        <button
          className="chip"
          data-active={category === 'figure' ? figType === 'all' && domain === 'all' : kind === 'all'}
          onClick={() => { setKind('all'); setFigType('all'); setDomain('all'); }}
        >
          全部 <span className="n">{scoped.length}</span>
        </button>

        {category === 'table' &&
          Object.entries(kindsInScope).map(([k, n]) => (
            <button key={k} className="chip" data-active={kind === k} onClick={() => setKind(k)}>
              {KIND_LABEL[k] || k} <span className="n">{n}</span>
            </button>
          ))}

        {category === 'figure' &&
          Object.entries(figTypesInScope)
            .sort((a, b) => b[1] - a[1])
            .map(([k, n]) => (
              <button key={k} className="chip" data-active={figType === k} onClick={() => setFigType(k)}>
                {FIGTYPE_LABEL[k] || k} <span className="n">{n}</span>
              </button>
            ))}

        {category === 'figure' && (
          <button
            className="chip"
            data-active={replicaOnly}
            onClick={() => setReplicaOnly((v) => !v)}
            title="只看按参考论文逐项复刻的图"
          >
            论文复刻 <span className="n">{scoped.filter((i) => i.group === 'replicas').length}</span>
          </button>
        )}

        {category === 'figure' && domainsInScope.length > 0 && <span className="filter-sep" />}
        {category === 'figure' &&
          domainsInScope.map(([d, n]) => (
            <button key={d} className="chip" data-active={domain === d} onClick={() => setDomain(d)}>
              {d} <span className="n">{n}</span>
            </button>
          ))}

        <span className="filter-sep" />
        <button className="chip" data-active={onlyRendered} onClick={() => setOnlyRendered((v) => !v)}>
          已渲染 <span className="n">{category === 'table' ? STATS.tableRender : STATS.figureRender}</span>
        </button>
        {venuesInScope.length > 0 && <span className="filter-sep" />}
        {venuesInScope.length > 0 && (
          <button className="chip" data-active={venue === 'all'} onClick={() => setVenue('all')}>
            所有会议
          </button>
        )}
        {venuesInScope.map(([v, n]) => (
          <button key={v} className="chip" data-active={venue === v} onClick={() => setVenue(v)}>
            {v} <span className="n">{n}</span>
          </button>
        ))}
      </div>

      <main className="grid-wrap">
        {filtered.length === 0 ? (
          <div className="empty">
            <h3>没有匹配的{CATEGORY_LABEL[category]}</h3>
            <p>换个关键词，或清除筛选条件。</p>
          </div>
        ) : (
          <div className="grid">
            {filtered.map((it) => (
              <Card key={it.id} item={it} onOpen={() => setOpenId(it.id)} />
            ))}
          </div>
        )}
      </main>

      <footer className="footer">
        <span>{STATS.tables} 个表格样式 · {STATS.figures} 个图样式</span>
        <span>表格：公开论文 LaTeX 片段精选 · 图：开源绘图库样式</span>
        <span>Apache-2.0 · FigTX</span>
      </footer>

      {open && (
        <Modal item={open} onClose={() => setOpenId(null)} onPrev={() => move(-1)} onNext={() => move(1)} />
      )}
    </div>
  );
}

function Card({ item, onOpen }: { item: Item; onOpen: () => void }) {
  const [broken, setBroken] = useState(false);
  const preview = item.render || null;

  return (
    <button className="card" onClick={onOpen}>
      <div
        className={
          'card-preview' +
          (item.category === 'figure' ? ' chart' : '') +
          (item.figType === 'framework' || item.figType === 'motivation' ? ' diagram' : '') +
          (preview ? '' : ' empty')
        }
      >
        {item.no && <span className="no-badge">{item.no}</span>}
        {preview && !broken ? (
          <img src={preview} alt={item.caption || item.title} loading="lazy" onError={() => setBroken(true)} />
        ) : (
          <div className="no-preview">
            <span className="np-mark">TeX</span>
            <span className="np-text">源码可用 · 暂无渲染预览</span>
          </div>
        )}
      </div>
      <div className="card-body">
        <div className="card-title">{item.caption || item.title || '（无标题）'}</div>
        <div className="card-caption">
          {item.number != null ? '#' + item.number + ' · ' : ''}
          {item.category === 'figure' ? item.source.repo : item.title || '无来源标题'}
        </div>
        <div className="card-foot">
          <span className="venue">
            {item.category === 'figure'
              ? FIGTYPE_LABEL[item.figType || 'style'] || '图'
              : KIND_LABEL[item.kind] || item.kind}
          </span>
          {item.category === 'table' &&
            item.venues.slice(0, 2).map((v) => (
              <span className="venue" key={v}>{v}</span>
            ))}
          {item.category === 'figure' &&
            item.tags.slice(0, 2).map((t) => (
              <span className="venue" key={t}>{t}</span>
            ))}
          {item.palette.length > 0 && (
            <span className="palette">
              {item.palette.slice(0, 5).map((c) => (
                <i key={c} style={{ background: c }} />
              ))}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

function Modal({ item, onClose, onPrev, onNext }: { item: Item; onClose: () => void; onPrev: () => void; onNext: () => void }) {
  const tabs = [
    item.render ? { key: 'render', label: item.category === 'table' ? 'LaTeX 渲染' : '效果预览' } : null,
    ...item.noteImages.map((src, i) => ({ key: 'note-' + i, label: '原图 ' + (i + 1), src })),
  ].filter(Boolean) as { key: string; label: string; src?: string }[];
  const [tab, setTab] = useState(tabs[0]?.key ?? 'render');
  const [copied, setCopied] = useState(false);
  const shown = tabs.find((t) => t.key === tab) || tabs[0];
  const src = shown?.src ?? item.render ?? item.noteImages[0] ?? '';

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(item.code);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = item.code;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  const download = () => {
    const ext = item.codeLang === 'latex' ? 'tex' : item.codeLang === 'python' ? 'py' : 'txt';
    const blob = new Blob([item.code], { type: 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = item.id + '.' + ext;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-visual">
          <div className="modal-tabs">
            {tabs.map((t) => (
              <button key={t.key} className="modal-tab" data-active={t.key === tab} onClick={() => setTab(t.key)}>
                {t.label}
              </button>
            ))}
          </div>
          <div className="modal-stage">
            {src ? (
              <img className={shown?.src ? 'photo' : ''} src={src} alt={item.caption || item.title} />
            ) : (
              <span style={{ color: 'var(--ink-3)' }}>暂无预览图</span>
            )}
          </div>
        </div>

        <div className="modal-side">
          <div className="modal-head">
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="modal-title">{item.caption || item.title || '（无标题）'}</div>
              <div className="modal-sub">
                {item.category === 'figure'
                  ? item.title
                  : item.title || '无 caption'}
              </div>
            </div>
            <button className="icon-btn" onClick={onPrev} title="上一个 (←/k)">‹</button>
            <button className="icon-btn" onClick={onNext} title="下一个 (→/j)">›</button>
            <button className="icon-btn" onClick={onClose} title="关闭 (Esc)">✕</button>
          </div>

          <div className="modal-meta">
            <span className="meta-pill">
              {item.category === 'figure'
                ? FIGTYPE_LABEL[item.figType || 'style'] || '图'
                : KIND_LABEL[item.kind] || item.kind}
            </span>
            {(item.domain || []).map((d) => (
              <span className="meta-pill" key={d}>{d}</span>
            ))}
            {item.venues.map((v) => (
              <span className="meta-pill" key={v}>{v}</span>
            ))}
            {item.year && <span className="meta-pill">{item.year}</span>}
            {item.no && <span className="meta-pill meta-no">{item.no}</span>}
            {item.number != null && <span className="meta-pill">#{item.number}</span>}
            {item.category === 'figure' && item.source.repo && (
              <a className="meta-pill" href={item.source.repoUrl || '#'} target="_blank" rel="noreferrer">
                {item.source.repo} ★{item.source.stars}
              </a>
            )}
            {item.category === 'figure' && item.source.license && (
              <span className="meta-pill">{item.source.license}</span>
            )}
            <span className="meta-pill">{item.code.split('\n').length} 行</span>
            {item.palette.map((c) => (
              <span key={c} className="meta-pill" style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                <i style={{ width: 9, height: 9, borderRadius: 2, background: c, display: 'inline-block' }} />
                {c}
              </span>
            ))}
          </div>

          {item.repaired && (
            <div className="repaired-note" title="原始 LaTeX 来自作者分享的 docx 片段，直接编译会失败；渲染时自动降级修复后排出表格">
              <span className="repaired-dot" />
              {item.repaired}
            </div>
          )}

          <div className="code-head">
            <span>{LANG_LABEL[item.codeLang] || item.codeLang} 源码</span>
            <div className="spacer" />
            <button className="btn btn-primary" onClick={copy} data-copied={copied}>
              {copied ? '已复制' : '复制'}
            </button>
            <button className="btn" onClick={download}>
              下载 .{item.codeLang === 'latex' ? 'tex' : item.codeLang === 'python' ? 'py' : 'txt'}
            </button>
          </div>

          {item.editFiles && item.editFiles.length > 0 && (
            <div className="edit-files">
              <div className="edit-files-head">
                可编辑矢量文件
                <span className="edit-files-hint">框架图通常要二次改图，这里给的是原生形状/路径</span>
              </div>
              <div className="edit-files-row">
                {item.editFiles.map((f) => (
                  <a key={f.ext} className="btn edit-file-btn" href={'./' + f.path} download>
                    <b>.{f.ext}</b>
                    <span>{f.label}</span>
                  </a>
                ))}
              </div>
            </div>
          )}

          <pre className="code">
            <code>{item.codeLang === 'latex' ? highlightLatex(item.code) : highlightPython(item.code)}</code>
          </pre>
        </div>
      </div>
    </div>
  );
}
