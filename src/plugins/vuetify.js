/**
 * plugins/vuetify.js
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import { VDateInput } from 'vuetify/labs/VDateInput'
// Composables
import { createVuetify } from 'vuetify'
import { aliases, mdi } from "vuetify/iconsets/mdi";
import { customIcons } from '@/iconsets/custom'

const customLight = {
  dark: false,
  colors: {
    background: '#FFFFFF',
    surface: '#FFFFFF',
    'on-background': '#000000',
    'on-surface': '#000000',
    'surface-bright': '#FFFFFF',
    'surface-light': '#EEEEEE',
    'surface-variant': '#424242',
    'on-surface-variant': '#EEEEEE',
    primary: '#078766',
    'primary-darken-1': '#045c45',
    'primary-lighten-1': '#4ca68f',
    secondary: '#0ad39f',
    'secondary-darken-1': '#06a179',
    tertiary: '#0cf5b8',
    'tertiary-darken-1': '#09b88a',
    info: '#1976D2',
    error: "#b61431"
  },
}
const customDark = {
  dark: true,
  colors: {
    background: '#121212',
    surface: '#121212',
    'on-background': '#efefef',
    'on-surface': '#efefef',
    'surface-bright': '#222222',
    'surface-light': '#333333',
    'surface-variant': '#424242',
    'on-surface-variant': '#cccccc',
    primary: '#078766',
    'primary-lighten-1': '#4ca68f',
    'primary-darken-1': '#045c45',
    secondary: '#0ad39f',
    'secondary-darken-1': '#06a179',
    tertiary: '#0cf5b8',
    'tertiary-darken-1': '#09b88a',
    info: '#1565C0',
    error: "#b61431"
  },
}

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  components: { VDateInput },
  defaults: {
    VTooltip: {
      contentClass: "tthover elevation-2"
    }
  },
  icons: {
    defaultSet: "mdi",
    aliases,
    sets: {
      mdi,
      cst: customIcons,
    },
  },
  theme: {
    defaultTheme: 'customLight',
    options: { customProperties: true },
    themes: { customLight, customDark },
  }
})
