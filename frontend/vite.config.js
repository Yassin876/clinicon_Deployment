import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    allowedHosts: true,
    proxy: {
      '/api': 'http://127.0.0.1:5000',
      '/agent': {
        target: 'http://127.0.0.1:8200',
        rewrite: (path) => path.replace(/^\/agent/, ''),
      },
    },
  },
})
