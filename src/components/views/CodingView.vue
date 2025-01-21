<template>
    <v-sheet class="pa-0">
        <div ref="el" style="width: 100%;" class="pa-2">
            <div v-if="!loading" class="mt-2 d-flex align-center flex-column">
                <EvidenceHeatmap/>
            </div>
        </div>
    </v-sheet>
</template>

<script setup>

    import EvidenceHeatmap from '../evidence/EvidenceHeatmap.vue';

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

</script>