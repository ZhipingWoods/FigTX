import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base './' 让构建产物既能跑在 GitHub Pages 的子路径下，
// 也能被 Electron 以 file:// 方式直接加载。
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: 'dist',
    assetsInlineLimit: 0,
    chunkSizeWarningLimit: 2000,
  },
  server: { port: 5173 },
});
