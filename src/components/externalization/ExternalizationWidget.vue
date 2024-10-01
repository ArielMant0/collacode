<template>
    <div>
        <v-text-field v-model="name"
            density="compact"
            label="Name"
            hide-details
            hide-spin-buttons/>
        <v-textarea v-model="desc"
            density="compact"
            class="mb-2"
            hide-details
            hide-spin-buttons/>
        <div class="d-flex justify-space-between mb-2">
            <v-btn
                prepend-icon="mdi-delete"
                :color="hasChanges ? 'error' : 'default'"
                density="comfortable"
                :disabled="!hasChanges"
                @click="discardChanges"
                >discard</v-btn>
            <v-btn
                prepend-icon="mdi-sync"
                :color="hasChanges ? 'primary' : 'default'"
                density="comfortable"
                :disabled="!hasChanges"
                @click="saveChanges"
                >sync</v-btn>
        </div>
        <TreeMap
            :data="allCats"
            :selected="selectedCats"
            :width="mapWidth"
            :height="mapHeight"
            @click="toggleCategory"/>
        <div class="d-flex mt-2">
            <EvidenceCell v-for="e in evidence"
                :key="e.id"
                :item="e"
                :allowed-tags="tags"
                :width="evidenceSize"
                :height="evidenceSize"/>
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import TreeMap from '../vis/TreeMap.vue';
    import EvidenceCell from '../evidence/EvidenceCell.vue';
    import { computed } from 'vue';
    import { useToast } from 'vue-toastification';
    import { updateExternalization } from '@/use/utility';
    import { useTimes } from '@/store/times';

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
            default: 700
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

    const times = useTimes()
    const toast = useToast();

    const name = ref(props.item.name)
    const desc = ref(props.item.description)
    const categories = ref(props.item.categories.map(d => Object.assign({}, d)))

    const hasChanges = computed(() => {
        const setA = new Set(props.item.categories.map(d => d.id))
        const setB = new Set(categories.value.map(d => d.id))
        return props.item.name !== name.value ||
            props.item.description !== desc.value ||
            setA.union(setB).size !== props.item.categories.length
    })

    const allCats = computed(() => DM.getData("ext_categories"))
    const selectedCats = computed(() => categories.value.map(d => d.cat_id))

    const tags = computed(() => {
        const t = DM.getData("tags")
        return props.item.tags.map(d => t.find(t => t.id === d.tag_id))
    })
    const tagNames = computed(() => {
        const obj = {};
        tags.value.forEach(d => obj[d.id] = d.name)
        return obj;
    })
    const evidence = computed(() => {
        return DM.getDataBy("evidence", d => {
            return d.game_id === props.item.game_id &&
                d.code_id === props.item.code_id &&
                tagNames.value[d.tag_id] !== undefined
        })
    })

    function toggleCategory(category) {
        if (props.allowEdit) {
            const before = categories.value.findIndex(d => d.parent === category.parent);
            if (before) {
                categories.value.splice(before, 1)
            }
            categories.value.push(category)
        }
    }

    function discardChanges() {
        if (!hasChanges) {
            return toast.warning("no changes to discard");
        }
        name.value = props.item.name;
        desc.value = props.item.description;
        categories.value = props.item.categories.map(d => Object.assign({}, d));
    }
    async function saveChanges() {
        if (!hasChanges) {
            return toast.warning("no changes to sync");
        }

        try {
            props.item.name = name.value;
            props.item.description = desc.value;
            props.item.categories = categories.value.map(d => Object.assign({}, d));
            await updateExternalization(props.item)
            toast.success("updated externalization")
            times.needsReload("externalizations")
        } catch {
            toast.error("error updating externalization")
        }
    }

    watch(() => props.item.id, function() {
        name.value = props.item.name;
        desc.value = props.item.description;
        categories.value = props.item.categories.map(d => Object.assign({}, d));
    })
</script>