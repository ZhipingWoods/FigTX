import { useMemo, useRef, useState } from 'react';
import Card from '../components/Card';
import Masonry from '../components/Masonry';
import type { Index, Lite } from '../lib/data';
import { exportJson, importJson, list as listFavs, setNote, useFavs } from '../lib/favs';

export default function Favorites({ idx, onOpen }: { idx: Index; onOpen: (it: Lite, list: Lite[]) => void }) {
  const favs = useFavs();
  const [msg, setMsg] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const byKey = useMemo(() => new Map(idx.items.map((it) => [it.no || it.id, it])), [idx]);
  const entries = useMemo(() => listFavs().filter((e) => byKey.has(e.id)), [favs, byKey]);
  const items = entries.map((e) => byKey.get(e.id)!);
  const noteOf = new Map(entries.map((e) => [e.id, e.note]));
  const missing = Object.keys(favs).length - entries.length;

  const doExport = () => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([exportJson()], { type: 'application/json' }));
    a.download = 'figtx-favorites.json';
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const doImport = async (file: File) => {
    try {
      const r = importJson(await file.text());
      setMsg(`导入完成：新增 ${r.added} 个，已存在 ${r.skipped} 个。`);
    } catch (e) {
      setMsg('导入失败：' + (e instanceof Error ? e.message : String(e)) + '。原有收藏没有改动。');
    }
  };

  return (
    <div className="wrap">
      <div className="page-head">
        <h1>我的收藏</h1>
        <p>收藏只存在这台设备的浏览器里，不需要登录。换电脑时先导出，再在新电脑上导入。</p>
      </div>
      <div className="fav-tools">
        <button type="button" onClick={doExport} disabled={!entries.length}>导出收藏</button>
        <button type="button" onClick={() => fileRef.current?.click()}>导入收藏</button>
        <input ref={fileRef} type="file" accept="application/json,.json" hidden
               onChange={(e) => { const f = e.target.files?.[0]; if (f) doImport(f); e.target.value = ''; }} />
        {msg && <span className="msg">{msg}</span>}
        {missing > 0 && <span className="msg">另有 {missing} 个收藏的条目已不在图库中。</span>}
      </div>
      {items.length === 0 ? (
        <div className="empty">还没有收藏。在图库里点卡片右上角的 ♡，或在详情里点「收藏」。</div>
      ) : (
        <Masonry items={items} render={(it) => (
          <Card key={it.id} it={it} fav onOpen={() => onOpen(it, items)}>
            <input className="note" placeholder="备注（例如：参考它的配色）" defaultValue={noteOf.get(it.no || it.id) || ''}
                   onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}
                   onBlur={(e) => setNote(it.no || it.id, e.target.value)} />
          </Card>
        )} />
      )}
    </div>
  );
}
