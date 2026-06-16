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
    // Increase warning limit since 1MB bundle is acceptable for this SPA
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        // Code split vendor libraries into separate chunks
        manualChunks: {
          // React core
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // State management
          'state': ['zustand', '@tanstack/react-query'],
          // Charts (largest dependency)
          'charts': ['recharts'],
          // Animation
          'motion': ['framer-motion'],
          // Icons
          'icons': ['lucide-react'],
          // Utilities
          'utils': ['axios', 'date-fns', 'clsx'],
        }
      }
    }
  }
})
