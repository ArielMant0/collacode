<template>
    <div style="width: 100%;">

        <div class="d-flex mb-4">
            <v-select v-model="exSortBy" :items="['name', 'evidence count']"
                hide-details
                hide-spin-buttons
                mandatory
                label="sort by"
                style="max-width: 200px;"
                density="compact"/>

            <v-btn-toggle v-model="exSortHow" class="ml-2" mandatory density="comfortable" color="primary" variant="text" rounded="sm">
                <v-btn value="asc" icon="mdi-sort-ascending"></v-btn>
                <v-btn value="des" icon="mdi-sort-descending"></v-btn>
            </v-btn-toggle>

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

        <div v-for="(d,idx) in selectedGames" class="d-flex justify-start ma-1">
            <div class="mr-2 d-flex">
                <div class="d-flex flex-column align-center justify-center mr-1">
                    <v-btn
                        :disabled="idx == 0"
                        density="compact"
                        rounded="sm"
                        variant="text"
                        icon="mdi-chevron-up"
                        @click="moveUp(d.id)"/>
                    <v-btn
                        :disabled="idx == selectedGames.length-1"
                        density="compact"
                        rounded="sm"
                        variant="text"
                        icon="mdi-chevron-down"
                        @click="moveDown(d.id)"/>
                </div>
                <div>
                    <v-hover :key="'g_row_'+d.id">
                        <template v-slot:default="{ isHovering, props }">
                            <v-img v-bind="props"
                                :src="d.teaser ? 'teaser/'+d.teaser : imgUrlS"
                                cover
                                @click="toggleSelected(d.id)"
                                class="cursor-pointer"
                                :width="width"
                                :height="height">
                                <v-overlay :model-value="d.teaser ? isHovering : true" contained class="d-flex align-center justify-center" :opacity="d.teaser || isHovering ? 0.8 : 0.5">
                                    <p style="color: white; white-space: break-spaces; text-align: center;" class="pa-1 font-weight-bold">{{ d.name }}</p>
                                </v-overlay>
                            </v-img>
                        </template>
                    </v-hover>
                </div>
            </div>

            <v-sheet v-for="e in data.evidence.get(d.id)" class="pa-0 mr-2" :width="showDesc.has(e.id) ? width*scaleFactor : height">

                <v-hover v-if="e.filepath">
                    <template v-slot:default="{ isHovering, props }">
                        <v-img v-bind="props"
                            class="cursor-pointer"
                            :src="'evidence/'+e.filepath"
                            cover
                            @click="enlarge(e)"
                            v-ripple.center
                            :width="showDesc.has(e.id) ? width*scaleFactor : height-10"
                            :height="showDesc.has(e.id) ? height*scaleFactor : height-10">
                            <v-overlay :model-value="isHovering" contained class="d-flex align-center justify-center" opacity="0.75">
                                <v-icon size="64" color="grey-lighten-2">mdi-magnify-plus-outline</v-icon>
                            </v-overlay>
                        </v-img>
                    </template>
                </v-hover>
                <div v-else>
                    <v-img class="pa-1" :src="imgUrlS" :width="height-10" :height="height-10"/>
                </div>

                <div class="d-flex cursor-pointer" @click="toggleDesc(e.id)">
                    <v-icon :icon="showDesc.has(e.id) ? 'mdi-menu-down' : 'mdi-menu-right'" density="compact"/>
                    <v-tooltip v-if="e.tag" :text="e.tag.name" open-delay="200" location="right">
                        <template v-slot:activator="{ props }">
                            <div v-bind="props" class="text-caption text-dots" style="max-width: 100%;">{{ e.tag.name }}</div>
                        </template>
                    </v-tooltip>
                </div>

                <v-card v-if="showDesc.has(e.id)" :text="e.description" :width="width*scaleFactor"></v-card>
            </v-sheet>
        </div>

        <v-divider v-if="selectedGames.length > 0" color="primary" class="mt-2 mb-2 border-opacity-100"></v-divider>

        <div v-for="d in otherGames" class="d-flex justify-start ma-1" style="width: 100%;">

            <div class="mr-2">
                <v-hover :key="'g_row_'+d.id">
                    <template v-slot:default="{ isHovering, props }">
                        <v-img v-bind="props"
                            :src="d.teaser ? 'teaser/'+d.teaser : imgUrlS"
                            cover
                            @click="toggleSelected(d.id)"
                            class="cursor-pointer"
                            :width="width"
                            :height="height">
                            <v-overlay :model-value="d.teaser ? isHovering : true" contained class="d-flex align-center justify-center" :opacity="d.teaser || isHovering ? 0.8 : 0.5">
                                <p style="color: white; white-space: break-spaces; text-align: center;" class="pa-1 font-weight-bold">{{ d.name }}</p>
                            </v-overlay>
                        </v-img>
                    </template>
                </v-hover>
            </div>

            <v-sheet v-for="e in data.evidence.get(d.id)" class="pa-0 mr-2" :width="showDesc.has(e.id) ? width*scaleFactor : height">

                <v-hover v-if="e.filepath">
                    <template v-slot:default="{ isHovering, props }">
                        <v-img v-bind="props"
                            class="cursor-pointer"
                            :src="'evidence/'+e.filepath"
                            cover
                            @click="enlarge(e)"
                            v-ripple.center
                            :width="showDesc.has(e.id) ? width*scaleFactor : height-10"
                            :height="showDesc.has(e.id) ? height*scaleFactor : height-10">
                            <v-overlay :model-value="isHovering" contained class="d-flex align-center justify-center" opacity="0.75">
                                <v-icon size="64" color="grey-lighten-2">mdi-magnify-plus-outline</v-icon>
                            </v-overlay>
                        </v-img>
                    </template>
                </v-hover>
                <div v-else>
                    <v-img class="pa-1" :src="imgUrlS" :width="height-10" :height="height-10"/>
                </div>

                <div class="d-flex cursor-pointer" @click="toggleDesc(e.id)">
                    <v-icon :icon="showDesc.has(e.id) ? 'mdi-menu-down' : 'mdi-menu-right'" density="compact"/>
                    <v-tooltip v-if="e.tag" :text="e.tag.name" open-delay="200" location="right">
                        <template v-slot:activator="{ props }">
                            <div v-bind="props" class="text-caption text-dots" style="max-width: 100%;">{{ e.tag.name }}</div>
                        </template>
                    </v-tooltip>
                </div>

                <v-card v-if="showDesc.has(e.id)" :text="e.description" :width="width*scaleFactor"></v-card>
            </v-sheet>
        </div>

        <v-overlay v-model="showEnlarged" opacity="0.8"
            class="d-flex align-center justify-center"
            @update:model-value="checkEnlarge"
            close-on-content-click>
            <div v-if="enlargedItem" class="pa-3">
                <img :src="'evidence/'+enlargedItem.filepath" style="max-width: 100%;" alt="Image Preview"/>
                <v-card class="mt-2" color="grey-darken-4">
                    <v-textarea :model-value="enlargedItem.description" readonly hide-details hide-spin-buttons></v-textarea>
                </v-card>
            </div>
        </v-overlay>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { reactive, onMounted, watch, ref, computed } from 'vue';
    import DM from '@/use/data-manager'

    import imgUrlS from '@/assets/__placeholder__s.png'
