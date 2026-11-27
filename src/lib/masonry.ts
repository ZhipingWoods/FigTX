/** 瀑布流分列：每张卡放进当前最矮的一列（高度按宽高比估算）。追加新卡不会挪动已有的卡，阅读顺序按行从左到右。 */
const CAPTION = 0.32; // 标题区相对图片宽度的大致高度
const DEFAULT_AR = 4 / 3;

export function distribute<T extends { ar?: number }>(items: T[], cols: number): T[][] {
  const n = Math.max(1, cols);
  const out: T[][] = Array.from({ length: n }, () => []);
  const h = new Array(n).fill(0);
  for (const it of items) {
    let k = 0;
    for (let i = 1; i < n; i++) if (h[i] < h[k] - 1e-9) k = i;
    out[k].push(it);
    h[k] += 1 / (it.ar && it.ar > 0 ? it.ar : DEFAULT_AR) + CAPTION;
  }
  return out;
}
