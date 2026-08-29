<template>
     <v-icon :color="getObjectionStatusColor(status, theme)" :icon="getObjectionStatusIcon(status)"></v-icon>
</template>

<script setup>
    import { getObjectionStatusColor, getObjectionStatusIcon } from '@/store/app';
    import { useTheme } from 'vuetify';

    const props = defineProps({
        status: {
            type: Number,
            required: true
        },
    })

    const theme = useTheme()
</script>