import { useSettings } from '@/store/settings';
import { storeToRefs } from 'pinia';

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
        }
    });

    const enlargedItem = ref(null);
    const showEnlarged = ref(false);

    const filterGames = ref("")

    const settings = useSettings();
    const { exSortBy, exSortHow } = storeToRefs(settings)

    const data = reactive({
        games: [],
        gameNames: [],
        evidence: new Map(),
        selected: [],
    })
    const showDesc = reactive(new Set());

    const selectedGames = computed(() => data.selected.map(id => data.games.find(d => d.id === id)))
    const otherGames = computed(() => {
        const rows = data.games.filter(d => {
            let filter = true;
            if (filterGames.value && filterGames.value.length > 0) {
                const special = /(\(\)\{\}\-\_\.\:)/g
                const regex = new RegExp(filterGames.value.replaceAll(special, "\$1"), "i")
                filter = d.name.match(regex) !== null;
            }
            return filter && !data.selected.includes(d.id)
        })

        const smaller = exSortHow.value === "asc" ? -1 : 1;
        rows.sort((a, b) => {
            if (exSortBy.value === "name") {
                const nameA = a.name.toLowerCase(); // ignore upper and lowercase
                const nameB = b.name.toLowerCase(); // ignore upper and lowercase
                if (nameA < nameB) { return smaller }
                if (nameA > nameB) { return -smaller }
            } else {
                const numA = data.evidence.has(a.id) ? data.evidence.has(a.id).length : null
                const numB = data.evidence.has(b.id) ? data.evidence.has(b.id).length : null
                if (numA !== null && numB !== null) { return numA - numB }
                else if (numA !== null && numB === null) { return smaller }
                else if (numA === null && numB !== null) { return -smaller }
            }
            return 0;
        });

        return rows
    })

    function readData() {
        data.gameNames = DM.getData("games", false).map(d => d.name);
        readGames();
        readEvidence();
    }
    function readGames() {
        const gameIds = new Set();
        const games = DM.getData("games", true);
        games.sort((a, b) => {
            gameIds.add(a.id)
            gameIds.add(b.id)
            const nameA = a.name.toLowerCase(); // ignore upper and lowercase
            const nameB = b.name.toLowerCase(); // ignore upper and lowercase
            if (nameA < nameB) { return -1 }
            if (nameA > nameB) { return 1 }
            return 0;
        });
        data.selected = data.selected.filter(id => gameIds.has(id));
        data.games = games;
    }
    function readEvidence() {
        const gameIds = new Set(DM.getSelectedIds("games"));
        const tagIds = DM.getSelectedIds("tags");
        showDesc.clear();
        if (props.code && gameIds.size > 0) {
            const ev = DM.getDataBy("evidence", d => d.code_id === props.code && gameIds.has(d.game_id));
            const grouped = d3.group(ev, d => d.game_id)
            if (tagIds.length > 0) {
                grouped.forEach(array => array.sort((a, b) => {
                    const iB = tagIds.indexOf(b.tag_id);
                    const iA = tagIds.indexOf(a.tag_id);
                    if (iA < 0 && iB < 0) return 0;
                    else if (iA < 0) return 1
                    else if (iB < 0) return -1
                }));
            }
            data.evidence = grouped;
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
    function toggleDesc(id) {
        if (showDesc.has(id)) {
            showDesc.delete(id)
        } else {
            showDesc.add(id)
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

<style scoped>
.text-dots {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis
}</style>