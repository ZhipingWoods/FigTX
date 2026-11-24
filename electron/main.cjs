// FigTX 桌面端主进程（macOS / Windows / Linux 通用）
//
// 注意：Vite 产物是 ES module，file:// 下会被 CORS 拦住，
// 所以这里注册自定义协议 app:// 来提供静态资源（有正常 origin）。
const { app, BrowserWindow, shell, Menu, protocol, net } = require('electron');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const DEV_SERVER = process.env.VITE_DEV_SERVER;
const isDev = Boolean(DEV_SERVER);
const DIST = path.join(__dirname, '..', 'dist');

protocol.registerSchemesAsPrivileged([
  {
    scheme: 'app',
    privileges: { standard: true, secure: true, supportFetchAPI: true, stream: true },
  },
]);

let win = null;

function registerAppProtocol() {
  protocol.handle('app', (request) => {
    const url = new URL(request.url);
    let rel = decodeURIComponent(url.pathname);
    if (rel === '/' || rel === '') rel = '/index.html';
    const abs = path.join(DIST, rel);
    // 防目录穿越
    if (!abs.startsWith(DIST)) return new Response('forbidden', { status: 403 });
    return net.fetch(pathToFileURL(abs).toString());
  });
}

function createWindow() {
  win = new BrowserWindow({
    width: 1440,
    height: 940,
    minWidth: 900,
    minHeight: 620,
    backgroundColor: '#fafaf9',
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.cjs'),
    },
    show: false,
  });

  win.once('ready-to-show', () => win.show());

  // 自检：FIGTX_SMOKE=<png路径> 时截图并退出（供 CI / 本地冒烟测试）
  if (process.env.FIGTX_SMOKE) {
    win.webContents.once('did-finish-load', () => {
      setTimeout(async () => {
        try {
          const count = await win.webContents.executeJavaScript(
            "document.querySelectorAll('.card').length",
          );
          const imgOk = await win.webContents.executeJavaScript(
            "(function(){var i=document.querySelector('.card-preview img');return i? (i.complete && i.naturalWidth>0): false})()",
          );
          const png = await win.webContents.capturePage();
          require('node:fs').writeFileSync(process.env.FIGTX_SMOKE, png.toPNG());
          console.log('SMOKE cards=' + count + ' img=' + imgOk);
        } catch (e) {
          console.log('SMOKE error ' + e);
        }
        app.quit();
      }, 3500);
    });
  }

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) shell.openExternal(url);
    return { action: 'deny' };
  });

  if (isDev) {
    win.loadURL(DEV_SERVER);
    win.webContents.openDevTools({ mode: 'detach' });
  } else {
    win.loadURL('app://figtx/index.html');
  }

  win.on('closed', () => {
    win = null;
  });
}

function buildMenu() {
  const isMac = process.platform === 'darwin';
  const template = [
    ...(isMac
      ? [{
          label: app.name,
          submenu: [
            { role: 'about' },
            { type: 'separator' },
            { role: 'hide' }, { role: 'hideOthers' }, { role: 'unhide' },
            { type: 'separator' },
            { role: 'quit' },
          ],
        }]
      : []),
    {
      label: '编辑',
      submenu: [
        { role: 'undo' }, { role: 'redo' }, { type: 'separator' },
        { role: 'cut' }, { role: 'copy' }, { role: 'paste' }, { role: 'selectAll' },
      ],
    },
    {
      label: '视图',
      submenu: [
        { role: 'reload' }, { role: 'forceReload' },
        { role: 'toggleDevTools' }, { type: 'separator' },
        { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' },
        { type: 'separator' }, { role: 'togglefullscreen' },
      ],
    },
    { label: '窗口', submenu: [{ role: 'minimize' }, { role: 'close' }] },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

app.whenReady().then(() => {
  if (!isDev) registerAppProtocol();
  buildMenu();
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
