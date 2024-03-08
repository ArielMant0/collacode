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
        v-model="selectedRows"
        v-model:items-per-page="itemsPerPage"
        v-model:page="page"
        v-model:sort-by="sortBy"
        :items="data"
        :headers="allHeaders"
        item-value="id"
        :show-select="selectable"
        @update:model-value="selectRows">

        <template v-slot:item="{ item }">
            <tr :class="item.edit ? 'bg-grey-lighten-2' : ''">

                <td v-if="selectable">
                    <v-checkbox
                        :model-value="selectedRows.includes(item.id)"
                        density="compact"
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

                    <v-icon v-if="h.key === 'tags'" class="mr-2" @click="openTagDialog(item.id)">mdi-plus</v-icon>
                    <span v-if="h.key === 'tags'" class="text-caption text-ww">
                        {{ tagsToString(item.tags) }}
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
                <v-pagination v-model="page" :length="pageCount" :total-visible="5" show-first-last-page density="comfortable" class="mb-1"/>
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

    <v-dialog v-model="addTagsDialog" min-width="400" width="auto" @update:model-value="onClose">
        <v-card max-width="500" title="Add tags">
            <v-card-text>
                <v-list density="compact">
                    <v-list-item v-for="tag in tagging.item.tags"
                        :title="tag.name"
                        :subtitle="app.getUserName(tag.created_by)"
                        density="compact"
                        hide-details>

                        <template v-slot:append>
                            <v-tooltip v-if="!tag.unsaved && app.activeUserId === tag.created_by" text="delete this tag" location="right">
                                <template v-slot:activator="{ props }">
                                    <v-icon color="error" v-bind="props" @click="deleteTag(tagging.item, tag.tag_id)">mdi-delete</v-icon>
                                </template>
                            </v-tooltip>
                            <v-tooltip :text="tag.description ? tag.description : getTagDesc(tag.tag_id)" location="right">
                                <template v-slot:activator="{ props }">
                                    <v-icon v-bind="props">mdi-information-outline</v-icon>
                                </template>
                            </v-tooltip>
                        </template>
                    </v-list-item>
                </v-list>

                <v-combobox v-model="tagging.newTag"
                    autofocus
                    :items="tagNames"
                    style="min-width: 250px"
                    class="mb-1"
                    density="compact"
                    hide-details
                    hide-spin-buttons
                    append-icon="mdi-plus"
                    @update:model-value="onTagChange"
                    @click:append="addNewTag"
                    @keyup="onKeyUpTag"/>

                <v-text-field v-model="tagging.newTagDesc"
                    :disabled="tagAlreadyExists"
                    style="min-width: 250px"
                    density="compact"
                    hide-details
                    hide-spin-buttons
                    placeholder="add a description"/>
            </v-card-text>

            <v-card-actions>
                <v-btn color="warning" @click="addTagsDialog = false">cancel</v-btn>
                <v-btn color="success" :disabled="!tagChanges" @click="saveAndClose">save</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-dialog v-model="deleteGameDialog" min-width="400" width="auto">
        <v-card max-width="500" title="Delete tags">
            <v-card-text>
                Are you sure that you want to delete the game {{ deletion.name }}?
            </v-card-text>
            <v-card-actions>
                <v-btn color="warning" @click="deleteGameDialog = false">cancel</v-btn>
                <v-btn color="error" @click="deleteRow">delete</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

</template>

<script setup>
    import { computed, reactive, ref } from 'vue'
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

    const tagChanges = ref(false);
    const filterNames = ref("")
    const filterTags = ref("")
    const tagging = reactive({
        item: null,
        newTag: "",
        newTagDesc: "",
    })
    const tagAlreadyExists = computed(() => {
        if (!tagging.item || !tagging.newTag) {
            return false;
        }
        return tags.value.find(d => d.name.toLowerCase() === tagging.newTag) !== undefined;
    })
    const addTagsDialog = ref(false)
    const selectedRows = ref([])

    const deleteGameDialog = ref(false);
    const deletion = reactive({ id: "", name: "" })

    const page = ref(1);
    const itemsPerPage = ref(10);
    const pageCount = computed(() => Math.ceil(props.data.length / itemsPerPage.value))

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
        return props.data.filter(d => d.name.toLowerCase() === filterNames.value ||
            d.tags.some(t => t.name.toLowerCase() === filterTags.value));
    })

    function reloadTags() {
        tags.value = DM.getData("tags")
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
    function onKeyUpTag(event) {
        if (event.code === "Enter") {
            addNewTag();
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
        app.selectByAttr("id", selectedRows.value);
    }

    function tagsToString(tags) {
        return tags.map(d => d.name + " (" + d.created_by + ")")
            .join(", ")
    }

    function getTagDesc(id) {
        const t = tags.value.find(d => d.id === id);
        return t ? t.description : "";
    }

    function openTagDialog(id) {
        tagging.item = props.data.find(d => d.id === id);
        addTagsDialog.value = true;
    }
    function onTagChange() {
        if (tagging.item && tagging.newTag) {
            const t = tags.value.find(d => d.name.toLowerCase() === tagging.newTag);
            if (t) {
                tagging.newTagDesc = t.description;
            }
        }
    }
    function addNewTag() {
        if (tagging.item && tagging.newTag) {
            const t = tags.value.find(d => d.name.toLowerCase() === tagging.newTag);
            tagging.item.tags.push({
                name: tagging.newTag,
                description: tagging.newTagDesc,
                created_by: app.activeUserId,
                tag_id: t ? t.id : null,
                unsaved: true,
            });
            tagging.newTag = "";
            tagging.newTagDesc = "";
            tagChanges.value = true;
        }
    }
    function onClose() {
        if (!addTagsDialog.value) {
            tagging.item = {};
            tagging.newTag = "";
            tagging.newTagDesc = "";
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
        tagging.newTag = "";
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
        emit('add-row');
        sortBy.value = []
        page.value = 1;
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
            emit("update-datatags", item);
        }
    }

    defineExpose({ parseType, defaultValue })

    watch(() => props.time, reloadTags)

</script>

<style scoped>
.text-ww {
    overflow: hidden;
    white-space: wrap;
}
</style>
