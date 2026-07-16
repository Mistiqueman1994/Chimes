const { app, BrowserWindow, Tray, Menu, nativeImage } = require('electron');
const path = require('path');

let mainWindow = null;
let tray = null;
app.isQuitting = false;

function createWindow(){
  mainWindow = new BrowserWindow({
    width: 480,
    height: 780,
    minWidth: 380,
    minHeight: 600,
    icon: path.join(__dirname, 'icon-192.png'),
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile('index.html');

  // Keep the schedule running in the background — closing the window
  // hides it instead of quitting, so chimes still fire from the tray.
  mainWindow.on('close', (event) => {
    if(!app.isQuitting){
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

function createTray(){
  const icon = nativeImage.createFromPath(path.join(__dirname, 'icon-192.png')).resize({ width: 16, height: 16 });
  tray = new Tray(icon);
  tray.setToolTip('Bell Scheduler');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Open Bell Scheduler', click: () => { mainWindow.show(); } },
    { type: 'separator' },
    { label: 'Quit', click: () => { app.isQuitting = true; app.quit(); } }
  ]));
  tray.on('click', () => { mainWindow.show(); });
}

app.whenReady().then(() => {
  createWindow();
  createTray();

  app.on('activate', () => {
    if(BrowserWindow.getAllWindows().length === 0) createWindow();
    else mainWindow.show();
  });
});

app.on('window-all-closed', () => {
  // no-op: app lives in the tray until the user explicitly quits
});

app.on('before-quit', () => { app.isQuitting = true; });
