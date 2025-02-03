<template>
    <div>
        <BarCode v-if="barData.length > 0"
            :data="barData"
            @click="toggleTag"
            @right-click="onRightClickTag"
            @hover="setHoverTag"
            selectable
            :selected="selectedTags"
            :domain="barDomain"
            id-attr="id"
            name-attr="name"
            value-attr="value"
            abs-value-attr="value"
            show-absolute
            quantiles
            discrete
            color-scale="schemeYlGnBu"
            :binary-color-fill="settings.lightMode ? '#000000' : '#ffffff'"
            :no-value-color="settings.lightMode ? '#dedede' : '#333333'"
            :no-value="-1"
            :min-value="0"
            :max-value="maxBarValue"
            :width="5"
            :height="15"/>

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

                <v-sheet v-for="e in visibleEvidence"
                    class="pa-1 mr-2"
                    :width="e.open ? width*scaleFactor : height">

                    <EvidenceCell
                        :key="'ev_t_'+e.id"
                        :item="e"
                        :width="width"
                        :height="height"
                        :scale-factor="scaleFactor"
                        :selected="hoverTag === e.tag_id || selectedItem !== null && selectedItem.id === e.id"
                        @select="selectEvidence"
                        @delete="checkOnDelete"
                        :allow-delete="allowEdit"
                        :allow-copy="allowEdit"
                        :allow-edit="allowEdit"/>
                </v-sheet>
            </div>
            <div style="width: 50%">
                <EvidenceWidget v-if="selectedItem" :item="selectedItem" :allowed-tags="tags" :allow-edit="allowEdit"/>
                <div style="text-align: center;" v-else>
                    <b>Click on an evidence tile to view the details</b>
                </div>
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
    import { computed, onMounted, ref, reactive, watch } from 'vue';
    import EvidenceWidget from './EvidenceWidget.vue';
    import NewEvidenceDialog from '../dialogs/NewEvidenceDialog.vue';
    import { useTimes } from '@/store/times';
    import BarCode from '../vis/BarCode.vue';
    import { ALL_ITEM_OPTIONS, useSettings } from '@/store/settings';
    import { pointer, schemeYlGnBu } from 'd3';

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
    const settings = useSettings()

    const { allowEdit, currentCode } = storeToRefs(app);

    const selected = ref(-1)
    const selectedItem = computed(() => {
        if (selected.value < 0) return null;
        return evidence.value.find(d => d.id === selected.value)
    });

    const evidence = ref([])
    const visibleEvidence = computed(() => {
        if (selectedTags.size === 0) {
            return evidence.value
        }
        return evidence.value.filter(d => isSelectedTag(d.tag_id))
    })

    const hoverTag = ref(-1)
    const selectedTags = reactive(new Set())

    const maxBarValue = ref(0)
    const barDomain = ref([])
    const barData = computed(() => {
        if (evidence.value.length === 0) return []

        let maxval = 0
        const list = []
        item.value.allTags.forEach(t => {
            const array = evidence.value.filter(d => d.tag_id === t.id)
            list.push({
                id: t.id,
                name: t.name,
                value: array.length,
                ids: array.map(d => d.id)
            })
            maxval = Math.max(maxval, array.length)

        })
        maxBarValue.value = maxval
        return list
    })

    const addEvidence = ref(false)
    const item = computed(() => DM.getDataItem("items", props.game))

    function isSelectedTag(id) {
        if (selectedTags.has(id)) return true
        const p = DM.getDerivedItem("tags_path", id)
        return p && p.path.some(d => selectedTags.has(d))
    }
    function toggleTag(tag) {
        if (tag.value === undefined) return
        if (selectedTags.has(tag.id)) {
            selectedTags.delete(tag.id)
        } else {
            selectedTags.add(tag.id)
        }
    }
    function setHoverTag(tag) {
        if (!tag || tag.value === undefined) {
            hoverTag.value = -1;
        } else {
            hoverTag.value = tag.id
        }
    }
    function onRightClickTag(tag, event) {
        event.preventDefault();
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "tag", tag.id,
            mx + 15, my,
            tag.name, { item: props.game },
            ALL_ITEM_OPTIONS
        )
    }

    function selectEvidence(item) {
        selected.value = item ? (selected.value === item.id ? -1 : item.id) : -1;
    }
    function checkOnDelete(id) {
        if (selected.value === id) { selected.value = -1; }
    }

    function readEvidence() {
        barDomain.value = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
        const evs = DM.getDataBy("evidence", d => d.item_id === props.game && d.code_id === currentCode.value)
        evs.forEach(e => {
            e.rows = e.rows ? e.rows : 2 + (e.description.includes('\n') ? e.description.match(/\n/g).length : 0)
            e.open = false;
        });

        const tagIdx = e => e.tag_id ? barDomain.value.indexOf(e.tag_id) : -1
        evs.sort((a, b) => tagIdx(a) - tagIdx(b))
        evidence.value = evs;

        if (selected.value >= 0 && ! selectedItem.value) {
            selected.value = -1;
        }
    }

    onMounted(readEvidence)

    watch(() => props.game, readEvidence)
    watch(() => [times.all, times.evidence], readEvidence)
</script>