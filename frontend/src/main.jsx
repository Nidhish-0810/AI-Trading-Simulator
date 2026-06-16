import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import App from './App.jsx'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,
      retry: (failureCount, error) => {
        if (error?.response?.status === 401) return false
        return failureCount < 2
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        <Toaster
          position="top-right"
          gutter={8}
          containerStyle={{ top: 80 }}
          toastOptions={{
            duration: 4000,
            style: {
              background: 'rgba(13,13,32,0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#f0f0f8',
              fontFamily: 'Inter, sans-serif',
              fontSize: '0.875rem',
              borderRadius: '0.75rem',
              boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
              padding: '12px 16px',
            },
            success: {
              iconTheme: { primary: '#00d4aa', secondary: '#0d0d20' },
              style: {
                borderColor: 'rgba(0,212,170,0.2)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.5), 0 0 20px rgba(0,212,170,0.1)',
              },
            },
            error: {
              iconTheme: { primary: '#ff4757', secondary: '#0d0d20' },
              style: {
                borderColor: 'rgba(255,71,87,0.2)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.5), 0 0 20px rgba(255,71,87,0.1)',
              },
            },
            loading: {
              iconTheme: { primary: '#7c3aed', secondary: '#0d0d20' },
            },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)
