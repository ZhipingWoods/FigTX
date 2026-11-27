import { describe, expect, it } from 'vitest';
import type { Lite } from './data';
import { applyFilters, facetCounts } from './filter';

const L = (o: Partial<Lite>): Lite => ({ id: 'x', no: null, cat: 'figure', ft: 'pipeline', grp: 'framework', t: '', y: 2024, ed: 'none', src: 'topconf', ...o });

const items: Lite[] = [
  L({ id: 'a', no: 'F036', t: 'Diffusion Pipeline for Video', v: ['CVPR'], y: 2025, d: ['cv', 'gen'], p: ['video generation'] }),
  L({ id: 'b', no: 'F037', t: 'Agent Memory System', v: ['NeurIPS'], y: 2024, d: ['agent'], aw: 'oral', grp: 'teaser', ft: 'teaser' }),
  L({ id: 'c', no: 'F038', t: 'Gaussian Splatting Compression', v: ['CVPR'], y: 2024, d: ['3d', 'cv'], ed: 'editable' }),
  L({ id: 'd', no: 'F001', t: 'Bar chart style', grp: 'experiment', ft: 'quantitative', ed: 'code' }),
  L({ id: 'e', no: 'T042', cat: 'table', grp: 'table', ft: null, t: 'Main results on MMEB', ed: 'code', v: ['ACL'] }),
];

describe('applyFilters', () => {
  it('keeps only the section', () => {
    expect(applyFilters(items, 'figures', {}).map((i) => i.id).sort()).toEqual(['a', 'b', 'c']);
    expect(applyFilters(items, 'experiments', {}).map((i) => i.id)).toEqual(['d']);
    expect(applyFilters(items, 'tables', {}).map((i) => i.id)).toEqual(['e']);
  });

  it('combines filters with AND across keys and OR within a key', () => {
    expect(applyFilters(items, 'figures', { d: ['cv'], v: ['CVPR'] }).map((i) => i.id).sort()).toEqual(['a', 'c']);
    expect(applyFilters(items, 'figures', { d: ['agent', '3d'] }).map((i) => i.id).sort()).toEqual(['b', 'c']);
    expect(applyFilters(items, 'figures', { d: ['cv'], y: [2024] }).map((i) => i.id)).toEqual(['c']);
    expect(applyFilters(items, 'figures', { ed: true }).map((i) => i.id)).toEqual(['c']);
    expect(applyFilters(items, 'figures', { top: true }).map((i) => i.id)).toEqual(['b']);
  });

  it('searches title, problems and venue words; numbers match exactly', () => {
    expect(applyFilters(items, 'figures', { q: 'video GENERATION' }).map((i) => i.id)).toEqual(['a']);
    expect(applyFilters(items, 'figures', { q: 'gaussian cvpr' }).map((i) => i.id)).toEqual(['c']);
    expect(applyFilters(items, 'figures', { q: 'f036' }).map((i) => i.id)).toEqual(['a']);
    expect(applyFilters(items, 'tables', { q: 'T042' }).map((i) => i.id)).toEqual(['e']);
  });

  it('returns [] when nothing matches', () => {
    expect(applyFilters(items, 'figures', { d: ['med'] })).toEqual([]);
  });

  it('sorts figures newest year first, then by number', () => {
    expect(applyFilters(items, 'figures', {}).map((i) => i.id)).toEqual(['a', 'b', 'c']);
  });
});

describe('facetCounts', () => {
  it('counts a key under the other active filters only', () => {
    const f = { d: ['cv'], v: ['CVPR'] };
    expect(facetCounts(items, 'figures', f, 'v')).toEqual({ CVPR: 2 });
    expect(facetCounts(items, 'figures', f, 'd')).toEqual({ cv: 2, gen: 1, '3d': 1 });
    expect(facetCounts(items, 'figures', {}, 'y')).toEqual({ 2025: 1, 2024: 2 });
  });
});

describe('search (review)', () => {
  it('matches Chinese domain names when labels are given', () => {
    expect(applyFilters(items, 'figures', { q: '计算机视觉' }, { cv: '计算机视觉' }).map((i) => i.id).sort()).toEqual(['a', 'c']);
  });
});
