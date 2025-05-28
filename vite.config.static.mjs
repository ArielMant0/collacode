// Plugins
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import Fonts from 'unplugin-fonts/vite'
import Layouts from 'vite-plugin-vue-layouts'
import Vue from '@vitejs/plugin-vue'
import VueRouter from 'unplugin-vue-router/vite'
import Vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

// Utilities
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'

import * as config from './collacode.config.static'

export const BASE_PATH = config.APP_BASE_PATH

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {

  const env = loadEnv(mode, process.cwd());

  return {
    base: BASE_PATH,
    plugins: [
    VueRouter({
      src: 'src/pages',
      path: BASE_PATH,
    }),
    Vue({
      template: { transformAssetUrls }
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
    "__APP_VERSION__": JSON.stringify(config.VERSION),
    "__APP_STATIC__": "false",
    "__APP_ANONYMOUS__": config.APP_ANONYMOUS,
    "__APP_BASE_PATH__": JSON.stringify(config.APP_BASE_PATH),
    "__APP_START_PAGE__": JSON.stringify(config.APP_START_PAGE),
    "__URL_TEASER__": JSON.stringify(config.URL_TEASER),
    "__URL_EVIDENCE__": JSON.stringify(config.URL_EVIDENCE),
    "__URL_STATIC_DATA__": JSON.stringify(config.URL_STATIC_DATA),
    "__URL_SOUND__": JSON.stringify(config.URL_SOUND),
    "__URL_IMAGES__": JSON.stringify(config.URL_IMAGES),
    "__API_URL__": JSON.stringify(config.getApiUrl(env.BACKEND_PORT))
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
    port: config.getPort(env.FRONTEND_PORT_INT),
    base: BASE_PATH
  },
  preview: {
    port: config.getPort(env.FRONTEND_PORT_INT),
    host: true,
    base: BASE_PATH,
    allowedHosts: config.ALLOWED_HOSTS
  },
}})
