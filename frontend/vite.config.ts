import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const devApiTarget = env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [vue()],

    // SPA 构建产出路径为后端的 static/app/
    base: '/static/app/',
    build: {
      outDir: '../static/app',
      emptyOutDir: true,
    },

    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },

    // 开发时反代到 FastAPI
    server: {
      port: 5173,
      // SPA 路由：所有 /static/app/* 都回退到 index.html
      historyApiFallback: {
        rewrites: [{ from: /^\/static\/app\/.*$/, to: '/static/app/index.html' }],
      },
      proxy: {
        '/api': {
          target: devApiTarget,
          changeOrigin: true,
        },
      },
    },

    // Vitest 配置
    test: {
      globals: true,
      environment: 'jsdom',
      include: ['src/**/*.{test,spec}.{ts,tsx}', 'tests/**/*.{test,spec}.{ts,tsx}'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html'],
        include: ['src/**'],
        exclude: ['src/main.ts', 'src/env.d.ts'],
      },
      server: {
        deps: {
          inline: ['vue', 'vue-router', 'pinia'],
        },
      },
    },

  }
})
