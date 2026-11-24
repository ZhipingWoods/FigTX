import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import data from './data/items.json';

type Item = {
  id: string;
  kind: string;
  title: string;
  caption: string;
  venues: string[];
  year: number | null;
  tags: string[];
  number: number | null;
  palette: string[];
  latexFile: string;
  latex: string;
  render: string | null;
  noteImages: string[];
  publishedAt: string | null;
  source: {
    platform: string;
    author: string;
    noteId: string | null;
    docId: string | null;
    noteUrl: string | null;
  };
};

const ITEMS = (data as unknown as { items: Item[]; stats: Stats }).items;
const STATS = (data as unknown as { items: Item[]; stats: Stats }).stats;

type Stats = {
  total: number;
  withRender: number;
  withImages: number;
  kinds: Record<string, number>;
  venues: Record<string, number>;
  generatedAt: string;
};

const KIND_LABEL: Record<string, string> = {
  table: '表格',
  figure: '图',
  mixed: '表+图',
  snippet: '片段',
};

function assetUrl(p: string) {
  // vite base './' 下用相对路径即可，Electron file:// 同样适用
  return p;
}

function highlight(code: string) {
  // 极简 LaTeX 高亮：命令 / 花括号 / 注释
  return code.split('\n').map((line, i) => {
    const commentAt = (() => {
      let esc = false;
      for (let k = 0; k < line.length; k++) {
        if (line[k] === '\\') { esc = !esc; continue; }
        if (line[k] === '%' && !esc) return k;
        esc = false;
      }
      return -1;
    })();
    const body = commentAt >= 0 ? line.slice(0, commentAt) : line;
    const comment = commentAt >= 0 ? line.slice(commentAt) : '';
    const parts: React.ReactNode[] = [];
    const re = /\\[a-zA-Z@]+\*?|[{}]/g;
    let last = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(body))) {
      if (m.index > last) parts.push(body.slice(last, m.index));
      const tok = m[0];
      const cls = tok === '{' || tok === '}' ? 'tok-brace' : 'tok-cmd';
      parts.push(<span key={i + ':' + m.index} className={cls}>{tok}</span>);
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

export default function App() {
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState<string>('all');
  const [venue, setVenue] = useState<string>('all');
  const [onlyRendered, setOnlyRendered] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  const venues = useMemo(
    () => Object.entries(STATS.venues).sort((a, b) => b[1] - a[1]).slice(0, 12),
    [],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return ITEMS.filter((it) => {
      if (kind !== 'all' && it.kind !== kind) return false;
      if (venue !== 'all' && !it.venues.includes(venue)) return false;
      if (onlyRendered && !it.render) return false;
      if (!q) return true;
      const hay = [it.title, it.caption, it.latex.slice(0, 3000), it.venues.join(' '), it.tags.join(' ')]
        .join(' ')
        .toLowerCase();
      return hay.includes(q);
    });
  }, [query, kind, venue, onlyRendered]);

  const openIndex = filtered.findIndex((i) => i.id === openId);
  const open = openIndex >= 0 ? filtered[openIndex] : null;

  const move = useCallback(
    (delta: number) => {
      if (!filtered.length) return;
      const next = Math.min(Math.max(openIndex + delta, 0), filtered.length - 1);
      if (openIndex < 0) setOpenId(filtered[0].id);
      else setOpenId(filtered[next].id);
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

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">TeX</div>
          <div className="brand-text">
            <div className="brand-title">FigTX</div>
            <div className="brand-sub">论文图表 LaTeX 样式库</div>
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
            placeholder="搜索标题、caption、会议、LaTeX 命令…"
            spellCheck={false}
          />
          <kbd>/</kbd>
        </label>

        <div className="spacer" />
        <div className="count">
          <b>{filtered.length}</b> / {ITEMS.length} 个样式
        </div>
      </header>

      <div className="filters">
        <button className="chip" data-active={kind === 'all'} onClick={() => setKind('all')}>
          全部 <span className="n">{ITEMS.length}</span>
        </button>
        {(['table', 'figure', 'mixed', 'snippet'] as const).map((k) =>
          STATS.kinds[k] ? (
            <button key={k} className="chip" data-active={kind === k} onClick={() => setKind(k)}>
              {KIND_LABEL[k]} <span className="n">{STATS.kinds[k]}</span>
            </button>
          ) : null,
        )}
        <span className="filter-sep" />
        <button
          className="chip"
          data-active={onlyRendered}
          onClick={() => setOnlyRendered((v) => !v)}
          title="只显示已成功渲染的样式"
        >
          已渲染 <span className="n">{STATS.withRender}</span>
        </button>
        <span className="filter-sep" />
        <button className="chip" data-active={venue === 'all'} onClick={() => setVenue('all')}>
          所有会议
        </button>
        {venues.map(([v, n]) => (
          <button key={v} className="chip" data-active={venue === v} onClick={() => setVenue(v)}>
            {v} <span className="n">{n}</span>
          </button>
        ))}
      </div>

      <main className="grid-wrap">
        {filtered.length === 0 ? (
          <div className="empty">
            <h3>没有匹配的样式</h3>
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
        <span>共 {STATS.total} 个样式 · {STATS.withRender} 个已用 tectonic 重编译渲染</span>
        <span>数据来源：小红书 @爱芝芝爱科研</span>
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
  const preview = item.render || item.noteImages[0] || null;
  const isPhoto = !item.render && !!item.noteImages[0];

  return (
    <button className="card" onClick={onOpen}>
      <div className={'card-preview' + (isPhoto ? ' photo' : '')}>
        {preview && !broken ? (
          <img
            src={assetUrl(preview)}
            alt={item.caption || item.title}
            loading="lazy"
            onError={() => setBroken(true)}
          />
        ) : (
          <span style={{ color: 'var(--ink-3)', fontSize: 12 }}>暂无预览</span>
        )}
        <span className="card-badge" data-kind={isPhoto ? 'photo' : 'render'}>
          {isPhoto ? '原图' : 'LaTeX 渲染'}
        </span>
      </div>
      <div className="card-body">
        <div className="card-title">{item.caption || item.title || '（无标题）'}</div>
        <div className="card-caption">
          {item.number != null ? '#' + item.number + ' · ' : ''}
          {item.title || '无来源标题'}
        </div>
        <div className="card-foot">
          <span className="venue">{KIND_LABEL[item.kind] || item.kind}</span>
          {item.venues.slice(0, 2).map((v) => (
            <span className="venue" key={v}>{v}</span>
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

function Modal({
  item,
  onClose,
  onPrev,
  onNext,
}: {
  item: Item;
  onClose: () => void;
  onPrev: () => void;
  onNext: () => void;
}) {
  const tabs = [
    item.render ? { key: 'render', label: 'LaTeX 渲染' } : null,
    ...item.noteImages.map((src, i) => ({ key: 'note-' + i, label: '原图 ' + (i + 1), src })),
  ].filter(Boolean) as { key: string; label: string; src?: string }[];
  const [tab, setTab] = useState(tabs[0]?.key ?? 'render');
  const [copied, setCopied] = useState(false);
  const shown = tabs.find((t) => t.key === tab) || tabs[0];
  const src = shown?.src ?? item.render ?? item.noteImages[0] ?? '';

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(item.latex);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = item.latex;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  const download = () => {
    const blob = new Blob([item.latex], { type: 'text/x-tex;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = item.id + '.tex';
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-visual">
          <div className="modal-tabs">
            {tabs.map((t) => (
              <button
                key={t.key}
                className="modal-tab"
                data-active={t.key === tab}
                onClick={() => setTab(t.key)}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="modal-stage">
            {src ? (
              <img
                className={shown?.src ? 'photo' : ''}
                src={assetUrl(src)}
                alt={item.caption || item.title}
              />
            ) : (
              <span style={{ color: 'var(--ink-3)' }}>暂无预览图</span>
            )}
          </div>
        </div>

        <div className="modal-side">
          <div className="modal-head">
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="modal-title">{item.title || '（无标题）'}</div>
              <div className="modal-sub">
                {item.caption || '无 caption'}
              </div>
            </div>
            <button className="icon-btn" onClick={onPrev} title="上一个 (←/k)">‹</button>
            <button className="icon-btn" onClick={onNext} title="下一个 (→/j)">›</button>
            <button className="icon-btn" onClick={onClose} title="关闭 (Esc)">✕</button>
          </div>

          <div className="modal-meta">
            <span className="meta-pill">{KIND_LABEL[item.kind] || item.kind}</span>
            {item.venues.map((v) => (
              <span className="meta-pill" key={v}>{v}</span>
            ))}
            {item.year && <span className="meta-pill">{item.year}</span>}
            {item.number != null && <span className="meta-pill">#{item.number}</span>}
            <span className="meta-pill">{item.latex.split('\n').length} 行</span>
            {item.palette.map((c) => (
              <span
                key={c}
                className="meta-pill"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}
              >
                <i style={{ width: 9, height: 9, borderRadius: 2, background: c, display: 'inline-block' }} />
                {c}
              </span>
            ))}
          </div>

          <div className="code-head">
            <span>LaTeX 源码</span>
            <div className="spacer" />
            <button className="btn btn-primary" onClick={copy} data-copied={copied}>
              {copied ? '已复制' : '复制'}
            </button>
            <button className="btn" onClick={download}>下载 .tex</button>
            {item.source.noteUrl && (
              <a className="btn" href={item.source.noteUrl} target="_blank" rel="noreferrer">
                原笔记
              </a>
            )}
          </div>

          <pre className="code">
            <code>{highlight(item.latex)}</code>
          </pre>
        </div>
      </div>
    </div>
  );
}
