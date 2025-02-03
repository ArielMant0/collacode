<template>
    <Teleport to="body">
        <div ref="el" v-if="data !== null" :style="{ 'top': y+'px', 'left': tx+'px', 'max-width': '400px' }" class="my-tooltip">
            <v-sheet class="pa-2" rounded="sm" elevation="2">
                <div v-html="data"></div>
            </v-sheet>
        </div>
    </Teleport>
</template>

<script setup>
    import { useSettings } from '@/store/settings';
    import { useTooltip } from '@/store/tooltip';
    import { useElementSize } from '@vueuse/core';
    import { storeToRefs } from 'pinia';
    import { computed } from 'vue';

    const tt = useTooltip();
    const settings = useSettings()

    const { x, y, data } = storeToRefs(tt);
    const { clickX, clickTargetId } = storeToRefs(settings);

    const el = ref(null)
    const { width } = useElementSize(el)

    const tx = computed(() => {
        if (clickTargetId.value !== null && x.value <= clickX.value && x.value+width.value > clickX.value) {
            return x.value - (width.value ? width.value+20 : 415)
        }
        return x.value
    })


</script>

<style scoped>
.my-tooltip {
    position: absolute;
    z-index: 4999;
    max-width: 600px;
}
</style>