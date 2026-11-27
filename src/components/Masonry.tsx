import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { distribute } from '../lib/masonry';

/** JS 分列瀑布流：列数随容器宽度变化；滚动加载追加的卡片只进最矮的列，已有卡片不动。 */
export default function Masonry<T extends { id: string; ar?: number }>({ items, wide, render }: {
  items: T[]; wide?: boolean; render: (it: T) => ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1200);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const min = wide ? 520 : 260;
  const cols = Math.max(1, Math.min(wide ? 2 : 4, Math.floor((width + 28) / (min + 28))));
  return (
    <div className="mcols" ref={ref}>
      {distribute(items, cols).map((col, i) => <div key={i}>{col.map(render)}</div>)}
    </div>
  );
}
