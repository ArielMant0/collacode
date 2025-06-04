<template>
    <div class="pb-1 pt-1">
        <div v-if="games.activeGame !== null"  class="navlink nonav">
            <v-icon v-if="icon" class="mr-1" :icon="icon"/>
            <span v-if="showTabNames">{{ text ? text : to }}</span>
        </div>
        <RouterLink v-else :to="to" :class="['navlink', active === to ? 'nav-active' : '']">
            <v-icon v-if="icon" class="mr-1" :icon="icon"/>
            <span v-if="showTabNames">{{ text ? text : to }}</span>
        </RouterLink>
    </div>
</template>

<script setup>
    import { useGames } from '@/store/games';
    import { useWindowSize } from '@vueuse/core';
    import { computed } from 'vue';

    const games = useGames()
    const wSize = useWindowSize()
    const showTabNames = computed(() => wSize.width.value > 1400)

    const props = defineProps({
        to: {
            type: String,
            required: true
        },
        active: {
            type: String,
            default: ""
        },
        text: {
            type: String,
            required: false
        },
        icon: {
            type: String,
            required: false
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

@media screen and (max-width: 960px) {
    .navlink, .navlink:visited {
        padding: 2px 4px;
    }

}
</style>