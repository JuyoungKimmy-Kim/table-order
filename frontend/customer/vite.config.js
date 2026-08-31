import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 개발 서버: /api → 백엔드(FastAPI, 기본 8000)로 프록시.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
