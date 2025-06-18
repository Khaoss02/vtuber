"use strict";
const electron = require("electron");
const preload = require("@electron-toolkit/preload");
const api = {
  setIgnoreMouseEvents: (ignore) => {
    electron.ipcRenderer.send("set-ignore-mouse-events", ignore);
  },
  toggleForceIgnoreMouse: () => {
    electron.ipcRenderer.send("toggle-force-ignore-mouse");
  },
  onForceIgnoreMouseChanged: (callback) => {
    const handler = (_event, isForced) => callback(isForced);
    electron.ipcRenderer.on("force-ignore-mouse-changed", handler);
    return () => electron.ipcRenderer.removeListener("force-ignore-mouse-changed", handler);
  },
  showContextMenu: () => {
    console.log("Preload showContextMenu");
    electron.ipcRenderer.send("show-context-menu");
  },
  onModeChanged: (callback) => {
    electron.ipcRenderer.on("mode-changed", (_, mode) => callback(mode));
  },
  onMicToggle: (callback) => {
    const handler = (_event) => callback();
    electron.ipcRenderer.on("mic-toggle", handler);
    return () => electron.ipcRenderer.removeListener("mic-toggle", handler);
  },
  onInterrupt: (callback) => {
    const handler = (_event) => callback();
    electron.ipcRenderer.on("interrupt", handler);
    return () => electron.ipcRenderer.removeListener("interrupt", handler);
  },
  updateComponentHover: (componentId, isHovering) => {
    electron.ipcRenderer.send("update-component-hover", componentId, isHovering);
  },
  onToggleInputSubtitle: (callback) => {
    const handler = (_event) => callback();
    electron.ipcRenderer.on("toggle-input-subtitle", handler);
    return () => electron.ipcRenderer.removeListener("toggle-input-subtitle", handler);
  },
  onToggleScrollToResize: (callback) => {
    const handler = (_event) => callback();
    electron.ipcRenderer.on("toggle-scroll-to-resize", handler);
    return () => electron.ipcRenderer.removeListener("toggle-scroll-to-resize", handler);
  },
  onSwitchCharacter: (callback) => {
    const handler = (_event, filename) => callback(filename);
    electron.ipcRenderer.on("switch-character", handler);
    return () => electron.ipcRenderer.removeListener("switch-character", handler);
  },
  getConfigFiles: () => electron.ipcRenderer.invoke("get-config-files"),
  updateConfigFiles: (files) => {
    electron.ipcRenderer.send("update-config-files", files);
  }
};
if (process.contextIsolated) {
  try {
    electron.contextBridge.exposeInMainWorld("electron", {
      ...preload.electronAPI,
      desktopCapturer: {
        getSources: (options) => electron.desktopCapturer.getSources(options)
      },
      ipcRenderer: {
        invoke: (channel, ...args) => electron.ipcRenderer.invoke(channel, ...args),
        on: (channel, func) => electron.ipcRenderer.on(channel, func),
        once: (channel, func) => electron.ipcRenderer.once(channel, func),
        removeListener: (channel, func) => electron.ipcRenderer.removeListener(channel, func),
        removeAllListeners: (channel) => electron.ipcRenderer.removeAllListeners(channel),
        send: (channel, ...args) => electron.ipcRenderer.send(channel, ...args)
      }
    });
    electron.contextBridge.exposeInMainWorld("api", api);
  } catch (error) {
    console.error(error);
  }
} else {
  window.electron = preload.electronAPI;
  window.api = api;
}
