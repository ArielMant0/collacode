<template>
    <div>
        <div class="d-flex justify-space-between">
            <div ref="el" style="width: 50%" class="pr-1">
                <v-text-field v-model="name"
                    density="compact"
                    label="Name"
                    class="mb-2"
                    :readonly="!allowEdit"
                    hide-details
                    hide-spin-buttons/>
                <v-select v-model="extGroup"
                    :items="gameGroups"
                    class="mb-2"
                    label="Group"
                    item-title="name"
                    item-value="id"
                    density="compact"
                    hide-spin-buttons
                    hide-details/>
                <v-text-field v-model="cluster"
                    density="compact"
                    label="Cluster"
                    class="mb-2"
                    :readonly="!allowEdit"
                    :messages="matchingClusters"
                    :hide-details="matchingClusters.length === 0"
                    hide-spin-buttons>

                    <template v-slot:message="{ message }">
                        <div class="cursor-pointer" @click="setCluster(message)">{{ message }}</div>
                    </template>
                </v-text-field>
                <v-textarea v-model="desc"
                    density="compact"
                    label="Description"
                    class="mb-2"
                    rows="9"
                    :readonly="!allowEdit"
                    hide-details
                    hide-spin-buttons/>
            </div>
            <div class="pl-1">
                <TreeMap
                    :data="allCats"
                    :time="time"
                    title-attr="name"
                    :selected="selectedCats"
                    :width="elSize.width.value"
                    :height="elSize.height.value-35"
                    @click="toggleCategory"
                    @right-click="onClickTree"/>
                <v-btn
                    density="compact"
                    variant="flat"
                    prepend-icon="mdi-plus"
                    block
                    @click="app.setAddExtCategory()">
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

        <div v-if="allowEdit" class="d-flex justify-space-between mt-4">
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

    </div>
</template>

