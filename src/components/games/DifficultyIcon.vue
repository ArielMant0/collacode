<template>
    <span>
        <span v-if="value == DIFFICULTY.EASY">
            <v-icon :color="DIFF_COLOR.EASY" size="small">mdi-star</v-icon>
            <v-icon :color="DIFF_COLOR.EASY" size="small">mdi-star-outline</v-icon>
            <v-icon :color="DIFF_COLOR.EASY" size="small">mdi-star-outline</v-icon>
        </span>
        <span v-else-if="value == DIFFICULTY.NORMAL">
            <v-icon :color="DIFF_COLOR.NORMAL" size="small">mdi-star</v-icon>
            <v-icon :color="DIFF_COLOR.NORMAL" size="small">mdi-star</v-icon>
            <v-icon :color="DIFF_COLOR.NORMAL" size="small">mdi-star-outline</v-icon>
        </span>
        <span v-else>
            <v-icon :color="DIFF_COLOR.HARD" size="small">mdi-star</v-icon>
            <v-icon :color="DIFF_COLOR.HARD" size="small">mdi-star</v-icon>
            <v-icon :color="DIFF_COLOR.HARD" size="small">mdi-star</v-icon>
        </span>
    </span>
</template>

<script setup>
    import { DIFF_COLOR, DIFFICULTY } from '@/store/games';

    const props = defineProps({
        value: {
            type: Number,
            required: true
        }
    })
</script>