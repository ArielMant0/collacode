<template>
    <div class="d-flex">
        <v-combobox
            v-model="filterNamesTmp"
            :items="dataNames"
            class="ml-1 mr-1"
            density="compact"
            clearable
            style="width: 50%;"
            @click:clear="filterNames = null"
            label="filter by game title ..">
            <template v-slot:append-inner>
                <v-btn
                    icon="mdi-magnify"
                    rounded="sm"
                    class="ml-0"
                    variant="plain"
                    :color="filterNamesTmp === filterNames ? 'default' : 'primary'"
                    :disabled="filterNamesTmp === filterNames"
                    @click.stop.prevent="filterNames = filterNamesTmp"/>
            </template>
        </v-combobox>
        <v-combobox
            v-model="filterTagsTmp"
            :items="tagNames"
            class="ml-1 mr-1"
            density="compact"
            clearable
            style="width: 50%;"
            @click:clear="filterTags = null"
            label="filter by tags ..">

            <template v-slot:append-inner>
                <v-btn
                    icon="mdi-magnify"
                    rounded="sm"
                    class="ml-0"
                    variant="plain"
                    :color="filterTagsTmp === filterTags ? 'default' : 'primary'"
                    @click.prevent="filterTags = filterTagsTmp"
                    :disabled="filterTagsTmp === filterTags"/>
            </template>

            <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props" :prepend-icon="isAssignedTag(item.raw) ? 'mdi-circle-small' : 'mdi-new-box'"
                    :title="item.raw"
                    :subtitle="pathFromTagName(item.raw, true)">
                    <template v-slot:subtitle="{ subtitle }">
                        <span class="text-caption">{{ subtitle }}</span>
                    </template>
                </v-list-item>
            </template>
        </v-combobox>
    </div>
    <v-data-table
        :key="'time_'+time"
        v-model="selection"
        v-model:items-per-page="itemsPerPage"
        v-model:page="page"
        v-model:sort-by="sortBy"
        :items="tableData"
        :headers="allHeaders"
        item-value="id"
        :show-select="selectable"
        style="min-height: 450px;"
        density="compact">

        <template v-slot:item="{ item, isSelected, toggleSelect }">
            <tr :class="item.edit ? 'edit data-row' : 'data-row'" :key="'row_'+item.id" @click="openTagDialog(item.id)">

                <td v-if="selectable">
                    <v-checkbox-btn
                        density="compact"
                        :model-value="isSelected({ value: item.id })"
                        @click="toggleSelect({ value: item.id })"
                        hide-details hide-spin-buttons/>
                </td>

                <td v-for="h in allHeaders">

                    <span v-if="editable && h.key === 'actions'">
                        <v-icon  v-if="item.id >= 0" class="mr-2" density="compact" variant="text" color="error" @click.stop="openDeleteDialog(item)">
                            mdi-delete
                        </v-icon>
                        <v-icon  v-else class="mr-2" density="compact" variant="text" color="error" @click.stop="removeItem(item.id)">
                            mdi-delete
                        </v-icon>
                        <v-icon class="mr-2" density="compact" variant="text" @click.stop="toggleEdit(item)">
                            {{ item.edit ? 'mdi-check' : 'mdi-pencil' }}
                        </v-icon>
                    </span>

                    <span v-if="h.key === 'tags'" class="text-caption text-ww">
                        <template v-for="([_, dts], idx) in tagGroups[item.id]" :key="'g'+(item.id?item.id:-1)+'_t'+dts[0].id">
                            <span class="cursor-pointer"
                                @click.stop="app.toggleSelectByTag(dts[0].tag_id)"
                                @contextmenu.stop="e => onRightClickTag(e, item.id, dts[0].tag_id)"
                                :title="getTagDescription(dts[0])"
                                :style="{
                                    'font-weight': filterTags && matchesTagFilter(dts[0].name) || isTagSelected(dts[0]) ? 'bold':'normal',
                                    'color': isTagLeaf(dts[0].tag_id) ? 'inherit' : 'red'
                                }">
                                {{ dts[0].name }}
                            </span>
                            <span v-if="app.showAllUsers">
                                <v-chip v-for="(u, i) in dts"
                                    :class="i > 0 ? 'pa-1 mr-1' : 'pa-1 mr-1 ml-1'"
                                    :color="app.getUserColor(u.created_by)"
                                    variant="flat"
                                    size="small"
                                    density="compact">{{ u.created_by }}</v-chip>
                            </span>
                            <span v-else-if="idx < tagGroups[item.id].size-1" class="ml-1 mr-1">-</span>
                        </template>
                    </span>


                    <div v-if="h.key === 'teaser'">
                        <v-btn v-if="item.edit"
                            icon="mdi-file-upload"
                            rounded="sm"
                            density="compact"
                            variant="plain"
                            size="x-large"
                            @click="openTeaserDialog(item)"/>
                        <v-img v-else
                            :src="'teaser/'+item[h.key]"
                            :lazy-src="imgUrlS"
                            class="ma-1"
                            cover
                            width="80"
                            height="40"/>
                    </div>
                    <div v-else-if="h.type === 'url' && !item.edit">
                        <v-img v-if="isSteamLink(item[h.key])"
                            density="compact"
                            width="30"
                            height="30"
                            class="cursor-pointer shadow-hover"
                            src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/480px-Steam_icon_logo.svg.png"
                            @click="openInNewTab(item[h.key])"
                            />
                        <v-btn v-else
                            icon="mdi-open-in-new"
                            variant="plain"
                            rounded="sm"
                            density="compact"
                            @click="openInNewTab(item[h.key])"
                            />
                    </div>

                    <span v-else-if="h.key === 'numEvidence'" class="text-caption text-ww">
                        {{ item.numEvidence }}
                    </span>

                    <input v-else-if="h.key !== 'actions' && h.key !== 'tags'"
                        v-model="item[h.key]"
                        style="width: 90%; color: inherit;"
                        @keyup="event => onKeyUp(event, item, h)"
                        @blur="parseType(item, h.key, h.type)"
                        :disabled="!item.edit"/>
                </td>
            </tr>
        </template>

        <template v-slot:bottom>
            <div class="d-flex justify-space-between align-center">
                <div v-if="editable">
                    <v-btn v-if="allowAdd" width="100" size="small" @click="addRow">add item</v-btn>
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
                    <v-select v-model="numPerPage"
                        class="mr-3 pa-0"
                        style="min-width: 100px"
                        density="compact"
                        variant="outlined"
                        value="10"
                        :items="['5', '10', '20', '50', '100', 'All']"
                        @update:model-value="updateItemsPerPage"
                        hide-details
                        hide-no-data/>
                    </div>
            </div>
        </template>

    </v-data-table>

    <ItemEditor v-model="editRowTags"
        :item="tagging.item"
        :data="tagging.allTags"
        @add-tag="readAllTags"
        @delete-tag="readAllTags"
        @cancel="onCancel"
        @save-tags="onSaveTagsForItem"/>

    <v-dialog v-model="editTagsSelection" width="80%" height="85%">
        <SelectionTagEditor
            :selection="selectedGames"
            :data="tagging.addTags"
            user-only
            @add="readAllTags"
            @delete="readAllTags"
            @cancel="onCancelSelection"
            @save="onSaveTagsForSelected"
            />
    </v-dialog>

    <v-dialog v-model="deleteGameDialog" min-width="400" width="auto">
        <v-card max-width="500" title="Delete tags">
            <v-card-text>
                Are you sure that you want to delete the game {{ dialogItem ? dialogItem.name : "GAME" }}?
            </v-card-text>
            <v-card-actions>
                <v-btn class="ms-auto" color="warning" @click="closeDeleteGameDialog">cancel</v-btn>
                <v-btn class="ms-2" color="error" @click="deleteRow">delete</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <MiniDialog v-model="teaserDialog" @cancel="closeTeaserDialog" @submit="uploadTeaser">
        <template v-slot:text>
            Edit teaser for {{ dialogItem ? dialogItem.name : "GAME" }}
            <v-file-input v-model="dialogItem.teaserFile"
                accept="image/*"
                class="mt-2"
                label="Upload a teaser image"
                density="compact"
                hide-details
                hide-spin-buttons
                @update:model-value="readTeaserFile"/>
            <v-img class="pa-1 mt-2"
                :src="dialogItem.teaserPreview ? dialogItem.teaserPreview : 'teaser/'+dialogItem.teaser"
                cover
                :lazy-src="imgUrl"
                alt="Image Preview"
                width="500"/>
        </template>
    </MiniDialog>

    <ContextMenu v-if="rightClickTag.id"
        :options="['edit tag', 'add evidence']"
        :top="rightClickTag.y"
        :left="rightClickTag.x"
        @select="selectContext"
        @cancel="cancelContext"/>
