<template>
    <v-sheet ref="el" class="pa-0">
        <div v-if="!loading && activeTransition" class="pa-2" style="width: 100%;">
            <ExplorationToolbar/>
            <div class="d-flex align-start justify-space-between mt-8" style="width: 100%; overflow-y: auto">
                <div :style="{ width: Math.max(width-350,600)+'px' }">
                    <CodingTransition :old-code="oldCode" :new-code="newCode"/>
                </div>
                <TransitionToolbar :width="300"/>
            </div>
        </div>
    </v-sheet>
</template>

<script setup>
    import CodingTransition from '@/components/CodingTransition.vue';
    import TransitionToolbar from '../TransitionToolbar.vue';

    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { ref } from 'vue'
    import { useElementSize } from '@vueuse/core';
    import ExplorationToolbar from '../ExplorationToolbar.vue';

    const app = useApp()

    const { activeTransition, oldCode, newCode } = storeToRefs(app);

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const el = ref(null);
    const { width } = useElementSize(el)

</script>
