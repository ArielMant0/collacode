<template>
    <div v-if="!hidden" :style="{ 'max-width': width+'px', 'text-align': 'center' }">
        <div class="d-flex justify-center align-center mb-2">

            <v-tooltip text="search items" location="bottom" open-delay="300">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props"
                        icon="mdi-magnify"
                        color="primary"
                        rounded="sm"
                        class="mr-1"
                        variant="plain"
                        density="compact"
                        @click="openSearchItems"/>
                </template>
            </v-tooltip>

            <v-tooltip text="clear search results" location="bottom" open-delay="300">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props"
                        icon="mdi-close"
                        class="mr-3"
                        color="error"
                        rounded="sm"
                        variant="plain"
                        density="compact"
                        @click="resetHighlightG"/>
                </template>
            </v-tooltip>

            <v-btn
                icon="mdi-cog-outline"
                density="compact"
                rounded="sm"
                variant="plain"
                @click="paramsLeft = !paramsLeft"/>

            <div v-if="paramsLeft" class="d-flex justify-center align-center ml-2">
                <EmbeddingParameters ref="paramsG" @update="calculateGamesDR" :defaults="defaultsG"/>
                <v-select v-model="colorByG"
                    class="ml-1"
                    style="max-width: 120px;"
                    label="color by number of"
                    :items="['cluster', 'binary', 'meta_items', 'evidence', 'tags']"
                    variant="solo"
                    density="compact"
                    return-object
                    hide-spin-buttons
                    hide-details
                    @update:model-value="updateColorG"
                    single-line/>
            </div>
            <v-divider class="ml-4 mr-4" vertical></v-divider>
            <v-tooltip text="clear all selections" location="bottom" open-delay="300">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props"
                        icon="mdi-delete"
                        class="mr-1"
                        color="error"
                        rounded="sm"
                        variant="plain"
                        density="compact"
                        @click="resetSelection"/>
                </template>
            </v-tooltip>
            <v-tooltip text="draw games as images" location="bottom" open-delay="300">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props"
                        :icon="showImages ? 'mdi-image' : 'mdi-image-off'"
                        class="ml-1"
                        rounded="sm"
                        variant="plain"
                        density="compact"
                        @click="showImages = !showImages"/>
                </template>
            </v-tooltip>

            <v-divider class="ml-4 mr-4" vertical></v-divider>

            <v-tooltip text="search meta items" location="bottom" open-delay="300">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props"
                        icon="mdi-magnify"
                        color="primary"
                        rounded="sm"
                        class="mr-1"
                        variant="plain"
                        density="compact"
                        @click="openSearchExts"/>
                </template>
            </v-tooltip>
            <v-tooltip text="clear search results" location="bottom" open-delay="300">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props"
                        icon="mdi-close"
                        class="mr-3"
                        color="error"
                        rounded="sm"
                        variant="plain"
                        density="compact"
                        @click="resetHighlightE"/>
                </template>
            </v-tooltip>

            <v-btn
                icon="mdi-cog-outline"
                density="compact"
                rounded="sm"
                variant="plain"
                @click="paramsRight = !paramsRight"/>

            <div v-if="paramsRight" class="d-flex justify-center align-center ml-2">
                <EmbeddingParameters ref="paramsE" v-model="paramsRight" @update="calculateExtsDR" :defaults="defaultsE"/>
                <v-select v-model="colorByE"
                    class="ml-1"
                    style="max-width: 120px;"
                    label="color by number of"
                    :items="['none', 'cluster', 'evidence', 'tags']"
                    variant="solo"
                    density="compact"
                    return-object
                    hide-spin-buttons
                    hide-details
                    @update:model-value="updateColorE"
                    single-line/>
            </div>
        </div>
        <div class="d-flex justify-center align-center text-caption mb-2">
            <div :style="{ 'width': size+'px' }">
                <span v-if="searchTermG">showing results for search <b>"{{ searchTermG }}"</b></span>
            </div>
            <div :style="{ 'width': size+'px' }">
                <span v-if="searchTermE">showing results for search <b>"{{ searchTermE }}"</b></span>
            </div>
        </div>
        <div style="position: relative;">
            <div class="d-flex">
            <ScatterPlot v-if="pointsG.length > 0"
                ref="scatterG"
                :data="pointsG"
                :selected="selectedG"
                :highlighted="highlightG"
                :refresh="refreshG"
                :time="timeG"
                x-attr="0"
                y-attr="1"
                id-attr="2"
                url-attr="3"
                fill-attr="4"
                :width="size"
                :height="size"
                :grid="showImages"
                :glyph-attr="colorByG === 'cluster' ? '4' : ''"
                :glyph-domain="clusters"
                :glyph-color-scale="glyphColors"
                :fill-color-scale="colorByG !== 'binary' ? d3.schemeGnBu[6] : ['#555', '#0acb99']"
                :fill-color-bins="colorByG === 'cluster' || colorByG === 'binary' ? 0 : 6"
                selected-color="#333"
                color-scale
                color-scale-pos="top"
                @hover="onHoverGame"
                @click="onClickGame"
                @click-color="onClickGameColor"
                @lasso="onClickGame"/>

            <h3 v-else class="text-uppercase" :style="{ textAlign: 'center', width: size+'px' }">
                NO {{ app.schemeItemName }}s AVAILABLE
            </h3>

            <v-divider vertical class="ml-2 mr-2"></v-divider>

            <ScatterPlot v-if="pointsE.length > 0"
                ref="scatterE"
                :data="pointsE"
                :selected="selectedE"
                :highlighted="highlightE"
                :refresh="refreshE"
                :time="timeE"
                x-attr="0"
                y-attr="1"
                id-attr="2"
                :fill-attr="colorByE !== 'none' ? '3' : null"
                :fill-domain="colorByE === 'cluster' ? clusters : []"
                :fill-color-scale="colorByE === 'cluster' ? glyphColors : d3.schemeGnBu[6]"
                :fill-color-bins="colorByE === 'cluster' ? 0 : 6"
                :width="size"
                :height="size"
                selected-color="#333"
                color-scale
                color-scale-pos="top"
                @hover="onHoverExt"
                @click="onClickExt"
                @click-color="onClickExtColor"
                @lasso="onClickExt"
                @right-click="onRightClickExt"/>

            <h3 v-else class="text-uppercase" :style="{ textAlign: 'center', width: size+'px' }">
                NO {{ app.schemeMetaItemName }}s AVAILABLE
            </h3>

            </div>
            <svg ref="el" :width="width" :height="size" style="pointer-events: none; position: absolute; top: 100; left: 0"></svg>
        </div>

        <MiniDialog v-model="openSearch" min-width="500" @cancel="cancelSearch" @submit="search" submit-text="search">
            <template v-slot:text>
                <v-text-field v-model="searchTerm"
                    :label="'search for '+searchLoc"
                    hide-spin-buttons
                    density="compact"
                    autofocus
                    @update:model-value="updateSearchSuggestions"
                    :hide-details="searchSuggestions.length === 0"
                    @keyup="checkEnter"
                    :messages="searchSuggestions"/>
            </template>
        </MiniDialog>
    </div>
