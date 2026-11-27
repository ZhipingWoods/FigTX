import { describe, expect, it } from 'vitest';
import { buildHash, parseHash } from './route';

describe('route', () => {
  it('parses pages and filters', () => {
    expect(parseHash('#/figures?d=cv,nlp&v=CVPR&y=2025&ed=1&q=diffusion%20model')).toEqual({
      page: 'figures', f: { d: ['cv', 'nlp'], v: ['CVPR'], y: [2025], ed: true, q: 'diffusion model' },
    });
    expect(parseHash('#/tables')).toEqual({ page: 'tables', f: {} });
  });

  it('round-trips', () => {
    const r = { page: 'experiments' as const, f: { ft: ['quantitative'], top: true, p: ['novel view synthesis'] } };
    expect(parseHash(buildHash(r))).toEqual(r);
    expect(buildHash({ page: 'home', f: {} })).toBe('#/');
  });

  it('keeps old number links', () => {
    expect(parseHash('#T042')).toEqual({ page: 'home', f: {}, open: 'T042' });
    expect(parseHash('#f036')).toEqual({ page: 'home', f: {}, open: 'F036' });
    expect(buildHash({ page: 'figures', f: {}, open: 'F036' })).toBe('#F036');
  });

  it('falls back to home', () => {
    expect(parseHash('')).toEqual({ page: 'home', f: {} });
    expect(parseHash('#/nonsense?x=1')).toEqual({ page: 'home', f: {} });
    expect(parseHash('#/figures?y=abc')).toEqual({ page: 'figures', f: {} });
  });
});

describe('route edge cases (review)', () => {
  it('survives malformed percent escapes', () => {
    expect(parseHash('#/figures?q=50%')).toEqual({ page: 'figures', f: { q: '50%' } });
  });

  it('round-trips &, +, % and commas in values', () => {
    const r = { page: 'figures' as const, f: { q: 'C++ & 3D 50%', p: ['correcting linguistic, factual, and logical errors', 'a+b'] } };
    expect(parseHash(buildHash(r))).toEqual(r);
  });

  it('keeps old comma-joined links working', () => {
    expect(parseHash('#/figures?d=cv,nlp').f.d).toEqual(['cv', 'nlp']);
  });
});
