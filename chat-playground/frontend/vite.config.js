import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/updates': {
        target: 'ws://localhost:8001',
        ws: true,
      },
      '/send_message': 'http://localhost:8001',
      '/api': 'http://localhost:8001',
    }
  }
})
