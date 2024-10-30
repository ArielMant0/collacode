<template>
    <div v-if="data !== null" :style="{ 'top': y+'px', 'left': x+'px' }" class="my-tooltip">
        <v-sheet class="pa-2" rounded="sm">
            {{ data }}
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
}
</style>