<template>
    <div class="d-flex">
        <v-combobox
            v-model="filterNames"
            :items="dataNames"
            class="ml-1 mr-1"
            density="compact"
            clearable
            @click:clear="filterNames = ''"
            label="filter by game title .."/>
        <v-combobox
            v-model="filterTags"
            :items="tagNames"
            class="ml-1 mr-1"
            density="compact"
            clearable
            @click:clear="filterTags = ''"
            label="filter by tags .."/>
    </div>
    <v-data-table
        :key="'time_'+time"
        v-model="selection"
        v-model:items-per-page="itemsPerPage"
        v-model:page="page"
        v-model:sort-by="sortBy"
        :items="data"
        :headers="allHeaders"
        item-value="id"
        :show-select="selectable"
        density="compact">

        <template v-slot:item="{ item, isSelected, toggleSelect }">
            <tr :class="item.edit ? 'bg-grey-lighten-2' : ''">

                <td v-if="selectable">
                    <v-checkbox-btn
                        density="compact"
                        :model-value="isSelected({ value: item.id })"
                        @click="toggleSelect({ value: item.id })"
                        hide-details hide-spin-buttons/>
                </td>

                <td v-for="h in allHeaders">

                    <span v-if="editable && h.key === 'actions'">
                        <v-icon  v-if="item.id" class="mr-2" density="compact" variant="text" color="error" @click="openDeleteDialog(item)">
                            mdi-delete
                        </v-icon>
                        <v-icon class="mr-2" density="compact" variant="text" @click="toggleEdit(item)">
                            {{ item.edit ? 'mdi-check' : 'mdi-pencil' }}
                        </v-icon>
                    </span>

                    <v-icon v-if="h.key === 'tags' && editable" class="mr-2" @click="openTagDialog(item.id)">mdi-plus</v-icon>
                    <span v-if="h.key === 'tags'" class="text-caption text-ww">
                        <template v-for="([_, dts]) in tagGroups[item.id]" :key="'g'+item.id+'_t'+dts[0].id">
                            <v-tooltip :text="getTagDescription(dts[0])" location="top" open-delay="200">
                                <template v-slot:activator="{ props }">
                                    <span v-bind="props" style="cursor: help;">
                                        {{ dts[0].name }}
                                    </span>
                                </template>
                            </v-tooltip>
                            (<v-chip v-for="(u, i) in dts" :class="i > 0 ? 'pa-1 ml-1' : 'pa-1'" :color="app.getUserColor(u.created_by)" variant="flat" size="small" density="compact">{{ u.created_by }}</v-chip>)
                        </template>
                        <!-- <span v-if="item.tags.length > 3">..</span> -->
                    </span>

                    <a v-if="!item.edit && h.type === 'url'" :href="item[h.key]" target="_blank">open in new tab</a>

                    <input v-else-if="h.key !== 'actions' && h.key !== 'tags'"
                        v-model="item[h.key]"
                        style="width: 90%;"
                        @keyup="event => onKeyUp(event, item, h)"
                        @blur="parseType(item, h.key, h.type)"
                        :disabled="!item.edit"/>
                </td>
            </tr>
        </template>

        <template v-slot:bottom>
            <div class="d-flex justify-space-between align-center">
                <div v-if="editable">
                    <v-btn v-if="allowAdd" width="100" size="small" @click="addRow">add row</v-btn>
                    <v-btn :disabled="selection.length === 0" size="small" class="ml-1"
                        @click="editTagsSelection = true" color="default">edit tags for selection</v-btn>
                </div>
                <span v-else style="min-width: 100px"></span>

                <v-pagination v-model="page"
                    :length="pageCount"
                    :total-visible="5"
                    show-first-last-page
                    density="comfortable"
                    class="mb-1"/>

                <div class="d-flex align-center">
                    <span class="mr-3">Items per Page: </span>
                    <v-select
                        class="mr-3 pa-0"
                        style="min-width: 100px"
                        density="compact"
                        variant="outlined"
                        value="10"
                        :items="['10', '25', '50', '100', 'All']"
                        @update:model-value="updateItemsPerPage"
                        hide-details
                        hide-no-data/>
                    </div>
            </div>
        </template>

    </v-data-table>

    <v-dialog v-model="editRowTags" width="80%" height="85%" @update:model-value="onClose">
        <ItemTagEditor
            :item="tagging.item"
            :data="tagging.allTags"
            user-only
            @add="readAllTags"
            @delete="readAllTags"
            @cancel="onCancel"
            @save="onSaveTagsForItem"
            />
    </v-dialog>

    <v-dialog v-model="editTagsSelection" width="80%" height="85%">
        <SelectionTagEditor
            :selection="selectedGames"
            :data="tagging.addTags"
            user-only
            @add="readAllTags"
            @delete="readAllTags"
            @cancel="editTagsSelection = false"
            @save="onSaveTagsForSelected"
            />
    </v-dialog>

    <v-dialog v-model="deleteGameDialog" min-width="400" width="auto">
        <v-card max-width="500" title="Delete tags">
            <v-card-text>
                Are you sure that you want to delete the game {{ deletion ? deletion.name : "GAME" }}?
            </v-card-text>
            <v-card-actions>
                <v-btn class="ms-auto" color="warning" @click="closeDeleteGameDialog">cancel</v-btn>
                <v-btn class="ms-2" color="error" @click="deleteRow">delete</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

