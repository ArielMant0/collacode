<template>
<div style="max-width: 100%;">

    <div ref="wrapper" class="d-flex" style="max-width: 100%;">

        <div class="d-flex flex-column justify-space-between mr-2">
            <v-btn @click="emit('edit', item)"
                block
                class="mb-1"
                density="comfortable"
                variant="tonal"
                color="primary"
                rounded="sm"
                size="small"
                icon="mdi-pencil"/>

            <v-btn @click="deleteItem"
                block
                class="mt-1"
                density="comfortable"
                variant="tonal"
                color="error"
                rounded="sm"
                size="small"
                :disabled="!allowEdit"
                icon="mdi-delete"/>
        </div>

        <div v-if="showBars" class="mr-2">
            <MiniBarCode
                binary
                :dimensions="dimensions"
                :options="dimOptions"
                :data="item.categories"
                :width="200"
                :height="140"
                @click="toggleDimension"
                @right-click="contextDimension"/>
        </div>

        <v-sheet class="mr-2 pa-1" style="width: 55%;" color="surface-light" rounded="sm">
            <div>
                <i><b>{{ item.name }}</b></i>
                <span style="float: right;" class="text-caption">
                    {{ item.tags.length }} {{ item.tags.length > 1 ? 'tags' : 'tag' }}, {{ item.evidence.length }} evidence
                </span>
            </div>
            <p style="white-space: pre-line">{{ item.description }}</p>
        </v-sheet>


        <TreeMap v-if="!showBars"
            :data="allCats"
            :time="time"
            title-attr="name"
            :selected="selectedCats"
            hide-headers
            :width="wrapSize.width.value*0.2"
            :height="120"/>

        <div class="d-flex flex-wrap ml-2" style="width: 30%;">
            <EvidenceCell v-for="(e, idx) in evidence"
                :key="'e_'+e.id"
                :item="e"
                :height="100"
                :index="idx"
                zoom-on-hover
                :evidence-list="evidence.map(dd => dd.id)"/>
        </div>
    </div>
    <div class="mt-1 d-flex text-caption">
        <div class="mr-2">
            <v-btn :icon="liked ? 'mdi-thumb-up' : 'mdi-thumb-up-outline'"
                density="compact"
                variant="plain"
                class="mr-1"
                :disabled="!allowEdit"
                @click="toggleLike"/>

            <v-tooltip>
                <template v-slot:activator="{ props }">
                    <span v-bind="props" style="cursor: help;">{{ numLike }}</span>
                </template>
                <template v-slot:default>
                    <div class="d-flex">
                        <v-chip v-for="(u, i) in item.likes"
                            :class="i > 0 ? 'mr-1' : 'mr-1 ml-1'"
                            :color="app.getUserColor(u.created_by)"
                            variant="flat"
                            size="small"
                            density="comfortable">{{ app.getUserShort(u.created_by) }}</v-chip>
                    </div>
                </template>
            </v-tooltip>
        </div>
        <div>
            <v-btn :icon="disliked ? 'mdi-thumb-down' : 'mdi-thumb-down-outline'"
                density="compact"
                variant="plain"
                class="mr-1"
                :disabled="!allowEdit"
                @click="toggleDislike"/>

            <v-tooltip>
                <template v-slot:activator="{ props }">
                    <span v-bind="props" style="cursor: help;">{{ numDislike }}</span>
                </template>
                <template v-slot:default>
                    <div class="d-flex">
                        <v-chip v-for="(u, i) in item.dislikes"
                            :class="i > 0 ? 'mr-1' : 'mr-1 ml-1'"
                            :color="app.getUserColor(u.created_by)"
                            variant="flat"
                            size="small"
                            density="comfortable">{{ app.getUserShort(u.created_by) }}</v-chip>
                    </div>
                </template>
            </v-tooltip>
        </div>
    </div>
