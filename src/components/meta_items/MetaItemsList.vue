<template>
    <div v-if="!hidden">
        <h3 class="mt-4 mb-4 text-uppercase">{{ selectedExts.size }} / {{ exts.size }} {{ app.schemeMetaItemName }}s</h3>
        <div class="d-flex justify-space-between mb-1">
            <v-text-field v-model="searchTerm"
                density="compact"
                class="pa-0 mr-2"
                label="search"
                clearable
                prepend-icon="mdi-magnify"
                style="max-width: 20%; max-height: 40px;"
                @update:model-value="checkPage"
                hide-details
                hide-spin-buttons/>

            <v-pagination v-model="page"
                :length="maxPages"
                :total-visible="5"
                density="compact"
                show-first-last-page
                style="min-width: 300px; max-height: 40px;"/>

            <div class="d-flex">
                <v-select v-model="numPerPage"
                    :items="[3, 5, 10, 25, 50]"
                    density="compact"
                    variant="outlined"
                    label="items per page"
                    class="mr-1"
                    hide-details
                    hide-spin-buttons
                    @update:model-value="checkPage"
                    style="width: 150px; max-height: 40px;"/>
                <v-number-input v-model="page"
                    :min="1" :step="1"
                    :max="maxPages"
                    variant="outlined"
                    density="compact"
                    control-variant="stacked"
                    hide-details
                    hide-spin-buttons
                    label="page"
                    style="width: 150px;"/>
            </div>
        </div>

        <v-sheet v-for="{ id, groups } in visibleExts" :key="id" style="width: 100%;" class="pa-1">
            <div class="d-flex align-center mb-2">
                <v-img
                    :src="'teaser/'+gameData.get(id).teaser"
                    :lazy-src="imgUrlS"
                    class="ml-1 cursor-pointer"
                    cover
                    @click="app.setShowGame(id)"
                    style="max-width: 80px; max-height: 40px;"
                    width="80"
                    height="40"/>
                <span class="ml-2 mr-2">{{ gameData.get(id).name }}</span>
                <BarCode v-if="barCodePerGame.has(id)"
                    :key="'bc_'+id"
                    :data="barCodePerGame.get(id)"
                    :domain="barCodeDomain"
                    @click="toggleTagHighlight"
                    id-attr="0"
                    value-attr="1"
                    :width="3"
                    :height="15"/>
            </div>
            <MetaGroupTile v-for="g in groups"
                :key="'group_'+g"
                :id="g"
                class="mb-2"
                :allow-edit="allowEdit"
                :selected="selectedExts.get(g)"
                :item="gameData.get(id)"/>
        </v-sheet>

        <div class="d-flex justify-space-between mt-1">

            <v-pagination v-model="page"
                :length="maxPages"
                :total-visible="5"
                density="compact"
                show-first-last-page
                style="min-width: 300px; max-height: 40px;"/>

            <div class="d-flex">
                <v-select v-model="numPerPage"
                    :items="[3, 5, 10, 25, 50]"
                    density="compact"
                    variant="outlined"
                    label="items per page"
                    class="mr-1"
                    hide-details
                    hide-spin-buttons
                    @update:model-value="checkPage"
                    style="width: 150px; max-height: 40px;"/>
                <v-number-input v-model="page"
                    :min="1" :step="1"
                    :max="maxPages"
                    variant="outlined"
                    density="compact"
                    control-variant="stacked"
                    hide-details
                    hide-spin-buttons
                    label="page"
                    style="width: 150px;"/>
            </div>
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import { useApp } from '@/store/app';
    import { group, InternMap } from 'd3';
    import MetaGroupTile from './MetaGroupTile.vue';
    import { computed, onMounted, reactive, watch } from 'vue';
    import BarCode from '../vis/BarCode.vue';

    import imgUrlS from '@/assets/__placeholder__s.png'
    import { storeToRefs } from 'pinia';

    const app = useApp()
    const times = useTimes();

    const props = defineProps({
        hidden: {
            type: Boolean,
            default: false
        }
    })

    const { allowEdit } = storeToRefs(app)

    const reading = ref(false)
    const searchTerm = ref("")

    const exts = ref(new Map())
    const exgs = ref(new Map())
    const gameData = reactive(new Map())

    const barCodeDomain = ref([])
    const barCodePerGame = reactive(new Map())

    const selectedGroups = ref(new Set())
    const selectedExts = reactive(new Map())

    const page = ref(1)
    const numPerPage = ref(3)
    const maxPages = computed(() => Math.max(1, Math.ceil(matches.value.length / numPerPage.value)))

    let loadOnShow = true;

    const matches = computed(() => {
        // selection but no matches
        if (reading.value || selectedGroups.value === null) return []

        // no selection
        const noSel = selectedGroups.value.size === 0

        const regex = searchTerm.value && searchTerm.value.length > 0 ?
            new RegExp(searchTerm.value, "i") : null

        const m = []
        exgs.value.forEach((array, game) => {
            let v = noSel ? array : array.filter(d => selectedGroups.value.has(d))
            if (v.length > 0) {
                const actual = []
                v.forEach(d => {
                    if (regex !== null) {
                        const matchesName = regex.test(gameData.get(game).name)
                        const g = exts.value.get(game).filter(e => e.group_id == d)
                        const subset = [];
                        g.forEach(e => {
                            if (matchesName || regex.test(e.name) || regex.test(e.cluster) || regex.test(e.description)) {
                                subset.push(e.id)
                            }
                        });

                        selectedExts.set(d, subset)
                        if (subset.length > 0) {
                            actual.push(d)
                        }
                    } else {
                        actual.push(d)
                    }
                })
                if (actual.length > 0) {
                    m.push({ id: game, groups: actual })
                }
            }
        })
        return m
    });
    const visibleExts = computed(() => {
        return matches.value.slice((page.value-1)*numPerPage.value, page.value*numPerPage.value)
    });

    function readExts() {
        reading.value = true;
        const data = DM.getData("meta_items", false)
        data.forEach(d => {
            const item = DM.getDataItem("items", d.item_id)
            if (item) gameData.set(d.item_id, item)
        })
        exts.value = group(data, d => d.item_id)
        exgs.value = new InternMap(Array.from(exts.value.entries()).map(([gameid, d]) => ([gameid, Array.from(new Set(d.map(dd => dd.group_id)))])))
        page.value = Math.max(1, Math.min(page.value, Math.ceil(exgs.value.size / numPerPage.value)))
        reading.value = false;
    }
    function updateExts() {
        if (!props.hidden) {
            if (reading.value) return
            loadOnShow = false;
            const ses = DM.getData("meta_items", true)
            if (ses.length === 0 && DM.hasFilter("meta_items")) {
                selectedGroups.value = null
            } else {
                selectedGroups.value = new Set(ses.map(d => d.group_id))
            }
            checkPage()
        } else {
            loadOnShow = true;
        }
    }

    function lastNames(n) {
        const parts = n.split("/")
        if (parts.length === 1) return n
        return parts.map((d, i) => i == 0 || i >= parts.length-2 ? d : "..")
            .reverse()
            .join(" / ")
    }
    function readBarCodes() {
        if (!props.hidden) {
            loadOnShow = false;
            barCodePerGame.clear()
            const tags = DM.getDataBy("tags", t => t.is_leaf === 1)
            tags.sort((a, b) => {
                const l = Math.min(a.path.length, b.path.length);
                for (let i = 0; i < l; ++i) {
                    if (a.path[i] < b.path[i]) return -1;
                    if (a.path[i] > b.path[i]) return 1;
                }
                return a.path.length-b.path.length
            });
            barCodeDomain.value = tags.map(t => t.id)
            updateBarCodes();
        } else {
            loadOnShow = true;
        }
    }
    function updateBarCodes() {
        gameData.forEach(g => {
            if (!barCodePerGame.has(g.id)) {
                barCodePerGame.set(g.id, g.allTags.map(t => ([t.id, lastNames(t.pathNames)])))
            }
        })
    }

    function toggleTagHighlight(tag) {
        app.toggleSelectByTag([tag[0]])
    }

    function checkPage(newval, oldval) {
        const maxval = maxPages.value
        if (oldval > newval) {
            page.value = Math.min(maxval, Math.max(1, Math.round(page.value * oldval / newval)-1))
        } else if (oldval < newval) {
            page.value = Math.min(maxval, Math.max(1, Math.round(page.value * oldval / newval)))
        } else {
            page.value = Math.min(maxval, Math.max(1, page.value))
        }
    }

    function init() {
        if (!props.hidden) {
            loadOnShow = false;
            readExts()
            readBarCodes()
        } else {
            loadOnShow = true;
        }
    }

    onMounted(init)

    watch(() => Math.max(times.tagging, times.datatags, times.tags, times.items), readBarCodes)
    watch(() => Math.max(times.all, times.meta_items), init)
    watch(() => times.f_meta_items, updateExts)

    watch(() => props.hidden, function(hidden) {
        if (!hidden && loadOnShow) {
            init()
        }
    })
</script>