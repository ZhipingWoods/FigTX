/** 极简语法高亮（LaTeX / Python），只用于灯箱里的源码预览。 */
import type { ReactNode } from 'react';

const RULES: Record<string, [RegExp, string][]> = {
  latex: [[/%.*$/gm, 'cm'], [/\\[a-zA-Z@]+\*?/g, 'kw'], [/\b\d+(\.\d+)?\b/g, 'nm']],
  python: [
    [/#.*$/gm, 'cm'], [/("""[\s\S]*?"""|'[^'\n]*'|"[^"\n]*")/g, 'st'],
    [/\b(import|from|as|def|return|for|in|if|else|elif|with|class|lambda|None|True|False)\b/g, 'kw'],
    [/\b\d+(\.\d+)?\b/g, 'nm'],
  ],
};

export function highlight(code: string, lang: string | null | undefined): ReactNode[] {
  const rules = RULES[lang || ''] || [];
  const marks: { s: number; e: number; c: string }[] = [];
  for (const [re, c] of rules) {
    for (const m of code.matchAll(re)) {
      const s = m.index!;
      const e = s + m[0].length;
      if (!marks.some((x) => s < x.e && e > x.s)) marks.push({ s, e, c });
    }
  }
  marks.sort((a, b) => a.s - b.s);
  const out: ReactNode[] = [];
  let last = 0;
  marks.forEach((m, i) => {
    if (m.s > last) out.push(code.slice(last, m.s));
    out.push(<span key={i} className={m.c}>{code.slice(m.s, m.e)}</span>);
    last = m.e;
  });
  out.push(code.slice(last));
  return out;
}
