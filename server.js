/**
 * server.js  —  Express estático + proxy WebSocket
 * Colócalo en la raíz (C:\vtuber) y lanza con:   node server.js
 */

require('dotenv').config();
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();

/* ---------- Configuración ---------- */
const FRONT_DIST = path.join(__dirname, 'frontend', 'out', 'renderer'); // build Electron‑Vite
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:12393';
const PORT = process.env.PORT || 3000;

/* ---------- Proxy a FastAPI ---------- */
app.use(
  '/api',
  createProxyMiddleware({
    target: BACKEND_URL,
    changeOrigin: true,
    ws: true,                      // proxy WebSocket (ASR/TTS streaming)
    pathRewrite: { '^/api': '' },  // /api/chat → /chat
  }),
);

/* ---------- Archivos estáticos SPA ---------- */
app.use(express.static(FRONT_DIST));

/* ---------- Fallback SPA (catch‑all) ----------
   app.use sin primer argumento responde a TODAS las rutas
   que no hayan sido atendidas antes, sin usar '*'
----------------------------------------------- */
app.use((_, res) => {
  res.sendFile(path.join(FRONT_DIST, 'index.html'));
});

/* ---------- Arranque ---------- */
app.listen(PORT, () => {
  console.log(`🌐  SPA servida en  http://localhost:${PORT}`);
  console.log(`🔄  Proxy /api/*  →  ${BACKEND_URL}`);
});
console.log(`🔄  Proxy WebSocket  →  ${BACKEND_URL}`);

