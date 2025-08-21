<template>
     <v-icon :color="getObjectionStatusColor(status)" :icon="getObjectionStatusIcon(status)"></v-icon>
</template>

<script setup>
    import { getObjectionStatusColor, getObjectionStatusIcon } from '@/store/app';

    const props = defineProps({
        status: {
            type: Number,
            required: true
        },
    })
</script>