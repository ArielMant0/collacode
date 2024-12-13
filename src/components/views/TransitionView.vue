<template>
    <v-sheet ref="el" class="pa-0">
        <div v-if="!loading && activeTransition" class="pa-2" style="width: 100%;">
            <div style="width: 100%">
                <h3 style="text-align: center" class="mb-4">
                    Transition from <i>{{ app.getCodeName(oldCode) }}</i> to <i>{{ app.getCodeName(newCode) }}</i>
                </h3>
                <ExplorationToolbar/>
            </div>
            <div class="d-flex" style="width: 100%; overflow-y: auto">
                <div :style="{ width: Math.max(width-325,600)+'px' }">
                    <CodingTransition :old-code="oldCode" :new-code="newCode"/>
                </div>
                <TransitionToolbar sticky :width="300"/>
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
