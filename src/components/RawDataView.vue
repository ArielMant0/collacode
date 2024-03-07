<template>
    <div class="d-flex">
        <v-combobox
            v-model="filterNames"
            :items="data"
            class="ml-1 mr-1"
            density="compact"
            clearable
            label="filter by game title .."
            item-title="name"
            item-value="name"/>
        <v-combobox
            v-model="filterTags"
            :items="tags"
            class="ml-1 mr-1"
            density="compact"
            clearable
            label="filter by tags .."
            item-title="name"
            item-value="name"/>
    </div>
    <v-data-table
        :key="'time_'+time"
        v-model="selectedRows"
        v-model:items-per-page="itemsPerPage"
        v-model:page="page"
        :items="data"
        :headers="headers"
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
                <td v-for="(h, i) in headers">

                    <v-icon v-if="i === 0" class="mr-2" density="compact" variant="text" @click="toggleEdit(item)">
                        {{ item.edit ? 'mdi-check' : 'mdi-pencil' }}
                    </v-icon>

                    <v-icon v-if="h.key === 'tags'" class="mr-2" @click="openTagDialog(item.id)">mdi-plus</v-icon>

                    <a v-if="!item.edit && h.type === 'url'" :href="item[h.key]" target="_blank">open in new tab</a>
                    <span v-else-if="!item.edit && h.key === 'tags'" class="text-caption text-ww" >
                        {{ tagsToString(item.tags) }}
                    </span>
                    <input v-else
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
                <v-btn v-if="allowAdd" width="100" size="small" @click="addRow">add row</v-btn>
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
            <template v-slot:text>
                <v-list density="compact">
                    <v-list-item v-for="tag in tagging.item.tags"
                        :title="tag.name"
                        :subtitle="app.getUserName(tag.created_by)"
                        density="compact"
                        hide-details>

                        <template v-slot:append>
                            <v-tooltip v-if="tag.tag_id" :text="getTagDesc(tag.tag_id)" location="right">
                                <template v-slot:activator="{ props }">
                                    <v-icon v-bind="props">mdi-information-outline</v-icon>
                                </template>
                            </v-tooltip>
                            <v-tooltip v-else-if="tag.description" :text="description" location="right">
                                <template v-slot:activator="{ props }">
                                    <v-icon v-bind="props">mdi-information-outline</v-icon>
                                </template>
                            </v-tooltip>
                        </template>
                    </v-list-item>
                </v-list>

                <v-combobox v-model="tagging.newTag"
                    autofocus
                    :items="tags"
                    item-title="name"
                    item-value="name"
                    style="min-width: 250px"
                    class="mb-1"
                    density="compact"
                    hide-details
                    hide-spin-buttons
                    append-icon="mdi-plus"
                    @update:model-value="tagChange"
                    @click:append="addNewTag"
                    @keyup="onKeyUpTag"/>

                <v-text-field v-model="tagging.newTagDesc"
                    :disabled="tagAlreadyExists"
                    style="min-width: 250px"
                    density="compact"
                    hide-details
                    hide-spin-buttons
                    placeholder="add a description"/>
            </template>

            <v-btn rounded="0" color="success" @click="saveAndClose">save</v-btn>
        </v-card>
    </v-dialog>

</template>

<script setup>
    import { computed, reactive, ref } from 'vue'
    import { useApp } from '@/store/app'
    import { useLoader } from '@/use/loader';
    import DM from '@/use/data-manager';

    const app = useApp();
    const loader = useLoader();

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
        const name = typeof(tagging.newTag) === "object" ? tagging.newTag.name : tagging.newTag;
        return tags.value.find(d => d.name.match(new RegExp(name, "i")) !== null) !== undefined;
    })
    const addTagsDialog = ref(false)
    const selectedRows = ref([])

    const page = ref(1);
    const itemsPerPage = ref(10);
    const pageCount = computed(() => Math.ceil(props.data.length / itemsPerPage.value))

    const tags = computed(() => DM.getData("tags"))

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
        }
    });
    const emit = defineEmits(["add-row"])

    const data = computed(() => {
        if (!filterNames.value && !filterTags.value) {
            return props.data
        }

        if (filterNames.value && typeof(filterNames.value) === "object") {
            filterNames.value = filterNames.value.name;
        }
        if (filterTags.value &&typeof(filterTags.value) === "object") {
            filterTags.value = filterTags.value.name;
        }
        const nameReg = filterNames.value ? new RegExp(filterNames.value, "i") : null;
        const tagReg = filterTags.value ? new RegExp(filterTags.value, "i") : null;

        return props.data.filter(d => {
            const matchName = nameReg ? d.name.match(nameReg) !== null : false;
            const matchTag = tagReg && d.tags ? d.tags.some(t => t.name.match(tagReg) !== null) : false;
            return matchName || matchTag;
        });
    })

    function onKeyUp(event, item, header) {
        if (item.edit && event.code === "Enter") {
            item[header.key] = event.target.value;
            parseType(item, header.key, header.type);
        }
    }
    function onKeyUpTag(event) {
        if (event.code === "Enter") {
            addNewTag();
        }
    }

    function toggleEdit(item) {
        if (item.edit) {
            props.headers.forEach(h => parseType(item, h.key, h.type));
            if (item.id !== null) {
                loader.post("update/game", { game: item }).then(app.needsReload)
            } else {
                loader.post("add/games", { rows: [item], dataset: app.ds }).then(app.needsReload)
            }
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
    function tagChange() {
        if (tagging.item && tagging.newTag) {
            const name = typeof(tagging.newTag) === "object" ? tagging.newTag.name : tagging.newTag;
            const t = tags.value.find(d => d.name.match(new RegExp(name, "i")) !== null);
            if (t) {
                tagging.newTagDesc = t.description;
            }
        }
    }
    function addNewTag() {
        if (tagging.item && tagging.newTag) {
            const name = typeof(tagging.newTag) === "object" ? tagging.newTag.name : tagging.newTag;
            const tag = tags.value.find(d => d.name === name)
            if (tagging.item.tags) {
                tagging.item.tags.push({
                    name: name,
                    description: tagging.newTagDesc,
                    created_by: app.activeUserId,
                    tag_id: tag ? tag.id : null
                });
            }
            tagging.newTag = "";
            tagging.newTagDesc = "";
        }
    }
    function onClose() {
        if (!addTagsDialog.value) {
            tagging.item = {};
            tagging.newTag = "";
            tagging.newTagDesc = "";
        }
    }
    function saveAndClose() {
        const body = {
            game_id: tagging.item.id,
            user_id: app.activeUserId,
            code_id: app.activeCode,
            created: Date.now(),
        };
        body.tags = tagging.item.tags.map(t => {
            if (t.tag_id !== null) {
                return  { tag_id: t.tag_id };
            }
            return { tag_name: t.name, description: t.description }
        })
        loader.post("update/game/datatags", body).then(app.needsReload)
        tagging.item = {};
        tagging.newTag = "";
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

    function addRow() {
        emit('add-row');
        page.value = 1;
    }

    defineExpose({ parseType, defaultValue })

</script>

<style scoped>
.text-ww {
    overflow: hidden;
    white-space: wrap;
}
</style>
