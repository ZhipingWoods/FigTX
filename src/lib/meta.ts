import type { Index, Lite } from './data';
import type { Page } from './route';

export const FIGTYPE_LABEL: Record<string, string> = {
  framework: '框架图', architecture: '架构图', pipeline: '流程图', mechanism: '机制示意',
  teaser: 'Teaser 主图', conceptual: '概念图', taxonomy: '分类图', comparison: '对比图',
  quantitative: '实验·定量', qualitative: '实验·定性', results: '结果对比', efficiency: '效率分析',
  tradeoff: '权衡曲线', motivation: '动机图', style: '绘图样式',
};

export const SECTIONS: { page: Exclude<Page, 'home' | 'favorites' | 'forge'>; label: string; desc: string;
  match: (it: Lite) => boolean }[] = [
  { page: 'figures', label: '框架图', desc: '方法总览、Pipeline、Figure 1 与 Teaser', match: (it) => it.grp === 'framework' || it.grp === 'teaser' },
  { page: 'experiments', label: '实验图', desc: '柱状、折线、热力图、雷达……附 matplotlib 源码', match: (it) => it.grp === 'experiment' },
  { page: 'tables', label: '表格', desc: 'booktabs 三线表，复制 .tex 就能编译', match: (it) => it.cat === 'table' },
];

export const sectionOf = (it: Lite) => SECTIONS.find((s) => s.match(it))!.page;

export function domainLabel(idx: Index, key: string) {
  return idx.taxonomy.find((d) => d.key === key)?.zh || key;
}

export const numOf = (no: string | null) => (no ? parseInt(no.slice(1), 10) : Number.MAX_SAFE_INTEGER);

export function venueLine(it: Lite) {
  return [(it.v || []).join(' / '), it.y].filter(Boolean).join(' ');
}
