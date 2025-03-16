<template>
  <v-app>
    <DefaultView/>
    <div style="position: absolute; bottom: 0; right: 0; font-size: 10px;">
      {{ version }}
    </div>
  </v-app>
</template>

<script setup>
  import DefaultView from './default/View.vue'
  const version = __APP_VERSION__
</script>
