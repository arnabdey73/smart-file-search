import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom']
        }
      }
    }
  },
  // Web deployment optimizations
  base: process.env.VITE_BASE_PATH || '/',
  define: {
    __DEPLOYMENT_MODE__: JSON.stringify(process.env.VITE_DEPLOYMENT_MODE || 'web'),
    __API_BASE_URL__: JSON.stringify(process.env.VITE_API_URL || '/api')
  }
})
