<template>
    <v-icon :size="size" :icon="games.resultIcon(result)" :color="games.resultColor(result)"/>
</template>

<script setup>
    import { useGames } from '@/store/games';

    const games = useGames()

    const props = defineProps({
        result: {
            type: [Number, Boolean],
            required: true
        },
        size: {
            type: Number,
            default: 60
        }
    })

</script>