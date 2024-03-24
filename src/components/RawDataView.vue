<template>
    <div class="d-flex">
        <v-combobox
            v-model="filterNames"
            :items="dataNames"
            class="ml-1 mr-1"
            density="compact"
            clearable
            label="filter by game title .."/>
        <v-combobox
            v-model="filterTags"
            :items="tagNames"
            class="ml-1 mr-1"
            density="compact"
            clearable
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
        density="compact"
        @update:model-value="selectRows">

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
                        <v-tooltip v-for="(t,i) in item.tags" :text="getTagDescription(t)" location="top" open-delay="200">
                            <template v-slot:activator="{ props }">
                                <span v-bind="props" style="cursor: help;">
                                    {{ t.name }} ({{ t.created_by }}){{ i < item.tags.length-1 ? ', ' : '' }}
                                </span>
                            </template>
                        </v-tooltip>
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
                <v-btn v-if="editable && allowAdd" width="100" size="small" @click="addRow">add row</v-btn>
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

    <v-dialog v-model="addTagsDialog" min-width="700" width="auto" :update:model-value="onClose">
        <v-card min-width="700" :title="'Add tags for '+tagging.item.name">
            <v-card-text>
                <v-list density="compact" height="400">
                    <v-list-item v-for="tag in tagging.item.tags"
                        :key="tag.id"
                        :title="tag.name"
                        :subtitle="getTagDescription(tag)"
                        density="compact"
                        hide-details>

                        <template v-slot:append>
                            <v-tooltip v-if="!tag.unsaved && app.activeUserId === tag.created_by" text="delete this tag" location="right">
                                <template v-slot:activator="{ props }">
                                    <v-icon color="error" class="mr-1" v-bind="props" @click="deleteTag(tagging.item, tag.tag_id)">mdi-delete</v-icon>
                                </template>
                            </v-tooltip>
                            <v-tooltip v-else-if="tag.unsaved && app.activeUserId === tag.created_by" text="delete this tag" location="right">
                                <template v-slot:activator="{ props }">
                                    <v-icon color="error" class="mr-1" v-bind="props" @click="deleteTempTag(tagging.item, tag.name)">mdi-delete</v-icon>
                                </template>
                            </v-tooltip>
                            <v-tooltip :text="app.getUserName(tag.created_by)" location="right">
                                <template v-slot:activator="{ props }">
                                    <v-icon v-bind="props">mdi-information-outline</v-icon>
                                </template>
                            </v-tooltip>
                        </template>
                    </v-list-item>

                    <v-list-item v-for="tag in tagsFiltered"
                        :key="tag.id"
                        :title="tag.name"
                        :subtitle="tag.description"
                        density="compact"
                        hide-details>

                        <template v-slot:append>
                            <v-tooltip text="add this tag" location="right">
                                <template v-slot:activator="{ props }">
                                    <v-icon color="primary" class="mr-1" v-bind="props" @click="addTag(tag)">mdi-plus</v-icon>
                                </template>
                            </v-tooltip>
                            <v-tooltip :text="app.getUserName(tag.created_by)" location="right">
                                <template v-slot:activator="{ props }">
                                    <v-icon v-bind="props">mdi-information-outline</v-icon>
                                </template>
                            </v-tooltip>
                        </template>
                    </v-list-item>

                </v-list>

                <v-checkbox v-model="tagging.add"
                    density="compact"
                    hide-details
                    hide-spin-buttons
                    label="create new tag"
                    />

                <TagWidget v-if="tagging.add"
                    :data="tagging.newTag"
                    name-label="New Tag Name"
                    desc-label="New Tag Description"
                    button-label="add"
                    button-icon="mdi-plus"
                    emit-only
                    @update="addNewTag"/>
            </v-card-text>

            <v-card-actions>
                <v-btn class="ms-auto" color="warning" @click="onCancel">cancel</v-btn>
                <v-btn class="ms-2" color="success" :disabled="!tagChanges" @click="saveAndClose">save</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-dialog v-model="deleteGameDialog" min-width="400" width="auto">
        <v-card max-width="500" title="Delete tags">
            <v-card-text>
                Are you sure that you want to delete the game {{ deletion.name }}?
            </v-card-text>
            <v-card-actions>
                <v-btn class="ms-auto" color="warning" @click="deleteGameDialog = false">cancel</v-btn>
                <v-btn class="ms-2" color="error" @click="deleteRow">delete</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

