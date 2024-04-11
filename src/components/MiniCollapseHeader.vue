<template>
    <div @click="model = !model" class="cursor-pointer">
        <v-icon class="mr-2">{{ model ? iconOpen : iconClosed }}</v-icon>
        <span>{{ text }}</span>
    </div>
</template>

<script setup>
    const model = defineModel();
    const props = defineProps({
        text: {
            type: String,
            required: true
        },
        iconOpen: {
            type: String,
            default: "mdi-arrow-down"
        },
        iconClosed: {
            type: String,
            default: "mdi-arrow-right"
        }
    })
</script>