/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: { 50: '#e6fff9', 100: '#b3ffee', 200: '#80ffe3', 300: '#4dffd8', 400: '#1affcd', 500: '#00d4aa', 600: '#00ab88', 700: '#008266', 800: '#005944', 900: '#003022' },
        accent: { 50: '#f3eeff', 100: '#ddd6fe', 200: '#c4b5fd', 300: '#a78bfa', 400: '#8b5cf6', 500: '#7c3aed', 600: '#6d28d9', 700: '#5b21b6', 800: '#4c1d95', 900: '#2e1065' },
        gain: { DEFAULT: '#00d4aa', light: '#4dffd8', dark: '#008266' },
        loss: { DEFAULT: '#ff4757', light: '#ff8090', dark: '#cc2233' },
        gold: { DEFAULT: '#f59e0b', light: '#fcd34d', dark: '#b45309' },
        dark: { 50: '#f0f0f5', 100: '#d1d1e0', 200: '#a3a3c2', 300: '#7575a3', 400: '#4d4d85', 500: '#333366', 600: '#1f1f4d', 700: '#141433', 800: '#0d0d24', 900: '#080818', 950: '#04040f' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Menlo', 'Monaco', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'glass-gradient': 'linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
        'brand-gradient': 'linear-gradient(135deg, #7c3aed 0%, #00d4aa 100%)',
        'brand-gradient-r': 'linear-gradient(135deg, #00d4aa 0%, #7c3aed 100%)',
        'gain-gradient': 'linear-gradient(135deg, #00d4aa 0%, #00ab88 100%)',
        'loss-gradient': 'linear-gradient(135deg, #ff4757 0%, #cc2233 100%)',
        'gold-gradient': 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
        'dark-gradient': 'linear-gradient(180deg, #0a0a0f 0%, #0d0d24 100%)',
        'hero-gradient': 'radial-gradient(ellipse at 50% 0%, rgba(124,58,237,0.3) 0%, rgba(0,212,170,0.1) 50%, transparent 70%)',
        'card-shine': 'linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0) 60%)',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1)',
        'glass-lg': '0 16px 48px 0 rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1)',
        'brand': '0 0 20px rgba(0,212,170,0.3), 0 0 40px rgba(0,212,170,0.1)',
        'accent': '0 0 20px rgba(124,58,237,0.3), 0 0 40px rgba(124,58,237,0.1)',
        'card': '0 4px 24px rgba(0,0,0,0.3)',
        'card-hover': '0 8px 40px rgba(0,0,0,0.4)',
      },
    },
  },
  plugins: [],
}