import { defineConfig, normalizePath } from 'vite';
import path from 'path';
import react from '@vitejs/plugin-react-swc';

// ────────────────────────────────────────────────────────────
// Polyfill de __dirname para ESM
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// ────────────────────────────────────────────────────────────

// helper para evitar repetir rutas
const r = (...segments: string[]) => path.resolve(__dirname, ...segments);

async function createConfig(outDir: string) {
  const { viteStaticCopy } = await import('vite-plugin-static-copy');

  return {
    plugins: [
      viteStaticCopy({
        targets: [
          { src: normalizePath(r('node_modules/@ricky0123/vad-web/dist/vad.worklet.bundle.min.js')), dest: './libs/' },
          { src: normalizePath(r('node_modules/@ricky0123/vad-web/dist/silero_vad_v5.onnx')),          dest: './libs/' },
          { src: normalizePath(r('node_modules/@ricky0123/vad-web/dist/silero_vad_legacy.onnx')),     dest: './libs/' },
          { src: normalizePath(r('node_modules/onnxruntime-web/dist/*.wasm')),                         dest: './libs/' },
        ],
      }),
      react(),
    ],

    resolve: {
      alias: {
        // import "@/…" = src/renderer/src/…
        '@': r('src/renderer/src'),

        // ───────────── Pixi v7 shim ─────────────
        //
        //  pixi-live2d-display‑lipsyncpatch (0.5.0‑ls‑8) espera los
        //  paquetes modulares de Pixi v7 (@pixi/core, @pixi/display…).
        //  Los mapeamos todos a pixi.js-legacy@7 para evitar conflictos.
        //
        '@pixi/core':        'pixi.js-legacy',
        '@pixi/display':     'pixi.js-legacy',
        '@pixi/runner':      'pixi.js-legacy',
        '@pixi/math':        'pixi.js-legacy',
        '@pixi/sprite':      'pixi.js-legacy',
        '@pixi/interaction': 'pixi.js-legacy',
        '@pixi/utils':       'pixi.js-legacy',
      },
    },

    // ───── Directorios y servidor ─────
    root:       r('src/renderer'),
    publicDir:  r('src/renderer/public'),
    base:       './',
    server:     { port: 3000 },

    // ───── Build (renderer) ─────
    build: {
      outDir:     r(outDir),
      emptyOutDir: true,
      assetsDir:  'assets',
      rollupOptions: {
        input: { main: r('src/renderer/index.html') },
      },
    },

    // Para que ‘vite-plugin-static-copy’ no se externalice en SSR
    ssr: { noExternal: ['vite-plugin-static-copy'] },
  };
}

export default defineConfig(async ({ mode }) => {
  // modo "web" genera build estático para publicación web;
  // cualquier otro (dev/electron) genera a dist/renderer
  return mode === 'web'
    ? createConfig('dist/web')
    : createConfig('dist/renderer');
});
