// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from 'vitest';
import { exportJson, importJson, isFav, list, setNote, toggle } from './favs';

beforeEach(() => localStorage.clear());

describe('favs', () => {
  it('toggles on and off', () => {
    expect(toggle('F036')).toBe(true);
    expect(isFav('F036')).toBe(true);
    expect(toggle('F036')).toBe(false);
    expect(list()).toEqual([]);
  });

  it('keeps notes and lists newest first', () => {
    toggle('F001');
    toggle('T042');
    setNote('T042', '用这个表头');
    const l = list();
    expect(l.map((x) => x.id)).toEqual(['T042', 'F001']);
    expect(l[0].note).toBe('用这个表头');
  });

  it('round-trips export and import', () => {
    toggle('F001');
    setNote('F001', 'a');
    const text = exportJson();
    localStorage.clear();
    expect(importJson(text)).toEqual({ added: 1, skipped: 0 });
    expect(list()[0]).toMatchObject({ id: 'F001', note: 'a' });
  });

  it('merges imports and skips existing ids', () => {
    toggle('F001');
    const other = JSON.stringify({ v: 1, items: { F001: { addedAt: 1, note: 'x' }, F002: { addedAt: 2, note: '' } } });
    expect(importJson(other)).toEqual({ added: 1, skipped: 1 });
    expect(list().map((x) => x.id).sort()).toEqual(['F001', 'F002']);
  });

  it('rejects broken or wrong-version files without touching favourites', () => {
    toggle('F001');
    expect(() => importJson('{not json')).toThrow();
    expect(() => importJson(JSON.stringify({ v: 2, items: {} }))).toThrow(/版本/);
    expect(list().map((x) => x.id)).toEqual(['F001']);
  });
});
