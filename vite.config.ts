import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base './' 让构建产物既能跑在 GitHub Pages 的子路径下，
// 也能被 Electron 以 file:// 方式直接加载。
//
// 关键：输出 iife 而不是 es module。
// 原因：浏览器对 file:// 下的 <script type="module"> 一律按 CORS 拦掉，
// 双击 dist/index.html 会得到空白页（实测）。打成经典脚本后
// 双击即可离线使用，不需要起本地服务器。
export default defineConfig({
  base: './',
  define: { __BUILD_ID__: JSON.stringify(String(Date.now())) },
  plugins: [react()],
  build: {
    outDir: 'dist',
    assetsInlineLimit: 0,
    chunkSizeWarningLimit: 2000,
    target: 'es2019',
    rollupOptions: {
      output: {
        format: 'iife',
        inlineDynamicImports: true,
        entryFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]',
      },
    },
  },
  server: { port: 5173 },
});
