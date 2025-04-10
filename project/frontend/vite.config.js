import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:6000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api/v1')
      },
      '/ws-test': {
        target: 'ws://127.0.0.1:6000',
        ws: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:6000',
        ws: true,
        rewrite: (path) => path.replace(/^\/ws/, '/api/v1/ws')
      }
    }
  }
}) 