import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    proxy: {
      '/api-mapchaxun': {
        target: 'https://www.mapchaxun.cn',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api-mapchaxun/, ''),
        headers: {
          'Referer': 'https://www.mapchaxun.cn/Regeo',
          'Origin': 'https://www.mapchaxun.cn'
        }
      },
      '/api-ip': {
        target: 'https://4.ipw.cn',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api-ip/, '')
      }
    }
  }
})