<script setup>
    import { pointer } from 'd3';
    import DM from '@/use/data-manager';
    import TreeMap from '../vis/TreeMap.vue';
    import EvidenceCell from '../evidence/EvidenceCell.vue';
    import { computed, onMounted } from 'vue';
    import { useToast } from 'vue-toastification';
    import { createExternalization, updateExternalization } from '@/use/utility';
    import { useTimes } from '@/store/times';
    import { useApp } from '@/store/app';
    import { group } from 'd3';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { sortObjByString } from '@/use/sorting';
    import { useElementSize } from '@vueuse/core';

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        allowEdit: {
            type: Boolean,
            default: false,
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
    const settings = useSettings();

    const name = ref(props.item.name)
    const cluster = ref(props.item.cluster)
    const desc = ref(props.item.description)
    const extGroup = ref(props.item.group_id)

    const el = ref(null)
    const elSize = useElementSize(el)

    const gameGroups = ref([])
    const categories = ref([])

    const time = ref(Date.now())
    const selectedTags = reactive(new Set())
    const selectedEvs = reactive(new Set())

    const allTags = ref([]);
    const existing = computed(() => props.item.id && props.item.id >= 0)
    const tags = computed(() => allTags.value.filter(d => selectedTags.has(d.id)))

    const clusterOptions = ref([])
    const matchingClusters = computed(() => {
        if (!cluster.value) return []
        const opts = clusterOptions.value.filter(d => d.includes(cluster.value))
        if (opts.some(d => d === cluster.value)) return []
        return opts.length <= 5 ? opts : opts.slice(0, 5).concat("..")
    })

    const hasChanges = computed(() => {
        const setA = new Set(props.item.categories.map(d => d.cat_id))
        const setB = new Set(categories.value.map(d => d.id))
        const setC = new Set(props.item.tags.map(d => d.tag_id))
        const setD = new Set(props.item.evidence.map(d => d.ev_id))
        return props.item.name !== name.value ||
            props.item.cluster !== cluster.value ||
            props.item.description !== desc.value ||
            props.item.group_id !== extGroup.value ||
            (setA.size !== setB.size || setA.union(setB).size !== setA.size) ||
            (setC.size !== selectedTags.size || setC.union(selectedTags).size !== setC.size) ||
            (setD.size !== selectedEvs.size || setD.union(selectedEvs).size !== setD.size)
    })

    const allCats = ref([])
    const requiredCats = computed(() => Array.from(group(leafCats.value, d => d.parent).keys()))
    const leafCats = computed(() => allCats.value.filter(d => d.is_leaf))
    const selectedCats = computed(() => categories.value.map(d => d.id))

    const allEvidence = computed(() => {
        const evs = DM.getDataBy("evidence", d => d.item_id === props.item.item_id && d.code_id === props.item.code_id)
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

    function setCluster(cls) {
        if (cls && clusterOptions.value.includes(cls)) {
            cluster.value = cls;
        }
    }

    function toggleTag(id) {
        if (!props.allowEdit) return;
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
            if (category.is_leaf) {
                // its a leaf node, so we can just add or remove it
                const before = categories.value.findIndex(d => d.id === category.id);
                if (before >= 0) {
                    categories.value.splice(before, 1)
                } else {
                    categories.value.push(category)
                }
            } else {
                // its an intermediate node, so we either add or remove all its leaf children
                const paths = DM.getDerived("meta_cats_path")
                const children = leafCats.value.filter(d => paths.find(p => p.id === d.id).path.includes(category.id))
                const hasAll = children.every(d => categories.value.find(dd => dd.id === d.id))
                children.forEach(c => {
                    const idx = categories.value.findIndex(dd => dd.id === c.id)
                    if (idx < 0 && !hasAll) {
                        // add if not there yet and not all were selected beforehand
                        categories.value.push(c)
                    } else if (idx >= 0 && hasAll) {
                        // remove if all children were selected beforehand
                        categories.value.splice(idx, 1)
                    }
                })
            }
        }
    }

    function toggleEvidence(id) {
        if (!props.allowEdit) return;
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
        cluster.value = props.item.cluster;
        extGroup.value = props.item.group_id;
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
            const obj = Object.assign(props.item)
            obj.name = name.value;
            obj.description = desc.value;
            obj.cluster = cluster.value ? cluster.value : null;
            obj.categories = categories.value.map(d => ({ cat_id: d.id, meta_id: props.item.id }));
            obj.tags = tags.value.map(d => ({ tag_id: d.id }))
            obj.evidence = evidence.value.filter(d => selectedEvs.has(d.id)).map(d => ({ ev_id: d.id }))

            if (existing.value) {
                obj.group_id = extGroup.value
                await updateExternalization(obj)
                toast.success("updated meta item")
            } else {
                obj.item_id = props.item.item_id;
                obj.code_id = app.currentCode;
                obj.created = Date.now();
                obj.created_by = app.activeUserId;
                await createExternalization(obj)
                times.needsReload("meta_groups")
                toast.success("created new meta item")
            }
            emit("update")
            times.needsReload("meta_items")
        } catch {
            toast.error(`error ${props.item.id ? 'updating' : 'creating'} meta item`)
        }
    }

    function onClickTree(data, event) {
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "meta_category", data.id,
            mx + 10,
            my + 10,
            { parent: data.id },
            CTXT_OPTIONS.ext_category.concat(CTXT_OPTIONS.ext_category_add)
        )
    }

    function init() {
        const game = DM.getDataItem("items", props.item.item_id);
        allTags.value = game ? game.allTags : []
        allTags.value.sort(sortObjByString("name"))
        gameGroups.value = DM.getDataBy("meta_groups", d => d.item_id === props.item.item_id)
        clusterOptions.value = DM.getData("meta_clusters", false)

        allCats.value = DM.getData("meta_categories", false)
        name.value = props.item.name;
        desc.value = props.item.description;
        cluster.value = props.item.cluster;
        categories.value = props.item.categories.map(d => allCats.value.find(dd => dd.id === d.cat_id));

        selectedTags.clear();
        props.item.tags.forEach(d => selectedTags.add(d.tag_id))

        selectedEvs.clear()
        props.item.evidence.forEach(d => selectedEvs.add(d.ev_id))

        time.value = Date.now()
    }

    onMounted(init)

    watch(() => props.item.id, init)
    watch(() => times.meta_items, init)
    watch(() => times.meta_groups, function() {
        gameGroups.value = DM.getDataBy("meta_groups", d => d.item_id === props.item.item_id)
    })
    watch(() => times.meta_categories, function() {
        allCats.value = DM.getData("meta_categories", false)
        time.value = Date.now()
    })
</script>