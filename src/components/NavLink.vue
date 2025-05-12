<template>
    <div v-if="games.activeGame !== null" class="navlink nonav">
        <v-icon class="mr-1" :icon="settings.tabIcons[to]"/>
        <span v-if="showTabNames">{{ settings.tabNames[to] }}</span>
    </div>
    <RouterLink v-else :to="to" :class="['navlink', activeTab === to ? 'nav-active' : '']">
        <v-icon class="mr-1" :icon="settings.tabIcons[to]"/>
        <span v-if="showTabNames">{{ settings.tabNames[to] }}</span>
    </RouterLink>
</template>

<script setup>
    import { useGames } from '@/store/games';
    import { useSettings } from '@/store/settings';
    import { useWindowSize } from '@vueuse/core';
    import { storeToRefs } from 'pinia';
    import { computed } from 'vue';

    const games = useGames()
    const settings = useSettings()
    const { activeTab } = storeToRefs(settings)

    const wSize = useWindowSize()
    const showTabNames = computed(() => wSize.width.value > 1400)

    const props = defineProps({
        to: {
            type: String,
            required: true
        }
    })
</script>

<style scoped>
.navlink, .navlink:visited {
    color: white;
    text-transform: uppercase;
    text-decoration: none;
    padding: 4px 8px;
    cursor: pointer;
}

.navlink.nonav {
    color: grey;
    cursor: not-allowed;
}

.navlink:not(.nonav):hover {
    background-color: #666;
}

.nav-active * {
    color: #0ad39f;
}
</style>