<template>
  <v-app>
    <DefaultView/>
    <div style="position: absolute; bottom: 2px; right: 2px; font-size: 10px;">
      {{ version }}
    </div>
  </v-app>
</template>

<script setup>
  import DefaultView from './default/View.vue'
  const version = __APP_VERSION__
</script>
