<template>
    <MiniDialog v-model="model" title="Add new externalization" @cancel="cancel" @submit="save" min-width="1400">
        <template v-slot:text>
            <div class="d-flex align-start">
                <div style="width: 35%;" class="mr-2">
                    <v-text-field v-model="name"
                        density="compact"
                        label="Name"
                        hide-details
                        hide-spin-buttons/>
                    <v-textarea v-model="desc"
                        class="mt-2 mb-2"
                        density="compact"
                        label="Description"
                        rows="10"
                        hide-details
                        hide-spin-buttons/>
                    <TreeMap
                        :data="allCats"
                        :selected="catIds"
                        :width="450"
                        :height="250"
                        @click="toggleCategory"
                        />
                    <v-btn
                        density="compact"
                        color="primary"
                        block
                        @click="addCat = true">
                        add category
                    </v-btn>
                </div>
                <div style="width: 35%; max-height: 80vh; overflow-y: auto;" class="mr-2">
                    <v-list
                        density="compact"
                        width="100%"
                        class="mt-2 mb-2">
                        <v-list-item v-for="t in item.allTags"
                            :key="'t_'+t.id"
                            :title="t.name"
                            :subtitle="t.description"
                            :active="selected[t.id]"
                            :color="selected[t.id] ? 'primary' : 'default'"
                            density="compact"
                            @click="toggleTag(t.id)"
                            >
                            <template v-slot:append>
                                <span>{{ numEv[t.id] }}</span>
                            </template>
                        </v-list-item>
                    </v-list>
                </div>
                <div class="d-flex flex-wrap" style="width: 30%;">
                    <EvidenceCell v-for="e in evidence"
                        class="pa-1 mr-2"
                        :key="'ev_t_'+e.id"
                        :item="e"
                        :allowed-tags="item.allTags"
                        :width="150"
                        :height="150"
                        :selected="false"
                        :title="e.description"/>
                </div>
            </div>
            <NewExtCategoryDialog v-model="addCat"/>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import MiniDialog from '../dialogs/MiniDialog.vue';
    import DM from '@/use/data-manager';
    import EvidenceCell from '../evidence/EvidenceCell.vue';
    import { group } from 'd3';
    import TreeMap from '../vis/TreeMap.vue';
    import NewExtCategoryDialog from './NewExtCategoryDialog.vue';
    import { useToast } from 'vue-toastification';
    import { createExternalization } from '@/use/utility';
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';

    const model = defineModel();
    const props = defineProps({
        item: {
            type: Object,
        },
    })

    const emit = defineEmits(["cancel", "submit"])

    const app = useApp()
    const toast = useToast()
    const times = useTimes();

    const name = ref("")
    const desc = ref("")
    const selected = reactive({})
    const selectedTags = computed(() => props.item.allTags.filter(d => selected[d.id]))

    const allEvidence = computed(() => {
        const evs = DM.getDataBy("evidence", d => d.game_id === props.item.id)
        evs.forEach(e => {
            e.rows = 2 + (e.description.includes('\n') ? e.description.match(/\n/g).length : 0)
            e.open = false;
        });
        return evs;
    });
    const evidence = computed(() => {
        if (selectedTags.value.length === 0) return [];
        return allEvidence.value.filter(d => selected[d.tag_id]);
    });
    const numEv = computed(() => {
        const obj = {};
        const g = group(allEvidence.value, d => d.tag_id)
        props.item.allTags.forEach(t => {
            obj[t.id] = g.has(t.id) ? g.get(t.id).length : 0
        });
        return obj
    });

    const allCats = ref(DM.getData("ext_categories"))
    const numCats = computed(() => {
        const leaves = allCats.value.filter(d => d.is_leaf)
        const g = group(leaves, d => d.parent)
        return g.size
    })
    const categories = ref([])
    const catIds = computed(() => categories.value.map(d => d.id))

    const addCat = ref(false)

    function toggleTag(id){
        if (selected[id]) {
            delete selected[id]
        } else {
            selected[id] = true
        }
    }
    function toggleCategory(category) {
        if (category.is_leaf) {
            const before = categories.value.findIndex(d => d.id === category.id);
            if (before >= 0) {
                categories.value.splice(before, 1)
            } else {
                categories.value.push(category)
            }
            categories.value = categories.value.filter(d => d.is_leaf)
        }
    }

    function cancel() {
        emit("cancel")
        model.value = false;
    }
    async function save() {
        if (categories.value.length < numCats.value) { return toast.warning("too few externalization categories") }
        if (selectedTags.value.length === 0) { return toast.warning("missing related tags") }
        if (name.value.length === 0) { return toast.warning("missing name") }
        if (desc.value.length === 0) { return toast.warning("missing description") }

        try {
            await createExternalization({
                name: name.value,
                game_id: props.item?.id,
                code_id: app.currentCode,
                description: desc.value,
                created: Date.now(),
                created_by: app.activeUserId,
                categories: categories.value.map(d => ({ cat_id: d.id })),
                tags: selectedTags.value.map(d => ({ tag_id: d.id }))
            })
            emit("save")
            model.value = false;
            times.needsReload("externalizations")
        } catch {
            toast.error("error creating new externalization")
        }
    }

    onMounted(() => allCats.value = DM.getData("ext_categories"))

    watch(() => props.item?.id, function() {
        const vals = Object.keys(selected);
        vals.forEach(d => delete selected[d])
        allCats.value = DM.getData("ext_categories")
    });
</script>