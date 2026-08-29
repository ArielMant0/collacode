<template>
     <v-icon
        :color="inactive ? 'default' : getActionColor(action, theme)"
        :icon="getActionIcon(action)">
    </v-icon>
</template>

<script setup>
    import { getActionColor, getActionIcon } from '@/store/app';
    import { useTheme } from 'vuetify';
    
    const theme = useTheme()

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