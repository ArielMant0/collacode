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
        <div class="d-flex mb-1">
            <v-select v-model="methodG"
                :items="DR_METHODS"
                @update:model-value="calculateGamesDR"
                density="compact"
                hide-details
                hide-spin-buttons/>
            <v-checkbox :model-value="showImages"
                density="compact"
                label="images"
                class="ml-1 mr-2"
                hide-details
                hide-spin-buttons
                single-line
                @click="showImages = !showImages"/>
            <v-checkbox :model-value="showConns"
                density="compact"
                label="connections"
                class="ml-1 mr-2"
                hide-details
                hide-spin-buttons
                single-line
                @click="toggleConns"/>
            <v-select v-model="methodE"
                :items="DR_METHODS"
                @update:model-value="calculateExtsDR"
                density="compact"
                hide-details
                hide-spin-buttons/>
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

    const tt = useTooltip();

    const props = defineProps({
        time: {
            type: Number,
            default: 0
        },
        size: {
            type: Number,
            default: 500
        }
    })

    const el = ref(null)

    const showDR = ref(false)
    const DR_METHODS = ["PCA", "UMAP", "TSNE", "MDS", "TopoMap"]

    const methodG = ref("TSNE")
    const pointsG = ref([])
    const selectedG = ref([])
    const refreshG = ref(props.time)

    const showImages = ref(false)
    const showConns = ref(true)
    const methodE = ref("TSNE")
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

    function getDR(method, matrix) {
        const DR = druid[method]
        switch (method) {
            // case "ISOMAP": return new DR(matrix, { metric: druid.cosine })
            case "TopoMap": return new DR(matrix, { metric: druid.cosine })
            case "MDS": return new DR(matrix, { metric: druid.cosine })
            case "TSNE": return new DR(matrix, { metric: druid.cosine, perplexity: 10 })
            case "UMAP": return new DR(matrix, { metric: druid.cosine, n_neighbors: 10, local_connectivity: 2, _n_epochs: 500 })
            default: return new DR(matrix)
        }
    }

    function calculateDR() {
        calculateGamesDR();
        calculateExtsDR();
    }
    function calculateGamesDR() {
        pointsG.value = Array.from(getDR(methodG.value, matrixG).transform()).map((d,i) => {
            const game = dataG[i]
            return [d[0], d[1], i, "teaser/"+game.teaser, game.numExt > 0 ? 1 : 0]
        })
        refreshG.value = Date.now();
    }
    function calculateExtsDR() {
        pointsE.value = Array.from(getDR(methodE.value, matrixE).transform()).map((d,i) => ([d[0], d[1], i]))
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
                <image src="teaser/${dataG[d[2]].teaser}" width="160" height="80"/>
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

        // const sG = new Set(selectedG.value)
        // const sE = new Set(selectedE.value)
        // svg.append("g")
        //     .attr("fill", "none")
        //     .attr("stroke", "black")
        //     .attr("stroke-width", 1)
        //     .attr("opacity", 0.5)
        //     .selectAll("path")
        //     .data(dataE.filter(d => sE.has(extMap.get(d.id)) || sG.has(gameMap.get(d.game_id))).map(d => {
        //         const idx = gameMap.get(d.game_id)
        //         const gameP = pointsG.value[idx]
        //         const extP = pointsE.value[extMap.get(d.id)]
        //         return [[gameP.px, gameP.py], [props.size+extP.px, extP.py]]
        //     }))
        //     .join("path")
        //     .attr("d", path)

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