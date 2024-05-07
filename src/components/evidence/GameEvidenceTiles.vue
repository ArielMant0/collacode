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
                <v-btn value="asc" icon="mdi-sort-ascending"></v-btn>
                <v-btn value="des" icon="mdi-sort-descending"></v-btn>
            </v-btn-toggle>

            <v-btn icon="mdi-select"
                class="ml-2 mr-1"
                color="secondary"
                rounded="sm"
                density="comfortable"
                @click="data.selected = []"
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

            <v-pagination v-model="page"
                :length="maxPages"
                :total-visible="5"
                density="compact"
                show-first-last-page
                style="min-width: 300px"/>

            <input :value="page"
                type="number"
                min="1"
                class="pa-1 bg-grey-lighten-2"
                :max="maxPages"
                step="1"
                @change="e => page = Number.parseInt(e.target.value)"
                />
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
                @enlarge="enlarge"
                :allow-edit="allowEdit"
                :allow-add="allowAdd"
                :allow-move-down="idx < selectedGames.length-1"
                :allow-move-up="idx > 0"
                />
        </div>

        <v-divider v-if="selectedGames.length > 0" color="primary" class="mt-2 mb-2 border-opacity-100"></v-divider>

        <div v-for="(d, idx) in otherGames" class="d-flex justify-start ma-1" style="width: 100%;">

            <GameEvidenceRow
                :key="'ger_'+d.id"
                :item="d"
                :evidence="data.evidence.get(d.id)"
                :selected="false"
                :width="width"
                :height="height"
                @select="toggleSelected"
                @move-up="moveUp"
                @move-down="moveDown"
                @enlarge="enlarge"
                :allow-edit="allowEdit"
                :allow-add="allowAdd"
                :allow-move-down="false"
                :allow-move-up="false"/>
        </div>

        <v-overlay v-model="showEnlarged" opacity="0.9"
            class="d-flex align-center justify-center"
            @update:model-value="checkEnlarge"
            >
            <div v-if="enlargedItem" class="pa-3">
                <v-btn icon="mdi-close"
                    style="position: absolute; right: 0; top: 0;"
                    color="error"
                    variant="flat"
                    density="comfortable"
                    @click="showEnlarged = false"/>
                <img :src="'evidence/'+enlargedItem.filepath" style="max-height: 90vh; max-width: 100%;" alt="Image Preview"/>
                <v-card class="mt-2" color="grey-darken-4">
                    <v-textarea
                        :model-value="enlargedItem.description"
                        :rows="enlargedItem.rows + 1"
                        readonly hide-details hide-spin-buttons/>
                </v-card>
            </div>
        </v-overlay>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { reactive, onMounted, watch, ref, computed } from 'vue';
    import DM from '@/use/data-manager'

    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import GameEvidenceRow from './GameEvidenceRow.vue';
    import { compareString } from '@/use/utility';

    const props = defineProps({
        time: {
            type: Number,
            required: true
        },
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

    const enlargedItem = ref(null);
    const showEnlarged = ref(false);

    const filterGames = ref("")

    const page = ref(1)
    const numPerPage = ref(5)
    const maxPages = computed(() => Math.ceil(data.games.length / numPerPage.value))

    const settings = useSettings();
    const { exSortBy, exSortHow } = storeToRefs(settings)

    const SPECIAL = /(\(\)\{\}\-\_\.\:)/g

    const data = reactive({
        games: [],
        gameNames: [],
        evidence: new Map(),
        selected: [],
    })

    const selectedGames = computed(() => data.selected.map(id => data.games.find(d => d.id === id)))
    const otherGames = computed(() => {
        const obj = { by: exSortBy.value, how: exSortHow.value };
        const startIndex = (page.value-1) * numPerPage.value;
        const endIndex = Math.min(page.value * numPerPage.value, data.games.length-1);
        return data.games.filter((d, i) => {
            let filter = !data.selected.includes(d.id);
            if (filter && filterGames.value && filterGames.value.length > 0) {
                const regex = new RegExp(filterGames.value.replaceAll(SPECIAL, "\$1"), "i")
                return d.name.match(regex) !== null;
            }
            return filter && i >= startIndex && i <= endIndex
        })
    })

    function sortData() {
        const smaller = exSortHow.value === "asc" ? -1 : 1;
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
        data.gameNames = DM.getData("games", false).map(d => d.name);
        readGames();
        readEvidence();
        sortData();
    }
    function readGames() {
        const gameIds = new Set();
        const games = DM.getData("games", true);
        games.forEach(d => gameIds.add(d.id));
        data.selected = data.selected.filter(id => gameIds.has(id));
        data.games = games;
    }
    function readEvidence() {
        const gameIds = new Set(DM.getSelectedIds("games"));
        if (props.code && gameIds.size > 0) {
            const ev = DM.getDataBy("evidence", d => d.code_id === props.code && gameIds.has(d.game_id));
            ev.forEach(e => {
                e.rows = 1 + (e.description.includes('\n') ? e.description.match(/\n/g).length : 0)
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
            d.tag = d.tag_id ? tags.find(t => t.id === d.tag_id) : null
        }));

        const tagIds = DM.getSelectedIds("tags");
        if (tagIds.length > 0) {
            data.evidence.forEach(array => array.sort((a, b) => {
                if (!a.tag_id && !b.tag_id) return 0
                const iB = tagIds.indexOf(b.tag_id);
                const iA = tagIds.indexOf(a.tag_id);
                if (iA < 0 && iB < 0 || iA >= 0 && iB >= 0) {
                    if (!a.tag || !b.tag) return 0
                    return compareString(a.tag.name, b.tag.name)
                }
                return iA < 0 ? 1 : -1
            }));
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

    function enlarge(item) {
        if (item) {
            enlargedItem.value = item;
            showEnlarged.value = true;
        }
    }
    function checkEnlarge() {
        if (!showEnlarged.value) {
            enlargedItem.value = null;
        }
    }
    onMounted(readData)

    watch(() => props.time, readData)
</script>

