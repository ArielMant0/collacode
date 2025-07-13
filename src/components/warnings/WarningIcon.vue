<template>
    <div class="d-flex align-center">
        <v-icon
            :size="size"
            icon="mdi-bell"
            :color="ws === 2 ? GR_COLOR.RED : GR_COLOR.YELLOW"/>
        <span v-if="text !== undefined" class="ml-1 text-caption">{{ text }}</span>
    </div>
</template>

<script setup>
    import { GR_COLOR } from '@/store/games';
    import { computed } from 'vue';

    const props = defineProps({
        warning: { type: Object, required: false },
        severity: { type: Number, required: false },
        text: { type: [String, Number], required: false },
        size: { type: String, default: "small" },
    })

    const ws = computed(() => props.warning ? props.warning.severity : props.severity)
</script>