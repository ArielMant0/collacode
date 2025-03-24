<template>
    <div>
        <div>
            <div class="d-flex align-center mb-2">
                <v-text-field v-model="name"
                    density="compact"
                    label="Group Name"
                    class="mr-2"
                    :readonly="!allowEdit"
                    hide-details
                    hide-spin-buttons/>
                <v-btn icon="mdi-sync"
                    class="mr-2"
                    density="compact"
                    variant="text"
                    rounded="sm"
                    :color="!allowEdit || !hasChanges ? 'default' : 'primary'"
                    :disabled="!allowEdit || !hasChanges"
                    @click="saveChanges"/>
                <v-btn icon="mdi-delete"
                    class="mr-2"
                    density="compact"
                    variant="text"
                    rounded="sm"
                    :color="!allowEdit || !hasChanges ? 'default' : 'error'"
                    :disabled="!allowEdit || !hasChanges"
                    @click="readName"/>
            </div>

            <v-btn
                icon="mdi-plus"
                size="small"
                class="mr-2"
                density="compact"
                rounded="sm"
                :disabled="!allowEdit"
                @click="addEmpty"
                color="primary"/>
            <v-btn v-for="e in exts"
                :key="'i_'+e.id"
                prepend-icon="mdi-circle"
                size="small"
                class="mr-2"
                variant="tonal"
                density="comfortable"
                @click="select(e.id)"
                :color="model === e.id ? 'primary' : 'black'">
                {{ e.name }}
            </v-btn>
        </div>
        <v-divider class="mt-4 mb-4" thickness="1"></v-divider>
        <MetaItemWidget v-if="selectedExt" :item="selectedExt" @update="emit('update')" @cancel="emit('update')"/>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { computed, onMounted, ref } from 'vue';
    import MetaItemWidget from './MetaItemWidget.vue';
    import { useTimes } from '@/store/times';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { useToast } from 'vue-toastification';
    import { updateExtGroups } from '@/use/data-api';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    const model = defineModel({ default: 0, type: Number })
    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
    })

    const emit = defineEmits(["update"])

    const { allowEdit } = storeToRefs(app)

    const name = ref(props.item.name)

    const hasChanges = computed(() => props.item.name !== name.value)

    const selectedExt = computed(() => {
        if (!model.value) return null;
        return exts.value.find(d => d.id === model.value)
    })
    const exts = ref([])

    function select(id) { model.value = id; }

    function readAll() {
        readName();
        readExts();
    }
    function readName() { name.value = props.item.name }
    function readExts() {
        exts.value = DM.getDataBy("meta_items", d => d.group_id === props.item.id);
        if (!exts.value.find(d => d.id === model.value)) {
            select(exts.value.length > 0 ? exts.value[0].id : 0)
        }
    }

    async function saveChanges() {
        try {
            const obj = Object.assign({}, props.item)
            obj.name = name.value
            await updateExtGroups([obj])
            toast.success("update group name to " + name.value)
            times.needsReload("meta_groups")
        } catch {
            toast.success("error updating group name to " + name.value)
        }
    }

    function addEmpty() {
        exts.value.push({
            id: -1,
            item_id: props.item.item_id,
            code_id: props.item.code_id,
            group_id: props.item.id,
            name: "",
            description: "",
            categories: [],
            tags: [],
            evidence: []
        })
        select(-1)
    }

    onMounted(readAll)

    watch(() => props.item.id, readAll)
    watch(() => times.meta_groups, readName)
    watch(() => times.meta_items, readExts)

</script>