import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Detail, Index, Lite } from '../lib/data';
import { loadDetail, thumbOf } from '../lib/data';
import { codeExt, editableMode } from '../lib/editable';
import { toggle, useFavs } from '../lib/favs';
import { highlight } from '../lib/highlight';
import { FIGTYPE_LABEL, domainLabel, venueLine } from '../lib/meta';

const INSTALL = 'uv tool install "git+https://github.com/ZhipingWoods/FigTX#subdirectory=packages/figtx-forge" && figtx skills install';
const SOURCE: Record<string, string> = { topconf: 'topconf-paper-figure-gallery', papergallery: 'PaperGallery', journal: '期刊' };

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
  }
}

function download(name: string, text: string) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}

function Editable({ d }: { d: Detail }) {
  const [copied, setCopied] = useState('');
  const [showCode, setShowCode] = useState(false);
  const mode = editableMode(d);
  const flash = (what: string) => { setCopied(what); setTimeout(() => setCopied(''), 1500); };
  if (mode === 'files') {
    return (
      <div className="dl">
        <h4>可编辑文件</h4>
        <p>原生形状和文字，下载后直接改成你的内容。</p>
        <div className="fs">
          {d.editFiles.map((f: { ext: string; path: string }) => <a key={f.ext} href={'./' + f.path} download>.{f.ext}</a>)}
        </div>
      </div>
    );
  }
  if (mode === 'code') {
    const ext = codeExt(d.codeLang);
    return (
      <div className="dl">
        <h4>{d.codeLang === 'latex' ? 'LaTeX 源码' : 'matplotlib 源码'}</h4>
        <p>{d.codeLang === 'latex' ? '复制进 Overleaf 就能编译，换成你的数字即可。' : '换成你的数据重新运行即可出图。'}</p>
        <div className="fs">
          <button type="button" onClick={() => copyText(d.code).then(() => flash('code'))}>{copied === 'code' ? '已复制' : '复制源码'}</button>
          <button type="button" onClick={() => download((d.no || d.id) + '.' + ext, d.code)}>下载 .{ext}</button>
          <button type="button" onClick={() => setShowCode(!showCode)}>{showCode ? '收起' : '看源码'}</button>
        </div>
        {showCode && <div className="code-box" style={{ marginTop: 12 }}>{highlight(d.code, d.codeLang)}</div>}
      </div>
    );
  }
  return (
    <div className="dl">
      <h4>还没有可编辑版</h4>
      <p>在 Claude Code / Codex 里用 FigTX 的 figtx-redraw-figure skill，可以把这张图一比一重画成可编辑的 SVG / PPTX；重画好的版本欢迎贡献回来。</p>
      <div className="fs">
        <button type="button" onClick={() => copyText(INSTALL).then(() => flash('cmd'))}>{copied === 'cmd' ? '已复制安装命令' : '复制安装命令'}</button>
        <a href="https://github.com/ZhipingWoods/FigTX#在-claude-code--codex-里用-figtx" target="_blank" rel="noreferrer">怎么用</a>
      </div>
    </div>
  );
}

