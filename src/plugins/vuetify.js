/**
 * plugins/vuetify.js
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import { VNumberInput } from 'vuetify/labs/VNumberInput'
import { VDateInput } from 'vuetify/labs/VDateInput'
// Composables
import { createVuetify } from 'vuetify'

const customLight = {
  dark: false,
  colors: {
    background: '#FFFFFF',
    surface: '#FFFFFF',
    'on-surface': '#000000',
    'surface-bright': '#FFFFFF',
    'surface-light': '#EEEEEE',
    'surface-variant': '#424242',
    'on-surface-variant': '#EEEEEE',
    primary: '#078766',
    'primary-darken-1': '#045c45',
    secondary: '#0ad39f',
    'secondary-darken-1': '#06a179',
    tertiary: '#0cf5b8',
    'tertiary-darken-1': '#09b88a',
  },
}
const customDark = {
  dark: true,
  colors: {
    background: '#121212',
    surface: '#121212',
    'on-surface': '#efefef',
    'surface-bright': '#222222',
    'surface-light': '#333333',
    'surface-variant': '#424242',
    'on-surface-variant': '#cccccc',
    primary: '#078766',
    'primary-darken-1': '#045c45',
    secondary: '#0ad39f',
    'secondary-darken-1': '#06a179',
    tertiary: '#0cf5b8',
    'tertiary-darken-1': '#09b88a',
  },
}

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  components: { VNumberInput, VDateInput },
  theme: {
    defaultTheme: 'customLight',
    themes: { customLight, customDark },
  }
})
