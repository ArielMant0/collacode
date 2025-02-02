<template>
    <div style="width: 100%;">
        <div class="d-flex justify-center align-center flex-wrap" style="width: 100%;">
            <div class="ml-2">

                <div class="d-flex">
                    <div style="width: 40px;" class="mr-4"></div>
                    <MiniTree :node-width="6" value-attr="irr" value-agg="mean" :value-scale="colors" :value-domain="[-1, 0, 1]"/>
                </div>
                <div class="d-flex align-center">
                    <div style="width: 40px;" class="mr-4"></div>
                    <div class="d-flex align-start">
                        <BarCode v-if="tagData.length > 0"
                            :data="tagData"
                            :domain="domain"
                            @click="toggleTag"
                            @right-click="(tag, e) => openContext(e, tag.id)"
                            @hover="(tag, e) => onHoverTag(e, tag)"
                            hide-tooltip
                            selectable
                            id-attr="id"
                            name-attr="name"
                            value-attr="alpha"
                            abs-value-attr="alpha"
                            show-absolute
                            hide-highlight
                            :color-scale="colors"
                            :min-value="-1"
                            :max-value="1"
                            :width="6"
                            :height="20"/>

                        <v-tooltip v-if="percentScale" :text="avgAgreeScoreTag.toFixed(2)" location="right" open-delay="300">
                            <template v-slot:activator="{ props }">
                            <v-icon v-bind="props"
                                size="small" density="compact" :color="percentScale(avgAgreeScoreTag)">mdi-circle</v-icon>
                            </template>
                        </v-tooltip>
                    </div>
                </div>
                <div class="d-flex align-center">
                    <div style="width: 40px;" class="mr-4"></div>
                    <div class="d-flex align-start">
                        <BarCode v-if="tagData.length > 0"
                            :data="tagData"
                            :domain="domain"
                            @click="toggleTag"
                            @right-click="(tag, e) => openContext(e, tag.id)"
                            selectable
                            id-attr="id"
                            name-attr="name"
                            value-attr="count"
                            abs-value-attr="count"
                            show-absolute
                            color-scale="interpolatePlasma"
                            :min-value="0"
                            :max-value="maxCount"
                            :width="6"
                            :height="20"/>
                    </div>
                </div>

                <div class="mt-2 text-caption d-flex align-center justify-center">
                    <v-icon class="mr-1" size="large">mdi-menu-down</v-icon>
                    mean alpha per tagged {{ app.schemeItemName }} per coder
                    <v-icon class="ml-1" size="large">mdi-menu-down</v-icon>
                </div>

                <div>
                    <div v-for="([uid, data]) in tagDataPerCoder" :key="uid" class="d-flex align-center">
                        <div style="width: 40px; text-align: right;" class="mr-4">
                            <v-chip
                                class="mr-1"
                                :color="app.getUserColor(+uid)"
                                variant="flat"
                                size="small"
                                density="compact">{{ app.getUserShort(+uid) }}</v-chip>
                        </div>
                        <BarCode
                            :data="data"
                            :domain="domain"
                            @click="toggleTag"
                            @right-click="(tag, e) => openContext(e, tag.id, +uid)"
                            @hover="(tag, e) => onHoverTag(e, tag)"
                            hide-tooltip
                            selectable
                            id-attr="id"
                            name-attr="name"
                            value-attr="alpha"
                            abs-value-attr="alpha"
                            show-absolute
                            :color-scale="colors"
                            hide-highlight
                            :min-value="-1"
                            :max-value="1"
                            :width="6"
                            :height="20"/>

                        <v-tooltip v-if="percentScale" :text="avgAgreeScoreUser.get(+uid).toFixed(2)" location="right" open-delay="300">
                            <template v-slot:activator="{ props }">
                                <v-icon v-bind="props"
                                    size="small" density="compact" :color="percentScale(avgAgreeScoreUser.get(+uid))">mdi-circle</v-icon>
                            </template>
                        </v-tooltip>
                    </div>
                </div>
            </div>
            <div class="ml-2 mt-2 d-flex">
                <ColorLegend v-if="colorValues.length > 0"
                    :colors="colorValues"
                    :ticks="colorTicks"
                    :size="200"
                    :rect-size="20"
                    :everyTick="5"
                    hide-domain
                    vertical/>
                <ColorLegend v-if="tagData.length > 0"
                    scale-name="interpolatePlasma"
                    :min-value="0"
                    :max-value="maxCount"
                    discrete
                    :size="200"
                    :rect-size="20"
                    :everyTick="5"
                    hide-domain
                    vertical/>
            </div>

            <div class="d-flex align-start mt-2">
                <ScatterPlot v-if="allItems.length > 0"
                    selectable
                    :data="allItems"
                    :selected="selItemIds"
                    :time="scatterTime"
                    color-scale
                    id-attr="id"
                    x-attr="numTags"
                    y-attr="alpha"
                    glyph-attr="glyph"
                    :glyph-domain="app.users.map(d => d.short)"
                    :glyph-color-scale="app.users.map(d => d.color)"
                    @lasso="onLassoItems"
                    @click-color="onClickColor"
                    @click="onClickItem"
                    @hover="onHoverItem"
                    x-label="#tags"
                    y-label="alpha"
                    :radius="3"
                    :width="375"
                    :height="270"/>

                <TagUserMatrix v-if="allItems.length > 0" :size="150"/>
            </div>
        </div>


        <div class="mt-4">
            <b>{{ sumInconsistent }}</b> disagreements in <b>{{ selItems.length }}</b> {{ app.schemeItemName+'s' }} with an average agreement score of {{ avgAgreeScoreItem.toFixed(2) }}
            <v-icon v-if="percentScale" class="pb-1" size="x-small" density="compact" :color="percentScale(avgAgreeScoreItem)">mdi-circle</v-icon>

            <div class="mt-2">
                <div class="d-flex mb-1 align-center">

                    <v-checkbox-btn
                        v-model="showBarCode"
                        label="show tags as bar code"
                        color="primary"
                        density="compact"
                        style="max-width: 220px;"/>

                    <v-text-field v-model="search"
                        label="Search"
                        prepend-inner-icon="mdi-magnify"
                        variant="outlined"
                        density="compact"
                        clearable
                        hide-details
                        single-line/>
                    </div>

                <v-data-table
                    v-model:items-per-page="itemsPerPage"
                    v-model:page="page"
                    v-model:sort-by="sortBy"
                    :search="search"
                    :items="selItems"
                    :headers="headers"
                    item-value="id"
                    multi-sort
                    style="min-height: 200px;"
                    density="compact">

                    <template v-slot:item="{ item }">
                        <tr class="text-caption" :key="'row_'+item.id">
                            <td><span class="cursor-pointer" @click="app.setShowItem(item.id)">{{ item.name }}</span></td>
                            <td>
                                <v-img
                                    :src="'teaser/'+item.teaser"
                                    :lazy-src="imgUrlS"
                                    class="ma-1 mr-4 cursor-pointer"
                                    cover
                                    @click="app.setShowItem(item.id)"
                                    style="max-width: 80px;"
                                    width="80"
                                    height="40"/>
                            </td>
                            <td>
                                <v-btn
                                    class="text-caption mt-1 mb-1"
                                    color="primary"
                                    variant="tonal"
                                    block
                                    @click="openResolver(item)"
                                    density="compact">
                                    resolve
                                </v-btn>
                            </td>
                            <td>
                                <div v-if="showBarCode" style="width: 100%;">
                                    <BarCode
                                        :data="getItemBarCodeData(item)"
                                        @click="toggleTag"
                                        @right-click="(tag, e) => openContext(e, tag.id, null, item)"
                                        selectable
                                        :domain="domain"
                                        id-attr="id"
                                        name-attr="name"
                                        value-attr="value"
                                        abs-value-attr="value"
                                        show-absolute
                                        binary
                                        selected-color="red"
                                        :binary-color-fill="settings.lightMode ? '#000000' : '#ffffff'"
                                        :no-value-color="settings.lightMode ? rgb(242,242,242).formatHex() : rgb(33,33,33).formatHex()"
                                        :min-value="1"
                                        :width="5"
                                        :height="15"/>
                                </div>
                                <div v-else class="d-flex flex-wrap mr-4" style="width: 100%;">
                                    <div v-for="([tag_id, list]) in item.grouped" :key="tag_id">
                                        <span class="mr-2" :style="{ opacity: isSelectedTag(tag_id) || list.length !== item.numCoders ? 1 : 0.2 }">
                                            <span
                                                class="cursor-pointer"
                                                @click="toggleTag({ id: tag_id })"
                                                @contextmenu="e => {
                                                    e.preventDefault()
                                                    if (list.length !== item.numCoders) {
                                                        openContext(e, tag_id, null, item)
                                                    }
                                                }"
                                                :style="{ fontWeight: isSelectedTag(tag_id) ? 'bold' : 'normal'}">
                                                {{ list[0].name }}
                                            </span>
                                            <v-chip v-for="dts in list" :key="dts.id"
                                                class="ml-1"
                                                :color="app.getUserColor(dts.created_by)"
                                                variant="flat"
                                                size="x-small"
                                                density="compact">{{ app.getUserShort(dts.created_by) }}</v-chip>
                                        </span>
                                    </div>
                                </div>
                            </td>
                            <td>{{ item.numCoders }}</td>
                            <td>
                                {{ item.alpha !== null ? item.alpha.toFixed(2) : 'none' }}
                                <v-icon v-if="percentScale" density="compact" size="small" :color="percentScale(item.alpha)">mdi-circle</v-icon>
                            </td>
                            <td>{{ item.inconsistent.length }}</td>
                            <td>{{ item.incInSel }}</td>
                        </tr>
                    </template>

                    <template v-slot:bottom="{ pageCount }">
                        <div class="d-flex justify-space-between align-center">

                            <v-pagination v-model="page"
                                :length="pageCount"
                                :total-visible="5"
                                show-first-last-page
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
            </div>
        </div>

        <MiniDialog v-model="resolveDialog"
            no-actions
            min-width="900"
            style="max-width: 90%;"
            :title="'Resolve disagreements for '+(resolveData.item ? resolveData.item.name : '?')"
            @cancel="closeResolver"
            close-icon>
            <template v-slot:text>
                <TagDiffResolver v-if="resolveData.item" :item="resolveData.item" :time="resolveData.time" @submit="closeResolver"/>
            </template>
        </MiniDialog>

        <ContextMenu v-model="contextData.show"
            :x="contextData.x"
            :y="contextData.y"
            :options="[{ value: 'add', name: 'add missing' }, { value: 'remove', name: 'remove single(s)' }]"
            @select="resolveTag"
            @cancel="closeContext"/>

    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted, reactive, watch } from 'vue';
    import BarCode from '../vis/BarCode.vue';
    import MiniTree from '../vis/MiniTree.vue';
    import { group, pointer, range, rgb, scaleSequential } from 'd3';
    import { useSettings } from '@/store/settings';
    import { addDataTags, deleteDataTags } from '@/use/utility';
    import imgUrlS from '@/assets/__placeholder__s.png'
    import ColorLegend from '../vis/ColorLegend.vue';
    import MiniDialog from '../dialogs/MiniDialog.vue';
    import { useToast } from 'vue-toastification';
    import ContextMenu from '../dialogs/ContextMenu.vue';
    import ScatterPlot from '../vis/ScatterPlot.vue';
    import { useTooltip } from '@/store/tooltip';
    import TagDiffResolver from './TagDiffResolver.vue';
    import TagUserMatrix from './TagUserMatrix.vue';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()
    const tt = useTooltip()

    const { users, allowEdit } = storeToRefs(app)

    const allItems = ref([])
    const selItems = computed(() => {
        if (selectedTags.value.size === 0){
            return allItems.value
        }
        return allItems.value.filter(d => d.allTags.some(t => isSelectedTag(t.id)))
    })
    const selItemIds = computed(() => selItems.value.map(d => d.id))
    const sumInconsistent = computed(() => selItems.value.reduce((acc, d) => acc + d.inconsistent.length, 0))

    const scatterTime = ref(Date.now())

    const resolveDialog = ref(false)
    const resolveData = reactive({ item: null })
    const contextData = reactive({
        show: false,
        x: 10,
        y: 10,
        item: null,
        tag: null,
        user: null
    })

    const inCount = new Map();

    const userScales = {}
    const tagUsers = ref([])

    const avgAgreeScoreUser = reactive(new Map())
    const avgAgreeScoreTag = computed(() => {
        if (tagData.value.length === 0) return 0
        const f = tagData.value.filter(d => d.alpha !== undefined && d.alpha !== null && !Number.isNaN(d.alpha))
        return f.length > 0 ? f.reduce((acc, d) => acc+d.alpha, 0) / f.length : 0
    })
    const avgAgreeScoreItem = computed(() => {
        if (selItems.value.length === 0) return 0
        const f = selItems.value.filter(d => d.alpha !== undefined && d.alpha !== null && !Number.isNaN(d.alpha))
        return f.length > 0 ? f.reduce((acc, d) => acc+d.alpha, 0) / f.length : 0
    })

    const sortBy = ref([{ key: "incInSel", order: "desc" }, { key: "alpha", order: "asc" }])
    const search = ref("")
    const page = ref(1);
    const itemsPerPage = ref(10);
    const numPerPage = ref("10")
    const pageCount = computed(() => Math.ceil(selItems.value.length / itemsPerPage.value))

    const selectedTags = ref(new Set())

    const showBarCode = ref(false)
    const colors = ref("interpolateRdYlBu")
    const percentScale = ref(null)
    const colorTicks = ref([])
    const colorValues = ref([])

    const tagData = ref([])
    const tagDataPerCoder = reactive(new Map())
    const domain = ref([])

    const maxCount = ref(1)

    let tags;

    const headers = [
        { title: "Name", key: "name", type: "string", minWidth: 100, width: 150 },
        { title: "Teaser", key: "teaser", type: "string", minWidth: 80, sortable: false },
        { title: "Actions", key: "actions", value: d => d.length, type: "integer", width: 100, sortable: false },
        { title: "Tags", key: "tags", value: d => getTagsValue(d), type: "array", minWidth: 400 },
        { title: "#Coders", key: "numCoders", type: "integer", width: 130 },
        { title: "Alpha", key: "alpha", width: 140 },
        { title: "#Contested", key: "incTotal" },
        { title: "#Cont. (active)", key: "incInSel" },
    ];

    function updateItemsPerPage(value) {
        switch(value) {
            case "All":
                itemsPerPage.value = selItems.value.length;
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
    function getTagsValue(item) {
        return item.allTags.map(d => d.name)
    }
    function isSelectedTag(id) {
        if (selectedTags.value.has(id)) return true
        const p = DM.getDerivedItem("tags_path", id)
        return p && p.path.some(d => selectedTags.value.has(d))
    }

    function openResolver(item) {
        resolveData.item = DM.getDataItem("items", item.id);
        resolveDialog.value = true;
    }
    function closeResolver() {
        resolveDialog.value = false;
        resolveData.item = null;
    }

    function openContext(event, tag, user=null, item=null) {
        event.preventDefault()
        if (!allowEdit.value) return
        contextData.tag = tag;
        contextData.user = user;
        contextData.item = item;
        const [x, y] = pointer(event, document.body)
        contextData.x = x + 15
        contextData.y = y
        contextData.show = true;
    }
    function closeContext() {
        contextData.show = false;
        contextData.item = null;
        contextData.tag = null;
    }

    async function resolveTag(option) {
        if (!allowEdit.value) return
        if (option === "add") {
            resolveTagAdd();
        } else {
            resolveTagRemove();
        }
    }

    async function resolveTagAdd() {
        if (!allowEdit.value) return
        if (contextData.tag) {
            const now = Date.now()
            const list = []
            try {
                let ex = []
                // filter data by tag, item and user
                if (contextData.item) {
                    ex = [{
                        id: contextData.item.id,
                        coders: contextData.item.coders,
                        list: contextData.item.inconsistent.filter(d => d.tag_id === contextData.tag)
                    }]
                } else {
                    ex = selItems.value
                        .map(d => ({
                            id: d.id,
                            coders: d.coders,
                            list: d.inconsistent.filter(i => i.tag_id === contextData.tag)
                        }))
                        .filter(d => d.list.length > 0)
                }

                if (contextData.user) {
                    ex = ex.filter(d => d.coders.includes(contextData.user))
                }

                ex.forEach(item => {
                    item.coders.forEach(uid => {
                        if (contextData.user !== null && uid !== contextData.user) return;
                        if (!item.list.some(d => d.created_by === uid)) {
                            list.push({
                                item_id: item.id,
                                tag_id: contextData.tag,
                                code_id: app.activeCode,
                                created_by: uid,
                                created: now
                            })
                        }
                    })
                })

                // just in case
                if (list.length === 0) {
                    return toast.warning("no user tags to add..")
                }

                await addDataTags(list)
                toast.success(`added ${list.length} user tags`)
                closeContext()
                times.needsReload("datatags")
            } catch (e) {
                console.error(e.toString())
                toast.error(`error adding ${list.length} user tags`)
            }
        }
    }

    async function resolveTagRemove() {
        if (!allowEdit.value) return
        if (contextData.tag) {
            let list = []
            try {
                // filter data by tag, item and user
                if (contextData.item) {
                    list = [{
                        id: contextData.item.id,
                        list: contextData.item.inconsistent.filter(d => d.tag_id === contextData.tag && (!contextData.user || contextData.user === d.created_by))
                    }]
                } else {
                    list = selItems.value
                        .map(d => ({
                            id: d.id,
                            list: d.inconsistent.filter(i => i.tag_id === contextData.tag && (!contextData.user || contextData.user === i.created_by))
                        }))
                        .filter(d => d.list.length > 0)
                }

                list = list.map(d => d.list.map(dt => dt.id)).flat()
                // just in case
                if (list.length === 0) {
                    return toast.warning("no user tags to remove..")
                }

                await deleteDataTags(list)
                toast.success(`removed ${list.length} user tags`)
                closeContext()
                times.needsReload("datatags")
            } catch (e) {
                console.error(e.toString())
                toast.error(`error removing ${list.length} user tags`)
            }
        }
    }


    function toggleTag(tag) {
        app.toggleSelectByTag([tag.id])
    }

    function recalculate() {
        if (!tags) return readTags()

        readSelectedItems()

        inCount.clear()
        selItems.value.forEach(item => calcAgreeScoreForItem(item))

        const perCoder = {}
        const array = [], domainArray = []

        tagUsers.value.forEach(u => perCoder[u.id] = {})

        maxCount.value = 0

        tags.forEach(t => {

            domainArray.push(t.id)

            if (inCount.has(t.id)) {
                const obj = {
                    id: t.id,
                    name: t.name,
                    inconsistent: [],
                    count: 0,
                    alpha: DM.getDataItem("tags_irr", t.id)
                }

                const other = inCount.get(t.id)
                maxCount.value = Math.max(maxCount.value, other.count)
                obj.count = other.count
                obj.inconsistent = Array.from(new Set(other.found.map(d => d.item_id)).values());

                other.users.forEach(u => {
                    const inc = other.found.filter(f => f.created_by === u && f.tag_id === t.id)
                    if (inc.length === 0) return;
                    perCoder[u][t.id] = {
                        id: t.id,
                        name: t.name,
                        inconsistent: inc.map(d => d.item_id),
                        alpha: inc.reduce((acc, d) => acc + DM.getDataItem("items_irr", d.item_id), 0) / inc.length
                    }
                })

                array.push(obj)
            }
        })

        for (const id in perCoder) {
            const list = Array.from(Object.values(perCoder[id]))
            avgAgreeScoreUser.set(+id, list.length > 0 ? d3.mean(list, d => d.alpha) : 0)
            tagDataPerCoder.set(+id, list)
        }

        domain.value = domainArray
        tagData.value = array;

        if (resolveData.item) {
            resolveData.item = DM.getDataItem("items", resolveData.item.id)
            resolveData.time = Date.now()
            if (!resolveData.item) {
                closeResolver()
            }
        }

        scatterTime.value = Date.now()
    }

    function calcAgreeScoreForItem(item) {
        const grouped = item.grouped ? item.grouped : d3.group(item.tags, d => d.tag_id)
        grouped.forEach((dts, tagId) => {
            if (inCount.has(tagId)) {
                const obj = inCount.get(tagId)
                obj.count++
                item.coders.forEach(u => obj.users.add(u))
                obj.found = obj.found.concat(dts)
            } else {
                inCount.set(tagId, {
                    users: new Set(item.coders),
                    found: dts,
                    count: 1
                })
            }
        })
    }

    function getItemBarCodeData(item) {
        const list = []
        item.grouped.forEach((dts, tagId) => {
            list.push({
                id: tagId,
                name: DM.getDataItem("tags_name", tagId),
                value: dts.length,
            })
        })
        return list
    }

    function makeColorScales() {
        colors.value = "interpolateRdYlBu"
        //  "interpolateRdBu";

        const value = 1;
        const scale = d3.scaleDiverging(d3[colors.value]).domain([-1, 0, value])
        const step = 1 / 10

        colorTicks.value = range(-1, 1+step, step).map(d => +d.toFixed(2))
        colorValues.value = colorTicks.value.map(scale)
        percentScale.value = scale
    }

    function readTags() {
        // get tags and sort by hierarchy
        tags = DM.getDataBy("tags", t => t.is_leaf === 1)
        tags.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return 0
        });

        readUsers()
        recalculate()
    }
    function readUsers() {
        const utc = DM.getData("tags_user_counts", false)
        tagUsers.value = users.value.filter(u => tags.some(t => utc.get(t.id).has(u.id)))
        d3.range(2, tagUsers.value.length+1).forEach(d => {
            userScales[d] = d3.scaleLinear().domain([1 / d, 1]).range([0, 1])
        })
    }
    function readSelectedTags() {
        selectedTags.value = DM.getSelectedIds("tags")
    }
    function readSelectedItems() {
        let array = DM.getData("items", true)
            .map(d => {
                const obj = Object.assign({}, d)
                const g = group(d.tags, t => t.tag_id)
                obj.inconsistent = []
                obj.incInSel = 0
                obj.incTotal = 0
                obj.coders = d.coders
                g.forEach((list, tagId) => {
                    if (list.length < d.numCoders) {
                        obj.incTotal++
                        list.forEach(l => obj.inconsistent.push(l))
                        if (isSelectedTag(tagId)) {
                            obj.incInSel++
                        }
                    }
                })
                obj.glyph = d.coders.map(dd => ({ name: app.getUserShort(dd), value: 1 }))
                obj.grouped = g;
                obj.alpha = DM.getDataItem("items_irr", d.id)
                if (obj.alpha === null || obj.alpha === undefined) {
                    obj.alpha = 0
                }
                return obj
            })
            .filter(d => d.numCoders > 1)

        allItems.value = array
        page.value = page.value > pageCount.value ? 1 : page.value
    }

    function onLassoItems(items) {
        app.selectById(items.map(d => d.id))
    }
    function onClickColor(value) {
        const u = app.users.find(d => d.short === value)
        if (u) {
            app.toggleSelectByItemValue("coders", "coders", u.id)
        }
    }
    function onClickItem(items) {
        app.selectById(items.map(d => d.id))
    }
    function onHoverItem(items, event) {
        if (items.length > 0) {
            let str = ""
            items.forEach(d => {
                str += `<div class="mb-1 mr-1">`
                str += `<div class="text-dots" style="max-width: 160px;"><b>${d.name}</b></div>`
                if (d.teaser) {
                    str += `<image src="teaser/${d.teaser}" width="160" height="80" style="object-fit: cover;"/>`
                }
                str += "</div>"
            })
            const all = `<div class="text-caption"><div class="d-flex flex-wrap justify-start">${str}</div></div>`

            const [x, y] = pointer(event, document.body)
            tt.show(all, x + 15, y)
        } else {
            tt.hide()
        }
    }

    function onHoverTag(event=null, tag=null) {
        if (event !== null && tag !== null) {
            let str = ""
            for (let i = 0; i < tag.inconsistent.length && i < 12; ++i) {
                const id = tag.inconsistent[i]
                const item = selItems.value.find(d => d.id === id)
                if (!item) continue
                str += `<div class="mb-1 mr-1">`
                str += `<div class="text-dots" style="max-width: 80px;">${item.name}</div>`
                if (item.teaser) {
                    str += `<image src="teaser/${item.teaser}" width="80" height="40" style="object-fit: cover;"/>`
                }
                str += "</div>"
            }
            const diff = tag.inconsistent.length - 12
            const all = `<div class="text-caption">
                <div><b>${tag.name}</b> - ${tag.alpha ? tag.alpha.toFixed(2) : "<none>"}</div>
                <div class="d-flex flex-wrap justify-start">
                    ${str}
                </div>
                <div>${diff > 0 ? "and "+diff+" more.." : ""}</div>
            </div>`

            const [x, y] = pointer(event, document.body)
            tt.show(all, x + 15, y)
        } else {
            tt.hide()
        }
    }

    function init() {
        tags = null;
        tagData.value = []
        tagDataPerCoder.clear()

        readTags()
        readSelectedTags()

        recalculate()
        makeColorScales()
    }

    onMounted(init)

    watch(() => times.all, init)
    watch(() => Math.max(times.items, times.tagging, times.tags, times.datatags), readTags)
    watch(() => times.evidence, function() {
        if (resolveData.item) {
            resolveData.item = DM.getDataItem("items", resolveData.item.id)
            resolveData.time = Date.now()
            if (!resolveData.item) {
                closeResolver()
            }
        }
    })
    watch(() => settings.lightMode, makeColorScales)

    watch(() => times.f_tags, readSelectedTags)
    watch(() => times.f_items, recalculate)

</script>
