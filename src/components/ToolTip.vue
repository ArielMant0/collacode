<template>
    <Teleport to="body">
    <div v-if="data !== null" :style="{ 'top': y+'px', 'left': x+'px' }" class="my-tooltip">
        <v-sheet class="pa-1" rounded="sm" elevation="2">
            <slot>
                <div v-html="data"></div>
            </slot>
        </v-sheet>
    </div>
    </Teleport>
</template>

<script setup>
    const props = defineProps({
        x: {
            type: Number,
            required: true
        },
        y: {
            type: Number,
            required: true
        },
        data: {
            required: true
        }
    })
</script>

<style scoped>
.my-tooltip {
    position: absolute;
    z-index: 4999;
    max-width: 600px;
}
</style>