<template>
    <v-sheet ref="el" class="pa-0" style="width: 100%; max-width: 100%;">
        <div v-if="!loading" class="pa-2">
            <ExplorationToolbar/>
            <div class="d-flex align-start justify-space-between mt-8" style="width: 100%; overflow-y: auto; min-height: 400px;">
                <CodingTransition :width=" Math.max(width-toolbarWidth-20,400)"/>
                <div :style="{ position: 'relative', minWidth: toolbarWidth+'px', maxWidt: toolbarWidth+'px' }">
                    <TransitionToolbar v-model="expandTransTools" :width="300" :rail-width="60" sticky :height="height"/>
                </div>
            </div>
        </div>
    </v-sheet>
</template>

<script setup>
    import CodingTransition from '@/components/CodingTransition.vue';
    import TransitionToolbar from '../TransitionToolbar.vue';

    import { storeToRefs } from 'pinia'
    import { computed, ref } from 'vue'
    import { useElementSize } from '@vueuse/core';
    import ExplorationToolbar from '../ExplorationToolbar.vue';
    import { useSettings } from '@/store/settings';

    const settings = useSettings()

    const { expandTransTools } = storeToRefs(settings)

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const el = ref(null);
    const { width, height } = useElementSize(el)

    const toolbarWidth = computed(() => 50 + (expandTransTools.value ? 300 : 60))

</script>