</template>

<script setup>
    import * as d3 from 'd3';
    import ItemTagEditor from '@/components/tags/ItemTagEditor.vue';
    import SelectionTagEditor from '@/components/tags/SelectionTagEditor.vue';
    import { computed, onMounted, reactive, ref } from 'vue'
    import { useApp } from '@/store/app'
    import { useToast } from "vue-toastification";
    import DM from '@/use/data-manager';

    const app = useApp();
    const toast = useToast();

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        headers: {
            type: Array,
            required: true
        },
        time: {
            type: Number,
            default: 0
        },
        allowAdd: {
            type: Boolean,
            default: false
        },
        selectable: {
            type: Boolean,
            default: false
        },
        editable: {
            type: Boolean,
            default: false
        },
    });
    const emit = defineEmits(["add-empty-row", "add-rows", "update-rows", "delete-rows", "add-datatags", "delete-datatags", "update-datatags"])

    const editRowTags = ref(false);
    const editTagsSelection = ref(false);

    const sortBy = ref([])
    const selection = ref([])
    const selectedGames = computed(() => selection.value.map(id => data.value.find(dd => dd.id === id)).filter(d => d))

    const tagging = reactive({
        item: null,
        allTags: []
    })

    const deleteGameDialog = ref(false);
    const deletion = reactive({ id: "", name: "" })

    const page = ref(1);
    const itemsPerPage = ref(10);
    const pageCount = computed(() => Math.ceil(data.value.length / itemsPerPage.value))

    const filterNames = ref("")
    const filterTags = ref("")

    const tags = ref([])
    const tagNames = computed(() => tags.value.map(d => d.name))
    const dataNames = computed(() => props.data.map(d => d.name))

    const allHeaders = computed(() => {
        if (!props.editable) {
            return props.headers;
        }
        return [{ title: "Actions", key: "actions", sortable: false, width: "100px" }].concat(props.headers)
    })

    const data = computed(() => {
        if (!filterNames.value && !filterTags.value) {
            return props.data
        }
        return props.data.filter(matchesFilters);
    })

    const tagGroups = computed(() => {
        const obj = { time: props.time };
        data.value.forEach(d => obj[d.id] = getTagsGrouped(d.tags))
        delete obj.time
        return obj;
    })

    function matchesFilters(d) {
        const n = filterNames.value.replaceAll("\(", "\\(").replaceAll("\)", "\\)")
        const f = filterTags.value.replaceAll("\(", "\\(").replaceAll("\)", "\\)")
        console.log(n, f)
        const r1 = new RegExp(n, "i");
        const r2 = new RegExp(f, "i");
        return (!filterNames.value || d.name.match(r1) !== null) &&
            (!filterTags.value || d.tags.some(t => t.name.match(r2) !== null));
    }

    function getTagsGrouped(itemTags) {
        return d3.group(itemTags.slice(0), d => d.tag_id);
    }
    function getTagDescription(datum) {
        if (datum.description) {
            return datum.description
        }
        const tag = tags.value.find(d => d.id === datum.tag_id);
        return tag ? tag.description : "";
    }

    function reloadTags() {
        if (DM.hasData("tags")) {
            tags.value = DM.getData("tags", false).slice()
            tags.value.sort((a, b) => {
                const nameA = a.name.toLowerCase(); // ignore upper and lowercase
                const nameB = b.name.toLowerCase(); // ignore upper and lowercase
                if (nameA < nameB) { return -1; }
                if (nameA > nameB) { return 1; }
                // names must be equal
                return 0;
            })
        } else {
            tags.value = [];
        }
        readAllTags();
    }

    function onKeyUp(event, item, header) {
        if (item.edit) {
            item.changes = true;
            if (event.code === "Enter") {
                item[header.key] = event.target.value;
                parseType(item, header.key, header.type);
            }
        }
    }

    function toggleEdit(item) {
        if (item.edit && item.changes) {
            props.headers.forEach(h => parseType(item, h.key, h.type));
            emit(item.id !== null ? "update-rows" : "add-rows", [item])
            item.changes = false;
        }
        item.edit = !item.edit;
    }

    function defaultValue(type) {
        switch (type) {
            case "string": return "";
            case "url": return new URL("https://store.steampowered.com/");
            case "integer": return 0;
            case "float": return 0.0;
            case "boolean": return false;
            case "datetime": return new Date();
            case "array": return [];
            case "object": return {};
        }
        return null;
    }
    function parseType(d, key, type) {
        if (!d[key]) return;
        try {
            switch (type) {
                case "string": d[key] = ""+d[key]; break;
                case "url": d[key] = new URL(d[key]); break;
                case "integer": d[key] = Number.parseInt(d[key]); break;
                case "float": d[key] = Number.parseFloat(d[key]); break;
                case "boolean": d[key] = (d[key] === true || d[key] === 1 || d[key].match(/true|yes/i) !== null); break;
                case "datetime": d[key] = Date.parse(d[key]); break;
                case "array":
                case "object":
                    if (typeof(d[key]) === "string") {
                        d[key] = JSON.parse(d[key]);
                    }
                    break;
            }
        } catch {
            console.error("could not convert field", key, "to", type)
        }
    }

    function openTagDialog(id) {
        tagging.add = false;
        tagging.item = props.data.find(d => d.id === id);
        editRowTags.value = true;
    }

    function readAllTags() {
        if (!tagging.item || !tagging.item.tags) {
            tagging.allTags =  tags.value;
            return;
        }
        const extra = [];
        tagging.item.tags.forEach(d => {
            if (d.tag_id === null) {
                extra.push({
                    name: d.name,
                    id: null,
                    description: d.description,
                    created_by: app.activeUserId
                });
            }
        });
        tagging.allTags = extra.concat(tags.value);
    }

    function onSaveTagsForItem(item) {
        if (item) {
            emit("update-datatags", item);
            tagging.item = null;
        }
        editRowTags.value = false;
    }
    function onCancel() {
        tagging.item = null;
        editRowTags.value = false;
    }
    function onClose() {
        if (!editRowTags.value) {
            tagging.item = null;
        }
    }
    function onSaveTagsForSelected(add, remove) {
        if (add.length > 0) emit("add-datatags", add)
        if (remove.length > 0) emit("delete-datatags", remove)
        if (add.length === 0 && remove.length === 0) {
            toast.warning("no tags to add or delete")
        }
        editTagsSelection.value = false;
    }

    function updateItemsPerPage(value) {
        switch(value) {
            case "All":
                itemsPerPage.value = props.data.length;
                break;
            default:
                const num = Number.parseInt(value);
                itemsPerPage.value = Number.isInteger(num) ? num : 10;
                break;
        }
        if (page.value > pageCount.value) {
            page.value = pageCount.value;
        }
    }

    function openDeleteDialog(item) {
        deletion.id = item.id;
        deletion.name = item.name;
        deleteGameDialog.value = true;
    }
    function closeDeleteGameDialog() {
        deleteGameDialog.value = false;
        deletion.id = "";
        deletion.name = "";
    }
    function addRow() {
        emit('add-empty-row');
        sortBy.value = []
        page.value = pageCount.value;
    }
    function deleteRow() {
        if (deletion.id) {
            emit('delete-rows', [deletion.id]);
        }
        closeDeleteGameDialog();
    }

    defineExpose({ parseType, defaultValue })

    onMounted(() => {
        selection.value = []
        reloadTags();
    })

    watch(() => props.time, function() {
        reloadTags();
        page.value = Math.min(page.value, pageCount.value);
    })
    watch(() => app.dataLoading.tags, reloadTags)

</script>

<style scoped>
.text-ww {
    overflow: hidden;
    white-space: wrap;
}
</style>
