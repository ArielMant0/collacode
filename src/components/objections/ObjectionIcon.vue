<template>
     <v-icon
        :color="inactive ? 'default' : getActionColor(action)"
        :icon="getActionIcon(action)">
    </v-icon>
</template>

<script setup>
    import { getActionColor, getActionIcon } from '@/store/app';

    const props = defineProps({
        action: {
            type: Number,
            required: true
        },
        inactive: {
            type: Boolean,
            default: false
        },
    })
</script>