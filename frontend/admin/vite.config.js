import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 개발 시 /api 요청을 백엔드(FastAPI, 기본 8000)로 프록시.
// SSE(/api/admin/orders/stream) 도 동일 프록시 사용.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
