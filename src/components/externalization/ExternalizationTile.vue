<template>
    <div ref="wrapper" class="d-flex">
        <div class="mr-1" style="width: 60%;">
            <v-text-field v-model="item.name"
                density="compact"
                label="Name"
                hide-details
                hide-spin-buttons/>
            <v-textarea v-model="item.description"
                readonly
                hide-details
                hide-spin-buttons
                label="Description"
                rows="3"
                density="compact"/>
        </div>
        <TreeMap
            :data="allCats"
            :selected="selectedCats"
            :width="wrapSize.width.value*0.2"
            :height="120"
            hide-names/>
        <div class="ml-1 mr-1" style="font-size: 10px; width: 16%;">
            <div v-for="c in selectedCats" :key="c">
                <i>{{ catPaths[c].map(d => catNames[d]).join(" / ") }}</i>
            </div>
        </div>
        <div v-if="allowEdit" class="d-flex flex-column">
            <v-btn @click="deleteItem" height="60" density="compact" variant="flat" color="error" rounded="0" icon="mdi-delete"></v-btn>
            <v-btn @click="emit('select', item)" height="60" density="compact" variant="flat" color="primary" rounded="0" icon="mdi-menu-right"></v-btn>
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { computed } from 'vue';
    import TreeMap from '../vis/TreeMap.vue';
    import { deleteExternalization, toToTreePath } from '@/use/utility';
    import { useTimes } from '@/store/times';
    import { useToast } from 'vue-toastification';
    import { useElementSize } from '@vueuse/core';

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
        }
    })
    const emit = defineEmits(["select"])

    const times = useTimes();
    const toast = useToast();
    const wrapper = ref(null)

    const wrapSize = useElementSize(wrapper)

    const allCats = computed(() => DM.getData("ext_categories"))
    const catNames = computed(() => {
        const obj = {};
        allCats.value.forEach(d => obj[d.id] = d.name);
        return obj;
    })
    const catPaths = computed(() => {
        const obj = {};
        allCats.value.forEach(d => obj[d.id] = toToTreePath(d, allCats.value));
        return obj;
    })
    const selectedCats = computed(() => props.item.categories.map(d => d.cat_id))

    async function deleteItem() {
        try {
            await deleteExternalization(props.item.id)
            toast.success("deleted 1 externalization")
            times.needsReload("externalizations")
        } catch {
            toast.error("error deleting externalization")
        }
    }

</script>