export default function Lightbox({ idx, item, list, onClose, onMove }: {
  idx: Index; item: Lite; list: Lite[]; onClose: () => void; onMove: (it: Lite) => void;
}) {
  const [d, setD] = useState<Detail | null>(null);
  const [err, setErr] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [bibCopied, setBibCopied] = useState(false);
  const favs = useFavs();
  const closeRef = useRef<HTMLButtonElement>(null);
  const key = item.no || item.id;
  const pos = list.findIndex((x) => x.id === item.id);

  useEffect(() => {
    let alive = true;
    setD(null);
    setErr('');
    loadDetail(item.id).then((x) => alive && setD(x)).catch((e) => alive && setErr(String(e.message || e)));
    return () => { alive = false; };
  }, [item.id, attempt]);

  const step = useCallback((delta: number) => {
    if (pos < 0 || !list.length) return;
    onMove(list[(pos + delta + list.length) % list.length]);
  }, [pos, list, onMove]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      else if (e.key === 'ArrowRight') step(1);
      else if (e.key === 'ArrowLeft') step(-1);
    };
    window.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    closeRef.current?.focus({ preventScroll: true });
    return () => { window.removeEventListener('keydown', onKey); document.body.style.overflow = ''; };
  }, [onClose, step]);

  const related = useMemo(() => {
    const dom = item.d?.[0];
    return idx.items.filter((x) => x.id !== item.id && x.grp === item.grp && (!dom || x.d?.includes(dom))).slice(0, 8);
  }, [idx, item]);

  const p = d?.paper;
  const title = p?.title || item.t;
  const links: [string, string | null | undefined][] = [
    ['论文', p?.url], ['PDF', p?.pdf], ['代码', p?.code], ['项目页', p?.project], ['高清原图', d?.original],
  ];

  return (
    <div className="modal open" onClick={onClose}>
      <div className="lb" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <button ref={closeRef} className="close" type="button" onClick={onClose} aria-label="关闭">×</button>
        <div className="stage">
          <div className="im"><img src={thumbOf(item)} alt={title} /></div>
          <div className="nav">
            <button type="button" onClick={() => step(-1)} aria-label="上一张">‹</button>
            <button type="button" onClick={() => step(1)} aria-label="下一张">›</button>
            {pos >= 0 && list.length > 1 && <span>{pos + 1} / {list.length.toLocaleString()} · ← → 翻页，Esc 关闭</span>}
          </div>
          {related.length > 0 && (
            <div className="more">
              <h5>同领域的{item.cat === 'table' ? '表格' : '图'}</h5>
              <div>{related.map((x) => (
                <img key={x.id} src={thumbOf(x)} alt={x.t} loading="lazy" tabIndex={0} role="button"
                     onClick={() => onMove(x)} onKeyDown={(e) => e.key === 'Enter' && onMove(x)} />
              ))}</div>
            </div>
          )}
        </div>
        <div className="sheet">
          <h3>{title}</h3>
          {p?.authors?.length > 0 && (
            <p className="au">{p.authors.length > 8 ? p.authors.slice(0, 8).join(', ') + ' 等' : p.authors.join(', ')}</p>
          )}
          <div className="tags">
            {item.no && <span className="v">{item.no}</span>}
            {venueLine(item) && <span>{venueLine(item)}</span>}
            {item.aw && <span>{item.aw}</span>}
            {item.ft && <span>{FIGTYPE_LABEL[item.ft] || item.ft}</span>}
            {(item.d || []).map((x) => <span key={x}>{domainLabel(idx, x)}</span>)}
            {(item.p || []).map((x) => <span key={x}>{x}</span>)}
          </div>
          {err && <div className="err">详情加载失败：{err}<button type="button" onClick={() => setAttempt((n) => n + 1)}>重试</button></div>}
          {!d && !err && <div><div className="skeleton" /><div className="skeleton" style={{ width: '70%' }} /></div>}
          {d && links.some(([, u]) => u) && (
            <div className="lk">{links.filter(([, u]) => u).map(([l, u]) => <a key={l} href={u!} target="_blank" rel="noreferrer">{l}</a>)}</div>
          )}
          {d && <Editable d={d} />}
          {p?.bibtex && (
            <div className="bib">
              <code>{p.bibtex.replace(/\s+/g, ' ')}</code>
              <button type="button" onClick={() => copyText(p.bibtex).then(() => { setBibCopied(true); setTimeout(() => setBibCopied(false), 1500); })}>
                {bibCopied ? '已复制' : '复制 BibTeX'}
              </button>
            </div>
          )}
          <button type="button" className={'favbtn' + (key in favs ? ' on' : '')} onClick={() => toggle(key)}>
            {key in favs ? '♥ 已收藏' : '♡ 收藏'}
          </button>
          {d && (
            <p className="src-note">
              {d.sources?.length
                ? <>来源：{[...new Set<string>(d.sources.map((s: { platform: string }) => s.platform))].map((s) => SOURCE[s] || s).join('、')} · </>
                : d.source?.repo ? <>来源：{d.source.repoUrl
                  ? <a href={d.source.repoUrl} target="_blank" rel="noreferrer">{d.source.repo}</a> : d.source.repo} · </> : null}
              图片版权归原论文作者所有，仅供学习参考。
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