</div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { computed, watch, ref, reactive, onMounted } from 'vue';
    import TreeMap from '../vis/TreeMap.vue';
    import { addExtAgreement, addMetaCatConns, deleteExternalization, deleteMetaCatConns, updateExtAgreement } from '@/use/data-api';
    import { useTimes } from '@/store/times';
    import { useToast } from 'vue-toastification';
    import { useElementSize } from '@vueuse/core';
    import EvidenceCell from '../evidence/EvidenceCell.vue';
    import { useApp } from '@/store/app';
    import MiniBarCode from '../vis/MiniBarCode.vue';
    import { group, pointer } from 'd3';
    import { storeToRefs } from 'pinia';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        buttonLabel: {
            type: String,
            default: "select"
        },
        allowEdit: {
            type: Boolean,
            default: false
        },
        showBars: {
            type: Boolean,
            default: false
        },
        showTreemap: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["edit"])

    const app = useApp();
    const times = useTimes();
    const toast = useToast();
    const settings = useSettings()

    const wrapper = ref(null)

    const { activeUserId } = storeToRefs(app)

    const time = ref(Date.now())

    const agreement = reactive({
        id: null,
        value: 0
    });

    const liked = computed(() => agreement.id !== null && agreement.value > 0)
    const disliked = computed(() => agreement.id !== null && agreement.value < 0)

    const numLike = computed(() => props.item.likes.length)
    const numDislike = computed(() => props.item.dislikes.length)

    const wrapSize = useElementSize(wrapper)

    const allCats = ref(DM.getData("meta_categories", false))
    const dimensions = computed(() => {
        const leaves = allCats.value.filter(d => !allCats.value.some(dd => dd.parent === d.id))
        const set = new Set(Array.from(group(leaves, d => d.parent).keys()))
        return allCats.value.filter(d => set.has(d.id)).map(d => d.name)
    })
    const dimOptions = computed(() => {
        const obj = {};
        dimensions.value.forEach(dim => {
            const id = allCats.value.find(d => d.name === dim).id
            obj[dim] = allCats.value.filter(d => d.parent === id).map(d => ({ id: d.id, name: d.name }))
        })
        return obj;
    })

    const selectedCats = computed(() => {
        time.value = Date.now();
        return props.item.categories.map(d => d.cat_id)
    })

    const tags = computed(() => {
        const game = DM.getDataItem("items", props.item.item_id)
        return game ? game.allTags : [];
    });

    const selectedEv = reactive(new Set())
    const evidence = computed(() => {
        const evs = DM.getDataBy("evidence", d => selectedEv.has(d.id));

        evs.forEach(e => {
            e.rows = e.rows ? e.rows : 2 + (e.description.includes('\n') ? e.description.match(/\n/g).length : 0)
            e.open = false;
        });

        evs.sort((a, b) => {
            const nameA = tags.value.find(d => d.id === a.tag_id).name.toLowerCase(); // ignore upper and lowercase
            const nameB = tags.value.find(d => d.id === b.tag_id).name.toLowerCase(); // ignore upper and lowercase
            if (nameA < nameB) { return -1; }
            if (nameA > nameB) { return 1; }
            // names must be equal
            return 0;
        })

        return evs;
    });

    async function deleteItem() {
        if (!props.allowEdit) return;
        try {
            await deleteExternalization(props.item.id)
            toast.success("deleted 1 meta item")
            times.needsReload("meta_groups")
            times.needsReload("meta_items")
        } catch {
            toast.error("error deleting meta item")
        }
    }

    async function toggleLike() {
        if (!props.allowEdit) return;
        try {
            if (!liked.value && !disliked.value) {
                const agg = { meta_id: props.item.id, value: 1, created_by: activeUserId.value, item_id: props.item.item_id }
                await addExtAgreement(agg)
            } else {
                if (liked.value) {
                    const agg = {
                        id: agreement.id,
                        meta_id: props.item.id,
                        item_id: props.item.item_id,
                        value: 0,
                        created_by: activeUserId.value
                    }
                    await updateExtAgreement(agg)
                } else if (disliked.value) {
                    const agg = {
                        id: agreement.id,
                        meta_id: props.item.id,
                        item_id: props.item.item_id,
                        value: 1,
                        created_by: activeUserId.value
                    }
                    await updateExtAgreement(agg)
                }
            }
            toast.success("updated agreement")
            times.needsReload("meta_agreements")
        } catch {
            toast.error("error updating externalization agreement")
        }
    }

    async function toggleDislike() {
        if (!props.allowEdit) return;
        try {
            if (!agreement.value) {
                const agg = { meta_id: props.item.id, value: -1, created_by: activeUserId.value, item_id: props.item.item_id }
                await addExtAgreement(agg)
            } else {
                if (liked.value) {
                    const agg = {
                        id: agreement.id,
                        meta_id: props.item.id,
                        item_id: props.item.item_id,
                        value: -1,
                        created_by: activeUserId.value
                    }
                    await updateExtAgreement(agg)
                } else if (disliked.value) {
                    const agg = {
                        id: agreement.id,
                        meta_id: props.item.id,
                        item_id: props.item.item_id,
                        value: 0,
                        created_by: activeUserId.value
                    }
                    await updateExtAgreement(agg)
                }
            }
            toast.success("updated agreement")
            times.needsReload("meta_agreements")
        } catch {
            toast.error("error updating externalization agreement")
        }
    }
    async function toggleDimension(dim) {
        // TODO: implement
        if (dim) {
            const d = props.item.categories.find(d => d.cat_id === dim.id)
            try {
                if (d) {
                    await deleteMetaCatConns([d.id])
                    toast.success("removed category " + dim.name)
                    times.needsReload("meta_items")
                } else {
                    await addMetaCatConns({
                        meta_id: props.item.id,
                        cat_id: dim.id,
                    })
                    toast.success("added category " + dim.name)
                    times.needsReload("meta_items")
                }
            } catch (e) {
                console.error(e.toString())
                toast.error("error changed category " + dim.name)
            }
        }
    }
    function contextDimension(dim, event) {
        if (dim) {
            const [mx, my] = pointer(event, document.body)
            settings.setRightClick(
                "meta_category", dim.id,
                mx, my,
                dim.name, null,
                CTXT_OPTIONS.meta_category
            )
        }
    }

    function readAgree() {
        const l = props.item.likes.find(d => d.created_by === activeUserId.value);
        const d = props.item.dislikes.find(d => d.created_by === activeUserId.value);
        if (l) {
            agreement.value = l.value;
            agreement.id = l.id;
        } else if (d) {
            agreement.value = d.value;
            agreement.id = d.id;
        } else {
            agreement.value = 0;
            agreement.id = null;
        }
        time.value = Date.now();
    }
    function readEvidence() {
        selectedEv.clear();
        props.item.evidence.forEach(d => selectedEv.add(d.ev_id))
    }

    function readAll() {
        readEvidence()
        readAgree()
    }
    onMounted(readAll)

    watch(() => props.item.id, readAll)
    watch(() => times.meta_categories, function() {
        allCats.value = DM.getData("meta_categories", false)
        time.value = Date.now()
    })
    watch(() => times.meta_agreements, readAgree)
    watch(() => times.meta_items, readAll)

</script>

<style scoped>
:global(.light-bg) {
    background-color: #f5f5f5 !important;
    border: 1px solid white;
}
</style>