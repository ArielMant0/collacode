<template>
    <div v-if="!hidden" style="width: 100%;">
        <h3 class="mt-4 mb-4"> {{ numVisible }} / {{ numAll }} EVIDENCE</h3>

        <div class="d-flex justify-space-between">

            <v-pagination v-model="page"
                :length="maxPages"
                :total-visible="5"
                density="compact"
                show-first-last-page
                style="min-width: 300px"/>

            <div class="d-flex">
                <v-select v-model="numPerPage"
                    :items="[5, 10, 25, 50]"
                    density="compact"
                    variant="outlined"
                    label="items per page"
                    class="mr-1"
                    hide-details
                    hide-spin-buttons
                    @update:model-value="checkPage"
                    style="width: 150px; max-height: 40px;"/>


                <v-number-input v-model="page"
                    :min="1" :step="1" :max="maxPages"
                    variant="outlined"
                    density="compact"
                    control-variant="stacked"
                    label="page"
                    style="width: 150px;"/>
            </div>
        </div>

        <div class="d-flex mb-4">
            <v-select v-model="exSortBy" :items="['name', 'evidence count']"
                hide-details
                hide-spin-buttons
                mandatory
                label="sort by"
                style="max-width: 200px;"
                density="compact"
                @update:model-value="sortData"/>

            <v-btn-toggle v-model="exSortHow"
                class="ml-2"
                mandatory
                density="comfortable"
                color="primary"
                variant="text"
                rounded="sm"
                @update:model-value="sortData">
                <v-btn value="asc" icon="mdi-sort-reverse-variant"></v-btn>
                <v-btn value="dsc" icon="mdi-sort-variant"></v-btn>
            </v-btn-toggle>

            <v-btn icon="mdi-select"
                class="ml-2 mr-1"
                color="secondary"
                rounded="sm"
                density="comfortable"
                @click="data.selected = []"
                />

            <v-checkbox-btn
                :model-value="filterByTags"
                label="filter evidence by tags"
                @click="filterByTags = !filterByTags"
                density="compact"
                class="ml-2 mr-2"
                style="max-width: 200px;"
                />

            <v-text-field v-model="searchTerm"
                density="compact"
                class="pa-0 ml-2"
                label="search"
                clearable
                prepend-icon="mdi-magnify"
                style="max-height: 40px;"
                hide-details
                hide-spin-buttons/>
        </div>

        <div v-for="(d, idx) in selectedGames" class="d-flex justify-start ma-1">
            <GameEvidenceRow
                :key="'ger_'+d.id+'_'+idx"
                :item="d"
                :evidence="matchingEvidence.get(d.id)"
                :selected="true"
                :width="width"
                :height="height"
                @select="toggleSelected"
                @move-up="moveUp"
                @move-down="moveDown"
                :allow-edit="allowEdit"
                :allow-add="allowAdd"
                :allow-move-down="idx < selectedGames.length-1"
                :allow-move-up="idx > 0"
                />
        </div>

        <v-divider v-if="selectedGames.length > 0" color="primary" class="mt-2 mb-2 border-opacity-100"></v-divider>

        <div v-for="(d, _) in otherGames" class="d-flex justify-start ma-1" style="width: 100%;">

            <GameEvidenceRow
                :key="'ger_'+d.id"
                :item="d"
                :evidence="matchingEvidence.get(d.id)"
                :selected="false"
                :width="width"
                :height="height"
                @select="toggleSelected"
                @move-up="moveUp"
                @move-down="moveDown"
                :allow-edit="allowEdit"
                :allow-add="allowAdd"
                :allow-move-down="false"
                :allow-move-up="false"/>
        </div>

        <div class="d-flex justify-space-between">

            <v-pagination v-model="page"
                :length="maxPages"
                :total-visible="5"
                density="compact"
                show-first-last-page
                style="min-width: 300px"/>

            <div class="d-flex">
                <v-select v-model="numPerPage"
                    :items="[5, 10, 25, 50]"
                    density="compact"
                    variant="outlined"
                    label="items per page"
                    class="mr-1"
                    hide-details
                    hide-spin-buttons
                    @update:model-value="checkPage"
                    style="width: 150px; max-height: 40px;"/>


                <v-number-input v-model="page"
                    :min="1" :step="1" :max="maxPages"
                    variant="outlined"
                    density="compact"
                    control-variant="stacked"
                    label="page"
                    style="width: 150px;"/>
            </div>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { reactive, onMounted, watch, ref, computed } from 'vue';
    import DM from '@/use/data-manager'

    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import GameEvidenceRow from './GameEvidenceRow.vue';
    import { useTimes } from '@/store/times';

    const times = useTimes();

    const props = defineProps({
        code: {
            type: Number
        },
        selected: {
            type: Object,
            required: false
        },
        highlightClicked: {
            type: Boolean,
            default: false
        },
        width: {
            type: Number,
            default: 150
        },
        height: {
            type: Number,
            default: 80
        },
        scaleFactor: {
            type: Number,
            default: 4
        },
        allowAdd: {
            type: Boolean,
            default: false
        },
        allowEdit: {
            type: Boolean,
            default: false
        },
        hidden: {
            type: Boolean,
            default: false
        },
    });

    const searchTerm = ref("")
    const filterByTags = ref(false)

    const page = ref(1)
    const numPerPage = ref(5)
    const maxPages = computed(() => Math.ceil((selectedGames.value.length + otherMatchingGames.value.length) / numPerPage.value))

    const numVisible = ref(0)
    const numAll = ref(0)

    const settings = useSettings();
    const { exSortBy, exSortHow } = storeToRefs(settings)

    let loadOnShow = true;

    const data = reactive({
        games: [],
        gameNames: [],
        evidence: new Map(),
        selected: [],
        selectedTags: new Set()
    })

    const selectedGames = computed(() => data.selected.map(id => data.games.find(d => d.id === id)))
    const otherMatchingGames = computed(() => {
        const obj = { by: exSortBy.value, how: exSortHow.value };
        const sel = new Set(data.selected)
        const selGames = DM.getSelectedIds("games")
        const regex = searchTerm.value && searchTerm.value.length > 0 ?
            new RegExp(searchTerm.value, "i") : null

        return data.games.filter(d=> {
            if (sel.has(d.id)) return false;
            let matchName = true, matchTags = true, matchSel = true;
            if (regex !== null) {
                const ev =  data.evidence.has(d.id) ? data.evidence.get(d.id) : []
                matchName = regex.test(d.name) || (ev.length > 0 && ev.some(e => regex.test(e.description)))
            }
            if (data.selectedTags.size > 0) {
                // check if selected
                if (selGames.size > 0) {
                    matchSel = selGames.has(d.id)
                } else {
                    matchSel = d.allTags.some(t => data.selectedTags.has(t.id) || t.path.some(p => data.selectedTags.has(p)))
                }

                if (filterByTags.value) {
                    const ev = data.evidence.get(d.id)
                    if (!ev) {
                        matchTags = false;
                    } else {
                        matchTags = ev.some(e => data.selectedTags.has(e.tag_id));
                    }
                }
            }
            return matchName && matchTags && matchSel
        })
    })
    const otherGames = computed(() => {
        const startIndex = (page.value-1) * numPerPage.value;
        const endIndex = Math.min(page.value * numPerPage.value - 1, data.games.length-1);
        return otherMatchingGames.value.filter((_, i) => i >= startIndex && i <= endIndex)
    })

    const matchingEvidence = computed(() => {
        const regex = searchTerm.value && searchTerm.value.length > 0 ?
            new RegExp(searchTerm.value, "i") : null

        let numItems = 0
        const m = new Map()
        const testMatch = d => {
            let matches = [];
            if (!filterByTags.value || data.selectedTags.size === 0) {
                matches = (data.evidence.has(d.id) ? data.evidence.get(d.id) : [])
                    .filter(dd => regex === null || (regex.test(DM.getDerivedItem(dd.tag_id)) || regex.test(dd.description)))
            } else {
                matches = (data.evidence.has(d.id) ? data.evidence.get(d.id) : [])
                    .filter(dd => data.selectedTags.has(dd.tag_id) && (regex === null || regex.test(dd.description)))
            }

            if (matches.length > 0) {
                m.set(d.id, matches)
                numItems += matches.length
            }
        }

        selectedGames.value.forEach(testMatch)
        otherMatchingGames.value.forEach(testMatch)

        numVisible.value = numItems

        return m
    })

    function sortData() {
        const smaller = exSortHow.value === "asc" ? 1 : -1;
        data.games.sort((a, b) => {
            if (exSortBy.value === "name") {
                const nameA = a.name.toLowerCase(); // ignore upper and lowercase
                const nameB = b.name.toLowerCase(); // ignore upper and lowercase
                if (nameA < nameB) { return smaller }
                if (nameA > nameB) { return -smaller }
            } else {
                const numA = data.evidence.has(a.id) ? data.evidence.get(a.id).length : null
                const numB = data.evidence.has(b.id) ? data.evidence.get(b.id).length : null
                if (numA !== null && numB !== null) {
                    return smaller < 0 ? numB - numA : numA - numB
                }
                else if (numA !== null && numB === null) { return smaller }
                else if (numA === null && numB !== null) { return -smaller }
            }
            return 0;
        });
    }

    function readData() {
        if (!props.hidden) {
            loadOnShow = false;
            readGames();
            readEvidence();
            sortData();
        } else {
            loadOnShow = true;
        }
    }
    function readGames() {
        const gameIds = new Set();
        const games = DM.getData("games", true).filter(d => d.allTags.length > 0);
        games.forEach(d => gameIds.add(d.id));
        data.selected = data.selected.filter(id => gameIds.has(id));
        data.games = games;
        const namesSorted = games.map(d => d.name);
        namesSorted.sort()
        data.gameNames = namesSorted;
    }
    function readEvidence() {
        const gameIds = new Set(data.games.map(d => d.id));
        let numItems = 0
        if (props.code && gameIds.size > 0) {
            const ev = DM.getDataBy("evidence", d => d.code_id === props.code && gameIds.has(d.game_id));
            ev.forEach(e => {
                e.rows = e.rows ? e.rows : 1 + (e.description.includes('\n') ? e.description.match(/\n/g).length : 0)
                e.open = false;
            })
            numItems += ev.length
            data.evidence = d3.group(ev, d => d.game_id);
        } else {
            data.evidence.clear();
        }
        numAll.value = numItems
        readTags();
    }
    function readTags() {
        if (!props.hidden) {
            loadOnShow = false;
            const tags = DM.getData("tags", false);
            data.evidence.forEach(array => array.forEach(d => {
                d.tag = d.tag ? d.tag : (d.tag_id ? tags.find(t => t.id === d.tag_id) : null)
            }));
            readSelectedTags()
        } else {
            loadOnShow = true;
        }
    }
    function readSelectedTags() {
        if (!props.hidden) {
            loadOnShow = false;
            data.selectedTags = DM.getSelectedIds("tags")
        } else {
            loadOnShow = true;
        }
    }

    function toggleSelected(id) {
        const idx = data.selected.indexOf(id)
        if (idx >= 0) {
            data.selected.splice(idx, 1)
        } else {
            data.selected.push(id)
        }
    }
    function moveUp(id) {
        const idx = data.selected.indexOf(id)
        if (idx > 0) {
            const copy = data.selected.slice();
            const tmp = copy[idx-1];
            copy[idx-1] = copy[idx];
            copy[idx] = tmp;
            data.selected = copy;
        }
    }
    function moveDown(id){
        const idx = data.selected.indexOf(id)
        if (idx >= 0 && idx < data.selected.length-1) {
            const copy = data.selected.slice();
            const tmp = copy[idx+1];
            copy[idx+1] = copy[idx];
            copy[idx] = tmp;
            data.selected = copy;
        }
    }

    function checkPage(newval, oldval) {
        const maxval = Math.ceil(data.games.length / newval)
        if (oldval > newval) {
            page.value = Math.min(maxval, Math.max(1, Math.round(page.value * oldval / newval)-1))
        } else if (oldval < newval) {
            page.value = Math.min(maxval, Math.max(1, Math.round(page.value * oldval / newval)))
        } else {
            page.value = Math.min(maxval, Math.max(1, page.value))
        }
    }

    onMounted(readData)

    watch(numPerPage, checkPage)

    watch(() => times.tags, readTags)
    watch(() => Math.max(times.f_tags, times.f_games), readSelectedTags)
    watch(() => Math.max(times.games, times.evidence), readData)

    watch(() => props.hidden, function(hidden) {
        if (!hidden && loadOnShow) {
            readData()
        }
    })
</script>

