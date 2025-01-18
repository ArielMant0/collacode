<template>
    <div class="d-flex align-start" style="width: 100%">
        <div class="d-flex flex-wrap" style="width: 50%">
        <v-btn class="pa-2 ma-1"
            color="secondary"
            :width="height"
            :height="height"
            rounded="sm"
            icon="mdi-plus"
            @click="addEvidence = true"
        </v-btn>

        <v-sheet v-for="e in evidence"
            class="pa-1 mr-2"
            :width="e.open ? width*scaleFactor : height">

            <EvidenceCell
                :key="'ev_t_'+e.id"
                :item="e"
                :allowed-tags="tags"
                :width="width"
                :height="height"
                :scale-factor="scaleFactor"
                :selected="selectedItem !== null && selectedItem.id === e.id"
                @select="selectEvidence"
                @delete="checkOnDelete"
                :allow-delete="allowEdit"
                :allow-copy="allowEdit"
                :allow-edit="allowEdit"/>
        </v-sheet>
        </div>
        <div style="width: 50%">
            <EvidenceWidget v-if="selectedItem" :item="selectedItem" :allowed-tags="tags" :allow-edit="allowEdit"/>
            <div v-else>
                Click on an evidence image to view the details
            </div>
        </div>

        <NewEvidenceDialog v-model="addEvidence" :item="item"/>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import EvidenceCell from './EvidenceCell.vue';
    import { storeToRefs } from 'pinia';
    import { useApp } from '@/store/app';
    import { computed, onMounted, watch } from 'vue';
    import EvidenceWidget from './EvidenceWidget.vue';
    import NewEvidenceDialog from '../dialogs/NewEvidenceDialog.vue';
    import { useTimes } from '@/store/times';

    const props = defineProps({
        name: {
            type: String,
            required: true
        },
        game: {
            type: Number,
            required: true
        },
        tags: {
            type: Array,
            required: true
        },
        width: {
            type: Number,
            default: 125,
        },
        height: {
            type: Number,
            default: 125,
        },
        scaleFactor: {
            type: Number,
            default: 4,
        },
    })

    const app = useApp();
    const times = useTimes();

    const { allowEdit, currentCode } = storeToRefs(app);

    const selected = ref(-1)
    const selectedItem = computed(() => {
        if (selected.value < 0) return null;
        return evidence.value.find(d => d.id === selected.value)
    });
    const evidence = ref([])

    const addEvidence = ref(false)
    const item = computed(() => DM.getDataItem("items", props.game))

    function selectEvidence(item) {
        selected.value = item ? item.id : null;
    }
    function checkOnDelete(id) {
        if (selected.value === id) { selected.value = -1; }
    }

    function readEvidence() {
        const evs = DM.getDataBy("evidence", d => d.item_id === props.game && d.code_id === currentCode.value)
        evs.forEach(e => {
            e.rows = 2 + (e.description.includes('\n') ? e.description.match(/\n/g).length : 0)
            e.open = false;
        });
        evidence.value = evs;

        if (selected.value >= 0 && ! selectedItem.value) {
            selected.value = -1;
        }
    }

    onMounted(readEvidence)

    watch(() => props.game, readEvidence)
    watch(() => [times.all, times.evidence], readEvidence)
</script>