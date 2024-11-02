<template>
    <div v-if="data !== null" :style="{ 'top': y+'px', 'left': x+'px' }" class="my-tooltip">
        <v-sheet class="pa-2" rounded="sm" elevation="2">
            <div v-html="data">
            </div>
        </v-sheet>
    </div>
</template>

<script setup>
    import { useTooltip } from '@/store/tooltip';
    import { storeToRefs } from 'pinia';

    const tt = useTooltip();
    const { x, y, data } = storeToRefs(tt);
</script>

<style scoped>
.my-tooltip {
    position: absolute;
    z-index: 4999;
    max-width: 600px;
}
</style>