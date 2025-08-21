<template>
  <v-main>
    <SideNavigation :size="navSize"/>
    <router-view />
  </v-main>
</template>

<script setup>
  import SideNavigation from '@/components/SideNavigation.vue';

  const navSize = ref(60)
</script>
