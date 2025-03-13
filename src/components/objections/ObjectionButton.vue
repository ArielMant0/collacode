<template>
    <v-btn
        icon="mdi-exclamation-thick"
        size="small"
        density="compact"
        variant="tonal"
        @click="makeObjection"/>
</template>

<script setup>
    import { OBJECTION_ACTIONS, useApp } from '@/store/app';

    const props = defineProps({
        action: {
            type: Number,
            default: OBJECTION_ACTIONS.DISCUSS
        },
        itemId: {
            type: [Number, null],
            default: null
        },
        tagId: {
            type: [Number, null],
            default: null
        }
    })

    const emit = defineEmits(["click"])

    const app = useApp()

    function makeObjection() {
        app.setAddObjection(props.tagId, props.itemId, props.action)
        emit("click")
    }
</script>