<template>
    <div style="width: 100%;">
        <h3 class="text-uppercase" style="text-align: center;">Evidence Tag Matrix</h3>
        <div class="d-flex">
            <div class="d-flex text-caption text-dots mr-2" style="min-width: 250px; max-width: 250px;">
                <b class="mr-2 cursor-pointer" @click="nextSortMode('name')">Name</b>
                <v-icon v-if="sortName > 0"
                    :icon="sortName === 1 ? 'mdi-sort-ascending' : 'mdi-sort-descending'"
                    density="compact"
                    rounded="sm"/>
            </div>
            <div class="text-caption text-dots mr-2" style="min-width: 100px; max-width: 100px;">
                <b class="mr-2 cursor-pointer" @click="nextSortMode('numTags')">#Tags</b>
                <v-icon v-if="sortTags > 0"
                    :icon="sortTags === 1 ? 'mdi-sort-ascending' : 'mdi-sort-descending'"
                    density="compact"
                    rounded="sm"/>
            </div>
            <div class="d-flex text-caption text-dots mr-2" style="min-width: 100px; max-width: 100px;">
                <b class="mr-2 cursor-pointer" @click="nextSortMode('numEvidence')">#Evidence</b>
                <v-icon v-if="sortEvs > 0"
                    :icon="sortEvs === 1 ? 'mdi-sort-ascending' : 'mdi-sort-descending'"
                    density="compact"
                    rounded="sm"/>
            </div>
        </div>
        <v-divider class="mb-2 mt-2"></v-divider>
        <div v-for="(item, i) in itemData" :key="item.id+'_'+i+'_'+time" style="width: 100%;" class="d-flex">
            <div class="text-caption text-dots mr-2 cursor-pointer onhover" style="min-width: 250px; max-width: 250px;" @click="app.setShowItem(item.id)">
                {{ item.name }}
            </div>
            <div class="text-caption text-dots mr-2" style="min-width: 100px; max-width: 100px;">
                {{ item.numTags }}
            </div>
            <div class="text-caption text-dots mr-2" style="min-width: 100px; max-width: 100px;">
                {{ item.numEvidence }}
            </div>
            <BarCode v-if="item.data.length > 0"
                :data="item.data"
                @click="t => app.toggleSelectByTag(t.id)"
                selectable
                :domain="tagDomain"
                id-attr="id"
                name-attr="name"
                value-attr="value"
                abs-value-attr="value"
                show-absolute
                :hide-highlight="i !== 0"
                highlight-pos="top"
                selected-color="red"
                categorical
                :color-scale="[settings.lightMode ? '#ccc' : '#333', settings.lightMode ? '#0ad39f' : '#078766']"
                hide-tooltip
                @hover="(t, e) => onHover(item, t, e)"
                :no-value-color="settings.lightMode ? rgb(238,238,238).formatHex() : rgb(33,33,33).formatHex()"
                :width="6"
                :height="20"/>
        </div>
    </div>
</template>

<script setup>

    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import { onMounted, watch } from 'vue';
    import BarCode from '../vis/BarCode.vue';
    import { useSettings } from '@/store/settings';
    import { useApp } from '@/store/app';
    import { pointer, rgb } from 'd3';
    import { useTooltip } from '@/store/tooltip';
    import { sortObjByString } from '@/use/sorting';

    const app = useApp()
    const tt = useTooltip()
    const times = useTimes()
    const settings = useSettings()

    const itemData = ref([])
    const tagDomain = ref([])
    const time = ref(Date.now())

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
    }

    function readAll() {
        readTags()
        readItems()
    }
    function readTags() {
        const tags = DM.getDataBy("tags", d => d.is_leaf === 1)
        tags.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return 0
        });
        tagDomain.value = tags.map(d => d.id)
    }
    function readItems() {

        const array = DM.getData("items", true)
            .map(d => {
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
                    list.push({
                        id: tid,
                        name: DM.getDataItem("tags_name", tid),
                        value: ev.has(tid) ? 2 : 1
                    })
                })

                return {
                    id: d.id,
                    name: d.name,
                    data: list,
                    numTags: d.numTags,
                    numEvidence: d.numEvidence,
                    evidence: d.evidence
                }
            })

        sortItems(array)

        itemData.value = array;
        time.value = Date.now()
    }

    function onHover(item, tag, event) {
        if (tag) {
            let str = ""
            item.evidence.forEach(d => {
                if (d.tag_id !== tag.id) return;
                str += `<div class="mb-1 mr-1">`
                if (d.filepath) {
                    str += `<image src="evidence/${d.filepath}" width="150" height="150" style="object-fit: cover;"/>`
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
            tt.show(all, x + 15, y)
        } else {
            tt.hide()
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
.onhover:hover {
    font-style: italic;
}
</style>