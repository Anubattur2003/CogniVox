import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // basicSsl() // Disabled for local development - enable if you need HTTPS
  ],
  server: {
    port: 3000,
    cors: true, // for development
    host: '0.0.0.0', // to run on ip network
    strictPort: true, // Enforce port 3000, don't fallback to other ports
    https: false, // Disabled for local development - set to true if you need HTTPS
    // Alternative HTTPS config if basic SSL doesn't work:
    // https: {
    //   key: undefined, // Let Vite generate
    //   cert: undefined, // Let Vite generate
    // },
    proxy: {
      // Proxy all API requests to internal services (only frontend is exposed)
      // Django Backend API
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => {
          // Ensure Django URLs have trailing slashes
          const newPath = path.replace(/^\/api/, '/api');
          if (!newPath.endsWith('/') && !newPath.includes('.') && !newPath.includes('?')) {
            return newPath + '/';
          }
          return newPath;
        }
      },
      // Graph RAG API (internal service)
      '/graphrag': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/graphrag/, ''),
      },
      // Memory Service API (internal service)
      '/memory': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/memory/, ''),
      }
    }
  },
})
