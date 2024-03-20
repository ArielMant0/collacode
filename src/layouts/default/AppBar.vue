<template>
  <v-app-bar flat density="compact" color="primary">
    <v-app-bar-title>
      <v-icon @click="router.push('/')" class="mr-1">mdi-tag-multiple</v-icon>
      <span class="cursor-pointer" @click="router.push('/')">
        CollaCode
      </span>
    </v-app-bar-title>
    <v-btn icon="mdi-upload" @click="router.push('/import')"/>
    <v-btn icon="mdi-download" @click="router.push('/export')"/>
  </v-app-bar>
</template>

<script setup>
  import router from '@/router';

  // yellow: fcd468
  // purple: 7650a1
</script>
