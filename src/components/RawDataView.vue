<template>
<div v-if="!hidden">
    <h3 style="text-align: center" class="mt-4 mb-4 text-uppercase">{{ data.length }} / {{ numItems }} {{ app.itemName }}s</h3>
    <div class="mb-2 d-flex align-center" :class="{ 'flex-column': mobile }">
        <v-checkbox-btn
            v-model="showBarCode"
            label="show tags as bar code"
            color="primary"
            class="mr-3"
            inline
            density="compact"/>
        <div>
            <b class="text-subtitle-2 mr-2">Available Headers:</b>
            <template v-for="h in allHeaders">
                <v-chip
                    density="compact"
                    :color="tableHeaders[h.key] ? 'primary' : 'default'"
                    class="mr-1 cursor-pointer text-caption"
                    @click="settings.toggleHeader(h.key)">
                    {{ h.title }}
                </v-chip>
            </template>
        </div>
    </div>
    <v-text-field v-model="search"
        label="Search"
        prepend-inner-icon="mdi-magnify"
        variant="outlined"
        density="compact"
        class="mb-1"
        clearable
        hide-details
        single-line/>

    <v-data-table
        :key="'time_'+time"
        v-model="selection"
        v-model:items-per-page="itemsPerPage"
        v-model:page="page"
        v-model:sort-by="sortBy"
        :search="search && search.length > 2 ? search : ''"
        :items="data"
        :headers="filteredHeaders"
        item-value="id"
        multi-sort
        @update:current-items="updateIndices"
        :show-select="selectable && allowEdit && !mobile"
        style="min-height: 300px; max-width: 100%;"
        density="compact">

        <template v-slot:item="{ item, index, isSelected, toggleSelect }">
            <tr :class="{ 'edit': item.edit }" class="data-row" @click="openTagDialog(item, index)">

                <td v-if="selectable && allowEdit && !mobile" style="max-width: 50px;">
                    <v-checkbox-btn
                        density="compact"
                        :model-value="isSelected({ value: item.id })"
                        @click.stop="toggleSelect({ value: item.id })"
                        :disabled="item.edit"
                        hide-details hide-spin-buttons/>
                </td>

                <td v-for="h in filteredHeaders">

                    <span v-if="allowEdit && h.key === 'actions'">
                        <v-btn class="mr-2"
                            density="compact"
                            color="error"
                            size="sm"
                            variant="plain"
                            icon="mdi-delete"
                            @click.stop="openDeleteDialog(item)">
                        </v-btn>
                        <v-btn
                            density="compact"
                            size="sm"
                            variant="plain"
                            @click.stop="toggleEdit(item)"
                            :icon="item.edit ? 'mdi-check' : 'mdi-pencil'">
                        </v-btn>
                    </span>

                    <span v-else-if="h.key === 'tags'" class="text-caption text-ww">
                        <span v-if="showBarCode">
                            <BarCode
                                :item-id="item.id"
                                :data="getItemBarCodeData(item, app.showAllUsers)"
                                @click="(t, e) => toggleItemTag(item, t, e)"
                                @right-click="(t, e) => onRightClickTag(e, item, t)"
                                selectable
                                :domain="tagDomain"
                                id-attr="id"
                                name-attr="name"
                                value-attr="value"
                                abs-value-attr="value"
                                show-absolute
                                discrete
                                categorical
                                hide-value
                                :color-domain="[1, 2]"
                                :color-scale="[
                                    settings.lightMode ? '#0ad39f' : '#078766',
                                    settings.lightMode ? '#bbb' : '#444',
                                ]"
                                selected-color="red"
                                :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                                :min-value="1"
                                :max-value="app.usersCanEdit.length"
                                :width="Math.max(3, barCodeNodeSize-2)"
                                :height="15"/>
                        </span>
                        <span v-else>
                            <template v-for="(tg, idx) in tagGroups[item.id]">
                                <TagText
                                    :id="tg.tag_id"
                                    :item-id="item.id"
                                    stop-propagation
                                    :class="{ 'tag-match': tg.match, 'tag-invalid': !tg.isLeaf }"/>
                                <span v-if="app.showAllUsers">
                                    <v-chip v-for="(u, i) in tg.users"
                                        :class="i > 0 ? 'mr-1' : 'mr-1 ml-1'"
                                        :color="app.getUserColor(u.created_by)"
                                        variant="flat"
                                        size="x-small"
                                        density="compact">
                                        {{ app.getUserShort(u.created_by) }}
                                    </v-chip>
                                </span>
                                <span v-else-if="idx < tagGroups[item.id].length-1" class="ml-1 mr-1">-</span>
                            </template>
                        </span>
                    </span>


                    <div v-else-if="h.key === 'teaser'">
                        <v-btn v-if="item.edit"
                            icon="mdi-file-upload"
                            rounded="sm"
                            density="compact"
                            variant="plain"
                            size="x-large"
                            @click.stop="openTeaserDialog(item)"/>
                        <ItemTeaser v-else
                            :item="item"
                            zoom-on-hover
                            prevent-click
                            class="ma-1"
                            :width="100"
                            :height="50"/>
                    </div>
                    <div v-else-if="h.type === 'url' && !item.edit">
                        <v-img v-if="isSteamLink(item[h.key])"
                            density="compact"
                            width="30"
                            height="30"
                            class="cursor-pointer shadow-hover"
                            src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/480px-Steam_icon_logo.svg.png"
                            @click.stop="openInNewTab(item[h.key])"
                            />
                        <v-btn v-else
                            icon="mdi-open-in-new"
                            variant="plain"
                            rounded="sm"
                            density="compact"
                            @click.stop="openInNewTab(item[h.key])"
                            />
                    </div>

                    <span v-else-if="h.key === 'expertise'" class="text-caption d-flex mt-1 mb-1">
                        <div v-if="app.showAllUsers && app.usersCanEdit.length > 3">
                            <ExpertiseRating v-if="allowEdit" :item="item" :user="app.activeUserId" :key="'rate_'+item.id"/>
                            <MiniExpertiseChart :item="item" :width="60" :height="10"/>
                        </div>
                        <div v-else-if="app.showAllUsers && app.usersCanEdit.length <= 3">
                            <div class="d-flex justify-space-between" v-for="u in app.usersCanEdit">
                                <v-chip class="mr-2"
                                    :color="app.getUserColor(u.id)"
                                    variant="flat"
                                    size="x-small"
                                    density="compact">{{ u.short }}</v-chip>
                                <ExpertiseRating :item="item" :user="u.id" :key="'rate_'+item.id+'_'+u.id"/>
                            </div>
                        </div>
                        <ExpertiseRating v-else :item="item" :user="app.activeUserId" :key="'rate_'+item.id"/>
                    </span>

                    <span v-else-if="h.key === 'numWarnings'" class="text-caption">
                        <div v-if="hasWarnings(item)">
                            <WarningIcon :severity="1" :text="getWarningText(item, 1)"/>
                            <WarningIcon :severity="2" :text="getWarningText(item, 2)"/>
                        </div>
                        <div v-else-if="couldHaveWarnings(item, null, app.showAllUsers)">
                            <v-tooltip text="finalize to see warnings" location="left" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-icon v-bind="props" size="small">mdi-help</v-icon>
                                </template>
                            </v-tooltip>
                        </div>
                    </span>

                    <span v-else-if="h.key === 'numEvidence'" class="text-caption">
                        <div>
                            <EvidenceIcon :type="EVIDENCE_TYPE.POSITIVE" location="left" prevent-click/>
                            {{ countEvidence(item, EVIDENCE_TYPE.POSITIVE) }}
                        </div>
                        <div>
                            <EvidenceIcon :type="EVIDENCE_TYPE.NEGATIVE" location="left" prevent-click/>
                            {{ countEvidence(item, EVIDENCE_TYPE.NEGATIVE) }}
                        </div>
                    </span>


                    <span v-else-if="!h.editable" class="text-caption text-ww">{{ h.value ? h.value(item) : item[h.key] }}</span>
                    <input v-else
                        v-model="item[h.key]"
                        style="width: 90%; color: inherit;"
                        @keyup="event => onKeyUp(event, item, h)"
                        @blur="parseType(item, h.key, h.type)"
                        :disabled="!item.edit"/>
                </td>
            </tr>
        </template>

        <template v-slot:bottom="{ pageCount }">
            <div class="d-flex justify-space-between align-center" :class="{ 'flex-column': smAndDown }">

                <div v-if="allowEdit" :class="{ 'mb-2': smAndDown }">
                    <v-btn v-if="allowAdd" width="100" size="small" @click="addRow">add {{ app.itemName }}</v-btn>
                    <v-btn :disabled="selection.length === 0" size="small" class="ml-1"
                        @click="editTagsSelection = true" color="default">edit tags for selection</v-btn>
                </div>
                <span v-else style="min-width: 100px"></span>


                <v-pagination v-model="page"
                    :length="pageCount"
                    :total-visible="5"
                    show-first-last-page
                    :class="{ 'mb-2': smAndDown }"
                    density="compact"/>


                <div class="d-flex">

                    <v-number-input v-model="page"
                        :min="1" :max="pageCount"
                        density="compact"
                        hide-details
                        hide-spin-buttons
                        max-width="80"
                        inset
                        class="pa-0 mr-2"
                        variant="outlined"
                        control-variant="stacked"
                        :step="1"/>

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
            </div>
        </template>

    </v-data-table>

    <ItemEditor v-model="editRowTags"
        :item="tagging.item"
        :has-prev="tagging.itemIndex > 0"
        :has-next="(tagging.itemIndex < numPerPage-1 && tagging.itemIndex < itemToIndex.size-1) || page < pageCount"
        @prev-item="goToPrev"
        @next-item="goToNext"
        @cancel="onCancel"/>

    <v-dialog v-model="editTagsSelection" width="80%" height="85%">
        <SelectionTagEditor
            :selection="selectedGames"
            :data="tagging.addTags"
            @cancel="onCancelSelection"/>
    </v-dialog>

    <v-dialog v-model="deleteItemDialog" min-width="400" width="auto">
        <v-card max-width="500" title="Delete tags">
            <v-card-text>
                Are you sure that you want to delete the item {{ dialogItem ? dialogItem.name : "ITEM" }}?
            </v-card-text>
            <v-card-actions>
                <v-btn class="ms-auto" color="warning" @click="closeDeleteItemDialog">cancel</v-btn>
                <v-btn class="ms-2" color="error" @click="deleteRow">delete</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <MiniDialog v-model="teaserDialog" @cancel="closeTeaserDialog" @submit="uploadTeaser">
        <template v-slot:text>
            Edit teaser for {{ dialogItem ? dialogItem.name : "ITEM" }}
            <v-file-input v-model="dialogItem.teaserFile"
                accept="image/*"
                class="mt-2"
                label="Upload a teaser image"
                density="compact"
                hide-details
                hide-spin-buttons
                @update:model-value="readTeaserFile"/>
            <v-img class="pa-1 mt-2"
                :src="dialogItem.teaserPreview ? dialogItem.teaserPreview : mediaPath('teaser', dialogItem.teaser)"
                cover
                :lazy-src="imgUrl"
                alt="Image Preview"
                width="500"/>
        </template>
    </MiniDialog>

    <NewItemDialog v-if="allowAdd" v-model="addNewGame"/>

