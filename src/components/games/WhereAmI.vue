<template>
    <div>
        <div v-if="state === STATES.START" class="d-flex align-center justify-center" style="height: 80vh;">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>

        <div v-else-if="state === STATES.LOADING"class="d-flex align-center justify-center">
            <LoadingScreen
                :messages="[
                    'you can pin items by right-clicking them',
                    'in hard mode, you can only hover over each item <b>once<b>',
                    'place your guess by clicking on the plot',
                ]"/>
        </div>

        <div v-else class="d-flex flex-column align-center">

            <Timer v-if="state === STATES.INGAME" ref="timer" :time-in-sec="timeInSec" @end="stopGame"/>
            <v-sheet v-else-if="state === STATES.EXCLUDE" style="font-size: x-large;" class="mb-4 pt-4 pb-4 pr-8 pl-8" rounded="sm" color="surface-light">
                Do you accept this {{ app.itemName }}?
            </v-sheet>
            <div v-else-if="state === STATES.END" style="width: 80%;" class="d-flex justify-center">
                <div style="width: max-content;">
                    <MiniTree :node-width="nodeWidth" :selectable="false"/>
                    <br/>
                    <BarCode
                        :item-id="gameData.targetId"
                        :data="barData"
                        :domain="barDomain"
                        hide-highlight
                        binary
                        selectable
                        id-attr="id"
                        name-attr="name"
                        value-attr="id"
                        desc-attr="desc"
                        selected-color="red"
                        @right-click="openTagContext"
                        :binary-color-fill="settings.lightMode ? '#000000' : '#ffffff'"
                        :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                        :width="nodeWidth"
                        :height="20"/>
                    </div>
            </div>


            <div class="d-flex align-start justify-center mt-4" style="width: 80%;">

                <div class="d-flex flex-column align-start mr-4">
                    <div class="d-flex flex-column align-center">
                        <div style="font-size: large; max-width: 160px;" class="text-dots" :title="gameData.target.name">{{ gameData.target.name }}</div>
                        <ItemTeaser
                            :item="gameData.target"
                            :prevent-click="state !== STATES.END"
                            :width="160"
                            :height="80"/>

                        <div v-if="allowExclude && state === STATES.EXCLUDE" class="mt-4" style="width: 160px;">
                            <v-btn
                                color="error"
                                density="compact"
                                block
                                @click="excludeItem(gameData.target.id)"
                                class="text-caption">
                                exclude item
                            </v-btn>

                            <v-btn
                                color="primary"
                                density="compact"
                                block
                                @click="startRound"
                                class="mt-1 text-caption">
                                accept item
                            </v-btn>
                        </div>

                    </div>

                    <div v-if="state === STATES.END" class="mt-8 d-flex flex-column align-center" style="font-size: large; width: 100%;">
                        <div>Distance</div>
                        <div><b>{{ gameData.distance }}</b></div>
                        <GameResultIcon v-if="gameData.result !== null"
                            :result="gameData.result"
                            class="mt-2"
                            show-effects
                            show-text
                            hide-icon
                            :effects-width="160" :effects-height="80"/>
                    </div>
                </div>

                <div v-if="state === STATES.INGAME || state === STATES.END" class="d-flex align-start justify-start">

                    <div>
                        <div style="text-align: center; width: 125px">
                            {{ selectedLeft.length }} / {{ maxPins }} pins
                        </div>
                        <div
                            style="position: relative; width: 125px;"
                            :style="{ height: (size+10)+'px' }"
                            class="ml-1 mr-1 bg-surface-light">

                            <v-sheet v-for="s in selectedLeft"
                                :key="'l_'+s.id"
                                :style="{ position: 'absolute', top: (s.index*90)+'px' }"
                                @click="removeSelected(s.id)"
                                rounded="sm"

                                class="pa-1 cursor-pointer secondary-on-hover">
                                <div style="max-width: 120px;" class="text-caption text-dots" :title="s.name">{{ s.name }}</div>
                                <v-img
                                    cover
                                    :src="s.teaser ? mediaPath('teaser', s.teaser) : imgUrlS"
                                    :lazy-src="imgUrlS"
                                    :width="120"
                                    :height="60"/>
                            </v-sheet>
                        </div>
                    </div>

                    <div>
                        <div style="min-height: 1.5em;"></div>
                        <div style="position: relative; border: 1px solid #efefef;" @pointerleave="clearIndicator">
                            <canvas ref="underlay" :width="size" :height="size"></canvas>
                            <ScatterPlot v-if="points.length > 0"
                                ref="scatter"
                                style="position: absolute; top: 0; left: 0;"
                                :data="pointsFiltered"
                                :refresh="refresh"
                                :time="time"
                                :highlighted="visitedList"
                                :highlighted-color="visitedColor"
                                :highlighted-bandwidth="4"
                                selectable
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
                                :fill-domain="[1, 2, 3]"
                                :fill-color-scale="[dotColor, '#0acb99', visitedDotColor]"
                                :fill-color-bins="0"
                                @click="onClickPlot"
                                @right-click="onRightClickPlot"
                                @hover="onHoverItem"/>

                            <svg ref="el" :width="size" :height="size" style="pointer-events: none; position: absolute; top: 0; left: 0;"></svg>
                        </div>
                    </div>

                    <div>
                        <div style="text-align: center; width: 125px">
                            {{ selectedRight.length }} / {{ maxPins }} pins
                        </div>
                        <div
                            style="position: relative; width: 125px;"
                            :style="{ height: (size+10)+'px' }"
                            class="ml-1 mr-1 bg-surface-light">

                            <v-sheet v-for="s in selectedRight"
                                :key="'r_'+s.id"
                                :style="{ position: 'absolute', top: (s.index*90)+'px' }"
                                @click="removeSelected(s.id)"
                                rounded="sm"
                                class="pa-1 cursor-pointer secondary-on-hover">
                                <div style="max-width: 120px;" class="text-caption text-dots" :title="s.name">{{ s.name }}</div>
                                <v-img
                                    cover
                                    :src="s.teaser ? mediaPath('teaser', s.teaser) : imgUrlS"
                                    :lazy-src="imgUrlS"
                                    :width="120"
                                    :height="60"/>
                            </v-sheet>
                        </div>
                    </div>

                </div>
                <div v-else class="d-flex align-start justify-start">
                    <div style="width: 125px; min-height: 200px;" class="ml-1 mr-1"></div>
                    <div style="border: 1px solid #efefef;" :style="{ width: size+'px', height: size+'px' }"></div>
                    <div style="width: 125px; min-height: 200px" class="ml-1 mr-1"></div>
                </div>

            </div>

            <div v-if="state === STATES.INGAME" class="mt-4">
                <v-btn size="large" color="error" @click="resetVisited">reset highlight</v-btn>
                <v-btn size="large" color="primary" class="ml-1" @click="stopGame" :disabled="gameData.clickX === null || gameData.clickY === null">submit</v-btn>
            </div>
            <div v-else-if="state === STATES.END" class="d-flex align-center justify-center mt-4">
                <v-btn class="mr-1" size="large" color="error" @click="close">close game</v-btn>
                <v-btn class="ml-1" size="large" color="primary" @click="startGame">play again</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import * as druid from '@saehrimnir/druidjs';

    import { DIFFICULTY, GAME_RESULT, STATES, useGames } from '@/store/games';
    import { useTimes } from '@/store/times';
    import { useSounds, SOUND } from '@/store/sounds';
    import { useToast } from 'vue-toastification';
    import { useTooltip } from '@/store/tooltip';
    import { OBJECTION_ACTIONS, useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';

    import { useTheme } from 'vuetify/lib/framework.mjs';
    import { euclidean, getMetric } from '@/use/metrics';
    import { computed, onMounted, reactive, watch } from 'vue';
    import ScatterPlot from '../vis/ScatterPlot.vue';
    import Cookies from 'js-cookie';
    import DM from '@/use/data-manager';
    import Timer from './Timer.vue';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import MiniTree from '../vis/MiniTree.vue';
    import BarCode from '../vis/BarCode.vue';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import { useWindowSize } from '@vueuse/core';
    import { randomChoice, randomInteger } from '@/use/random';

    import imgUrlS from '@/assets/__placeholder__s.png'
    import GameResultIcon from './GameResultIcon.vue';
    import LoadingScreen from './LoadingScreen.vue';
    import { mediaPath } from '@/use/utility';

    const DLEVELS = Object.freeze({
        CLOSE: 0,
        NEAR: 1,
        FAR: 2
    })

    const emit = defineEmits(["end", "close"])

    // stores
    const sounds = useSounds()
    const times = useTimes()
    const tt = useTooltip()
    const theme = useTheme()
    const settings = useSettings()
    const toast = useToast()
    const games = useGames()
    const app = useApp()

    // difficulty settings
    const { difficulty } = storeToRefs(games)
    const timeInSec = computed(() => {
        switch (difficulty.value) {
            case DIFFICULTY.EASY: return 300;
            case DIFFICULTY.NORMAL: return 180;
            case DIFFICULTY.HARD: return 120;
        }
    })

    const allowExclude = computed(() => difficulty.value !== DIFFICULTY.HARD)

    // elements
    const el = ref(null)
    const scatter = ref(null)
    const underlay = ref(null)

    const wSize = useWindowSize()
    const size = computed(() => {
        const value = Math.min(wSize.width.value, wSize.height.value)
        return Math.max(300, Math.round(value * 0.7))
    })

    const nodeWidth = computed(() => {
        if (wSize.width.value < 1500) {
            return 3
        } else if (wSize.width.value < 1750) {
            return 4
        } else if (wSize.width.value < 2000) {
            return 5
        } else {
            return 6
        }
    })
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
        result: null,
        color: "#078766"
    })
    const barData = computed(() => {
        if (gameData.target !== null) {
            return gameData.target.allTags.map(d => ({
                id: d.id,
                name: d.name,
                desc: DM.getDataItem("tags_desc", d.id)
            }))
        }
        return []
    })

    const excludedItems = reactive(new Set())
    const visited = reactive(new Set())
    const visitedOnce = reactive(new Set())
    const visitedList = computed(() => Array.from(visited.values()))

    let lastHover = [];

    const selected = reactive(new Map())
    const selectedLeft = computed(() => {
        const list = []
        selected.forEach(d => {
            if (d.left) {
                list.push(d)
            }
        })
        list.sort((a, b) => a.y - b.y)
        return list
    })
    const selectedRight = computed(() => {
        const list = []
        selected.forEach(d => {
            if (!d.left) {
                list.push(d)
            }
        })
        list.sort((a, b) => a.y - b.y)
        return list
    })
    const maxPins = computed(() => Math.floor(size.value / 90))

    const dotColor = computed(() => settings.lightMode ? "#555" : '#bbb')
    const visitedColor = computed(() => theme.current.value.colors.primary)
    const visitedDotColor = computed(() => settings.lightMode ? "#bbb" : "#555")

    const barDomain = ref()

    const timer = ref(null)

    // embedding related stuff
    const needsReload = ref(false)
    const defaultsG = reactive({ perplexity: 20, method: 'TSNE', metric: 'cosine' })

    let dataItems, matrix;

    const points = ref([])
    const pointsFiltered = computed(() => {
        if (state.value !== STATES.END && gameData.targetIndex !== null) {
            return points.value.filter(d => d[2] !== gameData.targetIndex)
                .map((d, i) => {
                    const copy = d.slice()
                    copy[4] = visited.has(d[2]) ? 3 : 1
                    copy.push(i)
                    return copy
                })
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
            CTXT_OPTIONS.items_tagged
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
        sounds.play(SOUND.START)
        state.value = STATES.LOADING
        setTimeout(() => {
            if (needsReload.value || points.value.length === 0) {
                calculateEmbedding().then(tryStartRound)
            } else {
                tryStartRound()
            }
        }, 100)

    }

    function excludeItem(id) {
        if (allowExclude.value) {
            excludedItems.add(id)
            const idx = findTargetItemIndex()
            gameData.targetIndex = idx;
            gameData.target = dataItems[idx]
            gameData.targetId = dataItems[idx].id
        }
    }
    function findTargetItemIndex() {
        if (allowExclude.value) {
            const allowed = dataItems
                .map((d, i) => ({ id: d.id, index: i }))
                .filter(d => !excludedItems.has(d.id))
                .map(d => d.index)

            return randomChoice(allowed, 1)
        } else {
            return randomInteger(0, dataItems.length-1)
        }
    }
    function tryStartRound() {
        // reset these values
        clear()

        const idx = findTargetItemIndex()
        gameData.targetIndex = idx;
        gameData.target = dataItems[idx]
        gameData.targetId = dataItems[idx].id

        if (allowExclude.value) {
            state.value = STATES.EXCLUDE
        } else {
            startRound()
        }
    }
    function startRound(starttime=null)  {
        state.value = STATES.LOADING
        starttime = starttime === null ? Date.now() : starttime
        if (points.length === 0) {
            return setTimeout(startRound, 100)
        }

        setTimeout(() => {
            state.value = STATES.INGAME
            startTimer()
            drawIndicator()
            time.value = Date.now()
        }, Date.now() - starttime > 500 ? 50 : 1000)
    }

    function stopGame() {
        if (state.value === STATES.END) return
        if (timer.value) {
            timer.value.stop()
        }
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
                    gameData.result = GAME_RESULT.WIN
                    break;
                case DLEVELS.NEAR:
                    sounds.play(SOUND.MEH)
                    gameData.result = GAME_RESULT.DRAW
                    break;
                case DLEVELS.FAR:
                    sounds.play(SOUND.FAIL)
                    gameData.result = GAME_RESULT.LOSS
                    break;
            }
            drawDistance()
            emit("end", gameData.result === GAME_RESULT.WIN, [gameData.target.id])

        }, 150)
    }

    function close() {
        d3.select(el.value).selectAll("*").remove()
        emit("close")
        reset(false)
    }

    function getDistanceLevel(distance) {
        const relative = distance / size.value
        if (relative < 0.05 || distance < 35) {
            return DLEVELS.CLOSE
        } else if (relative < 0.15 || distance < 125) {
            return DLEVELS.NEAR
        }
        return DLEVELS.FAR
    }

    function drawDistance() {
        const svg = d3.select(el.value)
        svg
            .selectAll(".distline")
            .data(gameData.clickX !== null && gameData.clickY !== null ? [gameData.target] : [])
            .join("line")
            .classed("distline", true)
            .attr("x1", gameData.clickX)
            .attr("y1", gameData.clickY)
            .attr("x2", gameData.targetX)
            .attr("y2", gameData.targetY)
            .attr("stroke-width", 3)
            .attr("stroke-dasharray", "4 1")
            .attr("stroke", gameData.color)
    }
    function clearIndicator() {
        const svg = d3.select(el.value)
        svg.selectAll(".lens").remove()
        svg.selectAll(".indicator").remove()
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

    function drawSelected() {
        const svg = d3.select(el.value)

        svg
            .selectAll(".connl")
            .data(selectedLeft.value)
            .join("line")
            .classed("connl", true)
            .attr("x1", d => d.x)
            .attr("y1", d => d.y)
            .attr("x2", 0)
            .attr("y2", d => (d.index * 90) + 55)
            .attr("stroke", "red")
            .attr("stroke-width", 1)

        svg
            .selectAll(".connr")
            .data(selectedRight.value)
            .join("line")
            .classed("connr", true)
            .attr("x1", d => d.x)
            .attr("y1", d => d.y)
            .attr("x2", size.value)
            .attr("y2", d => (d.index * 90) + 55)
            .attr("stroke", "red")
            .attr("stroke-width", 1)
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

    function removeSelected(id) {
        selected.delete(id)
        sounds.play(SOUND.PLOP)
        drawSelected()
    }
    function findSlotIndexUp(y, isLeft) {
        if (y < 0) {
            // invalid position
            return -1
        }
        const bestMatch = Math.floor(y / 90)
        const data = isLeft ? selectedLeft.value : selectedRight.value
        if (data.find(d => d.index === bestMatch)) {
            const up = findSlotIndexUp((bestMatch-1)*85, isLeft)
            if (up >= 0 && up !== bestMatch) {
                return up
            }
            return -1
        }
        return bestMatch
    }
    function findSlotIndexDown(y, isLeft) {
        if (y > size.value-90) {
            // invalid position
            return -1
        }
        const bestMatch = Math.floor(y / 90)
        const data = isLeft ? selectedLeft.value : selectedRight.value
        if (data.find(d => d.index === bestMatch)) {
            const down = findSlotIndexDown((bestMatch+1) * 90, isLeft)
            if (down >= 0 && down !== bestMatch) {
                return down
            }
            return -1
        }
        return bestMatch
    }
    function findSlotIndex(y, isLeft) {
        if (y < 0) {
            // invalid position
            return -1
        }
        const bestMatch = Math.floor(y / 90)
        const data = isLeft ? selectedLeft.value : selectedRight.value
        if (data.find(d => d.index === bestMatch)) {
            const up = findSlotIndexUp((bestMatch-1) * 90, isLeft)
            let upDist = null
            if (up >= 0 && up !== bestMatch) {
                upDist = Math.abs(up - bestMatch)
            }
            const down = findSlotIndexDown((bestMatch+1) * 90, isLeft)
            let downDist = null
            if (down >= 0 && down !== bestMatch) {
                downDist = Math.abs(down - bestMatch)
            }

            if (upDist !== null && downDist !== null) {
                return upDist <= downDist ? up : down
            }

            const indices = new Set(d3.range(maxPins.value))
            data.forEach(d => indices.delete(d.index))
            return Array.from(indices.values())[0]
        }
        return bestMatch
    }
    function onRightClickPlot(array, event) {
        if (state.value === STATES.END) {
            openItemContext(array, event)
        } else if (state.value === STATES.INGAME && array.length > 0) {
            const item = dataItems[array[0][2]]
            if (difficulty.value === DIFFICULTY.HARD && !selected.has(item.id)) {
                if (visitedOnce.has(array[0][2])) {
                    return toast.warning(app.itemName + " already visited")
                }
            }
            sounds.play(SOUND.PLOP)
            if (selected.has(item.id)) {
                selected.delete(item.id)
            } else {
                const [sx, sy] = scatter.value.coords(array[0].at(-1))
                const isLeft = sx < size.value * 0.5
                const num = isLeft ? selectedLeft.value.length : selectedRight.value.length
                if (num >= maxPins.value) {
                    return toast.warning("max. number of pinned items on "+(isLeft?"left":"right")+" side reached")
                }
                const si = findSlotIndex(sy, isLeft);
                selected.set(item.id, {
                    id: item.id,
                    name: item.name,
                    teaser: item.teaser,
                    left: isLeft,
                    index: si,
                    x: sx,
                    y: sy,
                })
            }
            drawSelected()
        }
    }
    function resetVisited() {
        selected.clear()
        drawSelected()
        visited.clear()
        time.value = Date.now()
    }
    function onHoverItem(array, event) {
        const [sx, sy] = d3.pointer(event, el.value)
        gameData.posX = sx;
        gameData.posY = sy;
        drawIndicator()
        if (array.length > 0) {

            if (state.value === STATES.INGAME) {
                array.forEach(d => visited.add(d[2]))
                time.value = Date.now()
            }

            let subset = array;
            if (state.value === STATES.INGAME && difficulty.value === DIFFICULTY.HARD) {
                subset = array.filter(d => !visitedOnce.has(d[2]))
                subset.forEach(d => lastHover.push(d[2]))
            }

            if (subset.length > 0) {
                const [mx, my] = d3.pointer(event, document.body)
                const res = subset.reduce((str, d) =>  str + `<div style="max-width: 165px" class="mr-1 mb-1">
                    <div class="text-caption text-dots" style="max-width: 100%">${dataItems[d[2]].name}</div>
                    <img src="${mediaPath('teaser', dataItems[d[2]].teaser)}" width="160"/>
                    </div>` , "")

                tt.show(`<div class="d-flex flex-wrap" style="max-width: 350px">${res}</div>`, mx, my)
            }

        } else {
            tt.hide()
            if (state.value === STATES.INGAME && difficulty.value === DIFFICULTY.HARD && lastHover.length > 0) {
                lastHover.forEach(d => visitedOnce.add(d))
                lastHover = []
            }
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
        const needR = points.value.length === 0
        const proj = await dr.transform_async()
        points.value = Array.from(proj).map((d,i) => ([d[0], d[1], i, mediaPath("teaser", dataItems[i].teaser), i === gameData.targetIndex ? 2 : 1]))
        if (needR) refresh.value = Date.now();
    }

    function clear() {
        if (el.value) {
            d3.select(el.value).selectAll("*").remove()
        }
        visited.clear()
        visitedOnce.clear()
        lastHover = [];
        selected.clear()
        gameData.result = null;
        gameData.targetIndex = null;
        gameData.targetId = null;
        gameData.target = null;
        gameData.clickX = null;
        gameData.clickY = null;
        gameData.posX = null;
        gameData.posY = null;
    }
    function reset(recalculate=false) {
        needsReload.value = false;
        state.value = STATES.START;
        gameData.color = theme.current.value.colors.primary
        if (timer.value) {
            timer.value.stop()
        }
        clear()
        if (recalculate) {
            calculateEmbedding()
        }
    }

    async function init() {
        reset()
        startGame()
    }

    onMounted(init)

    watch(difficulty, init)

    watch(() => Math.max(times.all, times.items), () => needsReload.value = true)

</script>