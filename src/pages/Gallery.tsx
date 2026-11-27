// 占位：Task 3 实现图库页
import type { Index, Lite } from '../lib/data';
import type { Route } from '../lib/route';
export default function Gallery(_: { idx: Index; route: Route; onOpen: (it: Lite, list: Lite[]) => void }) {
  return <div className="wrap"><div className="page-head"><h1>图库</h1></div></div>;
}
