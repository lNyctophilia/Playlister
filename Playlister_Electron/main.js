const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const musicApi = require('./modules/music-api');
const streamExtractor = require('./modules/stream-extractor');


function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        backgroundColor: '#121212',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: true
        },
        autoHideMenuBar: true
    });

    win.loadFile('index.html');
    // win.webContents.openDevTools(); // Uncomment for debugging
}

// IPC Handlers
const ytDlpWrapper = require('./modules/yt-dlp-wrapper');

ipcMain.handle('search', async (event, query) => {
    return await musicApi.search(query);
});

ipcMain.handle('getStream', async (event, videoId) => {
    return await streamExtractor.getAudioStream(videoId);
});


app.whenReady().then(async () => {
    await musicApi.init();
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
