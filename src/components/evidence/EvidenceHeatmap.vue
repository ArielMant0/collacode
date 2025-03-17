<template>
    <div style="width: 100%;">
        <h3 class="text-uppercase" style="text-align: center;">Evidence Tag Matrix</h3>

        <div class="d-flex">
            <div class="d-flex text-caption text-dots mr-3" style="min-width: 200px; max-width: 200px;">
                <b class="mr-2 cursor-pointer" @click="nextSortMode('name')">Name</b>
                <v-icon v-if="sortName > 0"
                    :icon="sortName === 1 ? 'mdi-sort-ascending' : 'mdi-sort-descending'"
                    density="compact"
                    rounded="sm"/>
            </div>
            <div class="text-caption text-dots mr-3" style="min-width: 80px; max-width: 80px;">
                <b class="mr-2 cursor-pointer" @click="nextSortMode('numTags')">#Tags</b>
                <v-icon v-if="sortTags > 0"
                    :icon="sortTags === 1 ? 'mdi-sort-ascending' : 'mdi-sort-descending'"
                    density="compact"
                    rounded="sm"/>
            </div>
            <div class="d-flex text-caption text-dots mr-3" style="min-width: 100px; max-width: 100px;">
                <b class="mr-2 cursor-pointer" @click="nextSortMode('numEvidence')">#Evidence</b>
                <v-icon v-if="sortEvs > 0"
                    :icon="sortEvs === 1 ? 'mdi-sort-ascending' : 'mdi-sort-descending'"
                    density="compact"
                    rounded="sm"/>
            </div>
        </div>
        <v-divider class="mb-2 mt-2"></v-divider>

        <div class="d-flex">
            <div class="mr-3" style="min-width: 200px; max-width: 200px;"></div>
            <div class="mr-3" style="min-width: 80px; max-width: 80px;"></div>
            <div class="mr-3" style="min-width: 100px; max-width: 100px; position: relative;">
                <v-btn-toggle v-model="globalMode" density="compact" mandatory border color="primary" style="position: absolute; right: 0; bottom: 5px">
                    <v-tooltip text="show absolute value" location="top" open-delay="300">
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props"
                                rounded="sm" size="small" value="absolute_range" density="comfortable" variant="plain" icon="mdi-relative-scale"/>
                        </template>
                    </v-tooltip>
                    <v-tooltip text="show relative value" location="top" open-delay="300">
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props"
                                rounded="sm" size="small" value="relative" density="comfortable" variant="plain" icon="mdi-percent-circle"/>
                        </template>
                    </v-tooltip>
                </v-btn-toggle>
            </div>
            <div>
                <MiniTree :node-width="6" value-attr="from_id" :value-data="barValues" value-agg="mean"/>
                <BarCode v-if="globalBarData.length > 0" :key="'global_'+time"
                    :data="globalBarData"
                    @click="t => app.toggleSelectByTag(t.id)"
                    @right-click="(t, e) => onRightClick(null, t, e)"
                    selectable
                    discrete
                    :domain="tagDomain"
                    id-attr="id"
                    name-attr="name"
                    value-attr="value"
                    abs-value-attr="absValue"
                    :show-absolute="globalMode !== 'relative'"
                    hide-highlight
                    :min-value="0"
                    :max-value="globalMode === 'relative' ? 1 : undefined"
                    :no-value-color="settings.lightMode ? rgb(242,242,242).formatHex() : rgb(22,22,22).formatHex()"
                    :width="6"
                    :height="15"/>
            </div>
        </div>

        <div style="max-height: 80vh; overflow-y: auto;">

            <v-hover v-for="(item, i) in itemData" :key="item.id+'_'+i+'_'+time">
            <template v-slot:default="{ isHovering, props }">
            <div v-bind="props"
                :style="{ width: '100%', maxHeight: selectedItem.id === item.id ? 'fit-content' : '15px' }"
                class="d-flex align-start justify-start onhover">

                <div class="text-caption text-dots mr-3 cursor-pointer"
                    :style="{ minWidth: '200px', maxWidth: '200px', fontWeight: selectedItem.id === item.id ? 'bold' : 'normal' }">
                    <span @click="toggleItemEvidence(item)">{{ item.name }}</span>
                    <div v-if="selectedItem.id === item.id">
                        <ItemTeaser :item="item" :width="160" :height="80"/>
                    </div>
                </div>
                <div class="text-caption text-dots mr-3"
                    :style="{ minWidth: '80px', maxWidth: '80px', fontWeight: selectedItem.id === item.id ? 'bold' : 'normal' }">
                    {{ item.numTags }}
                </div>
                <div class="text-caption text-dots mr-3"
                    :style="{ minWidth: '100px', maxWidth: '100px', fontWeight: selectedItem.id === item.id ? 'bold' : 'normal' }">
                    {{ item.numEvidence }}
                </div>
                <div class="pa-0 ma-0">
                    <BarCode v-if="barData.has(item.id)"
                        :item-id="item.id"
                        :data="barData.get(item.id)"
                        @click="t => app.toggleSelectByTag(t.id)"
                        @right-click="(t, e) => onRightClick(item, t, e)"
                        @hover="(t, e) => onHover(item, t, e)"
                        selectable
                        :domain="tagDomain"
                        id-attr="id"
                        name-attr="name"
                        value-attr="value"
                        abs-value-attr="value"
                        show-absolute
                        hide-highlight
                        highlight-pos="top"
                        selected-color="red"
                        categorical
                        :color-scale="[
                            isHovering || selectedItem.id === item.id ?
                                (settings.lightMode ? '#999' : '#777') :
                                (settings.lightMode ? '#ccc' : '#444'),
                            isHovering || selectedItem.id === item.id ?
                                (settings.lightMode ? 'black' : 'white') :
                                (settings.lightMode ? '#0ad39f' : '#078766')
                        ]"
                        hide-tooltip
                        :no-value-color="settings.lightMode ? rgb(242,242,242).formatHex() : rgb(22,22,22).formatHex()"
                        :width="6"
                        :height="15"/>

                    <div v-if="selectedItem.id === item.id" style="max-width: 100%;">
                        <EvidenceCell v-for="(e, idx) in selectedItem.evidence" :key="e.id+'_details'"
                            style="display: inline-block;"
                            :item="e"
                            :allow-edit="app.allowEdit"
                            @select="app.setShowEvidence(
                                e.id,
                                selectedItem.evidence.map(dd => dd.id),
                                idx
                            )"
                            :width="150"
                            :height="150"/>
                    </div>
                </div>
            </div>
            </template>
            </v-hover>

        </div>

    </div>