</template>

<script setup>
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import * as d3 from 'd3';
    import * as druid from '@saehrimnir/druidjs';
    import ScatterPlot from './vis/ScatterPlot.vue';
    import DM from '@/use/data-manager';
    import { useTooltip } from '@/store/tooltip';
    import EmbeddingParameters from './EmbeddingParameters.vue';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import { useApp } from '@/store/app';
    import MiniDialog from './dialogs/MiniDialog.vue';
    import { FILTER_TYPES } from '@/use/filters';
    import { getMetric } from '@/use/metrics';
    import { useToast } from 'vue-toastification';
    import Cookies from 'js-cookie';

    const tt = useTooltip();
    const settings = useSettings()
    const times = useTimes()
    const app = useApp();
    const toast = useToast()

    const props = defineProps({
        hidden: {
            type: Boolean,
            defaut: false
        },
        width: {
            type: Number,
            default: 700
        }
    })

    const el = ref(null)
    const paramsLeft = ref(false)
    const paramsRight = ref(false)
    const paramsG = ref(null)
    const paramsE = ref(null)
    const scatterG = ref(null)
    const scatterE = ref(null)

    const searchTerm = ref("")
    const searchTermG = ref("")
    const searchTermE = ref("")
    const searchSuggestions = ref([])
    const searchLoc = ref("items")
    const openSearch = ref(false)

    const colorByG = ref("cluster")
    const pointsG = ref([])
    const selectedG = ref([])
    const highlightG = ref([]);
    const refreshG = ref(Date.now())
    const timeG = ref(Date.now())

    const showImages = ref(false)
    const showConns = ref(true)

    const colorByE = ref("cluster")
    const pointsE = ref([])
    const selectedE = ref([])
    const highlightE = ref([]);
    const refreshE = ref(Date.now())
    const timeE = ref(Date.now())

    let matrixG, dataG;
    let matrixE, dataE;

    const gameMap = new Map();
    const extMap = new Map();
    let loadOnShow = true;

    const allClusters = settings.clusterOrder.flat()
    let clusters = []
    let glyphColors = []

    let connCacheG, connCacheE;

    const defaultsG = reactive({ perplexity: 20, method: 'TSNE', metric: 'cosine' })
    const defaultsE = reactive({ perplexity: 10, method: 'TSNE', metric: 'cosine' })

    const size = computed(() => props.width / 2 - 20)

    function readGames() {
        dataG = DM.getDataBy("items", d => d.allTags.length > 0)
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

        matrixG = dataG.length > 0 ? druid.Matrix.from(p) : []
    }
    function readExts() {
        dataE = DM.getData("meta_items", false)

        clusters = DM.getData("meta_clusters")
        if (clusters.length === 0) {
            if (colorByG.value === "cluster") {
                colorByG.value = "binary"
            }
            if (colorByE.value === "cluster") {
                colorByE.value = "none"
            }
        }

        clusters.sort((a, b) => allClusters.indexOf(a)-allClusters.indexOf(b))
        glyphColors = settings.clusterOrder.map((colors, i) => {
            const subset = colors.filter(c => clusters.includes(c))
            let scheme;
            switch (i) {
                case 0:
                    scheme = d3.schemeBlues[6].slice(1, 5)
                    break;
                case 1:
                    scheme = d3.schemeRdPu[6].slice(1, 5)
                    break;
                case 2:
                    scheme = d3.schemeGreens[6].slice(1, 5)
                    break;
                case 3:
                    scheme = d3.schemeOranges[6].slice(1, 5)
                    break;
                case 4:
                    scheme = d3.schemePurples[6].slice(1, 5)
                    break;
                default:
                    scheme = d3.schemeGreys[6].slice(1, 5)
                    break;
            }
            if (subset.length === 1) return scheme.at(-1)
            scheme.reverse()
            return scheme.slice(0, subset.length)
        }).flat()

        const allCats = DM.getData("meta_categories", false)
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

        matrixE = dataE.length > 0 ? druid.Matrix.from(p) : []
    }

    function getDR(which="items") {
        const params = Object.assign({}, which == "items" ? defaultsG : defaultsE)
        Cookies.set(which == "items" ? "ee-settings-g" : "ee-settings-e", JSON.stringify(params), { expires: 365 })
        params.metric = getMetric(params.metric)
        const method = params.method;
        delete params.method
        const matrix = which == "items" ? matrixG : matrixE;

        if (matrix.length === 0) {
            console.warn("empty matrix")
            return;
        }

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
    function getColorG(game) {
        switch(colorByG.value) {
                case "tags": return game.allTags.length;
                case "cluster": {
                    const g = d3.group(game.metas, d => d.cluster);
                    const res = []
                    g.forEach((array, cluster) => res.push({ name: cluster, value: array.length}))
                    res.sort((a, b) => allClusters.indexOf(a.name)-allClusters.indexOf(b.name))
                    return res
                }
                case "evidence": return game.numEvidence;
                case "meta_items": return game.numMeta;
                default: return game.numMeta > 0 ? "#items > 0" : "#items = 0";
            }
    }
    function calculateGamesDR(notify=false) {
        if (paramsG.value) Object.assign(defaultsG, paramsG.value.getParams())
        if (notify) toast.info("calculating items embedding")

        const dr = getDR("items")
        if (!dr) return
        pointsG.value = Array.from(dr.transform()).map((d,i) => {
            const game = dataG[i]
            const val = getColorG(game)
            return [d[0], d[1], i, "teaser/"+game.teaser, val]
        })
        refreshG.value = Date.now();
    }
    function updateColorG() {
        pointsG.value.forEach((d,i) => {
            const game = dataG[i]
            d[4] = getColorG(game)
        })
        refreshG.value = Date.now();
    }

    function getColorE(ext) {
        switch(colorByE.value) {
            case "tags": return ext.tags.length;
            case "evidence": return ext.evidence.length;
            case "cluster": return ext.cluster;
            default: return 1;
        }
    }
    function calculateExtsDR(notify=false) {
        if (paramsE.value) Object.assign(defaultsE, paramsE.value.getParams())
        if (notify) toast.info("calculating meta items embedding")

        const dr = getDR("evidence");
        if (!dr) return
        pointsE.value = Array.from(dr.transform()).map((d,i) => ([d[0], d[1], i, getColorE(dataE[i])]))
        refreshE.value = Date.now();
    }
    function updateColorE() {
        pointsE.value.forEach((d,i) => {
            const item = dataE[i]
            d[3] = getColorE(item)
        })
        refreshE.value = Date.now();
    }

    function readSelected() {
        if (!props.hidden) {
            loadOnShow = false;
            selectedG.value = DM.getSelectedIdsArray("items").map(id => gameMap.get(id))
            timeG.value = Date.now();
            selectedE.value = DM.getSelectedIdsArray("meta_items").map(id => extMap.get(id))
            timeE.value = Date.now();
        } else {
            loadOnShow = true;
        }
    }

    function openSearchItems() {
        searchSuggestions.value = []
        searchTerm.value = ""
        searchLoc.value = "items"
        openSearch.value = true;
    }
    function onHoverGame(array, event) {
        if (array.length > 0) {
            const res = array.reduce((str, d) =>  str + `<div style="max-width: 165px">
                <div class="text-caption text-dots" style="max-width: 100%">${dataG[d[2]].name}</div>
                <image src="teaser/${dataG[d[2]].teaser}" width="160"/>
                <div class="text-caption">${dataG[d[2]].numMeta} meta_items</div>
                <div class="text-caption">${dataG[d[2]].allTags.length} tags</div>
                <div class="text-caption">${dataG[d[2]].numEvidence} evidence</div>
            </div>` , "")

            tt.show(`<div class="d-flex flex-wrap">${res}</div>`, event.pageX+10, event.pageY+10)
            connCacheG = array.map(d => d[2])
            connCacheE = null
            drawConnections(connCacheG);
        } else {
            tt.hide()
            connCacheG = null
            connCacheE = null
            drawConnections();
        }
    }
    function onClickGame(array, reset=false) {
        if (reset) {
            app.selectById(array.map(d => dataG[d[2]].id))
        } else {
            app.toggleSelectById(array.map(d => dataG[d[2]].id))
        }
    }
    function onClickGameColor(value) {
        switch(colorByG.value) {
            default:
                app.toggleSelectByGameValue("metas", d => d.metas.length > 0, value)
                break;
            case "cluster":
                app.toggleSelectByGameValue("cluster", d => d.metas.map(d => d.cluster), value)
                break;
            case "evidence":
                app.toggleSelectByGameValue("numEvidence", "numEvidence", value, FILTER_TYPES.RANGE_IN_EX)
                break;
            case "meta_items":
                app.toggleSelectByGameValue("numMeta", "numMeta", value, FILTER_TYPES.RANGE_IN_EX)
                break;
            case "tags":
                app.toggleSelectByGameValue("tags", d => d.allTags.length, value, FILTER_TYPES.RANGE_IN_EX)
                break;
        }
    }

    function openSearchExts() {
        searchSuggestions.value = []
        searchTerm.value = ""
        searchLoc.value = "meta_items"
        openSearch.value = true;
    }
    function onHoverExt(array, event) {
        if (array.length > 0) {
            const res = array.reduce((str, d) => {
                const game = dataG[gameMap.get(dataE[d[2]].item_id)]
                return str + `<div style="max-width: 250px">
                    <div class="d-flex justify-space-between mb-2">
                        <div class="text-caption">
                            <div><b>${dataE[d[2]].name}</b></div>
                            <div><i>${dataE[d[2]].cluster}</i></div>
                            <div>${dataE[d[2]].tags.length} tags</div>
                            <div>${dataE[d[2]].evidence.length} evidence</div>
                        </div>
                        <div class="ml-2">
                            <image src="teaser/${game.teaser}" width="80"/>
                            <div class="text-caption text-dots" style="max-width: 100px">${game.name}</div>
                        </div>
                    </div>
                    <p class="text-caption">${dataE[d[2]].description.length > 100 ? dataE[d[2]].description.slice(0, 200)+'..' : dataE[d[2]].description}</p>
                </div>`
            }, "")

            tt.show(`<div class="d-flex flex-wrap">${res}</div>`, event.pageX+10, event.pageY+10)
            connCacheE = array.map(d => d[2])
            connCacheG = null
            drawConnections(null, connCacheE);
        } else {
            tt.hide()
            connCacheG = null
            connCacheE = null
            drawConnections();
        }
    }
    function onClickExt(array, reset=false) {
        if (reset) {
            app.selectByExternalization(array.map(d => dataE[d[2]].id))
        } else {
            app.toggleSelectByExternalization(array.map(d => dataE[d[2]].id))
        }
    }
    function onClickExtColor(value) {
        switch(colorByE.value) {
            default:
            case "cluster":
                app.toggleSelectByExtValue("cluster", "cluster", value)
                break;
            case "evidence":
                app.toggleSelectByExtValue("evidence", d => d.evidence.length, value, FILTER_TYPES.RANGE_IN_EX)
                break;
            case "tags":
                app.toggleSelectByExtValue("tags", d => d.tags.length, value, FILTER_TYPES.RANGE_IN_EX)
                break;
        }
    }
    function onRightClickExt(array, event) {
        if (array.length === 0) {
            settings.setRightClick("meta_items", null)
        } else {
            const [mx, my] = d3.pointer(event, document.body)
            settings.setRightClick(
                "meta_items",
                dataE[array[0][2]].id,
                mx-150,
                my+10,
                null,
                CTXT_OPTIONS.meta_items
            )
        }
    }

    function checkEnter(event) {
        if (event.code === "Enter") {
            search()
        }
    }

    function updateSearchSuggestions() {
        searchSuggestions.value = getSearchMatches(searchLoc.value !== "items" ?
                d => d.name + ` (${dataG[gameMap.get(d.item_id)].name})` :
                "name"
        );
    }
    function getSearchMatches(attr="name", limit=5) {
        if (!searchTerm.value || searchTerm.value.length === 0) {
            return []
        }

        let matches;
        const regex = new RegExp(searchTerm.value, "i")
        if (searchLoc.value === "items") {
            matches = dataG
                .filter(d => regex.test(d.name))
                .map(d => typeof attr === "function" ? attr(d) : d[attr])
        } else {
            matches = dataE
                .filter(d => regex.test(d.name) || regex.test(d.cluster))
                .map(d => typeof attr === "function" ? attr(d) : d[attr])
        }

        matches.sort()

        return limit > 0 && matches.length > limit ?
            matches.slice(0, 5).concat([`... and ${matches.length-5} more`]) :
            matches
    }
    function search() {
        const matches = getSearchMatches("id", 0)
        openSearch.value = false;
        if (searchLoc.value === "items") {
            searchTermG.value = searchTerm.value;
            highlightG.value = matches.map(id => gameMap.get(id))
            timeG.value = Date.now()
        } else {
            searchTermE.value = searchTerm.value;
            highlightE.value = matches.map(id => extMap.get(id))
            timeE.value = Date.now()
        }
    }
    function cancelSearch() {
        openSearch.value = false;
    }


    function resetSelection() {
        app.selectById()
        app.selectByExternalization()
    }
    function resetHighlightG() {
        searchTermG.value = ""
        highlightG.value = []
        timeG.value = Date.now()
    }
    function resetHighlightE() {
        searchTermE.value = ""
        highlightE.value = []
        timeE.value = Date.now()
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
                .data(dataE.filter(d => indices.has(gameMap.get(d.item_id))).map(d => {
                    const idx = gameMap.get(d.item_id)
                    const gameP = scatterG.value.coords(idx)
                    const extP = scatterE.value.coords(extMap.get(d.id))
                    return [gameP, [size.value+18+extP[0], extP[1]]]
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
                    const idx = gameMap.get(d.item_id)
                    const gameP = scatterG.value.coords(idx)
                    const extP = scatterE.value.coords(extMap.get(d.id))
                    return [gameP, [size.value+18+extP[0], extP[1]]]
                }))
                .join("path")
                .attr("d", path)
                .attr("stroke", "red")
                .attr("stroke-width", 2)
        }
    }

    function init() {
        readDefaults()
        if (!props.hidden) {
            loadOnShow = false;
            readGames()
            readExts()
            readSelected();
            calculateDR();
        } else {
            loadOnShow = true;
        }
    }
    function readDefaults() {
        const sg = Cookies.get("ee-settings-g")
        const se = Cookies.get("ee-settings-e")
        if (sg) Object.assign(defaultsG, JSON.parse(sg))
        if (se) Object.assign(defaultsE, JSON.parse(se))
    }
    function initGames() {
        if (!props.hidden) {
            loadOnShow = false;
            readGames()
            readSelected();
            calculateGamesDR();
        } else {
            loadOnShow = true;
        }
    }
    function initExts() {
        if (!props.hidden) {
            loadOnShow = false;
            readExts()
            readSelected();
            calculateExtsDR();
        } else {
            loadOnShow = true;
        }
    }

    onMounted(init)

    watch(() => props.width, function() {
        drawConnections(connCacheG, connCacheE)
        setTimeout(() => {
            refreshG.value = Date.now()
            refreshE.value = Date.now()
        }, 150)
    })
    watch(() => Math.max(times.f_meta_items, times.f_items), readSelected)
    watch(() => times.all, init)
    watch(() => Math.max(times.items, times.tagging, times.datatags), initGames)
    watch(() => times.meta_items, initExts)
    watch(() => props.hidden, function(hidden) {
        if (!hidden && loadOnShow) {
            init()
        }
    })
</script>