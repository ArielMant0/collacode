<template>
    <div style="width: 100%;">

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
                label="filter by tags"
                @click="filterByTags = !filterByTags"
                density="compact"
                class="ml-1 mr-2"
                style="max-width: 150px;"
                />

            <v-combobox v-model="filterGames"
                :items="data.gameNames"
                class="ml-2"
                density="compact"
                clearable
                hide-details
                hide-no-data
                hide-spin-buttons
                label="filter by game name .."/>
        </div>

        <div v-for="(d, idx) in selectedGames" class="d-flex justify-start ma-1">
            <GameEvidenceRow
                :key="'ger_'+d.id+'_'+idx"
                :item="d"
                :evidence="data.evidence.get(d.id)"
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
                :evidence="getEvidence(d.id)"
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

            <v-select v-model="numPerPage"
                :items="[5, 10, 25, 50]"
                density="compact"
                label="items per page"
                hide-details
                hide-spin-buttons
                @update:model-value="checkPage"
                style="max-width: 150px; max-height: 40px;"/>

            <v-pagination v-model="page"
                :length="maxPages"
                :total-visible="5"
                density="compact"
                show-first-last-page
                style="min-width: 300px"/>

            <v-number-input v-model="page"
                :min="1" :step="1" :max="maxPages"
                density="compact"
                control-variant="stacked"
                label="page"
                style="max-width: 150px;"/>
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
    });

    const filterGames = ref("")
    const filterByTags = ref(false)

    const page = ref(1)
    const numPerPage = ref(5)
    const maxPages = computed(() => Math.ceil((selectedGames.value.length + otherMatchingGames.value.length) / numPerPage.value))

    const settings = useSettings();
    const { exSortBy, exSortHow } = storeToRefs(settings)

    const SPECIAL = /(\(\)\{\}\-\_\.\:)/g

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
        return data.games.filter((d, i) => {
            if (sel.has(d.id)) return false;
            let matchName = true, matchTags = true;
            if (filterGames.value && filterGames.value.length > 0) {
                const regex = new RegExp(filterGames.value.replaceAll(SPECIAL, "\$1"), "i")
                matchName = d.name.match(regex) !== null;
            }
            if (filterByTags.value && data.selectedTags.size > 0) {
                matchTags = getEvidence(d.id).length > 0;
            }
            return matchName && matchTags
        })
    })
    const otherGames = computed(() => {
        const startIndex = (page.value-1) * numPerPage.value;
        const endIndex = Math.min(page.value * numPerPage.value - 1, data.games.length-1);
        return otherMatchingGames.value.filter((d, i) => i >= startIndex && i <= endIndex)
    })

    function getEvidence(id) {
        if (!filterByTags.value || data.selectedTags.size === 0) return data.evidence.get(id)
        return !data.evidence.has(id) ? []:
            data.evidence.get(id).filter(d => data.selectedTags.has(d.tag_id))

    }

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
        readGames();
        readEvidence();
        sortData();
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
        if (props.code && gameIds.size > 0) {
            const ev = DM.getDataBy("evidence", d => d.code_id === props.code && gameIds.has(d.game_id));
            ev.forEach(e => {
                e.rows = e.rows ? e.rows : 1 + (e.description.includes('\n') ? e.description.match(/\n/g).length : 0)
                e.open = false;
            })
            data.evidence = d3.group(ev, d => d.game_id);
        } else {
            data.evidence.clear();
        }
        readTags();
    }
    function readTags() {
        const tags = DM.getData("tags", false);
        data.evidence.forEach(array => array.forEach(d => {
            d.tag = d.tag ? d.tag : (d.tag_id ? tags.find(t => t.id === d.tag_id) : null)
        }));
        readSelectedTags()
    }
    function readSelectedTags() {
        data.selectedTags = new Set(DM.hasFilter("tags") ? DM.getSelectedIds("tags") : [])
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

    watch(() => times.tags, readTags)
    watch(() => times.f_tags, readSelectedTags)
    watch(() => Math.max(times.games, times.evidence), readData, { deep: true })
    watch(numPerPage, checkPage)
</script>

