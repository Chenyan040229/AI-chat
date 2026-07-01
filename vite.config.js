import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'


// https://vite.dev/config/
export default defineConfig({
  // 开发服务器配置（仅 npm run dev 时生效）
  server: {
    port: 5173, // 本地启动端口，默认 5173，可改成任意未占用端口
    open: true, // 启动后自动打开浏览器，不用手动复制地址
  },
  plugins: [
    vue(),
    vueDevTools(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  optimizeDeps: {
    include: ['pdfjs-dist'],
  },
})
