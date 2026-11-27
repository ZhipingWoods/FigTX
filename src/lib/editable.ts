import type { Detail } from './data';

/** 灯箱「可编辑区」显示哪一种：可下载的矢量文件 > 源码 > 引导用 skill 一比一重画。 */
export function editableMode(d: Pick<Detail, 'id'> & { editFiles?: unknown[]; code?: string }): 'files' | 'code' | 'redraw' {
  if (d.editFiles && d.editFiles.length) return 'files';
  if (d.code) return 'code';
  return 'redraw';
}

export const codeExt = (lang: string | null | undefined) => (lang === 'latex' ? 'tex' : lang === 'python' ? 'py' : 'txt');
