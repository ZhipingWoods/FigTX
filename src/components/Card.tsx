import type { Lite } from '../lib/data';
import { thumbOf } from '../lib/data';
import { toggle } from '../lib/favs';
import { venueLine } from '../lib/meta';

const Heart = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 4.5 6.8 4.5c2.1 0 3.5 1.1 5.2 3 1.7-1.9 3.1-3 5.2-3 3.8 0 5.9 3.9 4.4 7.3C19.5 16.4 12 21 12 21z" /></svg>
);

export default function Card({ it, fav, onOpen, children }: {
  it: Lite; fav: boolean; onOpen: () => void; children?: React.ReactNode;
}) {
  const key = it.no || it.id;
  return (
    <div className="card" onClick={onOpen} role="button" tabIndex={0} aria-label={it.t}
         onKeyDown={(e) => {
           if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onOpen(); }
         }}>
      {it.ed !== 'none' && <span className="sticker">{it.ed === 'editable' ? '可编辑' : '有源码'}</span>}
      <div className="im">
        <img src={thumbOf(it)} alt={it.t} loading="lazy" decoding="async"
             style={it.ar ? { aspectRatio: String(it.ar) } : undefined} />
        <button type="button" className={'heart' + (fav ? ' on' : '')} aria-label={fav ? '取消收藏' : '收藏'}
                onClick={(e) => { e.stopPropagation(); toggle(key); }}>
          <Heart />
        </button>
      </div>
      <div className="cap">
        <div className="t">{it.t || '（无标题）'}</div>
        <small>
          {it.no && <span className="no-tag">{it.no}</span>}
          {venueLine(it) && <b>{venueLine(it)}</b>}
          {it.aw && <span className={'aw' + (/best|outstanding/i.test(it.aw) ? '' : ' oral')}>{it.aw}</span>}
        </small>
      </div>
      {children}
    </div>
  );
}
