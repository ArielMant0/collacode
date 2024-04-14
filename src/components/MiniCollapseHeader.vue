<template>
    <div @click="model = !model" class="cursor-pointer">
        <v-btn class="mr-1" density="compact" :icon="model ? iconOpen : iconClosed" rounded="sm" variant="flat"/>
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
            default: "mdi-menu-down"
        },
        iconClosed: {
            type: String,
            default: "mdi-menu-right"
        }
    })
</script>