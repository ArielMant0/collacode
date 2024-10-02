<template>
    <div style="width: 100%;" class="mt-2">

    <div class="d-flex mb-2">
        <v-autocomplete v-model="searchTags"
            :items="contents.tags"
            label="search for tags"
            item-title="name"
            item-value="id"
            density="compact"
            class="mr-2"
            hide-details
            hide-no-data
            hide-spin-buttons
            clearable
            style="min-width: 300px"
            />

        <v-btn v-if="allowAdd" @click="openAddDialog" color="secondary" append-icon="mdi-plus">
            ADD NEW TAG
        </v-btn>
    </div>

    <div class="d-flex flex-wrap text-caption">

        <template v-for="group in filteredData">
            <v-card v-if="showLetter" class="ma-1 pa-2" color="primary" elevation=0 :height="height ? height : 'auto'">{{ group[0].toUpperCase() }}</v-card>
            <v-card v-for="tag in group[1]"
                :style="{ 'border': highlightClicked && contents && same(contents.clicked, tag) ? '1px solid #444' : '1px solid #eee' }"
                :width="width"
                :height="height ? height : 'auto'"
                density="compact"
                class="ma-1 pa-2"
                :color="tag[itemColor] ? tag[itemColor] : 'default'"
                :elevation="selected && (!tag.id || selected[tag.id]) ? 4 : 0"
                @click="e => onClick(tag, e)"
                @contextmenu="e => onRightClick(tag, e)"
                >
                <div class="d-flex flex-column justify-space-between" style="height: 100%">
                    <v-tooltip :text="tag.name" location="right" open-delay="200">
                        <template v-slot:activator="{ props }">
                            <span v-bind="props" class="text-dots cursor-help" style="max-width: 100%">{{ tag.name }}</span>
                        </template>
                    </v-tooltip>

                    <slot name="actions" :tag="tag"></slot>
                </div>
            </v-card>
        </template>

        <MiniDialog v-model="addDialog" title="Add New Tag" submitText="create" min-width="400" @submit="addNewTag" @cancel="closeAddDialog">
            <template v-slot:text>
                <TagWidget :data="newTag" :parents="contents.tags" emit-only can-edit no-buttons @change="setNewTagUpdated"/>
            </template>
        </MiniDialog>

    </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { reactive, onMounted, watch, computed, ref } from 'vue';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';
    import MiniDialog from '@/components/dialogs/MiniDialog.vue'
    import { useTimes } from '@/store/times';

    const app = useApp();
    const times = useTimes();
    const loader = useLoader();
    const toast = useToast()

    const props = defineProps({
        source: {
            type: String,
            required: false
        },
        data: {
            type: Array,
            required: false
        },
        selected: {
            type: Object,
            required: false
        },
        highlightClicked: {
            type: Boolean,
            default: false
        },
        width: {
            type: Number,
            default: 75
        },
        height: {
            type: Number,
            default: null
        },
        itemColor: {
            type: String,
            default: "color"
        },
        includeIntermediate: {
            type: Boolean,
            default: false
        },
        allowAdd: {
            type: Boolean,
            default: false
        },
        showLetter: {
            type: Boolean,
            default: false
        }
    });
    const emit = defineEmits(["click", "right-click", "edit", "delete", "add"])

    const searchTags = ref("")
    const addDialog = ref(false)
    const contents = reactive({ tags: [], clicked: null })
    const newTag = reactive({
        name: "",
        description: "",
        parent: null,
        created_by: app.activeUserId,
        is_leaf: 1,
        code_id: app.currentCode
    })
    const newTagUpdated = reactive({
        name: "",
        description: "",
        parent: null,
        created_by: app.activeUserId,
        is_leaf: 1,
        code_id: app.currentCode
    })

    const filteredData = computed(() => {
        if (searchTags.value) {
            return d3.group(
                contents.tags.filter(d => d.id === searchTags.value || d.path.includes(searchTags.value)),
                d => d.name[0].toLowerCase()
            )
        }
        return d3.group(contents.tags, d => d.name[0].toLowerCase())
    })

    function same(a, b) {
        if (!a || !b) return false;
        if (a.id && b.id) {
            return a.id == b.id;
        }
        if (a.name && b.name) {
            return a.name === b.name;
        }
        return false;
    }
    function readData() {
        let data = props.data ? props.data : DM.getData(props.source, false)
        if (!data) return;

        if (!props.data && !props.includeIntermediate) {
            data = data.filter(d => d.is_leaf === 1);
        }

        data.sort((a, b) => {
            const nameA = a.name.toLowerCase(); // ignore upper and lowercase
            const nameB = b.name.toLowerCase(); // ignore upper and lowercase
            if (nameA < nameB) { return -1; }
            if (nameA > nameB) { return 1; }
            // names must be equal
            return 0;
        })
        contents.tags = data
    }
    function onClick(tag, event) {
        contents.clicked = contents.clicked && same(contents.clicked, tag) ? null : tag;
        emit('click', tag, event)
    }
    function onRightClick(tag, event) {
        event.preventDefault()
        emit("right-click", tag, event)
    }

    function openAddDialog() {
        newTag.name = "";
        newTag.description = "";
        newTag.created_by = app.activeUserId;
        newTag.code_id = app.currentCode;
        newTag.parent = null;
        newTag.is_leaf = 1;
        setNewTagUpdated(newTag)
        addDialog.value = true
    }
    function closeAddDialog() {
        addDialog.value = false;
        newTag.name = "";
        newTag.description = "";
        newTag.parent = null;
        newTag.is_leaf = 1;
    }
    async function addNewTag() {
        if (!newTagUpdated.name) {
            toast.error("unique tag name is missing")
            return;
        }
        if (contents.tags.find(d => d.name === newTagUpdated.name)) {
            toast.error(`tag name ${newTagUpdated.name} already exists`)
            return;
        }

        newTagUpdated.created = Date.now();
        await loader.post("add/tags", { rows: [newTagUpdated] })
        toast.success("added new tag " + newTagUpdated.name)
        closeAddDialog();
        times.needsReload("tags");
    }
    function setNewTagUpdated(obj) {
        newTagUpdated.name = obj.name;
        newTagUpdated.description = obj.description;
        newTagUpdated.parent = obj.parent;
        newTagUpdated.is_leaf = obj.is_leaf;
        newTagUpdated.created_by = app.activeUserId;
        newTagUpdated.code_id = app.currentCode;
    }

    onMounted(readData);

    watch(() => props.data, readData, { deep: true })

    watch(() => ([
        times.all,
        times.transition,
        times[props.source],
    ]), readData, { deep: true });

</script>

<style scoped>
.text-dots {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis
}
</style>