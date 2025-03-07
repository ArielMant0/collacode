<template>
    <div ref="el" style="width: 100%;">
        <div v-if="state === STATES.START" class="d-flex align-center justify-center" style="height: 80vh;">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>

        <div v-else-if="state === STATES.LOADING" class="d-flex align-center justify-center" style="height: 80vh;">
            <div class="game-loader"></div>
        </div>

        <div v-else-if="state === STATES.INGAME" class="d-flex flex-column align-center">

            <v-sheet v-if="numQuestion <= maxQuestions"
                style="font-size: large;"
                class="mt-4 mb-4 pt-4 pb-4 pr-8 pl-8"
                rounded="sm"
                :color="maxQuestions-numQuestion < 2 ? '#ed5a5a' : 'surface-light'">
                Question {{ numQuestion }} / {{ maxQuestions }}
            </v-sheet>

            <div class="d-flex flex-column align-center" style="width: 100%;">

                <div class="d-flex justify-center align-center mb-4">

                    <div class="d-flex justify-center align-center mr-2 pa-2 pl-4 pr-4" style="border: 2px solid #efefef; border-radius: 5px;">
                        <div>
                            Does the {{ app.itemName }} have
                            {{ logic.askTag && logic.askTag.is_leaf == 1 ? 'tag' : 'tags from' }}
                            <b>{{ logic.askTag ? logic.askTag.name : '...' }}</b> ?
                        </div>
                        <v-btn class="ml-4" :color="logic.askTag === null?'default':'primary'" :disabled="logic.askTag === null" @click="askTag">ask</v-btn>
                    </div>

                    <div class="d-flex justify-center align-center ml-2 pa-2 pl-4 pr-4" style="border: 2px solid #efefef; border-radius: 5px;">
                        <div>
                            Is it <b>{{ logic.askItem ? logic.askItem.name : '...' }}</b> ?
                        </div>
                        <v-btn class="ml-4" :color="logic.askItem === null?'default':'primary'" :disabled="logic.askItem === null" @click="stopGame">ask</v-btn>
                    </div>
                </div>

                <div class="d-flex justify-space-between" style="width: 100%;">

                    <div :style="{ width: itemsWidth+'px', maxWidth: itemsWidth+'px' }">

                        <div class="d-flex align-center">
                            <v-text-field v-model="search"
                                :label="'Search for '+app.itemName+'s'"
                                prepend-inner-icon="mdi-magnify"
                                variant="outlined"
                                density="compact"
                                class="mb-1"
                                clearable
                                hide-details
                                single-line/>

                            <v-tooltip text="clear selection" location="top" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-btn v-bind="props"
                                        icon="mdi-delete"
                                        class="ml-1"
                                        color="error"
                                        rounded="sm"
                                        variant="text"
                                        density="compact"
                                        @click="logic.excluded.clear()"/>
                                </template>
                            </v-tooltip>

                            <v-tooltip text="clear selection" location="top" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-btn v-bind="props"
                                        :icon="showImages ? 'mdi-image' : 'mdi-image-off'"
                                        class="ml-1"
                                        rounded="sm"
                                        variant="text"
                                        density="compact"
                                        @click="showImages = !showImages"/>
                                </template>
                            </v-tooltip>
                        </div>

                        <ScatterPlot v-if="points.length > 0"
                            ref="scatter"
                            :data="pointsFiltered"
                            :selected="selectedItems"
                            :refresh="refresh"
                            :time="time"
                            selectable
                            selected-color="white"
                            hide-axes
                            x-attr="0"
                            y-attr="1"
                            id-attr="2"
                            url-attr="3"
                            fill-attr="4"
                            :radius="4"
                            :search-radius="15"
                            :grid="showImages"
                            @hover="onHoverItem"
                            @click="onClickItem"
                            @right-click="onRightClickItem"
                            @lasso="onLasso"
                            :width="itemsWidth"
                            :height="itemsWidth"
                            :fill-color-scale="['#555', '#0acb99']"
                            :fill-color-bins="0"/>

                    </div>

                    <TreeMap v-if="tags.length > 0"
                        :data="tags"
                        :time="time"
                        :width="treeWidth"
                        :height="treeHeight"
                        collapsible
                        :selected="gameData.tagsYes"
                        :frozen="gameData.tagsNo"
                        frozen-color="#e02d2d"
                        hide-color-filter
                        @click="setAskTag"
                        />
                </div>
            </div>
        </div>

        <div v-else-if="state === STATES.END" class="d-flex flex-column align-center justify-center mt-8" style="min-height: 50vh;">

            <div class="d-flex">
                <div v-if="logic.askItem">
                    <div><b>Your Guess:</b></div>
                    <v-sheet class="ma-1" rounded="sm" style="text-align: center;">
                        <v-img
                            cover
                            :src="logic.askItem.teaser ? 'teaser/'+logic.askItem.teaser : imgUrlS"
                            :lazy-src="imgUrlS"
                            :width="imageWidth*2"
                            :height="imageWidth"/>
                        <div>{{ logic.askItem.name }}</div>
                    </v-sheet>
                </div>

                <div>
                    <b>The Solution:</b>
                    <v-sheet class="ma-1" rounded="sm" style="text-align: center;">
                        <v-img
                            cover
                            :src="gameData.target.teaser ? 'teaser/'+gameData.target.teaser : imgUrlS"
                            :lazy-src="imgUrlS"
                            :width="imageWidth*2"
                            :height="imageWidth"/>
                        <div>{{ gameData.target.name }}</div>
                    </v-sheet>
                </div>
            </div>

            <v-sheet class="mt-8 d-flex align-center">
                <v-icon
                    size="60"
                    class="mr-4"
                    :icon="answerCorrect ? 'mdi-check-bold' : 'mdi-close-circle-outline'"
                    :color="answerCorrect ? 'primary' : 'error'"/>

                <span v-if="answerCorrect">Yay, you found the right game!</span>
                <span v-else>Wrong, maybe next time ...</span>
            </v-sheet>

            <div class="d-flex align-center justify-center" style="margin-top: 200px;">
                <v-btn class="mr-1" size="x-large" color="error" @click="close">close</v-btn>
                <v-btn class="ml-1" size="x-large" color="primary" @click="startGame">play again</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import * as druid from '@saehrimnir/druidjs';
    import { SOUND, useGames } from '@/store/games';
    import { useTimes } from '@/store/times';
    import { computed, onMounted, reactive, toRaw, watch } from 'vue';
    import { Chance } from 'chance';
    import imgUrlS from '@/assets/__placeholder__s.png'
    import DM from '@/use/data-manager';
    import { useElementSize, useWindowSize } from '@vueuse/core';
    import TreeMap from '../vis/TreeMap.vue';
    import { sortObjByString } from '@/use/sorting';
    import { useApp } from '@/store/app';
    import { POSITION, useToast } from 'vue-toastification';
    import ScatterPlot from '../vis/ScatterPlot.vue';
    import Cookies from 'js-cookie';
    import { getMetric } from '@/use/metrics';
    import { useTooltip } from '@/store/tooltip';

    const STATES = Object.freeze({
        START: 0,
        LOADING: 1,
        INGAME: 2,
        END: 3
    })

    const props = defineProps({
        maxQuestions: {
            type: Number,
            default: 10
        },
        imageWidth:  {
            type: Number,
            default: 160
        },
    })

    const emit = defineEmits(["end"])

    // stores
    const games = useGames()
    const times = useTimes()
    const toast = useToast()
    const app = useApp()
    const tt = useTooltip()

    // elements
    const el = ref(null)
    const elSize = useElementSize(el)
    const wSize = useWindowSize()

    const itemsWidth = computed(() => Math.max(500, elSize.width.value * 0.425))
    const treeWidth = computed(() => Math.max(400, elSize.width.value - itemsWidth.value - 30))
    const treeHeight = computed(() => Math.max(800, wSize.height.value * 0.80))

    // optics and settings

    const needsReload = ref(false)
    const showImages = ref(true)

    const time = ref(0)
    const refresh = ref(0)

    let dataItems, matrix;
    const defaultsG = reactive({ perplexity: 20, method: 'TSNE', metric: 'cosine' })

    const points = ref([])
    const pointsFiltered = computed(() => {
        if (state.value !== STATES.END && gameData.targetIndex !== null) {
            return points.value.filter((_, i) => i !== gameData.targetIndex)
        }
        return points.value
    })

    // game related stuff
    const state = ref(STATES.START)
    const gameData = reactive({
        target: null,
        targetIndex: null,
        tagsAsked: [],
        tagsYes: [],
        tagsNo: [],
    })
    const logic = reactive({
        askTag: null,
        askItem: null,
        history: [],
        excluded: new Set()
    })
    const selectedItems = computed(() => {
        if (logic.excluded.size === 0) {
            return []
        }
        return points.value.filter(d => !logic.excluded.has(d[2])).map(d => d[2])
    })
    const answerCorrect = computed(() => logic.askItem && gameData.target ? logic.askItem.id === gameData.target.id : false)

    const tags = ref([])
    const search = ref("")
    const numQuestion = ref(0)

    ///////////////////////////////////////////////////////////////////////////
    // Functions
    ///////////////////////////////////////////////////////////////////////////

    function setAskItem(item) {
        logic.askItem = logic.askItem && logic.askItem.id === item.id ? null : item;
    }

    function setAskTag(tag) {
        logic.askTag = logic.askTag && logic.askTag.id === tag.id ? null : tag;
    }
    function askTag() {
        if (logic.askTag && gameData.target) {
            const tid = logic.askTag.id;
            const isLeaf = logic.askTag.is_leaf === 1
            const hasTag = gameData.target.allTags.find(d => isLeaf ? d.id === tid : d.path.includes(tid)) !== undefined
            logic.history.push({
                id: tid,
                name: logic.askTag.name,
                result: hasTag
            })
            if (hasTag) {
                gameData.tagsYes.push(tid)
            } else {
                gameData.tagsNo.push(tid)
            }

            if (numQuestion.value > props.maxQuestions) {
                stopGame()
            } else {
                logic.askTag = null;
                if (hasTag) {
                    toast.success("Correct!", { position: POSITION.TOP_CENTER, timeout: 2000 })
                    games.playSingle(SOUND.WIN)
                } else {
                    toast.error("Wrong!", { position: POSITION.TOP_CENTER, timeout: 2000 })
                    games.playSingle(SOUND.FAIL)
                }
                numQuestion.value++
            }
        }
    }

    function startGame() {
        const starttime = Date.now()
        games.playSingle(SOUND.START)
        state.value = STATES.LOADING
        // reset these values
        clear()
        // recalculate if necessary
        if (needsReload.value) {
            calculateEmbedding()
        }

        const chance = new Chance()
        const idx = chance.integer({ min: 0, max: dataItems.length-1 })

        gameData.target = dataItems[idx]
        gameData.targetIndex = idx

        setTimeout(() => {
            numQuestion.value = 1;
            state.value = STATES.INGAME
            time.value = Date.now()
        }, Date.now() - starttime < 500 ? 1000 : 50)
    }

    function stopGame() {
        state.value = STATES.END;
        if (answerCorrect.value) {
            games.playSingle(SOUND.WIN)
        } else {
            games.playSingle(SOUND.FAIL)
        }
    }

    function close() {
        reset()
        emit("end")
    }

    function clear() {
        search.value = ""
        numQuestion.value = 0;
        gameData.target = null
        gameData.targetIndex = null
        gameData.tagsAsked = []
        gameData.tagsYes = []
        gameData.tagsNo = []
        logic.askTag = null;
        logic.askItem = null
        logic.history = []
        logic.excluded.clear()
    }
    function reset(recalculate=true) {
        needsReload.value = false
        state.value = STATES.START;
        clear()
        if (recalculate) {
            calculateEmbedding()
        }
    }

    function onClickItem(array) {
        if (array.length > 0) {
            setAskItem(dataItems[array[0][2]])
        }
    }
    function onRightClickItem(array) {
        if (array.length > 0) {
            const index = array[0][2]
            if (logic.excluded.has(index)) {
                logic.excluded.delete(index)
            } else {
                logic.excluded.add(index)
            }
            time.value = Date.now()
        }
    }
    function onLasso(array) {
        if (array.length > 0) {
            const set = new Set(logic.excluded)
            array.forEach(d => {
                if (set.has(d[2])) {
                    set.delete(d[2])
                } else {
                    set.add(d[2])
                }
            })
            logic.excluded = set
            time.value = Date.now()
        }
    }
    function onHoverItem(array, event) {
        if (array.length > 0) {
            const [mx, my] = d3.pointer(event, document.body)
            const res = array.reduce((str, d) =>  str + `<div style="max-width: 165px">
                <div class="text-caption text-dots" style="max-width: 100%">${dataItems[d[2]].name}</div>
                <img src="teaser/${dataItems[d[2]].teaser}" width="160"/>
            </div>` , "")

            tt.show(`<div class="d-flex flex-wrap" style="max-width: 330px">${res}</div>`, mx, my)
        } else {
            tt.hide()
        }
    }

    function readDefaults() {
        const sg = Cookies.get("ee-settings-g")
        if (sg) Object.assign(defaultsG, JSON.parse(sg))
    }
    function readData() {
        readDefaults()

        dataItems = DM.getDataBy("items", d => d.allTags.length > 0)
        dataItems.sort(sortObjByString("name"))

        const allTags = DM.getDataBy("tags", d => d.is_leaf === 1)
        allTags.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return a.path.length - b.path.length
        });
        const idToIdx = new Map()
        allTags.forEach((d, i) => idToIdx.set(d.id, i))

        const p = new Array(dataItems.length)
        dataItems.forEach((d, i) => {
            const arr = new Array(allTags.length)
            arr.fill(0)
            d.allTags.forEach(t => {
                const nev = d.evidence.filter(d => d.tag_id === t.id)
                arr[idToIdx.get(t.id)] = nev.length > 0 ? nev.length : 1
            })
            p[i] = arr;
        });
        tags.value = DM.getData("tags", false);
        matrix = dataItems.length > 0 ? druid.Matrix.from(p) : []
    }
    function getEmbedding() {
        const params = Object.assign({}, defaultsG)
        params.metric = getMetric(params.metric)
        const method = params.method;
        delete params.method

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
    function calculateEmbedding() {
        readData()
        const dr = getEmbedding()
        if (!dr) return
        points.value = Array.from(dr.transform()).map((d,i) => ([d[0], d[1], i, "teaser/"+dataItems[i].teaser, i === gameData.targetIndex ? 2 : 1]))
        refresh.value = Date.now();
    }

    onMounted(function() {
        reset()
        startGame()
    })

    watch(() => Math.max(times.all, times.items, times.tags), () => needsReload.value = true)

</script>