// 预留：如需向渲染进程暴露安全 API，在此通过 contextBridge 添加。
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('figtx', {
  platform: process.platform,
  versions: {
    electron: process.versions.electron,
    chrome: process.versions.chrome,
    node: process.versions.node,
  },
});
