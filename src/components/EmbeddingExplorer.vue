<template>
    <div :style="{ 'max-width': (2*size+5)+'px', 'text-align': 'center' }">
        <v-btn
            class="mb-2 text-caption"
            color="primary"
            density="compact"
            @click="showDR = !showDR">
            {{ showDR ? 'hide' : 'show' }} scatter plots
        </v-btn>
        <div v-if="showDR">
        <div class="d-flex justify-center mb-2">
            <EmbeddingParameters ref="paramsG" @update="calculateGamesDR"/>
            <v-select v-model="colorByG"
                class="ml-1"
                style="max-width: 120px;"
                label="color by number of"
                :items="['externalizations', 'evidence', 'tags']"
                variant="outlined"
                density="compact"
                return-object
                hide-spin-buttons
                hide-details
                @update:model-value="updateColorG"
                single-line/>
            <v-checkbox :model-value="showImages"
                density="compact"
                label="images"
                class="ml-6 mr-2"
                hide-details
                hide-spin-buttons
                single-line
                @click="showImages = !showImages"/>
            <v-checkbox :model-value="showConns"
                density="compact"
                label="connections"
                class="ml-1 mr-6"
                hide-details
                hide-spin-buttons
                single-line
                @click="toggleConns"/>
            <EmbeddingParameters ref="paramsE" @update="calculateExtsDR"/>
            <v-select v-model="colorByE"
                class="ml-1"
                style="max-width: 120px;"
                label="color by number of"
                :items="['likes/dislikes', 'evidence', 'tags']"
                variant="outlined"
                density="compact"
                return-object
                hide-spin-buttons
                hide-details
                @update:model-value="updateColorE"
                single-line/>
        </div>
        <div style="position: relative">
            <ScatterPlot v-if="pointsG.length > 0"
                :data="pointsG"
                :time="time"
                :selected="selectedG"
                :refresh="refreshG"
                x-attr="0"
                y-attr="1"
                id-attr="2"
                url-attr="3"
                fill-attr="4"
                :width="size"
                :height="size"
                :grid="showImages"
                :fill-color-scale="['#ffffff'].concat(d3.schemeRdPu[6].slice(1))"
                :fill-color-bins="6"
                canvas
                @hover="onHoverGame"
                @click="onClickGame"/>
            <ScatterPlot v-if="pointsE.length > 0"
                :data="pointsE"
                :time="time"
                :selected="selectedE"
                :refresh="refreshE"
                x-attr="0"
                y-attr="1"
                id-attr="2"
                fill-attr="3"
                :fill-color-scale="['#ffffff'].concat(d3.schemeGnBu[6].slice(1))"
                :fill-color-bins="6"
                :width="size"
                :height="size"
                canvas
                @hover="onHoverExt"
                @click="onClickExt"/>

            <svg ref="el" :width="size*2" :height="size" style="pointer-events: none; position: absolute; top: 0; left: 0;"></svg>
        </div>
        </div>
    </div>
</template>

