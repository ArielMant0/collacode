<template>
    <div>
        <div class="d-flex justify-space-between">
            <div style="width: 45%">
                <v-text-field v-model="name"
                    density="compact"
                    label="Name"
                    class="mb-2"
                    hide-details
                    hide-spin-buttons/>
                <v-textarea v-model="desc"
                    density="compact"
                    label="Description"
                    class="mb-2"
                    rows="9"
                    hide-details
                    hide-spin-buttons/>
            </div>
            <div>
                <TreeMap
                    :data="allCats"
                    :time="time"
                    title-attr="name"
                    :selected="selectedCats"
                    :width="mapWidth"
                    :height="mapHeight"
                    @click="toggleCategory"/>
                <v-btn
                    density="compact"
                    variant="flat"
                    prepend-icon="mdi-plus"
                    block
                    @click="addCat = true">
                    add category
                </v-btn>
            </div>
        </div>

        <div class="d-flex mt-4" style="max-height: 50vh; overflow-y: auto;">
            <div style="width: 50%;">
                <b>Tags</b>
                <div class="d-flex flex-wrap">
                    <v-chip v-for="t in allTags"
                        :key="'t_'+t.id"
                        size="small"
                        class="pt-1 pb-1 pl-2 pr-2 mr-1 mb-1"
                        :color="selectedTags.has(t.id) ? 'primary' : 'default'"
                        @click="toggleTag(t.id)">
                        {{ t.name }} ({{ numEv[t.id] }})
                    </v-chip>
                </div>
            </div>
            <div style="width: 50%;">
                <b>Evidence</b>
                <div class="d-flex flex-wrap">
                    <EvidenceCell v-for="e in evidence"
                        :key="'e_'+e.id"
                        :item="e"
                        class="mb-1 mr-1"
                        :allowed-tags="allTags"
                        :width="evidenceSize"
                        :height="evidenceSize"
                        :selected="selectedEvs.has(e.id)"
                        disable-context-menu
                        @right-click="app.setShowEvidence(e.id)"
                        @select="toggleEvidence(e.id)"/>
                </div>
            </div>
        </div>

        <div class="d-flex justify-space-between mt-4">
            <v-btn
                class="mr-1"
                prepend-icon="mdi-delete"
                :color="hasChanges ? 'error' : 'default'"
                density="comfortable"
                :disabled="!hasChanges"
                @click="discardChanges">
                {{ existing ? 'discard changes' : 'reset' }}
            </v-btn>
            <v-btn
                class="ml-1"
                prepend-icon="mdi-sync"
                :color="hasChanges ? 'primary' : 'default'"
                density="comfortable"
                :disabled="!hasChanges"
                @click="saveChanges">
                {{ existing ? 'save changes' : 'create' }}
            </v-btn>
        </div>

        <NewExtCategoryDialog v-model="addCat"/>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import TreeMap from '../vis/TreeMap.vue';
    import EvidenceCell from '../evidence/EvidenceCell.vue';
    import { computed, onMounted } from 'vue';
    import { useToast } from 'vue-toastification';
    import { createExternalization, updateExternalization } from '@/use/utility';
    import { useTimes } from '@/store/times';
    import { useApp } from '@/store/app';
    import NewExtCategoryDialog from '../dialogs/NewExtCategoryDialog.vue';
    import { group } from 'd3';

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        allowEdit: {
            type: Boolean,
            default: false,
        },
        mapWidth: {
            type: Number,
            default: 950
        },
        mapHeight: {
            type: Number,
            default: 250
        },
        evidenceSize: {
            type: Number,
            default: 100
        },
    })

    const emit = defineEmits(["update"])

    const app = useApp();
    const times = useTimes()
    const toast = useToast();

    const addCat = ref(false)

    const name = ref(props.item.name)
    const desc = ref(props.item.description)
    const categories = ref([])

    const time = ref(Date.now())
    const selectedTags = reactive(new Set())
    const selectedEvs = reactive(new Set())

    const allTags = ref([]);
    const existing = computed(() => props.item.id && props.item.id >= 0)
    const tags = computed(() => allTags.value.filter(d => selectedTags.has(d.id)))

    const hasChanges = computed(() => {
        const setA = new Set(props.item.categories.map(d => d.cat_id))
        const setB = new Set(categories.value.map(d => d.id))
        const setC = new Set(props.item.tags.map(d => d.tag_id))
        const setD = new Set(props.item.evidence.map(d => d.ev_id))
        return props.item.name !== name.value ||
            props.item.description !== desc.value ||
            (setA.size !== setB.size || setA.union(setB).size !== setA.size) ||
            (setC.size !== selectedTags.size || setC.union(selectedTags).size !== setC.size) ||
            (setD.size !== selectedEvs.size || setD.union(selectedEvs).size !== setD.size)
    })

    const allCats = ref(DM.getData("ext_categories"))
    const requiredCats = ref(getRequiredCategories())
    const selectedCats = computed(() => categories.value.map(d => d.id))

    const allEvidence = computed(() => {
        const evs = DM.getDataBy("evidence", d => d.game_id === props.item.game_id && d.code_id === props.item.code_id)
        evs.forEach(e => {
            e.rows = 2 + (e.description.includes('\n') ? e.description.match(/\n/g).length : 0)
            e.open = false;
        });
        return evs;
    });
    const evidence = computed(() => {
        if (selectedTags.size === 0) return [];
        const array = allEvidence.value.filter(d => selectedEvs.has(d.id) || selectedTags.has(d.tag_id));
        array.sort((a, b) => {
            const inA = selectedEvs.has(a.id)
            const inB = selectedEvs.has(b.id)
            if (inA === inB) {
                const nameA = tags.value.find(d => d.id === a.tag_id).name.toLowerCase()
                const nameB = tags.value.find(d => d.id === b.tag_id).name.toLowerCase()
                if (nameA < nameB) return -1
                if (nameA > nameB) return 1
                return 0
            }
            return inA ? -1 : 1
        })
        return array
    });

    const numEv = computed(() => {
        const obj = {};
        const g = group(allEvidence.value, d => d.tag_id)
        allTags.value.forEach(t => obj[t.id] = g.has(t.id) ? g.get(t.id).length : 0);
        return obj
    });

    function getRequiredCategories() {
        const leaves = allCats.value.filter(d => !allCats.value.some(dd => dd.parent === d.id))
        return Array.from(group(leaves, d => d.parent).keys())
    }

    function toggleTag(id) {
        if (selectedTags.has(id)) {
            allEvidence.value.forEach(e => {
                if (e.tag_id === id) {
                    selectedEvs.delete(e.id)
                }
            })
            selectedTags.delete(id)
        } else {
            allEvidence.value.forEach(e => {
                if (e.tag_id === id) {
                    selectedEvs.add(e.id)
                }
            })
            selectedTags.add(id)
        }
    }

    function toggleCategory(category) {
        if (props.allowEdit) {
            const before = categories.value.findIndex(d => d.id === category.id);
            if (before >= 0) {
                categories.value.splice(before, 1)
            } else {
                categories.value.push(category)
            }
        }
    }

    function toggleEvidence(id) {
        if (selectedEvs.has(id)) {
            selectedEvs.delete(id)
        } else {
            selectedEvs.add(id)
        }
    }

    function discardChanges() {
        if (!hasChanges.value) {
            return toast.warning("no changes to discard");
        }
        name.value = props.item.name;
        desc.value = props.item.description;
        categories.value = props.item.categories.map(d => allCats.value.find(dd => dd.id === d.cat_id))
        selectedTags.clear()
        props.item.tags.forEach(d => selectedTags.add(d.tag_id))
        selectedEvs.clear()
        props.item.evidence.forEach(d => selectedEvs.add(d.ev_id))
    }
    async function saveChanges() {
        if (!hasChanges.value) {
            return toast.warning("no changes to save");
        }

        if (!name.value) { return toast.error("missing name") }
        if (!desc.value) { return toast.error("missing description") }
        if (requiredCats.value.some(id => !categories.value.find(d => d.parent === id))) {
            return toast.error("missing required externalization category")
        }

        try {
            props.item.name = name.value;
            props.item.description = desc.value;
            props.item.categories = categories.value.map(d => ({ cat_id: d.id }));
            props.item.tags = tags.value.map(d => ({ tag_id: d.id }))
            props.item.evidence = evidence.value.filter(d => selectedEvs.has(d.id)).map(d => ({ ev_id: d.id }))
            if (existing.value) {
                await updateExternalization(props.item)
                toast.success("updated externalization")
            } else {
                props.item.game_id = props.item.game_id;
                props.item.code_id = app.currentCode;
                props.item.created = Date.now();
                props.item.created_by = app.activeUserId;
                await createExternalization(props.item)
                toast.success("created new externalization")
            }
            emit("update")
            times.needsReload("externalizations")
        } catch {
            toast.error(`error ${props.item.id ? 'updating' : 'creating'} externalization`)
        }
    }

    function init() {
        const game = DM.getDataItem("games", props.item.game_id);
        allTags.value = game ? game.allTags : []
        allCats.value = DM.getData("ext_categories")
        name.value = props.item.name;
        desc.value = props.item.description;
        categories.value = props.item.categories.map(d => allCats.value.find(dd => dd.id === d.cat_id));
        selectedTags.clear();
        props.item.tags.forEach(d => selectedTags.add(d.tag_id))
        selectedEvs.clear()
        props.item.evidence.forEach(d => selectedEvs.add(d.ev_id))
        time.value = Date.now()
    }

    onMounted(init)

    watch(() => props.item.id, init)
    watch(() => times.ext_categories, function() {
        allCats.value = DM.getData("ext_categories")
        requiredCats.value = getRequiredCategories();
        time.value = Date.now()
    })
</script>