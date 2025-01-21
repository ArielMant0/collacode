<template>
    <div style="width: 100%;">
        <div class="d-flex justify-center align-center" style="width: 100%;">
            <div class="mr-8">
                <div v-for="u in users" :key="u.id" class="d-flex mb-1 align-center">
                    <v-chip
                        class="mr-1"
                        :color="u.color"
                        variant="flat"
                        size="small"
                        density="compact">{{ u.id }}</v-chip>
                    <v-tooltip text="in- or exclude this coder" location="top" open-delay="300">
                        <template v-slot:activator="{ props }">
                            <v-checkbox-btn v-bind="props"
                                :model-value="selected.has(u.id)"
                                :label="u.name"
                                :color="u.color"
                                density="compact"
                                @click="toggleUser(u.id)"
                                class="ml-1"/>
                        </template>
                    </v-tooltip>
                </div>
            </div>
            <div class="ml-2">
                <div class="d-flex">
                    <div style="width: 120px;" class="mr-4"></div>
                    <MiniTree :node-width="6"/>
                </div>
                <div class="d-flex align-center">
                    <div style="width: 120px; text-align: right;" class="mr-4">
                        <v-btn-toggle v-model="mode" density="compact" mandatory @update:model-value="checkMode" border color="primary">
                            <v-tooltip text="color relative to #tags" location="top" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-btn v-bind="props"
                                        rounded="sm" size="small" value="absolute" density="comfortable" variant="plain" icon="mdi-weight"/>
                                </template>
                            </v-tooltip>
                            <v-tooltip text="color relative to maximum #inconsistencies" location="top" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-btn v-bind="props"
                                        rounded="sm" size="small" value="absolute_range" density="comfortable" variant="plain" icon="mdi-relative-scale"/>
                                </template>
                            </v-tooltip>
                            <v-tooltip text="color relative tag occurences" location="top" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-btn v-bind="props"
                                        rounded="sm" size="small" value="relative" density="comfortable" variant="plain" icon="mdi-percent-circle"/>
                                </template>
                            </v-tooltip>
                        </v-btn-toggle>
                    </div>
                    <BarCode v-if="tagData.length > 0"
                        :data="tagData"
                        :domain="domain"
                        @click="toggleTag"
                        selectable
                        id-attr="id"
                        name-attr="name"
                        value-attr="count_inconsistent_rel"
                        abs-value-attr="count_inconsistent"
                        selected-color="#0ad39f"
                        :color-scale="colors"
                        :show-absolute="absolute"
                        :max-value="mode === 'absolute' ? globalMaxValue : (mode === 'relative' ? 1 : maxValue)"
                        :min-value="0"
                        :width="6"
                        :height="20"/>
                </div>
                <div class="mt-2">
                    <div v-for="([uid, data]) in tagDataPerCoder" :key="uid" class="d-flex align-center">
                        <div v-if="selected.has(+uid)" style="width: 120px; text-align: right;" class="mr-4">
                            <v-chip
                                class="mr-1"
                                :color="app.getUserColor(+uid)"
                                variant="flat"
                                size="small"
                                density="compact">{{ uid }}</v-chip>
                        </div>
                        <BarCode v-if="selected.has(+uid)"
                            :data="data"
                            :domain="domain"
                            @click="toggleTag"
                            selectable
                            id-attr="id"
                            name-attr="name"
                            value-attr="count_inconsistent_rel"
                            abs-value-attr="count_inconsistent"
                            :color-scale="colors"
                            hide-highlight
                            :show-absolute="absolute"
                            :max-value="mode === 'absolute' ? globalMaxValue : (mode === 'relative' ? 1 : maxValue)"
                            :min-value="0"
                            :width="6"
                            :height="20"/>
                    </div>
                </div>
            </div>
            <div class="ml-4 mt-2">
                <ColorLegend v-if="colorValues.length > 0"
                    :colors="colorValues"
                    :ticks="colorTicks"
                    :size="200"
                    :rect-size="20"
                    :everyTick="5"
                    hide-domain
                    vertical/>
            </div>
        </div>

        <div class="mt-4">
            <b>{{ sumInconsistent }}</b> Inconsistencies in <b>{{ selItems.length }}</b> {{ capitalize(app.schemeItemName+'s') }}
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
                            <td><span>{{ item.name }}</span></td>
                            <td>
                                <v-img
                                    :src="'teaser/'+item.teaser"
                                    :lazy-src="imgUrlS"
                                    class="ma-1 mr-4"
                                    cover
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
                                        @right-click="(tag, e) => openContext(e, item, tag.id)"
                                        selectable
                                        :domain="domain"
                                        id-attr="id"
                                        name-attr="name"
                                        value-attr="value"
                                        selected-color="#0ad39f"
                                        :color-scale="[settings.lightMode ? 'black' : 'white', 'red']"
                                        :no-value-color="settings.lightMode ? rgb(238,238,238) : rgb(33,33,33)"
                                        :max-value="2"
                                        :min-value="1"
                                        :width="6"
                                        :height="15"/>
                                </div>
                                <div v-else class="d-flex flex-wrap mr-4" style="width: 100%;">
                                    <div v-for="([tag_id, list]) in item.grouped" :key="tag_id">
                                        <span class="mr-2" :style="{ opacity: isSelectedTag(tag_id) || list.length !== item.numCoders ? 1 : 0.2 }">
                                            <span
                                                class="cursor-pointer"
                                                @click="toggleTag({ id: tag_id })"
                                                @contextmenu="e => openContext(e, item, tag_id)"
                                                :style="{ fontWeight: isSelectedTag(tag_id) ? 'bold' : 'normal'}">
                                                {{ list[0].name }}
                                            </span>
                                            <v-chip v-for="dts in list" :key="dts.id"
                                                class="ml-1"
                                                :color="app.getUserColor(dts.created_by)"
                                                variant="flat"
                                                size="x-small"
                                                density="compact">{{ dts.created_by }}</v-chip>
                                        </span>
                                    </div>
                                </div>
                            </td>
                            <td>{{ item.numCoders }}</td>
                            <td>{{ item.inconsistent.length }}</td>
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
            style="max-width: 80%;"
            :title="'Resolve inconsistencies for '+(resolveData.item ? resolveData.item.name : '?')"
            close-icon>
            <template v-slot:text>
                <div>
                    <div class="d-flex">
                    <v-sheet class="mr-1">
                        <div class="mb-2">
                            <v-icon color="primary">mdi-plus</v-icon>
                            add missing tags
                        </div>
                        <div class="mb-2" style="text-align: center;">
                            <v-chip v-for="u in resolveUsers" :key="'toggle_add_'+u.id"
                                class="mr-1"
                                :color="resolveData.addCount.get(u.id) > 0 ? u.color : 'default'"
                                variant="flat"
                                size="small"
                                @click="toggleResolveAddUser(u.id)"
                                density="compact">{{ u.name }}</v-chip>
                        </div>
                        <div class="d-flex flex-wrap text-caption" style="width: 100%;">
                            <div v-for="([tagId, list]) in resolveData.add" :key="'add_'+tagId">
                                <span class="mr-2">
                                    <span
                                        class="cursor-pointer"
                                        @click="toggleResolveAddTag(tagId)"
                                        :style="{ opacity: list.some(d => d.selected) ? 1 : 0.5, fontWeight: isSelectedTag(tagId) ? 'bold' : 'normal' }">
                                        {{ list[0].name }}
                                    </span>
                                    <v-chip v-for="dts in list" :key="'add_'+tagId+'_'+dts.created_by"
                                        class="ml-1"
                                        :color="dts.selected ? app.getUserColor(dts.created_by) : 'default'"
                                        :style="{ opacity: dts.selected ? 1 : 0.5 }"
                                        @click="toggleResolveAddSingle(dts)"
                                        variant="flat"
                                        size="x-small"
                                        density="compact">{{ dts.created_by }}</v-chip>
                                </span>
                            </div>
                        </div>
                    </v-sheet>

                    <v-sheet class="ml-1">
                        <div class="mb-2">
                            <v-icon color="error">mdi-delete</v-icon>
                            remove single tags
                        </div>
                        <div class="mb-2" style="text-align: center;">
                            <v-chip v-for="u in resolveUsers" :key="'toggle_remove_'+u.id"
                                class="mr-1"
                                :color="resolveData.removeCount.get(u.id) > 0 ? u.color : 'default'"
                                variant="flat"
                                size="small"
                                @click="toggleResolveRemoveUser(u.id)"
                                density="compact">{{ u.name }}</v-chip>
                        </div>
                        <div class="d-flex flex-wrap text-caption" style="width: 100%;">
                            <div v-for="([tagId, list]) in resolveData.remove" :key="'remove_'+tagId">
                                <span class="mr-2">
                                    <span
                                        class="cursor-pointer"
                                        @click="toggleResolveRemoveTag(tagId)"
                                        :style="{ opacity: list.some(d => d.selected) ? 1 : 0.5, fontWeight: isSelectedTag(tagId) ? 'bold' : 'normal' }">
                                        {{ list[0].name }}
                                    </span>
                                    <v-chip v-for="dts in list" :key="'add_'+tagId+'_'+dts.created_by"
                                        class="ml-1"
                                        :color="dts.selected ? app.getUserColor(dts.created_by) : 'default'"
                                        @click="toggleResolveRemoveSingle"
                                        :style="{ opacity: dts.selected ? 1 : 0.5 }"
                                        variant="flat"
                                        size="x-small"
                                        density="compact">{{ dts.created_by }}</v-chip>
                                </span>
                            </div>
                        </div>

                    </v-sheet>
                    </div>

                    <div class="d-flex justify-space-between mt-4">
                        <v-btn
                            class="text-caption mb-1"
                            color="primary"
                            variant="tonal"
                            style="width: 49%;"
                            :disabled="sumAdd === 0"
                            @click="submitResolveAdd"
                            density="compact">
                            add {{ sumAdd }} user tags
                        </v-btn>
                        <v-btn
                            class="text-caption mb-1"
                            color="error"
                            variant="tonal"
                            style="width: 49%;"
                            :disabled="sumRemove === 0"
                            @click="submitResolveRemove"
                            density="compact">
                            remove {{ sumRemove }} user tags
                        </v-btn>
                    </div>
                </div>
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
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted, reactive, watch } from 'vue';
    import BarCode from '../vis/BarCode.vue';
    import MiniTree from '../vis/MiniTree.vue';
    import { group, pointer, range, rgb, scaleSequential } from 'd3';
    import { useSettings } from '@/store/settings';
    import { addDataTags, capitalize, deleteDataTags } from '@/use/utility';
    import imgUrlS from '@/assets/__placeholder__s.png'
    import ColorLegend from '../vis/ColorLegend.vue';
    import MiniDialog from '../dialogs/MiniDialog.vue';
    import { useToast } from 'vue-toastification';
