/// <reference types="vitest" />
import { fileURLToPath } from 'node:url';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { apiStub } from './dev-stub/stub';

// Без API_TARGET в режиме разработки работает заглушка API (GAP-13).
// С API_TARGET запросы /api идут на настоящий бэкенд.
// Единый .env лежит в корне репозитория.
const rootDir = fileURLToPath(new URL('../..', import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, rootDir, '');
  const target = env.API_TARGET;
  return {
    envDir: rootDir,
    plugins: [react(), ...(target || process.env.VITEST ? [] : [apiStub(env)])],
    server: {
      port: 5173,
      proxy: target ? { '/api': { target, changeOrigin: true } } : undefined,
    },
    test: { environment: 'node', include: ['src/**/*.test.ts'] },
  };
});
