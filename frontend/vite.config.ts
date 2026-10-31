import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Build into the APX app's static/ dir so FastAPI can serve the compiled SPA.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../src/apx_app/static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
    },
  },
});