import ContextMenu from '../dialogs/ContextMenu.vue';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { users } = storeToRefs(app)

    const selected = reactive(new Set())

    const selItems = ref([])
    const sumInconsistent = computed(() => selItems.value.reduce((acc, d) => acc + d.inconsistent.length, 0))

    const resolveDialog = ref(false)
    const resolveData = reactive({
        item: null,
        add: new Map(),
        remove: new Map(),
        addCount: new Map(),
        removeCount: new Map()
    })
    const contextData = reactive({
        show: false,
        x: 10,
        y: 10,
        item: null,
        tag: null
    })
    const resolveUsers = computed(() => resolveData.item ?
        users.value.filter(u => resolveData.item.coders.some(d => d === u.id)) :
        users.value)

    const sumAdd = computed(() => {
        let sum = 0;
        resolveData.addCount.forEach(count => sum += count)
        return sum
    })
    const sumRemove = computed(() => {
        let sum = 0;
        resolveData.removeCount.forEach(count => sum += count)
        return sum
    })

    const sortBy = ref([{ key: "inconsistent", order: "desc" }])
    const search = ref("")
    const page = ref(1);
    const itemsPerPage = ref(10);
    const numPerPage = ref("10")
    const pageCount = computed(() => Math.ceil(selItems.value.length / itemsPerPage.value))

    const selectedTags = ref(new Set())

    const showBarCode = ref(false)
    const colors = ref([])
    const colorTicks = ref([])
    const colorValues = ref([])

    const tagData = ref([])
    const tagDataPerCoder = reactive(new Map())
    const domain = ref([])

    const globalMaxValue = ref(1)
    const maxValue = ref(1)

    const absolute = ref(true)
    const mode = ref("absolute_range")
    checkMode()

    let tags;

    const headers = [
        { title: "Name", key: "name", type: "string", minWidth: 100, width: 150 },
        { title: "Teaser", key: "teaser", type: "string", minWidth: 80, sortable: false },
        { title: "Actions", key: "actions", value: d => d.length, type: "integer", width: 100, sortable: false },
        { title: "Tags", key: "tags", value: d => getTagsValue(d), type: "array", minWidth: 400 },
        { title: "# Coders", key: "numCoders", type: "integer", width: 130 },
        { title: "# Incons.", key: "inconsistent", value: d => d.inconsistent.length, type: "integer", width: 140 },
    ];

    function checkMode() {
        switch(mode.value) {
            case "relative":
                absolute.value = false
                break;
            default:
                absolute.value = true;
                break;
        }
        makeColorScales()
    }
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
        resolveData.item = item;
        resolveData.add.clear()
        resolveData.remove.clear()

        resolveData.addCount.clear()
        resolveData.removeCount.clear()
        resolveUsers.value.forEach(u => {
            resolveData.addCount.set(u.id, 0)
            resolveData.removeCount.set(u.id, 0)
        });

        item.grouped.forEach((list, tagId) => {
            const arrayAdd = []
            const arrayRemove = []
            if (list.length !== item.numCoders) {
                resolveUsers.value.forEach(u => {
                    const ex = list.find(d => d.created_by === u.id)
                    // tag for this user already exists
                    if (ex) {
                        const obj = Object.assign({}, ex)
                        obj.selected = true
                        resolveData.removeCount.set(u.id, resolveData.removeCount.get(u.id)+1)
                        arrayRemove.push(obj)
                    } else {
                        const obj = Object.assign({}, list[0])
                        obj.created_by = u.id
                        resolveData.addCount.set(u.id, resolveData.addCount.get(u.id)+1)
                        obj.selected = true
                        arrayAdd.push(obj)
                    }
                })
            }
            if (arrayAdd.length > 0) {
                resolveData.add.set(tagId, arrayAdd)
            }
            if (arrayRemove.length > 0) {
                resolveData.remove.set(tagId, arrayRemove)
            }
        })
        resolveDialog.value = true;
    }
    function closeResolver() {
        resolveDialog.value = false;
        resolveData.item = null;
        resolveData.add.clear()
        resolveData.remove.clear()
        resolveData.addCount.clear()
        resolveData.removeCount.clear()
    }

    function toggleResolveAddSingle(dts) {
        dts.selected = !dts.selected;
        resolveData.addCount.set(
            dts.created_by,
            resolveData.addCount.get(dts.created_by) + (dts.selected ? 1 : -1)
        );
    }
    function toggleResolveRemoveSingle(dts) {
        dts.selected = !dts.selected;
        resolveData.removeCount.set(
            dts.created_by,
            resolveData.removeCount.get(dts.created_by) + (dts.selected ? 1 : -1)
        );
    }

    function toggleResolveAddUser(user) {
        let count = 0;
        const sel = resolveData.addCount.get(user) > 0
        resolveData.add.forEach(list => {
            list.forEach(d => {
                if (d.created_by === user) {
                    d.selected = !sel
                    count += d.selected ? 1 : 0;
                }
            })
        })
        resolveData.addCount.set(user, count);
    }
    function toggleResolveRemoveUser(user) {
        let count = 0;
        const sel = resolveData.removeCount.get(user) > 0
        resolveData.remove.forEach(list => {
            list.forEach(d => {
                if (d.created_by === user) {
                    d.selected = !sel
                    count += d.selected ? 1 : 0;
                }
            })
        })
        resolveData.removeCount.set(user, count);
    }
    function toggleResolveAddTag(tag) {
        const list = resolveData.add.get(tag)
        const sel = list.some(d => d.selected)
        list.forEach(d => {
            d.selected = !sel
            const diff = d.selected ? 1 : -1
            resolveData.addCount.set(
                d.created_by,
                resolveData.addCount.get(d.created_by) + diff
            )
        })
    }
    function toggleResolveRemoveTag(tag) {
        const list = resolveData.remove.get(tag)
        const sel = list.some(d => d.selected)
        list.forEach(d => {
            d.selected = !sel
            const diff = d.selected ? 1 : -1
            resolveData.removeCount.set(
                d.created_by,
                resolveData.removeCount.get(d.created_by) + diff
            )
        })
    }

    function openContext(event, item, tag) {
        event.preventDefault()
        contextData.item = item;
        contextData.tag = tag;
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
        if (option === "add") {
            resolveTagAdd();
        } else {
            resolveTagRemove();
        }
    }

    async function resolveTagAdd() {
        if (contextData.item && contextData.tag) {
            const now = Date.now()
            const list = []
            try {
                const ex = contextData.item.inconsistent.filter(d => d.tag_id === contextData.tag)
                contextData.item.coders.forEach(uid =>  {
                    if (!ex.some(d => d.created_by === uid)) {
                        list.push({
                            item_id: contextData.item.id,
                            tag_id: contextData.tag,
                            code_id: app.activeCode,
                            created_by: uid,
                            created: now
                        })
                    }
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
        if (contextData.item && contextData.tag) {
            const list = contextData.item.inconsistent.filter(d => d.tag_id === contextData.tag)
            try {
                // just in case
                if (list.length === 0) {
                    return toast.warning("no user tags to remove..")
                }

                await deleteDataTags(list.map(d => d.id))
                toast.success(`removed ${list.length} user tags`)
                closeContext()
                times.needsReload("datatags")
            } catch (e) {
                console.error(e.toString())
                toast.error(`error removing ${list.length} user tags`)
            }
        }
    }

    async function submitResolveAdd() {
        if (resolveData.item) {
            const now = Date.now()
            const list = Array.from(resolveData.add.values())
                .flat()
                .filter(d => d.selected)

            try {
                await addDataTags(list.map(d => ({
                    item_id: d.item_id,
                    tag_id: d.tag_id,
                    code_id: d.code_id,
                    created_by: d.created_by,
                    created: now
                })))
                toast.success(`added ${list.length} user tags`)
                closeResolver()
                times.needsReload("datatags")
            } catch (e) {
                console.error(e.toString())
                toast.error(`error adding ${list.length} user tags`)
            }
        }
    }
    async function submitResolveRemove() {
        if (resolveData.item) {
            const list = Array.from(resolveData.remove.values())
                .flat()
                .filter(d => d.selected)
            try {
                await deleteDataTags(list.map(d => d.id))
                toast.success(`removed ${list.length} user tags`)
                closeResolver()
                times.needsReload("datatags")
            } catch (e) {
                console.error(e.toString())
                toast.error(`error removing ${list.length} user tags`)
            }
        }
    }

    function toggleUser(id) {
        if (selected.has(id)) {
            selected.delete(id)
        } else {
            selected.add(id)
        }
        recalculate()
    }
    function toggleTag(tag) {
        app.toggleSelectByTag([tag.id])
    }

    function recalculate() {
        if (!tags) readTags()

        const inCount = new Map()
        const items = DM.getDataBy("items", d => d.numCoders > 1)

        items.forEach(item => {
            const grouped = group(item.tags, d => d["tag_id"])
            grouped.forEach((dts, tagId) => {
                if (dts.length < item.numCoders && dts.some(d => selected.has(d.created_by))) {
                    if (inCount.has(tagId)) {
                        const obj = inCount.get(tagId)
                        obj.found.push({ item: item.id, users: dts.map(d => d.created_by) })
                        obj.value++
                    } else {
                        inCount.set(tagId, {
                            found: [{ item: item.id, users: dts.map(d => d.created_by) }],
                            value: 1
                        })
                    }
                }
            });
        })

        maxValue.value = 1
        globalMaxValue.value = tags.length
        const array = [], domainArray = []

        const perCoder = {}
        users.value.forEach(u => perCoder[u.id] = {})

        const utc = DM.getData("tags_user_counts", false)

        tags.forEach(t => {
            const obj = {
                id: t.id,
                name: t.name,
                count: DM.getDataItem("tags_counts", t.id),
                count_inconsistent: 0,
                count_inconsistent_rel: 0,
                inconsistent: [],
            }
            domainArray.push(t.id)

            if (inCount.has(t.id)) {
                const other = inCount.get(t.id)
                obj.inconsistent = other.found
                obj.count_inconsistent = other.value
                obj.count_inconsistent_rel = other.value / obj.count

                other.found.forEach(item => item.users.forEach(u => {
                    if (!perCoder[u][t.id]) {
                        perCoder[u][t.id] = {
                            id: t.id,
                            name: t.name,
                            inconsistent: [{ item: item.item }],
                            count: utc.get(t.id).get(u) || 0,
                            count_inconsistent: 1,
                            count_inconsistent_rel: 1,
                        }
                    } else {
                        perCoder[u][t.id].count_inconsistent++
                        perCoder[u][t.id].inconsistent.push({ item: item.item })
                    }
                }))
            }

            maxValue.value = Math.max(maxValue.value, obj.count_inconsistent)
            array.push(obj)
        })

        for (const id in perCoder) {
            const list = []
            tags.forEach(t => {
                const obj = perCoder[id][t.id]
                if (obj) {
                    obj.count_inconsistent_rel = obj.count_inconsistent / obj.count
                    maxValue.value = Math.max(maxValue.value, obj.count_inconsistent)
                    list.push(obj)
                }
            })
            tagDataPerCoder.set(id, list)
        }

        domain.value = domainArray
        tagData.value = array;

        readSelectedItems()
    }
    function getItemBarCodeData(item) {
        const list = []
        item.allTags.forEach(t => {
            const obj = {
                id: t.id,
                name: t.name,
                count: item.numCoders,
                value: 1
            }
            if (item.inconsistent.some(d => d.tag_id === t.id)) {
                obj.value = 2;
            }
            list.push(obj)
        })
        return list
    }

    function makeColorScales() {
        colors.value = [settings.lightMode ? rgb(238,238,238) : rgb(33,33,33), "red"]

        let value = 100;
        if (mode.value === "absolute") {
            value = globalMaxValue.value
        } else if (mode.value === "absolute_range") {
            value = maxValue.value
        }

        const scale = scaleSequential(colors.value).domain([0, value])

        colorTicks.value = range(0, value+1, value / 15).map(d => Math.round(d))
        colorValues.value = colorTicks.value.map(scale)
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

        recalculate()
    }
    function readUsers() {
        selected.clear()
        users.value.forEach(d => selected.add(d.id))
    }
    function readSelectedTags() {
        selectedTags.value = DM.getSelectedIds("tags")
    }
    function readSelectedItems() {
        const array = DM.getData("items", true)
            .map(d => {
                const obj = Object.assign({}, d)
                const g = group(d.tags, t => t.tag_id)
                obj.inconsistent = []
                g.forEach((list, _) => {
                    if (list.length < d.numCoders) {
                        list.forEach(l => {
                            if (selected.has(l.created_by)) {
                                obj.inconsistent.push(l)
                            }
                        })
                    }
                })
                obj.grouped = g;
                return obj
            })
            .filter(d => {
                return d.inconsistent.length > 0 &&
                    (selectedTags.value.size === 0 || d.inconsistent.some(dts => isSelectedTag(dts.tag_id)))
            })

        page.value = 1
        selItems.value = array
    }

    function init() {
        tags = null;
        selItems.value = []
        tagData.value = []
        tagDataPerCoder.clear()

        makeColorScales()
        readUsers()
        readTags()
        readSelectedTags()

        recalculate()
    }

    onMounted(init)

    watch(() => times.all, init)
    watch(() => Math.max(times.items, times.tagging, times.tags, times.datatags), readTags)
    watch(() => settings.lightMode, makeColorScales)

    watch(() => times.f_tags, readSelectedTags)
    watch(() => times.f_items, readSelectedItems)

</script>
