<template>
    <v-sheet ref="el" class="pa-0">
        <div v-if="!loading && activeTransition" class="pa-2" style="width: 100%;">
            <ExplorationToolbar/>
            <div class="d-flex align-start justify-space-between mt-8" style="width: 100%; overflow-y: auto">
                <div :style="{ width: Math.max(width-toolbarWidth,600)+'px' }">
                    <CodingTransition :old-code="oldCode" :new-code="newCode"/>
                </div>
                <div style="position: relative;">
                    <TransitionToolbar v-model="expandTransTools" :width="300" :rail-width="60" sticky/>
                </div>
            </div>
        </div>
    </v-sheet>
</template>

<script setup>
    import CodingTransition from '@/components/CodingTransition.vue';
    import TransitionToolbar from '../TransitionToolbar.vue';

    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { computed, ref } from 'vue'
    import { useElementSize } from '@vueuse/core';
    import ExplorationToolbar from '../ExplorationToolbar.vue';
    import { useSettings } from '@/store/settings';

    const app = useApp()
    const settings = useSettings()

    const { activeTransition, oldCode, newCode } = storeToRefs(app);
    const { expandTransTools } = storeToRefs(settings)

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const el = ref(null);
    const { width } = useElementSize(el)

    const toolbarWidth = computed(() => 50 + (expandTransTools.value ? 300 : 60))

</script>
