<template>
    <span>
        <span v-if="value == DIFFICULTY.EASY">
            <v-icon :color="DIFF_COLOR.EASY" :size="size">mdi-star</v-icon>
            <v-icon :color="DIFF_COLOR.EASY" :size="size">mdi-star-outline</v-icon>
            <v-icon :color="DIFF_COLOR.EASY" :size="size">mdi-star-outline</v-icon>
        </span>
        <span v-else-if="value == DIFFICULTY.NORMAL">
            <v-icon :color="DIFF_COLOR.NORMAL" :size="size">mdi-star</v-icon>
            <v-icon :color="DIFF_COLOR.NORMAL" :size="size">mdi-star</v-icon>
            <v-icon :color="DIFF_COLOR.NORMAL" :size="size">mdi-star-outline</v-icon>
        </span>
        <span v-else>
            <v-icon :color="DIFF_COLOR.HARD" :size="size">mdi-star</v-icon>
            <v-icon :color="DIFF_COLOR.HARD" :size="size">mdi-star</v-icon>
            <v-icon :color="DIFF_COLOR.HARD" :size="size">mdi-star</v-icon>
        </span>
    </span>
</template>

<script setup>
    import { DIFF_COLOR, DIFFICULTY } from '@/store/games';

    const props = defineProps({
        value: {
            type: Number,
            required: true
        },
        size: {
            type: String,
            default: "small"
        }
    })
</script>