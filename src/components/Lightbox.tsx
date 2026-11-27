// 占位：Task 4 实现灯箱
import type { Index, Lite } from '../lib/data';
export default function Lightbox({ item, onClose }: { idx: Index; item: Lite; list: Lite[]; onClose: () => void; onMove: (it: Lite) => void }) {
  return <div className="modal open" onClick={onClose}><div className="lb"><h3>{item.t}</h3></div></div>;
}
