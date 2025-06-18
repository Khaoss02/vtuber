"use strict";
const electron = require("electron");
const utils = require("@electron-toolkit/utils");
const path = require("path");
const isMac = process.platform === "darwin";
class WindowManager {
  constructor() {
    this.window = null;
    this.windowedBounds = null;
    this.hoveringComponents = /* @__PURE__ */ new Set();
    this.currentMode = "window";
    this.forceIgnoreMouse = false;
    electron.ipcMain.on("renderer-ready-for-mode-change", (_event, newMode) => {
      if (newMode === "pet") {
        setTimeout(() => {
          this.continueSetWindowModePet();
        }, 500);
      } else {
        setTimeout(() => {
          this.continueSetWindowModeWindow();
        }, 500);
      }
    });
    electron.ipcMain.on("mode-change-rendered", () => {
      this.window?.setOpacity(1);
    });
    electron.ipcMain.on("window-unfullscreen", () => {
      const window = this.getWindow();
      if (window && window.isFullScreen()) {
        window.setFullScreen(false);
      }
    });
    electron.ipcMain.on("toggle-force-ignore-mouse", () => {
      this.toggleForceIgnoreMouse();
    });
  }
  createWindow(options) {
    this.window = new electron.BrowserWindow({
      width: 900,
      height: 670,
      show: false,
      transparent: true,
      backgroundColor: "#ffffff",
      autoHideMenuBar: true,
      frame: false,
      icon: process.platform === "win32" ? path.join(__dirname, "../../resources/icon.ico") : path.join(__dirname, "../../resources/icon.png"),
      ...isMac ? { titleBarStyle: "hiddenInset" } : {},
      webPreferences: {
        preload: path.join(__dirname, "../preload/index.js"),
        sandbox: false,
        contextIsolation: true,
        nodeIntegration: true
      },
      hasShadow: false,
      paintWhenInitiallyHidden: true,
      ...options
    });
    this.setupWindowEvents();
    this.loadContent();
    this.window.on("enter-full-screen", () => {
      this.window?.webContents.send("window-fullscreen-change", true);
    });
    this.window.on("leave-full-screen", () => {
      this.window?.webContents.send("window-fullscreen-change", false);
    });
    return this.window;
  }
  setupWindowEvents() {
    if (!this.window) return;
    this.window.on("ready-to-show", () => {
      this.window?.show();
      this.window?.webContents.send(
        "window-maximized-change",
        this.window.isMaximized()
      );
    });
    this.window.on("maximize", () => {
      this.window?.webContents.send("window-maximized-change", true);
    });
    this.window.on("unmaximize", () => {
      this.window?.webContents.send("window-maximized-change", false);
    });
    this.window.on("resize", () => {
      const window = this.getWindow();
      if (window) {
        const bounds = window.getBounds();
        const { width, height } = electron.screen.getPrimaryDisplay().workArea;
        const isMaximized = bounds.width >= width && bounds.height >= height;
        window.webContents.send("window-maximized-change", isMaximized);
      }
    });
    this.window.webContents.setWindowOpenHandler((details) => {
      electron.shell.openExternal(details.url);
      return { action: "deny" };
    });
  }
  loadContent() {
    if (!this.window) return;
    if (utils.is.dev && process.env.ELECTRON_RENDERER_URL) {
      this.window.loadURL(process.env.ELECTRON_RENDERER_URL);
    } else {
      this.window.loadFile(path.join(__dirname, "../renderer/index.html"));
    }
  }
  setWindowMode(mode) {
    if (!this.window) return;
    this.currentMode = mode;
    this.window.setOpacity(0);
    if (mode === "window") {
      this.setWindowModeWindow();
    } else {
      this.setWindowModePet();
    }
  }
  setWindowModeWindow() {
    if (!this.window) return;
    this.window.setAlwaysOnTop(false);
    this.window.setIgnoreMouseEvents(false);
    this.window.setSkipTaskbar(false);
    this.window.setResizable(true);
    this.window.setFocusable(true);
    this.window.setAlwaysOnTop(false);
    this.window.setBackgroundColor("#ffffff");
    this.window.webContents.send("pre-mode-changed", "window");
  }
  continueSetWindowModeWindow() {
    if (!this.window) return;
    if (this.windowedBounds) {
      this.window.setBounds(this.windowedBounds);
    } else {
      this.window.setSize(900, 670);
      this.window.center();
    }
    if (isMac) {
      this.window.setWindowButtonVisibility(true);
      this.window.setVisibleOnAllWorkspaces(false, {
        visibleOnFullScreen: false
      });
    }
    this.window?.setIgnoreMouseEvents(false, { forward: true });
    this.window.webContents.send("mode-changed", "window");
  }
  setWindowModePet() {
    if (!this.window) return;
    this.windowedBounds = this.window.getBounds();
    if (this.window.isFullScreen()) {
      this.window.setFullScreen(false);
    }
    this.window.setBackgroundColor("#00000000");
    this.window.setAlwaysOnTop(true, "screen-saver");
    this.window.setPosition(0, 0);
    this.window.webContents.send("pre-mode-changed", "pet");
  }
  continueSetWindowModePet() {
    if (!this.window) return;
    const { width, height } = electron.screen.getPrimaryDisplay().workAreaSize;
    this.window.setSize(width, height);
    if (isMac) this.window.setWindowButtonVisibility(false);
    this.window.setResizable(false);
    this.window.setSkipTaskbar(true);
    this.window.setFocusable(false);
    if (isMac) {
      this.window.setIgnoreMouseEvents(true);
      this.window.setVisibleOnAllWorkspaces(true, {
        visibleOnFullScreen: true
      });
    } else {
      this.window.setIgnoreMouseEvents(true, { forward: true });
    }
    this.window.webContents.send("mode-changed", "pet");
  }
  getWindow() {
    return this.window;
  }
  setIgnoreMouseEvents(ignore) {
    if (!this.window) return;
    if (isMac) {
      this.window.setIgnoreMouseEvents(ignore);
    } else {
      this.window.setIgnoreMouseEvents(ignore, { forward: true });
    }
  }
  maximizeWindow() {
    if (!this.window) return;
    if (this.isWindowMaximized()) {
      if (this.windowedBounds) {
        this.window.setBounds(this.windowedBounds);
        this.windowedBounds = null;
        this.window.webContents.send("window-maximized-change", false);
      }
    } else {
      this.windowedBounds = this.window.getBounds();
      const { width, height } = electron.screen.getPrimaryDisplay().workArea;
      this.window.setBounds({
        x: 0,
        y: 0,
        width,
        height
      });
      this.window.webContents.send("window-maximized-change", true);
    }
  }
  isWindowMaximized() {
    if (!this.window) return false;
    const bounds = this.window.getBounds();
    const { width, height } = electron.screen.getPrimaryDisplay().workArea;
    return bounds.width >= width && bounds.height >= height;
  }
  updateComponentHover(componentId, isHovering) {
    if (this.currentMode === "window") return;
    if (this.forceIgnoreMouse) return;
    if (isHovering) {
      this.hoveringComponents.add(componentId);
    } else {
      this.hoveringComponents.delete(componentId);
    }
    if (this.window) {
      const shouldIgnore = this.hoveringComponents.size === 0;
      if (isMac) {
        this.window.setIgnoreMouseEvents(shouldIgnore);
      } else {
        this.window.setIgnoreMouseEvents(shouldIgnore, { forward: true });
      }
      if (!shouldIgnore) {
        this.window.setFocusable(true);
      }
    }
  }
  // Toggle force ignore mouse events
  toggleForceIgnoreMouse() {
    this.forceIgnoreMouse = !this.forceIgnoreMouse;
    if (this.forceIgnoreMouse) {
      if (isMac) {
        this.window?.setIgnoreMouseEvents(true);
      } else {
        this.window?.setIgnoreMouseEvents(true, { forward: true });
      }
    } else {
      const shouldIgnore = this.hoveringComponents.size === 0;
      if (isMac) {
        this.window?.setIgnoreMouseEvents(shouldIgnore);
      } else {
        this.window?.setIgnoreMouseEvents(shouldIgnore, { forward: true });
      }
    }
    this.window?.webContents.send("force-ignore-mouse-changed", this.forceIgnoreMouse);
  }
  // Get current force ignore state
  isForceIgnoreMouse() {
    return this.forceIgnoreMouse;
  }
}
const trayIcon = path.join(__dirname, "../../resources/icon.png");
class MenuManager {
  constructor(onModeChange) {
    this.onModeChange = onModeChange;
    this.tray = null;
    this.currentMode = "window";
    this.configFiles = [];
    this.setupContextMenu();
  }
  createTray() {
    const icon = electron.nativeImage.createFromPath(trayIcon);
    const trayIconResized = icon.resize({
      width: process.platform === "win32" ? 16 : 18,
      height: process.platform === "win32" ? 16 : 18
    });
    this.tray = new electron.Tray(trayIconResized);
    this.updateTrayMenu();
  }
  getModeMenuItems() {
    return [
      {
        label: "Window Mode",
        type: "radio",
        checked: this.currentMode === "window",
        click: () => {
          this.setMode("window");
        }
      },
      {
        label: "Pet Mode",
        type: "radio",
        checked: this.currentMode === "pet",
        click: () => {
          this.setMode("pet");
        }
      }
    ];
  }
  updateTrayMenu() {
    if (!this.tray) return;
    const contextMenu = electron.Menu.buildFromTemplate([
      ...this.getModeMenuItems(),
      { type: "separator" },
      // Only show toggle mouse ignore in pet mode
      ...this.currentMode === "pet" ? [
        {
          label: "Toggle Mouse Passthrough",
          click: () => {
            const windows = electron.BrowserWindow.getAllWindows();
            windows.forEach((window) => {
              window.webContents.send("toggle-force-ignore-mouse");
            });
          }
        },
        { type: "separator" }
      ] : [],
      {
        label: "Show",
        click: () => {
          const windows = electron.BrowserWindow.getAllWindows();
          windows.forEach((window) => {
            window.show();
          });
        }
      },
      {
        label: "Hide",
        click: () => {
          const windows = electron.BrowserWindow.getAllWindows();
          windows.forEach((window) => {
            window.hide();
          });
        }
      },
      {
        label: "Exit",
        click: () => {
          electron.app.quit();
        }
      }
    ]);
    this.tray.setToolTip("Open LLM VTuber");
    this.tray.setContextMenu(contextMenu);
  }
  getContextMenuItems(event) {
    const template = [
      {
        label: "Toggle Microphone",
        click: () => {
          event.sender.send("mic-toggle");
        }
      },
      {
        label: "Interrupt",
        click: () => {
          event.sender.send("interrupt");
        }
      },
      { type: "separator" },
      // Only show in pet mode
      ...this.currentMode === "pet" ? [
        {
          label: "Toggle Mouse Passthrough",
          click: () => {
            event.sender.send("toggle-force-ignore-mouse");
          }
        }
      ] : [],
      {
        label: "Toggle Scrolling to Resize",
        click: () => {
          event.sender.send("toggle-scroll-to-resize");
        }
      },
      // Only show this item in pet mode
      ...this.currentMode === "pet" ? [
        {
          label: "Toggle InputBox and Subtitle",
          click: () => {
            event.sender.send("toggle-input-subtitle");
          }
        }
      ] : [],
      { type: "separator" },
      ...this.getModeMenuItems(),
      { type: "separator" },
      {
        label: "Switch Character",
        visible: this.currentMode === "pet",
        submenu: this.configFiles.map((config) => ({
          label: config.name,
          click: () => {
            event.sender.send("switch-character", config.filename);
          }
        }))
      },
      { type: "separator" },
      {
        label: "Hide",
        click: () => {
          const windows = electron.BrowserWindow.getAllWindows();
          windows.forEach((window) => {
            window.hide();
          });
        }
      },
      {
        label: "Exit",
        click: () => {
          electron.app.quit();
        }
      }
    ];
    return template;
  }
  setupContextMenu() {
    electron.ipcMain.on("show-context-menu", (event) => {
      const win = electron.BrowserWindow.fromWebContents(event.sender);
      if (win) {
        const screenPoint = electron.screen.getCursorScreenPoint();
        const menu = electron.Menu.buildFromTemplate(this.getContextMenuItems(event));
        menu.popup({
          window: win,
          x: Math.round(screenPoint.x),
          y: Math.round(screenPoint.y)
        });
      }
    });
  }
  setMode(mode) {
    this.currentMode = mode;
    this.updateTrayMenu();
    this.onModeChange(mode);
  }
  destroy() {
    this.tray?.destroy();
    this.tray = null;
  }
  updateConfigFiles(files) {
    this.configFiles = files;
  }
}
let windowManager;
let menuManager;
let isQuitting = false;
function setupIPC() {
  electron.ipcMain.handle("get-platform", () => process.platform);
  electron.ipcMain.on("set-ignore-mouse-events", (_event, ignore) => {
    const window = windowManager.getWindow();
    if (window) {
      windowManager.setIgnoreMouseEvents(ignore);
    }
  });
  electron.ipcMain.on("window-minimize", () => {
    windowManager.getWindow()?.minimize();
  });
  electron.ipcMain.on("window-maximize", () => {
    const window = windowManager.getWindow();
    if (window) {
      windowManager.maximizeWindow();
    }
  });
  electron.ipcMain.on("window-close", () => {
    const window = windowManager.getWindow();
    if (window) {
      if (process.platform === "darwin") {
        window.hide();
      } else {
        window.close();
      }
    }
  });
  electron.ipcMain.on(
    "update-component-hover",
    (_event, componentId, isHovering) => {
      windowManager.updateComponentHover(componentId, isHovering);
    }
  );
  electron.ipcMain.handle("get-config-files", () => {
    const configFiles = JSON.parse(localStorage.getItem("configFiles") || "[]");
    menuManager.updateConfigFiles(configFiles);
    return configFiles;
  });
  electron.ipcMain.on("update-config-files", (_event, files) => {
    menuManager.updateConfigFiles(files);
  });
  electron.ipcMain.handle("get-screen-capture", async () => {
    const sources = await electron.desktopCapturer.getSources({ types: ["screen"] });
    return sources[0].id;
  });
}
electron.app.whenReady().then(() => {
  utils.electronApp.setAppUserModelId("com.electron");
  windowManager = new WindowManager();
  menuManager = new MenuManager((mode) => windowManager.setWindowMode(mode));
  const window = windowManager.createWindow({
    titleBarOverlay: {
      color: "#111111",
      symbolColor: "#FFFFFF",
      height: 30
    }
  });
  menuManager.createTray();
  window.on("close", (event) => {
    if (!isQuitting) {
      event.preventDefault();
      window.hide();
    }
    return false;
  });
  if (process.env.NODE_ENV === "development") {
    electron.globalShortcut.register("F12", () => {
      const window2 = windowManager.getWindow();
      if (!window2) return;
      if (window2.webContents.isDevToolsOpened()) {
        window2.webContents.closeDevTools();
      } else {
        window2.webContents.openDevTools();
      }
    });
  }
  setupIPC();
  electron.app.on("activate", () => {
    const window2 = windowManager.getWindow();
    if (window2) {
      window2.show();
    }
  });
  electron.app.on("browser-window-created", (_, window2) => {
    utils.optimizer.watchWindowShortcuts(window2);
  });
  electron.app.on("web-contents-created", (_, contents) => {
    contents.session.setPermissionRequestHandler((webContents, permission, callback) => {
      if (permission === "media") {
        callback(true);
      } else {
        callback(false);
      }
    });
  });
});
electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    electron.app.quit();
  }
});
electron.app.on("before-quit", () => {
  isQuitting = true;
  menuManager.destroy();
  electron.globalShortcut.unregisterAll();
});
