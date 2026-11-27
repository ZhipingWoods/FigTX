// 占位：Task 5 实现收藏页
import type { Index, Lite } from '../lib/data';
export default function Favorites(_: { idx: Index; onOpen: (it: Lite, list: Lite[]) => void }) {
  return <div className="wrap"><div className="page-head"><h1>我的收藏</h1></div></div>;
}
