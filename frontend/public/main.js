const { app, BrowserWindow, ipcMain, shell } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

const isDev = !app.isPackaged

let mainWindow
let backendProcess = null

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 720,
    backgroundColor: '#121212',
    icon: path.join(__dirname, 'public', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    }
  })

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, 'frontend', 'dist', 'index.html'))
  }

  // Abrir links externos en el navegador
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
    if (backendProcess) {
      backendProcess.kill()
      backendProcess = null
    }
  })
}

function startBackend() {
  if (backendProcess) return // ya arrancado

  const exe = isDev
    ? 'python'
    : path.join(process.resourcesPath, 'backend.exe')

  const args = isDev
    ? ['server/run_server.py']
    : []

  backendProcess = spawn(exe, args, { stdio: 'inherit' })

  backendProcess.on('close', (code) => {
    console.log('Backend closed with code', code)
    backendProcess = null
  })

  backendProcess.on('error', (err) => {
    console.error('Error starting backend:', err)
  })
}

app.whenReady().then(() => {
  startBackend()
  createMainWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

ipcMain.handle('app:version', () => app.getVersion())
