<template>
    <div>
        <div v-if="state === STATES.START" class="d-flex align-center justify-center" style="height: 80vh;">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>

        <div v-else-if="state === STATES.LOADING" class="d-flex align-center justify-center" style="height: 80vh;">
            <div class="game-loader"></div>
        </div>

        <div v-else class="d-flex flex-column align-center">

            <Timer ref="timer" :time-in-sec="timeInSec" @end="stopGame"/>

            <div v-if="state === STATES.END" style="width: 80%;" class="d-flex justify-center">
                <div style="width: max-content;">
                    <MiniTree :node-width="5" :selectable="false"/>
                    <br/>
                    <BarCode
                        :data="gameData.target ? gameData.target.allTags : []"
                        :domain="barDomain"
                        hide-highlight
                        binary
                        selectable
                        id-attr="id"
                        name-attr="name"
                        value-attr="id"
                        selected-color="red"
                        @right-click="openTagContext"
                        :binary-color-fill="settings.lightMode ? '#000000' : '#ffffff'"
                        :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                        :width="5"
                        :height="20"/>
                    </div>
            </div>

            <div class="d-flex align-start justify-center mt-4" style="width: 80%;">

                <div class="d-flex flex-column align-start mr-4">
                    <div class="d-flex flex-column align-center">
                        <div style="font-size: large; max-width: 160px;" class="text-dots" :title="gameData.target.name">{{ gameData.target.name }}</div>
                        <ItemTeaser v-if="state === STATES.END" :item="gameData.target" :width="160" :height="80"/>
                        <v-img v-else
                            cover
                            :src="gameData.target.teaser ? 'teaser/'+gameData.target.teaser : imgUrlS"
                            :lazy-src="imgUrlS"
                            :width="160"
                            :height="80"/>
                    </div>
                    <div v-if="state === STATES.END" class="mt-8" style="font-size: large; width: 100%; text-align: center;">
                        <div>Distance</div>
                        <div><b>{{ gameData.distance }}</b></div>
                    </div>

                </div>

                <div style="position: relative; border: 1px solid #efefef;">
                    <ScatterPlot v-if="points.length > 0"
                        ref="scatter"
                        :data="pointsFiltered"
                        :refresh="refresh"
                        :time="time"
                        :highlighted="visitedList"
                        :highlighted-color="visitedColor"
                        :highlighted-bandwidth="4"
                        selectable
                        @right-click="openItemContext"
                        hide-axes
                        x-attr="0"
                        y-attr="1"
                        id-attr="2"
                        url-attr="3"
                        fill-attr="4"
                        :radius="4"
                        :search-radius="20"
                        :width="size"
                        :height="size"
                        :fill-color-scale="[dotColor, '#0acb99']"
                        :fill-color-bins="0"
                        @click="onClickPlot"
                        @hover="onHoverItem"/>

                    <svg ref="el" :width="size" :height="size" style="pointer-events: none; position: absolute; top: 0; left: 0;"></svg>
                </div>
            </div>

            <div v-if="state === STATES.INGAME">
                <v-btn size="x-large" color="primary" class="mt-4" @click="stopGame" :disabled="gameData.posX === null || gameData.posY === null">submit</v-btn>
            </div>
            <div v-else-if="state === STATES.END" class="d-flex align-center justify-center mt-4">
                <v-btn class="mr-1" size="x-large" color="error" @click="close">close</v-btn>
                <v-btn class="ml-1" size="x-large" color="primary" @click="startGame">play again</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import * as druid from '@saehrimnir/druidjs';
    import { DIFFICULTY } from '@/store/games';
    import { useTimes } from '@/store/times';
    import { euclidean, getMetric } from '@/use/metrics';
    import { computed, onMounted, reactive, watch } from 'vue';
    import { Chance } from 'chance';
    import ScatterPlot from '../vis/ScatterPlot.vue';
    import { useTooltip } from '@/store/tooltip';
    import imgUrlS from '@/assets/__placeholder__s.png'
    import Cookies from 'js-cookie';
    import DM from '@/use/data-manager';
    import Timer from './Timer.vue';
    import { useTheme } from 'vuetify/lib/framework.mjs';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import MiniTree from '../vis/MiniTree.vue';
    import BarCode from '../vis/BarCode.vue';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import { useSounds, SOUND } from '@/store/sounds';

    const STATES = Object.freeze({
        START: 0,
        LOADING: 1,
        INGAME: 2,
        END: 3
    })

    const DLEVELS = Object.freeze({
        CLOSE: 0,
        NEAR: 1,
        FAR: 2
    })

    const props = defineProps({
        difficulty: {
            type: Number,
            required: true
        },
        size: {
            type: Number,
            default: 800
        },
    })

    const emit = defineEmits(["end", "close"])

    // difficulty settings
    const timeInSec = computed(() => {
        switch (props.difficulty) {
            case DIFFICULTY.EASY: return 300;
            case DIFFICULTY.NORMAL: return 180;
            case DIFFICULTY.HARD: return 60;
        }
    })

    // stores
    const sounds = useSounds()
    const times = useTimes()
    const tt = useTooltip()
    const theme = useTheme()
    const settings = useSettings()

    // elements
    const el = ref(null)
    const scatter = ref(null)

    // game related stuff
    const state = ref(STATES.START)
    const gameData = reactive({
        target: null,
        targetId: null,
        targetIndex: null,
        posX: null,
        posY: null,
        clickX: null,
        clickY: null,
        targetX: null,
        targetY: null,
        distance: 0,
        distanceLevel: null,
        color: "#078766"
    })
    const visited = reactive(new Set())
    const visitedList = computed(() => Array.from(visited.values()))

    const dotColor = computed(() => settings.lightMode ? "#555" : '#bbb')
    const visitedColor = computed(() => theme.current.value.colors.primary)

    const barDomain = ref()

    const timer = ref(null)

    // embedding related stuff
    const needsReload = ref(false)
    const defaultsG = reactive({ perplexity: 20, method: 'TSNE', metric: 'cosine' })

    let dataItems, matrix;

    const points = ref([])
    const pointsFiltered = computed(() => {
        if (state.value !== STATES.END && gameData.targetIndex !== null) {
            return points.value.filter((_, i) => i !== gameData.targetIndex)
        }
        return points.value
    })
    const time = ref(0)
    const refresh = ref(0)

    function openTagContext(tag, event, has) {
        const [x, y] = d3.pointer(event, document.body)
        const action = has ? OBJECTION_ACTIONS.REMOVE : OBJECTION_ACTIONS.ADD
        settings.setRightClick(
            "tag", tag.id,
            x, y,
            tag.name,
            { item: gameData.target.id, action: action },
            CTXT_OPTIONS.items
        )
    }
    function openItemContext(list, event) {
        if (list.length === 0) {
            settings.setRightClick("item", null)
        } else {
            const it = dataItems[list[0][2]]
            if (!it) return
            const [x, y] = d3.pointer(event, document.body)
            settings.setRightClick(
                "item", it.id,
                x, y,
                it.name,
                null,
                CTXT_OPTIONS.items
            )
        }
    }

    function startTimer() {
        if (timer.value) {
            timer.value.start()
        } else {
            setTimeout(startTimer, 50)
        }
    }

    function startGame() {
        const starttime = Date.now()
        sounds.play(SOUND.START)
        state.value = STATES.LOADING
        if (needsReload.value) {
            calculateEmbedding().then(() => startRound(starttime))
        } else {
            startRound(starttime)
        }

    }
    function startRound(starttime)  {
        // reset these values
        clear()

        const chance = new Chance()
        const idx = chance.integer({ min: 0, max: dataItems.length-1 })
        gameData.targetIndex = idx;
        gameData.target = dataItems[idx]
        gameData.targetId = dataItems[idx].id

        setTimeout(() => {
            state.value = STATES.INGAME
            startTimer()
            drawIndicator()
        }, Date.now() - starttime < 500 ? 1000 : 50)
    }

    function stopGame() {
        timer.value.stop()
        state.value = STATES.END;
        refresh.value = Date.now();
        setTimeout(() => {

            const pos = scatter.value.coords(gameData.targetIndex)
            gameData.targetX = pos[0]
            gameData.targetY = pos[1]
            if (gameData.clickX !== null && gameData.clickY !== null) {
                gameData.distance = Math.floor(euclidean(
                    [gameData.targetX, gameData.targetY],
                    [gameData.clickX, gameData.clickY]
                ))
            } else {
                gameData.distance = Infinity
            }
            gameData.distanceLevel = getDistanceLevel(gameData.distance)
            switch(gameData.distanceLevel) {
                case DLEVELS.CLOSE:
                    sounds.play(SOUND.WIN)
                    break;
                case DLEVELS.NEAR:
                    sounds.play(SOUND.MEH)
                    break;
                case DLEVELS.FAR:
                    sounds.play(SOUND.FAIL)
                    break;
            }
            drawDistance()
            emit("end", gameData.distanceLevel === DLEVELS.CLOSE, [gameData.target.id])

        }, 150)
    }

    function close() {
        d3.select(el.value).selectAll("*").remove()
        emit("close")
        reset(false)
    }

    function getDistanceLevel(distance) {
        if (distance < Math.max(distance / props.size, 50)) {
            return DLEVELS.CLOSE
        } else if (distance < Math.max(distance / props.size, 125)) {
            return DLEVELS.NEAR
        }
        return DLEVELS.FAR
    }

    function drawDistance() {
        const svg = d3.select(el.value)
        svg
            .selectAll("line")
            .data(gameData.clickX !== null && gameData.clickY !== null ? [gameData.target] : [])
            .join("line")
            .attr("x1", gameData.clickX)
            .attr("y1", gameData.clickY)
            .attr("x2", gameData.targetX)
            .attr("y2", gameData.targetY)
            .attr("stroke-width", 3)
            .attr("stroke-dasharray", "4 1")
            .attr("stroke", gameData.color)
    }
    function drawIndicator() {
        const svg = d3.select(el.value)

        svg
            .selectAll(".lens")
            .data(gameData.posX !== null && gameData.posY !== null ? [gameData.target] : [])
            .join("circle")
            .classed("lens", true)
            .attr("cx", gameData.posX)
            .attr("cy", gameData.posY)
            .attr("r", 20)
            .attr("fill", "none")
            .attr("stroke-width", 2)
            .attr("stroke", gameData.color)
        svg
            .selectAll(".indicator")
            .data(gameData.posX !== null && gameData.posY !== null ? [gameData.target] : [])
            .join("circle")
            .classed("indicator", true)
            .attr("cx", gameData.posX)
            .attr("cy", gameData.posY)
            .attr("r", 6)
            .attr("fill", "none")
            .attr("stroke-width", 4)
            .attr("stroke", settings.lightMode ? "black" : "white")

        svg
            .selectAll(".choice")
            .data(gameData.clickX !== null && gameData.clickY !== null ? [gameData.target] : [])
            .join("circle")
            .classed("choice", true)
            .attr("cx", gameData.clickX)
            .attr("cy", gameData.clickY)
            .attr("r", 6)
            .attr("stroke", settings.lightMode ? "black" : "white")
            .attr("stroke-width", 1)
            .attr("fill", gameData.color)
    }

    function onClickPlot(_array, event) {
        const [sx, sy] = d3.pointer(event, el.value)
        gameData.posX = sx;
        gameData.posY = sy;
        gameData.clickX = sx;
        gameData.clickY = sy;
        drawIndicator()
        sounds.play(SOUND.PLOP)
    }
    function onHoverItem(array, event) {
        const [sx, sy] = d3.pointer(event, el.value)
        gameData.posX = sx;
        gameData.posY = sy;
        drawIndicator()
        if (array.length > 0) {
            if (state.value === STATES.INGAME) {
                array.forEach(d => visited.add(d[2]))
            }
            const [mx, my] = d3.pointer(event, document.body)
            const res = array.reduce((str, d) =>  str + `<div style="max-width: 165px" class="mr-1 mb-1">
                <div class="text-caption text-dots" style="max-width: 100%">${dataItems[d[2]].name}</div>
                <img src="teaser/${dataItems[d[2]].teaser}" width="160"/>
            </div>` , "")

            tt.show(`<div class="d-flex flex-wrap" style="max-width: 350px">${res}</div>`, mx, my)
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

        barDomain.value = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)


        const p = new Array(dataItems.length)
        dataItems.forEach((d, i) => {
            const arr = new Array(tags.length)
            arr.fill(0)
            d.allTags.forEach(t => {
                const nev = d.evidence.filter(d => d.tag_id === t.id)
                arr[idToIdx.get(t.id)] = nev.length > 0 ? nev.length : 1
            })
            p[i] = arr;
        });
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
    async function calculateEmbedding() {
        readData()
        const dr = getEmbedding()
        if (!dr) return
        const proj = await dr.transform_async()
        points.value = Array.from(proj).map((d,i) => ([d[0], d[1], i, "teaser/"+dataItems[i].teaser, i === gameData.targetIndex ? 2 : 1]))
        refresh.value = Date.now();
    }

    function clear() {
        if (el.value) {
            d3.select(el.value).selectAll("*").remove()
        }
        visited.clear()
        gameData.targetIndex = null;
        gameData.targetId = null;
        gameData.target = null;
        gameData.clickX = null;
        gameData.clickY = null;
        gameData.posX = null;
        gameData.posY = null;
    }
    function reset(recalculate=true) {
        sounds.fadeAll()
        needsReload.value = false;
        state.value = STATES.START;
        if (timer.value) {
            timer.value.stop()
        }
        clear()
        if (recalculate) {
            calculateEmbedding()
        }
    }

    onMounted(function() {
        reset()
        startGame()
    })

    watch(props, function() {
        reset()
        startGame()
    }, { deep: true })

    watch(() => Math.max(times.all, times.items), () => needsReload.value = true)

</script>