</template>

<script setup>
    import * as d3 from 'd3';
    import SelectionTagEditor from '@/components/tags/SelectionTagEditor.vue';
    import MiniDialog from './dialogs/MiniDialog.vue';
    import { v4 as uuidv4 } from 'uuid';
    import { computed, onMounted, reactive, ref } from 'vue'
    import { useApp } from '@/store/app'
    import { useToast } from "vue-toastification";
    import DM from '@/use/data-manager';

    import imgUrl from '@/assets/__placeholder__.png'
    import imgUrlS from '@/assets/__placeholder__s.png'
    import ContextMenu from './dialogs/ContextMenu.vue';
    import ItemEditor from './dialogs/ItemEditor.vue';

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
        checkAssigned: {
            type: Boolean,
            default: false
        },
    });
    const emit = defineEmits([
        "add-empty-row", "add-rows", "update-rows", "delete-rows", "delete-tmp-row",
        "update-teaser",
        "add-datatags", "delete-datatags", "update-datatags"
    ])

    const editRowTags = ref(false);
    const editTagsSelection = ref(false);

    const rightClickTag = reactive({
        id: null, game: null,
        x: 0, y: 0,
    });

    const sortBy = ref([])
    const selection = ref([])
    const selectedGames = computed(() => selection.value.map(id => tableData.value.find(dd => dd.id === id)).filter(d => d))

    const tagging = reactive({
        item: null,
        allTags: []
    })

    const deleteGameDialog = ref(false);
    const teaserDialog = ref(false);

    const dialogItem = reactive({
        id: "", name: "",
        teaser: "",
        teaserFile: [],
        teaserPreview: "",
    })

    const page = ref(1);
    const itemsPerPage = ref(10);
    const numPerPage = ref("10")
    const pageCount = computed(() => {
        const obj = { time: props.time };
        delete obj.time
        return Math.ceil(tableData.value.length / itemsPerPage.value)
    })

    const filterNames = ref("")
    const filterNamesTmp = ref("")
    const filterTags = ref("")
    const filterTagsTmp = ref("")

    const tags = ref([])
    const tagNames = computed(() => tags.value.map(d => d.name))
    const dataNames = computed(() => props.data.map(d => d.name))

    const allHeaders = computed(() => {
        if (!props.editable) {
            return props.headers;
        }
        return [{ title: "Actions", key: "actions", sortable: false, width: "100px" }].concat(props.headers)
    })

    const tableData = computed(() => {
        if (!props.time || !filterNames.value && !filterTags.value) {
            return props.data
        }
        return props.data.filter(matchesFilters);
    })

    const tagGroups = computed(() => {
        const obj = { time: props.time };
        tableData.value.forEach(d => obj[d.id] = getTagsGrouped(d.tags))
        delete obj.time
        return obj;
    })

    function openInNewTab(url) {
        window.open(url, "_blank")
    }
    function isSteamLink(url) {
        if (!url) {
            return false;
        }
        return url.includes("store.steampowered.com")
    }
    function pathFromTagName(name, small=false) {
        const item = tags.value.find(d => d.name === name);
        if (item && item.pathNames) {
            if (small && item.path.length > 3) {
                const parts = item.pathNames.split(" / ")
                return parts[0] + " / " +
                    Array.from({ length: parts.length-3 }, () => "..").join(" / ") +
                    " / " + parts.at(-2) +
                    " / " + parts.at(-1)
            }
            return item.pathNames;
        }
        return ""
    }
    function isAssignedTag(name) {
        const item = tags.value.find(d => d.name === name)
        return item ? !props.checkAssigned || item.assigned && item.assigned.length > 0 : false
    }

    function isTagSelected(tag) {
        const f = DM.getFilter("tags", "id");
        return f ? f.includes(tag.id) || tag.path.some(t => f.includes(t)) : false;
    }
    function isTagLeaf(id) {
        const t = tags.value.find(d => d.id === id);
        return t ? t.is_leaf === 1 : false
    }

    function matchesGameFilter(name) {
        if (!filterNames.value) return true;
        const special = /(\(\)\{\}\-\_\.\:)/g
        const n = filterNames.value.replaceAll(special, "\$1")
        const r = new RegExp(n, "i");
        return name.match(r) !== null
    }
    function matchesTagFilter(name) {
        if (!filterTags.value) return true;
        const special = /(\(\)\{\}\-\_\.\:)/g
        const t = filterTags.value.replaceAll(special, "\$1")
        const r = new RegExp(t, "i");
        return name.match(r) !== null
    }
    function matchesFilters(d) {
        if (d.id < 0) return true;
        return matchesGameFilter(d.name) && (
            (!filterTags.value && d.tags.length === 0) ||
            d.tags.some(t => matchesTagFilter(t.name) || t.path.some(p => matchesTagFilter(getTagName(p))))
        )
    }

    function getTagsGrouped(itemTags) {
        const g = d3.group(itemTags.slice(0), d => d.tag_id);
        g.forEach(array => array.sort((a, b) => a.created_by - b.created_by))
        return g;
    }
    function getTagName(id) {
        const tag = tags.value.find(d => d.id === id);
        return tag ? tag.name : "";
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
            tags.value = DM.getDataBy("tags", t => t.is_leaf === 1).slice()
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

    function onRightClickTag(event, gameId, tagId) {
        event.preventDefault();
        if (rightClickTag.game === gameId && rightClickTag.id === tagId) {
            cancelContext();
        } else {
            rightClickTag.x = event.pageX + 10;
            rightClickTag.y = event.pageY - 20;
            rightClickTag.game = gameId;
            rightClickTag.id = tagId;
        }
    }
    function cancelContext() {
        rightClickTag.id = null;
        rightClickTag.game = null;
    }
    function selectContext(option) {
        if (option === "edit tag") {
            app.toggleEditTag(rightClickTag.id);
        } else {
            app.toggleAddEvidence(rightClickTag.game, rightClickTag.id)
        }
        cancelContext();
    }

    function toggleEdit(item) {
        if (item.edit && item.changes) {
            props.headers.forEach(h => parseType(item, h.key, h.type));
            if (item.id < 0) {
                item.id = null;
            }
            emit(item.id !== null ? "update-rows" : "add-rows", [item])
        }
        item.edit = !item.edit;
    }

    function defaultValue(type) {
        switch (type) {
            case "string": return "";
            case "url": return "https://store.steampowered.com/";
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
                case "url": d[key] = d[key]; break;
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
        if (!props.editable) return;
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
    function onCancel(changes) {
        if (changes) {
            toast.warning("discarding changes ..")
        }
        tagging.item = null;
        editRowTags.value = false;
    }
    function onCancelSelection(changes) {
        if (changes) {
            toast.warning("discarding changes ..")
        }
        editTagsSelection.value = false;
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
                itemsPerPage.value = tableData.value.length;
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
        dialogItem.id = item.id;
        dialogItem.name = item.name;
        dialogItem.teaserFile = [];
        dialogItem.teaser = item.teaser;
        dialogItem.teaserPreview = ""
        deleteGameDialog.value = true;
    }
    function closeDeleteGameDialog() {
        deleteGameDialog.value = false;
        dialogItem.id = "";
        dialogItem.name = "";
        dialogItem.teaserFile = [];
        dialogItem.teaserPreview = "";
    }
    function openTeaserDialog(item) {
        dialogItem.id = item.id;
        dialogItem.name = item.name;
        dialogItem.teaserFile = [];
        dialogItem.teaser = item.teaser;
        dialogItem.teaserPreview = ""
        teaserDialog.value = true;
    }
    function closeTeaserDialog() {
        teaserDialog.value = false;
        const item = tableData.value.find(d => d.id === dialogItem.id);
        if (item) { item.edit = false; }
        dialogItem.id = "";
        dialogItem.name = "";
        dialogItem.teaserFile = [];
        dialogItem.teaserPreview = "";
    }
    function readTeaserFile() {
        if (!dialogItem.teaserFile || dialogItem.teaserFile.length === 0) {
            dialogItem.teaserPreview = "";
            return;
        }

        const reader = new FileReader();
        reader.addEventListener('load', () => { dialogItem.teaserPreview = reader.result });
        reader.readAsDataURL(dialogItem.teaserFile[0]);
    }

    function addRow() {
        emit('add-empty-row');
        sortBy.value = []
        app.addAction("table", "last-page");
    }
    function removeItem(id) {
        if (id < 0) {
            emit('delete-tmp-row', id)
        }
    }
    async function uploadTeaser() {
        if (dialogItem.id) {
            if (!dialogItem.teaserFile || dialogItem.teaserFile.length === 0) {
                toast.error("upload a new image first")
                return;
            }

            const item = tableData.value.find(d => d.id === dialogItem.id);
            emit("update-teaser", item, uuidv4(), dialogItem.teaserFile[0]);
            teaserDialog.value = false;
            item.changes = false;
            item.edit = false;
            dialogItem.teaserFile = [];
            dialogItem.teaserPreview = "";
        }
    }
    function deleteRow() {
        if (dialogItem.id) {
            emit('delete-rows', [dialogItem.id]);
        }
        closeDeleteGameDialog();
    }

    defineExpose({ parseType, defaultValue })

    onMounted(() => {
        selection.value = []
        reloadTags();
        page.value = Math.max(1, Math.min(page.value, pageCount.value));
    })

    watch(() => props.time, function() {
        reloadTags();

        switch (numPerPage.value) {
            case "All":
                itemsPerPage.value = tableData.value.length;
                page.value = 1;
                break;
            default:
                const num = Number.parseInt(numPerPage.value);
                itemsPerPage.value = Number.isInteger(num) ? num : 10;
                page.value = Math.max(1, Math.min(page.value, pageCount.value));
                break;
        }

        let ac = app.popAction("table");
        while (ac) {
            switch(ac.action) {
                case "last-page":
                    page.value = pageCount.value;
                    break;
                default: break;
            }
            ac = app.popAction("table");
        }
    })
    watch(() => app.dataLoading.tags, function(val) {
        if (val === false) reloadTags();
    })

</script>

<style scoped>
.text-ww {
    overflow: hidden;
    white-space: wrap;
}
.shadow-hover:hover {
    filter: saturate(3)
}
.data-row:hover {
    background-color: #efefef;
    cursor: pointer;
}
.data-row.edit {
    background-color: grey;
    color: white;
}
</style>
