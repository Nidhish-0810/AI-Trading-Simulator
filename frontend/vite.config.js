import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      }
    }
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  },
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'state': ['zustand', '@tanstack/react-query'],
          'charts': ['recharts'],
          'motion': ['framer-motion'],
          'icons': ['lucide-react'],
          'utils': ['axios', 'date-fns', 'clsx'],
        }
      }
    }
  }
})
