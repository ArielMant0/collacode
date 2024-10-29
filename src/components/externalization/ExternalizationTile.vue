<template>
<div style="max-width: 100%;">
    <div ref="wrapper" class="d-flex" style="max-width: 100%;">
        <div v-if="allowEdit" class="d-flex flex-column mr-2">
            <v-btn @click="deleteItem"
                height="55"
                class="mb-1"
                density="comfortable"
                variant="outlined"
                color="error"
                rounded="0"
                size="small"
                icon="mdi-delete"/>

            <v-btn @click="emit('edit', item)"
                height="55"
                class="mt-1"
                density="comfortable"
                variant="outlined"
                color="primary"
                rounded="0"
                size="small"
                icon="mdi-pencil"/>
        </div>

        <div v-if="showBars">
            <MiniBarCode
                :dimensions="dimensions"
                :options="dimOptions"
                :data="selectedCatsNames"
                :width="120"
                :height="120"
                />
        </div>

        <v-sheet class="mr-2 pa-2" style="width: 50%;" color="grey-lighten-4" rounded="sm">
            <div>
                <i><b>{{ item.name }}</b></i>
                <span style="float: right;" class="text-caption">{{ item.tags.length }} tags</span>
            </div>
            <p>{{ item.description }}</p>
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
            <EvidenceCell v-for="e in evidence"
                :key="'e_'+e.id"
                :item="e"
                :allowed-tags="tags"
                @select="app.setShowEvidence(e.id)"/>
        </div>
    </div>
    <div class="mt-1 d-flex text-caption">
        <div class="mr-2">
            <v-btn :icon="liked ? 'mdi-thumb-up' : 'mdi-thumb-up-outline'"
                density="compact"
                variant="plain"
                class="mr-1"
                :disabled="item.created_by === app.activeUserId"
                @click="toggleLike"/>
            <v-tooltip content-class="light-bg">
                <template v-slot:activator="{ props }">
                    <span v-bind="props">{{ numLike }}</span>
                </template>
                <template v-slot:default>
                    <div class="d-flex">
                        <v-chip v-for="(u, i) in item.likes"
                            :class="i > 0 ? 'mr-1' : 'mr-1 ml-1'"
                            :color="app.getUserColor(u.created_by)"
                            variant="flat"
                            size="x-small"
                            density="compact">{{ u.created_by }}</v-chip>
                    </div>
                </template>
            </v-tooltip>
        </div>
        <div>
            <v-btn :icon="disliked ? 'mdi-thumb-down' : 'mdi-thumb-down-outline'"
                density="compact"
                variant="plain"
                class="mr-1"
                :disabled="item.created_by === app.activeUserId"
                @click="toggleDislike"/>
            <v-tooltip content-class="light-bg">
                <template v-slot:activator="{ props }">
                    <span v-bind="props">{{ numDislike }}</span>
                </template>
                <template v-slot:default>
                    <div class="d-flex">
                        <v-chip v-for="(u, i) in item.dislikes"
                            :class="i > 0 ? 'mr-1' : 'mr-1 ml-1'"
                            :color="app.getUserColor(u.created_by)"
                            variant="flat"
                            size="x-small"
                            density="compact">{{ u.created_by }}</v-chip>
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
    import { addExtAgreement, deleteExternalization, updateExtAgreement } from '@/use/utility';
    import { useTimes } from '@/store/times';
    import { useToast } from 'vue-toastification';
    import { useElementSize } from '@vueuse/core';
    import EvidenceCell from '../evidence/EvidenceCell.vue';
    import { useApp } from '@/store/app';
    import MiniBarCode from '../vis/MiniBarCode.vue';
    import { group } from 'd3';

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
    const wrapper = ref(null)

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

    const allCats = ref(DM.getData("ext_categories"))
    const dimensions = computed(() => {
        const leaves = allCats.value.filter(d => !allCats.value.some(dd => dd.parent === d.id))
        const set = new Set(Array.from(group(leaves, d => d.parent).keys()))
        return allCats.value.filter(d => set.has(d.id)).map(d => d.name)
    })
    const dimOptions = computed(() => {
        const obj = {};
        dimensions.value.forEach(dim => {
            const id = allCats.value.find(d => d.name === dim).id
            obj[dim] = allCats.value.filter(d => d.parent === id).map(d => d.name)
        })
        return obj;
    })

    const selectedCats = computed(() => {
        time.value = Date.now();
        return props.item.categories.map(d => d.cat_id)
    })
    const selectedCatsNames = computed(() => {
        return props.item.categories.map(d => allCats.value.find(dd => dd.id === d.cat_id).name)
    })

    const tags = computed(() => {
        const game = DM.getDataItem("games", props.item.game_id)
        return game ? game.allTags : [];
    });
    const evidence = computed(() => {
        const evs = DM.getDataBy("evidence", d => {
            return d.game_id === props.item.game_id &&
                props.item.tags.find(t => t.tag_id === d.tag_id)
        });

        evs.forEach(e => {
            e.rows = 2 + (e.description.includes('\n') ? e.description.match(/\n/g).length : 0)
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
        try {
            await deleteExternalization(props.item.id)
            toast.success("deleted 1 externalization")
            times.needsReload("externalizations")
        } catch {
            toast.error("error deleting externalization")
        }
    }

    async function toggleLike() {
        try {
            if (!liked.value && !disliked.value) {
                const agg = { ext_id: props.item.id, value: 1, created_by: app.activeUserId }
                await addExtAgreement(agg)
            } else {
                if (liked.value) {
                    const agg = {
                        id: agreement.id,
                        ext_id: props.item.id,
                        value: 0,
                        created_by: app.activeUserId
                    }
                    await updateExtAgreement(agg)
                } else if (disliked.value) {
                    const agg = {
                        id: agreement.id,
                        ext_id: props.item.id,
                        value: 1,
                        created_by: app.activeUserId
                    }
                    await updateExtAgreement(agg)
                }
            }
            toast.success("updated agreement")
            times.needsReload("ext_agreements")
        } catch {
            toast.error("error updating externalization agreement")
        }
    }

    async function toggleDislike() {
        try {
            if (!agreement.value) {
                const agg = { ext_id: props.item.id, value: -1, created_by: app.activeUserId }
                await addExtAgreement(agg)
            } else {
                if (liked.value) {
                    const agg = {
                        id: agreement.id,
                        ext_id: props.item.id,
                        value: -1,
                        created_by: app.activeUserId
                    }
                    await updateExtAgreement(agg)
                } else if (disliked.value) {
                    const agg = {
                        id: agreement.id,
                        ext_id: props.item.id,
                        value: 0,
                        created_by: app.activeUserId
                    }
                    await updateExtAgreement(agg)
                }
            }
            toast.success("updated agreement")
            times.needsReload("ext_agreements")
        } catch {
            toast.error("error updating externalization agreement")
        }
    }

    function readAgree() {
        const l = props.item.likes.find(d => d.created_by === app.activeUserId);
        const d = props.item.dislikes.find(d => d.created_by === app.activeUserId);
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

    onMounted(readAgree)

    watch(() => times.ext_categories, function() {
        allCats.value = DM.getData("ext_categories")
        time.value = Date.now()
    })
    watch(() => times.ext_agreements, readAgree)

</script>

<style scoped>
:global(.light-bg) {
    background-color: #f5f5f5 !important;
    border: 1px solid white;
}
</style>