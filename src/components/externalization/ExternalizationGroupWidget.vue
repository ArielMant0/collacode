<template>
    <div>
        <div>
            <v-btn
                icon="mdi-plus"
                size="small"
                class="mr-2"
                density="compact"
                rounded="sm"
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
        <v-divider class="mt-4 mb-4" thickness="2"></v-divider>
        <ExternalizationWidget v-if="selectedExt" :item="selectedExt" :allow-edit="allowEdit" @update="emit('update')"/>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { computed, onMounted } from 'vue';
    import ExternalizationWidget from './ExternalizationWidget.vue';
    import { useTimes } from '@/store/times';

    const times = useTimes()
    const model = defineModel({ default: 0, type: Number })
    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        allowEdit: {
            type: Boolean,
            default: false,
        },
    })

    const emit = defineEmits(["update"])

    const selectedExt = computed(() => {
        if (!model.value) return null;
        return exts.value.find(d => d.id === model.value)
    })
    const exts = ref([])

    function select(id) { model.value = id; }

    function readExts() {
        exts.value = DM.getDataBy("externalizations", d => d.group_id === props.item.id);
        if (!exts.value.find(d => d.id === model.value)) {
            select(exts.value[0].id)
        }
    }

    function addEmpty() {
        exts.value.push({
            id: -1,
            game_id: props.item.game_id,
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

    onMounted(readExts)

    watch(() => props.item.id, readExts)
    watch(() => times.externalizations, readExts)

</script>