<script setup>
    import { onMounted, ref, watch } from 'vue';
    import * as d3 from 'd3';
    import * as druid from '@saehrimnir/druidjs';
    import ScatterPlot from './vis/ScatterPlot.vue';
    import DM from '@/use/data-manager';
    import { useTooltip } from '@/store/tooltip';
    import EmbeddingParameters from './EmbeddingParameters.vue';

    const tt = useTooltip();

    const props = defineProps({
        time: {
            type: Number,
            default: 0
        },
        size: {
            type: Number,
            default: 700
        }
    })

    const el = ref(null)
    const paramsG = ref(null)
    const paramsE = ref(null)

    const showDR = ref(false)

    const colorByG = ref("externalizations")
    const pointsG = ref([])
    const selectedG = ref([])
    const refreshG = ref(props.time)

    const showImages = ref(false)
    const showConns = ref(true)

    const colorByE = ref("likes/dislikes")
    const pointsE = ref([])
    const selectedE = ref([])
    const refreshE = ref(props.time)

    let matrixG, dataG;
    let matrixE, dataE;

    const gameMap = new Map();
    const extMap = new Map();

    function readData() {
        readGames()
        readExts()
    }
    function readGames() {
        dataG = DM.getDataBy("games", d => d.allTags.length > 0)
        const tags = DM.getDataBy("tags", d => d.is_leaf === 1)
        tags.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return a.path.length-b.path.length
        });
        const idToIdx = new Map()
        tags.forEach((d, i) => idToIdx.set(d.id, i))

        gameMap.clear()
        const p = new Array(dataG.length)
        dataG.forEach((d, i) => {
            gameMap.set(d.id, i)
            const arr = new Array(tags.length)
            arr.fill(0)
            d.allTags.forEach(t => arr[idToIdx.get(t.id)] = 1)
            p[i] = arr;
        });
        matrixG = druid.Matrix.from(p)
    }
    function readExts() {
        dataE = DM.getData("externalizations", false)
        const allCats = DM.getData("ext_categories", false)
        const cats = allCats.filter(d => !allCats.some(dd => dd.parent === d.id))
        cats.sort((a, b) => a.parent-b.parent);
        const idToIdx = new Map()
        cats.forEach((d, i) => idToIdx.set(d.id, i))

        extMap.clear()
        const p = new Array(dataE.length)
        dataE.forEach((d, i) => {
            extMap.set(d.id, i)
            const arr = new Array(cats.length)
            arr.fill(0)
            d.categories.forEach(t => arr[idToIdx.get(t.cat_id)] = 1)
            p[i] = arr;
        });
        matrixE = druid.Matrix.from(p)
    }

    function getDR(which="games") {
        const params = which == "games" ? paramsG.value.getParams() : paramsE.value.getParams()
        const method = params.method;
        delete params.method
        const matrix = which == "games" ? matrixG : matrixE;
        const DR = druid[method]
        switch (method) {
            // case "ISOMAP": return new DR(matrix, { metric: druid.cosine })
            case "TopoMap": return new DR(matrix, params)
            case "MDS": return new DR(matrix, params)
            case "TSNE": return new DR(matrix, params)
            case "UMAP": return new DR(matrix, params)
            default: return new DR(matrix)
        }
    }

    function calculateDR() {
        calculateGamesDR();
        calculateExtsDR();
    }
    function calculateGamesDR() {
        if (!paramsG.value) return setTimeout(calculateGamesDR, 250);
        console.log(colorByG.value)
        pointsG.value = Array.from(getDR("games").transform()).map((d,i) => {
            const game = dataG[i]
            let val;
            switch(colorByG.value) {
                case "tags":
                    val = game.allTags.length;
                    break;
                case "evidence":
                    val = game.numEvidence;
                    break;
                default:
                    val = game.numExt;
                    break;
            }
            return [d[0], d[1], i, "teaser/"+game.teaser, val]
        })
        refreshG.value = Date.now();
    }
    function updateColorG() {
        pointsG.value.forEach((d,i) => {
            const game = dataG[i]
            switch(colorByG.value) {
                case "tags":
                    d[4] = game.allTags.length;
                    break;
                case "evidence":
                    d[4] =  game.numEvidence;
                    break;
                default:
                    d[4] = game.numExt;
                    break;
            }
        })
        refreshG.value = Date.now();
    }
    function calculateExtsDR() {
        if (!paramsE.value) return setTimeout(calculateExtsDR, 250);
        pointsE.value = Array.from(getDR("evidence").transform()).map((d,i) => {
            const ext = dataE[i]
            let val;
            switch(colorByE.value) {
                case "tags":
                    val = ext.tags.length;
                    break;
                case "evidence":
                    val =  ext.evidence.length;
                    break;
                default:
                    val = ext.likes.length - ext.dislikes.length;
                    break;
            }
            return [d[0], d[1], i, val]
        })
        refreshE.value = Date.now();
    }
    function updateColorE() {
        pointsE.value.forEach((d,i) => {
            const ext = dataE[i]
            switch(colorByE.value) {
                case "tags":
                    d[3] = ext.tags.length;
                    break;
                case "evidence":
                    d[3] =  ext.evidence.length;
                    break;
                default:
                    d[3] = ext.likes.length - ext.dislikes.length;
                    break;
            }
        })
        refreshE.value = Date.now();
    }

    function readSelected() {
        selectedG.value = DM.hasFilter("games") ? DM.getData("games").map(d => gameMap.get(d.id)) : []
        selectedE.value = DM.hasFilter("externalizations") ? DM.getData("externalizations").map(d => extMap.get(d.id)) : []
    }

    function onHoverGame(array, event) {
        if (array.length > 0) {
            const res = array.reduce((str, d) =>  str + `<div>
                <div class="text-caption text-dots" style="max-width: 165px">${dataG[d[2]].name}</div>
                <image src="teaser/${dataG[d[2]].teaser}" width="160"/>
            </div>` , "")

            tt.show(`<div class="d-flex flex-wrap">${res}</div>`, event.pageX+10, event.pageY+10)
            drawConnections(array.map(d => d[2]), null);
        } else {
            tt.hide()
            drawConnections();
        }
    }
    function onClickGame(array) {
        if (array.length === 0) {
            DM.removeFilter("externalizations", "game_id")
            if (DM.hasFilter("externalizations")) {
                DM.setFilter(
                    "games",
                    "id",
                    DM.getData("externalizations").map(d => d.game_id)
                )
            }
        } else {
            DM.toggleFilter("games", "id", array.map(d => dataG[d[2]].id))
            const ids = DM.getFilter("games", "id");
            DM.setFilter("externalizations", "game_id", ids);
        }
        readSelected()
        refreshG.value = Date.now()
    }
    function onHoverExt(array, event) {
        if (array.length > 0) {
            const res = array.reduce((str, d) => {
                const game = dataG[gameMap.get(dataE[d[2]].game_id)]
                return str + `<div class="d-flex">
                    <div class="mr-2">
                        <div class="text-caption text-dots" style="max-width: 85px">${game.name}</div>
                        <image src="teaser/${game.teaser}" width="80" height="40"/>
                    </div>
                    <p class="text-caption" style="max-width: 250px"><b>${dataE[d[2]].name}</b></br>${dataE[d[2]].description}</p>
                </div>`
            }, "")

            tt.show(`<div class="d-flex flex-wrap">${res}</div>`, event.pageX+10, event.pageY+10)
            drawConnections(null, array.map(d => d[2]));
        } else {
            tt.hide()
            drawConnections();
        }
    }
    function onClickExt(array) {
        if (array.length === 0) {
            DM.removeFilter("externalizations", "id")
        } else {
            DM.toggleFilter("externalizations", "id", array.map(d => dataE[d[2]].id))
        }

        if (DM.hasFilter("externalizations")) {
            DM.setFilter(
                "games",
                "id",
                DM.getData("externalizations").map(d => d.game_id)
            )
        }
        readSelected()
        refreshE.value = Date.now()
    }

    function drawConnections(gameIdx=null, extIdx=null) {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove();
        if (!showConns.value) return;

        const path = d3.line()
            .x(d => d[0])
            .y(d => d[1])

        if (gameIdx !== null) {
            const indices = new Set(gameIdx)
            svg.append("g")
                .attr("fill", "none")
                .attr("stroke", "red")
                .attr("stroke-width", 2)
                .selectAll("path")
                .data(dataE.filter(d => indices.has(gameMap.get(d.game_id))).map(d => {
                    const idx = gameMap.get(d.game_id)
                    const gameP = pointsG.value[idx]
                    const extP = pointsE.value[extMap.get(d.id)]
                    return [[gameP.px, gameP.py], [props.size+extP.px, extP.py]]
                }))
                .join("path")
                .attr("d", path)
        } else if (extIdx !== null) {
            const indices = new Set(extIdx)
            svg.append("g")
                .attr("fill", "none")
                .attr("stroke", "red")
                .attr("stroke-width", 2)
                .selectAll("path")
                .data(dataE.filter(d => indices.has(extMap.get(d.id))).map(d => {
                    const idx = gameMap.get(d.game_id)
                    const gameP = pointsG.value[idx]
                    const extP = pointsE.value[extMap.get(d.id)]
                    return [[gameP.px, gameP.py], [props.size+extP.px, extP.py]]
                }))
                .join("path")
                .attr("d", path)
                .attr("stroke", "red")
                .attr("stroke-width", 2)
        }
    }

    function toggleConns() {
        showConns.value = !showConns.value
    }

    onMounted(function() {
        if (showDR.value) {
            console.log(paramsG.value, paramsE.value)
            readData()
            readSelected(false);
            calculateDR();
        }
    })

    watch(() => props.time, readSelected)
    watch(showDR, function(show) {
        if (show && (!dataG || !dataE)) {
            readData()
            readSelected(false);
            calculateDR();
        }
    });
</script>