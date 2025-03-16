// Plugins
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import Fonts from 'unplugin-fonts/vite'
import Pages from 'vite-plugin-pages'
import Layouts from 'vite-plugin-vue-layouts'
import Vue from '@vitejs/plugin-vue'
import VueRouter from 'unplugin-vue-router/vite'
import Vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

// Utilities
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'

export const BASE_PATH = "/collacode"

// https://vitejs.dev/config/
export default defineConfig({
    base: BASE_PATH,
    plugins: [
    VueRouter(),
    Vue({
      template: { transformAssetUrls }
    }),
    Pages({
      // basic
      dirs: [{ dir: 'src/pages', baseRoute: 'collacode' }],
      extensions: ['vue', 'md'],
      syncIndex: false,
    }),
    Layouts(),
    // https://github.com/vuetifyjs/vuetify-loader/tree/master/packages/vite-plugin#readme
    Vuetify({
      autoImport: true,
      styles: {
        configFile: 'src/styles/settings.scss',
      },
    }),
    Components(),
    Fonts({
      google: {
        families: [{
          name: 'Roboto',
          styles: 'wght@100;300;400;500;700;900',
        }],
      },
    }),
    AutoImport({
      imports: [
        'vue',
        'vue-router',
      ],
      eslintrc: {
        enabled: true,
      },
      vueTemplate: true,
    }),
  ],
  define: {
    "process.env": {},
    "__APP_VERSION__": JSON.stringify("v0.1.0"),
    "__APP_STATIC__": "true",
    "__APP_ANONYMOUS__": "false",
    "__APP_BASE_PATH__": JSON.stringify("/collacode"),
    "__APP_START_PAGE__": JSON.stringify("explore_meta"),
    "__API_URL__": JSON.stringify("http://localhost:8000/colladata/api/v1")
  },
  build: {
    publicDir: "public",
    copyPublicDir: false
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    extensions: [
      '.js',
      '.json',
      '.jsx',
      '.mjs',
      '.ts',
      '.tsx',
      '.vue',
    ],
  },
  server: {
    port: 3000,
    base: BASE_PATH
  },
  preview: {
    port: 3000,
    host: true,
    base: BASE_PATH
  },
})