</template>

<script setup>
    import TagWidget from './TagWidget.vue';
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
    const emit = defineEmits(["add-empty-row", "add-rows", "update-rows", "delete-rows", "update-datatags"])

    const sortBy = ref([])
    const selection = ref(DM.selection.slice())

    const tagChanges = ref(false);
    const filterNames = ref("")
    const filterTags = ref("")
    const tagging = reactive({
        add: false,
        item: null,
        newTag: { name: "", description: "" },
    })

    const addTagsDialog = ref(false)

    const deleteGameDialog = ref(false);
    const deletion = reactive({ id: "", name: "" })

    const page = ref(1);
    const itemsPerPage = ref(10);
    const pageCount = computed(() => Math.ceil(data.value.length / itemsPerPage.value))

    const tags = ref([])
    const tagsFiltered = computed(() => {
        if (!tagging.item || !tagging.item.tags) return tags.value;
        return tags.value.filter(d => tagging.item.tags.find(dd => dd.tag_id === d.id) === undefined)
    })
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

    function matchesFilters(d) {
        const r1 = new RegExp(filterNames.value, "i");
        const r2 = new RegExp(filterTags.value, "i");
        return (!filterNames.value || d.name.match(r1) !== null) &&
            (!filterTags.value || d.tags.some(t => t.name.match(r2) !== null));
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

    function selectRows() {
        app.selectByAttr("id", selection.value)
    }

    function openTagDialog(id) {
        tagging.add = false;
        tagging.item = props.data.find(d => d.id === id);
        addTagsDialog.value = true;
    }

    function addTag(tag) {
        if (tagging.item && tag) {
            tagging.item.tags.push({
                name: tag.name,
                description: tag.description,
                created_by: tag.created_by,
                tag_id: tag.id,
                unsaved: true,
            });
            tagging.newTag.name = "";
            tagging.newTag.description = "";
            tagChanges.value = true;
        }
    }
    function addNewTag(tag) {
        if (tagging.item) {
            const tagName = tag.name.toLowerCase();
            const t = tags.value.find(d => d.name.toLowerCase() === tagName);
            if (t) {
                toast.error("tag with name "+tag.name+" already exists");
                tagging.newTag.name = "";
                return;
            }

            tagging.item.tags.push({
                name: tag.name,
                description: tag.description,
                created_by: app.activeUserId,
                tag_id: null,
                unsaved: true,
            });
            tagging.add = false;
            tagging.newTag.name = "";
            tagging.newTag.description = "";
            tagChanges.value = true;
        }
    }
    function onCancel() {
        addTagsDialog.value = false;
        onClose();
    }
    function onClose() {
        if (!addTagsDialog.value) {
            tagging.item.tags = tagging.item.tags.filter(d => !d.unsaved)
            tagging.item = {};
            tagging.add = false;
            tagging.newTag.name = "";
            tagging.newTag.description = "";
            if (tagChanges.value) {
                toast.warning("unsaved changes were discarded")
            }
            tagChanges.value = false;
        }
    }
    function saveAndClose() {
        if (tagChanges.value) {
            emit("update-datatags", tagging.item);
        }
        tagging.item = {};
        tagging.add = false;
        tagging.newTag.name = "";
        tagging.newTag.description = "";
        tagChanges.value = false;
        addTagsDialog.value = false;
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

    function addRow() {
        emit('add-empty-row');
        sortBy.value = []
        page.value = pageCount.value;
    }
    function deleteRow() {
        if (deletion.id) {
            emit('delete-row', deletion.id);
            deletion.id = "";
            deletion.name = "";
        }
    }
    function deleteTag(item, tagId) {
        const idx = item.tags.findIndex(t => t.tag_id === tagId);
        if (idx >= 0) {
            item.tags.splice(idx, 1);
            tagChanges.value = true;
        }
    }
    function deleteTempTag(item, tagName) {
        const idx = item.tags.findIndex(t => t.unsaved && t.name === tagName);
        if (idx >= 0) {
            item.tags.splice(idx, 1);
            tagChanges.value = true;
        }
    }

    defineExpose({ parseType, defaultValue })

    onMounted(() => {
        selection.value = DM.selection.slice(0);
        reloadTags();
    })

    watch(() => props.time, reloadTags)
    watch(() => app.dataLoading.tags, reloadTags)

</script>

<style scoped>
.text-ww {
    overflow: hidden;
    white-space: wrap;
}
</style>
