<template>
    <div>
        <MatchingGame v-if="!loading && active"/>
    </div>
</template>

<script setup>
    import { useSettings } from '@/store/settings'
    import MatchingGame from '../games/MatchingGame.vue'
    import { computed } from 'vue'

    const settings = useSettings()

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const active = computed(() => settings.activeTab === "games")
</script>