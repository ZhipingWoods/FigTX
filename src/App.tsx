import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Forge from './Forge';
import Header from './components/Header';
import Lightbox from './components/Lightbox';
import type { Index, Lite } from './lib/data';
import { loadIndex } from './lib/data';
import { useFavs } from './lib/favs';
import { sectionOf } from './lib/meta';
import type { Route } from './lib/route';
import { buildHash, parseHash } from './lib/route';
import Favorites from './pages/Favorites';
import Gallery from './pages/Gallery';
import Home from './pages/Home';

export default function App() {
  const [idx, setIdx] = useState<Index | null>(null);
  const [error, setError] = useState('');
  const [route, setRoute] = useState<Route>(() => parseHash(location.hash));
  // 灯箱打开时，背后显示的页面（直接打开 #F036 时用条目所属分区）
  const [bg, setBg] = useState<Route>(() => (route.open ? { page: 'home', f: {} } : route));
  const favs = useFavs();
  const listRef = useRef<Lite[]>([]);
  const pushedRef = useRef(false);

  useEffect(() => {
    loadIndex().then(setIdx).catch((e) => setError(String(e.message || e)));
  }, []);

  useEffect(() => {
    const onHash = () => setRoute(parseHash(location.hash));
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const byNo = useMemo(() => new Map((idx?.items || []).map((it) => [it.no || it.id, it])), [idx]);
  const opened = route.open && idx ? byNo.get(route.open) || null : null;

  useEffect(() => {
    if (!route.open) {
      setBg(route);
      pushedRef.current = false;
    } else if (opened && bg.page === 'home' && !pushedRef.current) {
      setBg({ page: sectionOf(opened), f: {} });
    }
    window.scrollTo({ top: route.open ? window.scrollY : 0 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [route, opened]);

  const open = useCallback((it: Lite, list: Lite[]) => {
    listRef.current = list;
    pushedRef.current = true;
    location.hash = '#' + (it.no || it.id);
  }, []);

  const close = useCallback(() => {
    if (pushedRef.current) history.back();
    else location.hash = buildHash(bg);
  }, [bg]);

  const move = useCallback((it: Lite) => {
    history.replaceState(null, '', '#' + (it.no || it.id));
    setRoute(parseHash('#' + (it.no || it.id)));
  }, []);

  const page = bg.page;
  return (
    <>
      <Header page={page} favCount={Object.keys(favs).length} solid={page !== 'home'} />
      {error && <div className="wrap"><div className="page-head"><p className="err">数据加载失败：{error}</p></div></div>}
      {!idx && !error && <div className="wrap"><div className="page-head"><p>正在加载图库…</p></div></div>}
      {idx && page === 'home' && <Home idx={idx} onOpen={open} />}
      {idx && (page === 'figures' || page === 'experiments' || page === 'tables') && (
        <Gallery idx={idx} route={bg} onOpen={open} />
      )}
      {idx && page === 'favorites' && <Favorites idx={idx} onOpen={open} />}
      {page === 'forge' && <div className="forge-page forge-scope"><Forge /></div>}
      <footer>
        FigTX · 开源的论文图表库。图片版权归原论文作者所有，仅供学习参考，见{' '}
        <a href="https://github.com/ZhipingWoods/FigTX/blob/main/IMAGES_POLICY.md" target="_blank" rel="noreferrer">图片政策</a>。
      </footer>
      {idx && opened && (
        <Lightbox idx={idx} item={opened} list={listRef.current.length ? listRef.current : [opened]} onClose={close} onMove={move} />
      )}
    </>
  );
}
