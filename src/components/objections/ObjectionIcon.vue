<template>
     <v-icon
        :color="status !== OBJECTION_STATUS.OPEN ? 'default' : getActionColor(action, theme)"
        :icon="getActionIcon(action)">
    </v-icon>
</template>

<script setup>
    import { getActionColor, getActionIcon, OBJECTION_ACTIONS, OBJECTION_STATUS } from '@/store/app';
    import { useTheme } from 'vuetify';
    
    const theme = useTheme()

    const props = defineProps({
        action: {
            type: Number,
            required: true
        },
        status: {
            type: Number,
            default: OBJECTION_STATUS.OPEN
        },
    })
</script>