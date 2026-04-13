import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { copyFileSync, mkdirSync, readdirSync, statSync, existsSync } from 'fs';
import { join, resolve } from 'path';

/* Recursively copy a directory — used to vendor MediaPipe WASM files so they
// are served from the same origin and can't be blocked by ad blockers or CDN
// outages. */

function copyDir(src, dest) {
  if (!existsSync(src)) return;
  mkdirSync(dest, { recursive: true });
  for (const entry of readdirSync(src)) {
    const s = join(src, entry);
    const d = join(dest, entry);
    statSync(s).isDirectory() ? copyDir(s, d) : copyFileSync(s, d);
  }
}

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'vendor-mediapipe',
      buildStart() {
        const root = resolve(__dirname);
        copyDir(
          join(root, 'node_modules/@mediapipe/face_mesh'),
          join(root, 'public/mediapipe/face_mesh'),
        );
      },
    },
  ],
  server: {
    port: 3000,
    host: true,
  },
  build: {
    outDir: 'dist',
  },
});
