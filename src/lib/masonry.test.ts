import { describe, expect, it } from 'vitest';
import { distribute } from './masonry';

const it_ = (id: string, ar?: number) => ({ id, ar });

describe('distribute', () => {
  it('puts each item into the currently shortest column', () => {
    const cols = distribute([it_('a', 1), it_('b', 2), it_('c', 0.5), it_('d', 1)], 2);
    expect(cols.map((c) => c.map((x) => x.id))).toEqual([['a', 'd'], ['b', 'c']]);
  });

  it('never moves earlier items when more are appended', () => {
    const base = [it_('a', 1.2), it_('b', 0.8), it_('c', 1.6), it_('d', 1), it_('e', 2)];
    const before = distribute(base, 3).map((c) => c.map((x) => x.id));
    const after = distribute([...base, it_('f', 1), it_('g', 0.7)], 3).map((c) => c.map((x) => x.id));
    before.forEach((col, i) => expect(after[i].slice(0, col.length)).toEqual(col));
  });

  it('treats unknown aspect ratios as 4:3 and keeps the first row in reading order', () => {
    const cols = distribute([it_('a'), it_('b'), it_('c'), it_('d')], 4);
    expect(cols.map((c) => c[0].id)).toEqual(['a', 'b', 'c', 'd']);
  });
});
