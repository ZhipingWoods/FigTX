import { describe, expect, it } from 'vitest';
import { codeExt, editableMode } from './editable';

describe('editableMode', () => {
  it('prefers downloadable vector files', () => {
    expect(editableMode({ id: 'a', editFiles: [{ ext: 'svg', label: 'SVG', path: 'x.svg' }], code: 'x' })).toBe('files');
  });
  it('falls back to source code', () => {
    expect(editableMode({ id: 'b', editFiles: [], code: '\\begin{tabular}' })).toBe('code');
  });
  it('offers a redraw guide when there is nothing editable', () => {
    expect(editableMode({ id: 'c', code: '' })).toBe('redraw');
  });
  it('maps code languages to file extensions', () => {
    expect(codeExt('latex')).toBe('tex');
    expect(codeExt('python')).toBe('py');
    expect(codeExt(null)).toBe('txt');
  });
});