</div>
</template>

<script setup>
    import * as d3 from 'd3';
    import SelectionTagEditor from '@/components/tags/SelectionTagEditor.vue';
    import MiniDialog from './dialogs/MiniDialog.vue';
    import ExpertiseRating from './ExpertiseRating.vue';
    import { computed, onMounted, reactive, ref, watch } from 'vue'
    import { EVIDENCE_TYPE, useApp } from '@/store/app'
    import { useToast } from "vue-toastification";
    import DM from '@/use/data-manager';

    import imgUrl from '@/assets/__placeholder__.png'
    import ItemEditor from './dialogs/ItemEditor.vue';
    import NewItemDialog from './dialogs/NewItemDialog.vue';
    import { addDataTags, deleteDataTags, deleteItems, updateItems, updateItemTeaser } from '@/use/data-api';
    import { useTimes } from '@/store/times';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import { sortObjByString } from '@/use/sorting';
    import Cookies from 'js-cookie';
    import BarCode from './vis/BarCode.vue';
    import ItemTeaser from './items/ItemTeaser.vue';
    import MiniExpertiseChart from './vis/MiniExpertiseChart.vue';
    import TagText from './tags/TagText.vue';
    import { mediaPath, parseType } from '@/use/utility';
    import { useDisplay } from 'vuetify';
    import WarningIcon from './warnings/WarningIcon.vue';
    import EvidenceIcon from './evidence/EvidenceIcon.vue';
    import { couldHaveWarnings, hasWarnings } from '@/use/similarities';

    const app = useApp();
    const toast = useToast();
    const times = useTimes()
    const settings = useSettings();

    const { allowEdit } = storeToRefs(app)
    const { tableHeaders, barCodeNodeSize } = storeToRefs(settings)
    const { mobile, smAndDown } = useDisplay()

    const props = defineProps({
        allowAdd: {
            type: Boolean,
            default: false
        },
        selectable: {
            type: Boolean,
            default: false
        },
        checkAssigned: {
            type: Boolean,
            default: false
        },
        hidden: {
            type: Boolean,
            default: false
        },
    });

    const time = ref(Date.now())

    const numItems = ref(0)
    const editRowTags = ref(false);
    const editTagsSelection = ref(false);
    const addNewGame = ref(false);

    const showBarCode = ref(false)

    const sortBy = ref([])
    const selection = ref([])
    const selectedGames = computed(() => selection.value.map(id => data.value.find(dd => dd.id === id)).filter(d => d))

    const tagging = reactive({
        item: null,
        itemIndex: -1,
        allTags: []
    })

    const deleteItemDialog = ref(false);
    const teaserDialog = ref(false);

    const dialogItem = reactive({
        id: "", name: "",
        teaser: "",
        teaserFile: null,
        teaserPreview: "",
    })

    const page = ref(1);
    const itemsPerPage = ref(10);
    const numPerPage = ref("10")
    const pageCount = computed(() => Math.ceil(data.value.length / itemsPerPage.value))

    const data = ref([])
    const itemToIndex = reactive(new Map())

    const search = ref("")
    const tags = ref([])
    const tagDomain = ref([])

    let loadOnShow = true;

    const headers = [
        { editable: true, title: "Name", key: "name", type: "string", minWidth: 100, width: 150 },
        { editable: true, sortable: false, title: "Teaser", key: "teaser", type: "string", minWidth: 80 },
        { editable: true, sortable: false, title: "Description", key: "description", type: "string", minWidth: 100, width: 150 },
        { editable: false, title: "Expertise", key: "expertise", value: d => getExpValue(d), type: "array", width: 80 },
        { editable: false, title: "Tags", key: "tags", value: d => getTagsValue(d), type: "array", minWidth: 400 },
        { editable: false, title: "#Coders", key: "numCoders", type: "integer", width: 130 },
        { editable: false, title: "#Tags", key: "numTags", value: d => getTagsNumber(d), type: "integer", width: 120 },
        { editable: false, title: "#Ev", key: "numEvidence", width: 100 },
        { editable: false, title: "#Objs", key: "numObjs", type: "integer", width: 100 },
        {
            editable: false,
            title: "#Warn",
            key: "numWarnings",
            value: d => app.showAllUsers ? d.numWarningsAll : d.numWarnings,
            type: "integer",
            width: 100
        },
        { editable: false, title: "#Meta", key: "numMeta", type: "integer", width: 100 },
        { editable: true, sortable: false, title: "URL", key: "url", type: "url", width: 100 },
    ];

    const allHeaders = computed(() => {
        let list = allowEdit.value ?
            [{ title: "Actions", key: "actions", sortable: false, width: "100px" }] :
            []

        // add additional item columns
        if (app.schema && app.schema.columns) {
            list = list.concat(headers.slice(0, 3))
                .concat(app.schema.columns.map(d => {
                    const obj = Object.assign({}, d)
                    const n = (d.name[0].toUpperCase() + d.name.slice(1).replaceAll("_", " "))
                    obj.editable = true;
                    obj.sortable = true;
                    obj.title = n.length > 10 ? n.slice(0, 9)+".." : n;
                    obj.key = d.name;
                    return obj
                }))
                .concat(headers.slice(3))
        } else {
            list = list.concat(headers)
        }

        // filter out warnings if they are disabled
        if (!app.warningsEnabled) {
            list = list.filter(d => d.key !== "numWarnings")
        }

        // filter out meta items if there are none
        if (!app.hasMetaItems) {
            list = list.filter(d => d.key !== "numMeta")
        }

        return list
    })

    const filteredHeaders = computed(() => allHeaders.value.filter(d => tableHeaders.value[d.key]))

    let tagGroups = {}

    function makeTagGroups() {
        const obj = {}
        data.value.forEach(item => {
            const itemTags = app.showAllUsers ?
                item.tags :
                item.tags.filter(t => t.created_by === app.activeUserId)

            const final = []
            const g = d3.group(itemTags, d => d.tag_id)
            g.forEach((array, tid) => {
                array.sort((a, b) => a.created_by - b.created_by)
                final.push({
                    tag_id: tid,
                    tag_name: array[0].name,
                    isLeaf: tags.value.find(d => d.id == tid).is_leaf === 1,
                    match: matchesTagFilter(array[0].name),
                    users: array
                })
            })
            obj[item.id] = final
        })
        tagGroups = obj
        time.value = Date.now()
    }

    function countEvidence(item, type=null) {
        if (type !== null) {
            return item.evidence.reduce((acc, d) => acc + (d.type === type ? 1 : 0), 0)
        }
        return item.evidence.length
    }

    function getWarningText(item, severity=null) {
        const all = severity ?
            item.warnings.filter(d => d.severity === severity) :
            item.warnings

        const me = !item.finalized ? [] : all.filter(d => d.users.includes(app.activeUserId))

        return app.showAllUsers ? `${all.length} (${me.length})`: me.length
    }

    function openInNewTab(url) {
        window.open(url, "_blank")
    }
    function isSteamLink(url) {
        if (!url) {
            return false;
        }
        return url.includes("store.steampowered.com")
    }
    function getExpValue(game) {
        if (app.showAllUsers) {
            return d3.sum(game.expertise.map(d => {
                switch (d.value) {
                    default: return d.value;
                    case 2: return 3;
                    case 3: return 9;
                }
            }))
        }
        const r = game.expertise.find(d => d.user_id === app.activeUserId)
        return r ? r.value : 0
    }
    function getTagsValue(game) {
        if (app.showAllUsers) {
            return game.allTags.map(d => d.name)
        }
        return game.tags
            .filter(d => !d.unsaved && d.created_by === app.activeUserId)
            .map(d => game.allTags.find(t => t.id === d.tag_id).name)
    }
    function getTagsNumber(game) {
        if (app.showAllUsers) {
            return game.allTags.length
        }
        return game.tags.filter(d => d.created_by === app.activeUserId).length
    }

    function matchesTagFilter(name) {
        return search.value ? name.includes(search.value) : false
    }

    function getItemBarCodeData(item, showAll) {
        if (showAll) {
            return item.allTags
                .map(d => ({
                    id: d.id,
                    name: d.name,
                    value: item.tags.some(dd => dd.tag_id === d.id && dd.created_by === app.activeUserId) ? 1 : 2
                }))
        }
        return item.tags
            .filter(d => d.created_by === app.activeUserId)
            .map(d => ({ id: d.tag_id, name: d.name, value: 1 }))
    }

    function reloadTags() {
        if (!props.hidden) {
            loadOnShow = false;
            if (DM.hasData("tags")) {
                tags.value = DM.getDataBy("tags", t => t.is_leaf === 1)
                tags.value.sort(sortObjByString("name"))

                const arr = tags.value.map(d => d)
                arr.sort((a, b) => {
                    const l = Math.min(a.path.length, b.path.length);
                    for (let i = 0; i < l; ++i) {
                        if (a.path[i] < b.path[i]) return -1;
                        if (a.path[i] > b.path[i]) return 1;
                    }
                    return 0
                });
                tagDomain.value = arr.map(d => d.id)
            } else {
                tags.value = [];
            }
        } else {
            loadOnShow = true;
        }
    }
    function updateIndices(currentItems) {
        itemToIndex.clear()
        currentItems.forEach((d, i) => itemToIndex.set(i, d.index))
    }
    function readData() {
        if (!props.hidden) {
            loadOnShow = false;
            numItems.value = DM.getSize("items", false)
            data.value = DM.getData("items", true).slice()
            makeTagGroups()
            time.value = Date.now()
        } else {
            loadOnShow = true;
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

    async function toggleItemTag(item, tag, event) {
        event.stopPropagation()
        if (!allowEdit.value) return;
        if (item && tag) {
            const existing = item.tags.find(d => d.tag_id === tag.id && d.created_by === app.activeUserId)
            if (existing) {
                try {
                    await deleteDataTags([existing.id])
                    toast.success("deleted user tag for " + tag.name)
                    times.needsReload("datatags")
                } catch(e) {
                    console.error(e.toString())
                    toast.error("error adding user tag " + tag.name)
                }
            } else {
                try {
                    await addDataTags([{
                        item_id: item.id,
                        code_id: app.activeCode,
                        tag_id: tag.id,
                        created: Date.now(),
                        created_by: app.activeUserId
                    }])
                    toast.success("added user tag for " + tag.name)
                    times.needsReload("datatags")
                } catch(e) {
                    console.error(e.toString())
                    toast.error("error adding user tag " + tag.name)
                }
            }
        }
    }

    function onRightClickTag(event, item, tag) {
        const [mx, my] = d3.pointer(event, document.body)
        event.preventDefault();
        settings.setRightClick(
            "tag", tag.id,
            mx, my,
            tag.name, { item: item.id },
            CTXT_OPTIONS.items_tagged
        )
    }

    async function toggleEdit(item) {
        if (!allowEdit.value) return;
        if (item.edit && item.changes) {
            allHeaders.value.forEach(h => parseType(item, h.key, h.type));
            try {
                await updateItems([item])
                toast.success("updated " + item.name)
                times.needsReload("items")
            } catch {
                toast.error("error updating " + item.name)
                times.needsReload("items")
            }
        }
        item.edit = !item.edit;
    }

    function openTagDialog(item, index) {
        if (item.edit) return;
        tagging.add = false;
        tagging.itemIndex = index;
        tagging.item = item;
        editRowTags.value = true;
    }
    function goToPrev() {
        if (tagging.item) {
            if (tagging.itemIndex > 0) {
                tagging.itemIndex--;
                tagging.item = data.value[itemToIndex.get(tagging.itemIndex)];
            } else if (page.value > 1) {
                // editRowTags.value = false;
                page.value--;
                const num = getNumPerPage()-1;
                setTimeout(() => openTagDialog(data.value[itemToIndex.get(num)], num), 250)
            } else {
                return;
            }
            tagging.item = data.value[itemToIndex.get(tagging.itemIndex)];

        }
    }
    function goToNext() {
        if (tagging.item) {
            if (tagging.itemIndex < getNumPerPage()-1 && tagging.itemIndex < itemToIndex.size-1) {
                tagging.itemIndex++;
                tagging.item = data.value[itemToIndex.get(tagging.itemIndex)];
            } else if (page.value < pageCount.value) {
                // editRowTags.value = false;
                page.value++;
                setTimeout(() => openTagDialog(data.value[itemToIndex.get(0)], 0), 250)
            } else {
                return;
            }
        }
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

    function updateItemsPerPage(value) {
        switch(value) {
            case "All":
                itemsPerPage.value = data.value.length;
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
        dialogItem.teaserFile = null;
        dialogItem.teaser = item.teaser;
        dialogItem.teaserPreview = ""
        deleteItemDialog.value = true;
    }
    function closeDeleteItemDialog() {
        deleteItemDialog.value = false;
        dialogItem.id = "";
        dialogItem.name = "";
        dialogItem.teaserFile = null;
        dialogItem.teaserPreview = "";
    }
    function openTeaserDialog(item) {
        dialogItem.id = item.id;
        dialogItem.name = item.name;
        dialogItem.teaserFile = null;
        dialogItem.teaser = item.teaser;
        dialogItem.teaserPreview = ""
        teaserDialog.value = true;
    }
    function closeTeaserDialog() {
        teaserDialog.value = false;
        dialogItem.id = "";
        dialogItem.name = "";
        dialogItem.teaserFile = null;
        dialogItem.teaserPreview = "";
    }
    function readTeaserFile() {
        if (!dialogItem.teaserFile) {
            dialogItem.teaserPreview = "";
            return;
        }

        const reader = new FileReader();
        reader.addEventListener('load', () => { dialogItem.teaserPreview = reader.result });
        reader.readAsDataURL(dialogItem.teaserFile);
    }

    function addRow() {
        if (!allowEdit.value) return;
        addNewGame.value = true;
    }

    async function uploadTeaser() {
        if (!allowEdit.value) return;
        if (dialogItem.id) {
            if (!dialogItem.teaserFile) {
                toast.error("upload a new image first")
                return;
            }

            const item = data.value.find(d => d.id === dialogItem.id);
            try {
                const idx = dialogItem.teaserFile.name.lastIndexOf(".")
                const teasername = idx >= 0 ?
                    dialogItem.teaserFile.name.slice(0, idx) :
                    dialogItem.teaserFile.name

                await updateItemTeaser(item, teasername, dialogItem.teaserFile)
                toast.success("updated teaser for " + dialogItem.name)
                times.needsReload("items")
            } catch {
                toast.error("error updating teaser for " + dialogItem.name)
                times.needsReload("items")
            }
            teaserDialog.value = false;
            item.changes = false;
            item.edit = false;
            dialogItem.teaserFile = null;
            dialogItem.teaserPreview = "";
        }
    }
    async function deleteRow() {
        if (!allowEdit.value) return;
        if (dialogItem.id) {
            try {
                await deleteItems([dialogItem.id])
                toast.success("deleted " + dialogItem.name)
                times.needsReload("items")
            } catch {
                toast.error("error deleting " + dialogItem.name)
                times.needsReload("items")
            }
        }
        closeDeleteItemDialog();
    }

    function getNumPerPage() {
        switch (numPerPage.value) {
            case "All": return data.value.length
            default: return Number.parseInt(numPerPage.value)
        }
    }

    function readHeaders() {
        const savedHeaders = Cookies.get("table-headers") ?
            JSON.parse(Cookies.get("table-headers")) :
            null

        let numSaved = 0;
        if (savedHeaders) {
            Object.keys(savedHeaders).forEach(h => {
                if (!allHeaders.value.some(d => d.key === h)) {
                    delete savedHeaders[h]
                } else {
                    numSaved++
                }
            })
        }

        if (numSaved > 0) {
            allHeaders.value.forEach(h => {
                if (savedHeaders[h] === undefined) {
                    savedHeaders[h] = true;
                }
            });
            settings.setHeaders(savedHeaders)
        } else {
            settings.setHeaders(allHeaders.value.map(d => d.key))
        }
    }

    onMounted(() => {
        selection.value = []

        readHeaders()

        window.addEventListener("keyup", function(event) {
            const at = document.activeElement ? document.activeElement.tagName.toLowerCase() : null
            // text element active
            if (at !== null && (at == "input" || at == "textarea")) return
            if (editRowTags.value && tagging.item) {
                if (event.code === "ArrowLeft") {
                    goToPrev();
                } else if (event.code === "ArrowRight") {
                    goToNext();
                }
            } else {
                if (event.code === "ArrowLeft" && page.value > 1) {
                    page.value = page.value - 1
                } else if (event.code === "ArrowRight" && page.value < pageCount.value) {
                    page.value = page.value + 1
                }
            }
        })
        reloadTags();
        readData();
        page.value = Math.max(1, Math.min(page.value, pageCount.value));
    })

    watch(() => times.items, function() {
        reloadTags();
        readData();

        switch (numPerPage.value) {
            case "All":
                itemsPerPage.value = data.value.length;
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

    watch(() => times.tags, reloadTags)
    watch(() => Math.max(
        app.userTime,
        times.all,
        times.items,
        times.f_items,
        times.tagging,
        times.datatags,
        times.evidence,
        times.meta_items,
        times.items_finalized,
        times.similarity
    ), readData)

    watch(() => times.all, readHeaders)
    watch(filteredHeaders, function() {
        sortBy.value = sortBy.value.filter(s => filteredHeaders.value.find(d => d.key === s.key))
    })

    watch(() => props.hidden, function(hidden) {
        if (!hidden && loadOnShow) {
            reloadTags()
            readData()
        }
    })

</script>

<style scoped>
.user-tag:hover { font-style: italic; }
.tag-match { text-decoration: underline }
.tag-selected { font-weight: bold; }
.tag-invalid { color: red }

.shadow-hover:hover {
    filter: saturate(3)
}

.v-theme--customDark .data-row:hover {
    background-color: #3d3d3d;
    cursor: pointer;
}
.v-theme--customDark .data-row.edit {
    background-color: #42504c;
    color: white;
}

.v-theme--customLight .data-row:hover {
    background-color: #efefef;
    cursor: pointer;
}
.v-theme--customLight .data-row.edit {
    background-color: #b8e0d6;
    color: black;
}
</style>