</template>

<script setup>

    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import { onMounted, reactive, watch } from 'vue';
    import BarCode from '../vis/BarCode.vue';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useApp } from '@/store/app';
    import { pointer, rgb } from 'd3';
    import { useTooltip } from '@/store/tooltip';
    import { sortObjByString } from '@/use/sorting';
    import EvidenceCell from './EvidenceCell.vue';
    import MiniTree from '../vis/MiniTree.vue';
    import ItemTeaser from '../items/ItemTeaser.vue';

    const app = useApp()
    const tt = useTooltip()
    const times = useTimes()
    const settings = useSettings()

    const itemData = ref([])
    const tagDomain = ref([])
    const time = ref(Date.now())

    const globalMode = ref("relative")

    let globalBarData = []
    const barValues = ref({})
    let barData = new Map()

    const gEvCount = new Map(), gTagCount = new Map();

    const selectedItem = reactive({
        id: null,
        evidence: []
    })

    const sortName = ref(0)
    const sortTags = ref(0)
    const sortEvs = ref(0)

    function nextSortMode(name) {
        switch(name) {
            default:
            case "name":
                sortName.value = sortName.value < 2 ? sortName.value + 1 : 0;
                sortTags.value = 0;
                sortEvs.value = 0;
                break;
            case "numTags":
                sortTags.value = sortTags.value < 2 ? sortTags.value + 1 : 0;
                sortName.value = 0;
                sortEvs.value = 0;
                break;
            case "numEvidence":
                sortEvs.value = sortEvs.value < 2 ? sortEvs.value + 1 : 0;
                sortName.value = 0;
                sortTags.value = 0;
                break;
        }
        sortItems()
    }
    function sortItems(array) {
        let sorted = false;
        array = array ? array : itemData.value
        if (sortName.value > 0) {
            array.sort(sortObjByString("name", { ascending: sortName.value === 2 }))
            sorted = true
        } else if (sortTags.value > 0) {
            const mod = sortTags.value === 2 ? 1 : -1
            array.sort((a, b) => (a.numTags - b.numTags) * mod)
            sorted = true
        } else if (sortEvs.value > 0) {
            const mod = sortEvs.value === 2 ? 1 : -1
            array.sort((a, b) => (a.numEvidence - b.numEvidence) * mod)
            sorted = true
        }

        if (!sorted) {
            array.sort((a, b) => a.id - b.id)
        }
        tt.hide()
    }

    function readAll() {
        readTags()
        readItems()
    }
    function readTags() {
        tagDomain.value = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
    }
    function readItems() {
        barData.clear()
        gEvCount.clear()
        gTagCount.clear()

        const array = DM.getData("items", true)
            .map(d => {
                if (d.numTags > 0 || d.numEvidence > 0) {
                    barData.set(d.id, getItemBarData(d))
                }
                return {
                    id: d.id,
                    name: d.name,
                    numTags: d.numTags,
                    numEvidence: d.numEvidence,
                    evidence: d.evidence,
                    teaser: d.teaser
                }
            })

        sortItems(array)

        globalBarData = []
        const valueObj = {}

        gEvCount.forEach((count, tid) => {
            valueObj[tid] = 0
            if (count > 0) {
                valueObj[tid] = count / gTagCount.get(tid)
                globalBarData.push({
                    id: tid,
                    name: DM.getDataItem("tags_name", tid),
                    value: valueObj[tid],
                    absValue: count
                })
            }
        })

        barValues.value = valueObj
        itemData.value = array;
        time.value = Date.now()
    }

    function getItemBarData(d) {
        const tags = new Set()
        const ev = new Set();

        if (app.showAllUsers) {
            d.tags.forEach(dts => tags.add(dts.tag_id))
        } else {
            d.allTags.forEach(t => tags.add(t.id))
        }

        d.evidence.forEach(e => {
            if (e.tag_id !== null) {
                ev.add(e.tag_id)
            }
        });

        const list = []
        tags.forEach(tid => {
            const val = ev.has(tid) ? 2 : 1
            list.push({
                id: tid,
                name: DM.getDataItem("tags_name", tid),
                value: val
            })

            if (val > 0) {
                gTagCount.set(tid, (gTagCount.get(tid) || 0) + 1)
            }
            if (val > 1) {
                gEvCount.set(tid, (gEvCount.get(tid) || 0) + 1)
            }
        })

        return list
    }

    function onHover(item, tag, event) {
        if (tag) {
            let str = ""
            item.evidence.forEach(d => {
                if (d.tag_id !== tag.id) return;
                str += `<div class="mb-1 mr-1">`
                if (d.filepath) {
                    str += `<img src="evidence/${d.filepath}" width="150" height="150" style="object-fit: cover;"/>`
                }
                if (d.description) {
                    str += `<div class="text-ww" style="max-width: 150px;">
                        ${d.description.length > 40 ? d.description.slice(0, 40)+'..' : d.description}
                    </div>`
                }
                str += "</div>"
            })
            const all = `<div class="text-caption">
                <div><b>${item.name}</b> (${tag.name})</div>
                <div class="d-flex flex-wrap justify-start">${str}</div>
                </div>`

            const [x, y] = pointer(event, document.body)
            tt.show(all, x, y)
        } else {
            tt.hide()
        }
    }
    function onRightClick(item, tag, event) {
        event.preventDefault();
        if (tag) {
            const [mx, my] = pointer(event, document.body)
            settings.setRightClick(
                "tag", tag.id,
                mx, my,
                tag.name,
                item ? { item: item.id } : null,
                item ? CTXT_OPTIONS.items_tagged : CTXT_OPTIONS.tag
            );
        } else {
            settings.setRightClick(null)
        }
    }

    function toggleItemEvidence(item) {
        if (selectedItem.id !== item.id) {
            selectedItem.evidence = item.evidence;
            selectedItem.id = item.id;
        } else {
            selectedItem.id = null;
            selectedItem.evidence = [];
        }
    }

    onMounted(readAll)

    watch(() => Math.max(times.all, times.tagging, times.tags), readAll)

    watch(() => Math.max(
        times.items,
        times.evidence,
        times.tagging,
        times.tags,
        times.f_items
    ), readItems)
</script>

<style scoped>
.onhover:hover, .onhover:hover > * {
    text-decoration: underline;
}
.tag-label {
    font-size: 6px;
    text-align: start;
    text-overflow: clip;
    overflow: hidden;
    white-space: nowrap;

    transform: rotate(-90deg);
    /* Safari */
    -webkit-transform: rotate(-90deg);
    /* Firefox */
    -moz-transform: rotate(-90deg);
    /* IE */
    -ms-transform: rotate(-90deg);
    /* Opera */
    -o-transform: rotate(-90deg);
}
</style>