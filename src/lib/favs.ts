/** 本地收藏：存在 localStorage（不需要登录），可导出 / 导入 JSON 换电脑。 */
import { useEffect, useState } from 'react';

const KEY = 'figtx:favs:v1';
type Entry = { addedAt: number; note: string };
type Store = { v: 1; items: Record<string, Entry> };

function read(): Store {
  try {
    const s = JSON.parse(localStorage.getItem(KEY) || '');
    if (s && s.v === 1 && s.items) return s;
  } catch {
    /* 空或损坏：当作没有收藏 */
  }
  return { v: 1, items: {} };
}

function write(s: Store) {
  localStorage.setItem(KEY, JSON.stringify(s));
  window.dispatchEvent(new Event('figtx-favs'));
}

export const isFav = (id: string) => id in read().items;

export function toggle(id: string): boolean {
  const s = read();
  const on = !(id in s.items);
  if (on) s.items[id] = { addedAt: Date.now() + Object.keys(s.items).length * 1e-3, note: '' };
  else delete s.items[id];
  write(s);
  return on;
}

export function setNote(id: string, note: string) {
  const s = read();
  if (s.items[id]) {
    s.items[id].note = note;
    write(s);
  }
}

export function list(): ({ id: string } & Entry)[] {
  return Object.entries(read().items)
    .map(([id, e]) => ({ id, ...e }))
    .sort((a, b) => b.addedAt - a.addedAt);
}

export const exportJson = () => JSON.stringify(read(), null, 1);

export function importJson(text: string): { added: number; skipped: number } {
  const incoming = JSON.parse(text);
  if (!incoming || incoming.v !== 1 || typeof incoming.items !== 'object') throw new Error('收藏文件的版本或格式不对');
  const s = read();
  let added = 0;
  let skipped = 0;
  for (const [id, e] of Object.entries(incoming.items as Record<string, Partial<Entry>>)) {
    if (id in s.items) skipped++;
    else {
      s.items[id] = { addedAt: Number(e.addedAt) || Date.now(), note: String(e.note || '') };
      added++;
    }
  }
  write(s);
  return { added, skipped };
}

/** React：订阅收藏变化（本页和其他标签页）。 */
export function useFavs(): Record<string, Entry> {
  const [items, setItems] = useState(() => read().items);
  useEffect(() => {
    const on = () => setItems(read().items);
    window.addEventListener('figtx-favs', on);
    window.addEventListener('storage', on);
    return () => {
      window.removeEventListener('figtx-favs', on);
      window.removeEventListener('storage', on);
    };
  }, []);
  return items;
}
