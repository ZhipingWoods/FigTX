import type { Page } from '../lib/route';

const NAV: { page: Page; label: string }[] = [
  { page: 'home', label: '首页' }, { page: 'figures', label: '框架图' }, { page: 'experiments', label: '实验图' },
  { page: 'tables', label: '表格' }, { page: 'favorites', label: '收藏' }, { page: 'forge', label: '工作台' },
];

export default function Header({ page, favCount, solid }: { page: Page; favCount: number; solid: boolean }) {
  return (
    <header className={solid ? 'solid' : ''}>
      <a className="logo" href="#/">Fig<span>TX</span></a>
      <nav>
        {NAV.map((n) => (
          <a key={n.page} className={n.page === page ? 'on' : ''} href={n.page === 'home' ? '#/' : '#/' + n.page}>
            {n.label}
            {n.page === 'favorites' && favCount > 0 && <span className="badge">{favCount}</span>}
          </a>
        ))}
        <a href="https://github.com/ZhipingWoods/FigTX" target="_blank" rel="noreferrer">GitHub</a>
      </nav>
    </header>
  );
}
