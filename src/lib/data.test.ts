// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { shardOf, pad } from '../../tools/shard.mjs';
import { _reset, loadDetail, loadIndex, setScriptLoader, thumbOf } from './data';

const ID = 'tc-icml2023-0064';

function fakeLoader(fail = new Set<string>()) {
  const calls: string[] = [];
  const fn = vi.fn(async (url: string) => {
    calls.push(url);
    if (fail.has(url)) throw new Error('offline');
    if (url.includes('index.js')) {
      (window as any).__FIGTX_INDEX__ = { v: 1, items: [{ id: ID, cat: 'figure' }], stats: {}, taxonomy: [] };
    } else {
      const n = Number(url.match(/detail-(\d+)\.js/)![1]);
      (window as any).__figtxDetail(n, n === shardOf(ID) ? { [ID]: { id: ID, title: 'BPipe' } } : {});
    }
  });
  return { fn, calls };
}

beforeEach(() => _reset());

describe('data loader', () => {
  it('loads the index once', async () => {
    const { fn, calls } = fakeLoader();
    setScriptLoader(fn);
    const [a, b] = await Promise.all([loadIndex(), loadIndex()]);
    expect(a.items[0].id).toBe(ID);
    expect(a).toBe(b);
    expect(calls).toHaveLength(1);
    expect(calls[0]).toMatch(/^\.\/data\/index\.js(\?v=\d+)?$/);
  });

  it('injects each detail shard only once', async () => {
    const { fn, calls } = fakeLoader();
    setScriptLoader(fn);
    const [d1, d2] = await Promise.all([loadDetail(ID), loadDetail(ID)]);
    expect(d1.title).toBe('BPipe');
    expect(d2).toBe(d1);
    expect(calls).toEqual([`./data/detail-${pad(shardOf(ID))}.js`]);
  });

  it('rejects on a failed shard and retries next time', async () => {
    const url = `./data/detail-${pad(shardOf(ID))}.js`;
    const fail = new Set([url]);
    const { fn, calls } = fakeLoader(fail);
    setScriptLoader(fn);
    await expect(loadDetail(ID)).rejects.toThrow();
    fail.clear();
    expect((await loadDetail(ID)).title).toBe('BPipe');
    expect(calls).toEqual([url, url]);
  });

  it('rejects for an unknown id', async () => {
    setScriptLoader(fakeLoader().fn);
    await expect(loadDetail('nope-unknown')).rejects.toThrow(/not found/);
  });

  it('derives thumbnail paths', () => {
    expect(thumbOf({ id: 'tc-x' } as any)).toBe('thumbs/tc-x.webp');
    expect(thumbOf({ id: 'fig-a', r: 'renders-fig/a.webp' } as any)).toBe('renders-fig/a.webp');
  });

  it('adds the index version to shard URLs (cache busting)', async () => {
    const calls: string[] = [];
    setScriptLoader(async (url) => {
      calls.push(url);
      if (url.includes('index.js')) {
        (window as any).__FIGTX_INDEX__ = { v: 1, generatedAt: '2026-11-27T08:00:00Z', items: [], stats: {}, taxonomy: [] };
      } else {
        const n = Number(url.match(/detail-(\d+)\.js/)![1]);
        (window as any).__figtxDetail(n, { [ID]: { id: ID } });
      }
    });
    await loadIndex();
    await loadDetail(ID);
    expect(calls[1]).toBe(`./data/detail-${pad(shardOf(ID))}.js?v=2026-11-27T08%3A00%3A00Z`);
  });
});
