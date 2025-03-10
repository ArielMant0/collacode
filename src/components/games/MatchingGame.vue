<template>
    <div>
        <div v-if="state === STATES.START" class="d-flex align-center justify-center" style="height: 80vh;">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>

        <div v-else-if="state === STATES.LOADING" class="d-flex align-center justify-center" style="height: 80vh;">
            <div class="game-loader"></div>
        </div>

        <div v-else-if="state === STATES.INGAME" class="d-flex flex-column align-center">

            <Timer ref="timer" :time-in-sec="timeInSec" @end="stopGame"/>

            <div class="d-flex justify-space-around">
                <div style="width: 20%;" class="d-flex flex-column align-end prevent-select">
                    <div style="min-height: 75px;"></div>
                    <div class="d-flex align-center mt-1 mb-1" v-for="(item, idx) in itemsLeft" :key="item.id+':'+idx">
                        <div draggable class="cursor-grab secondary-on-hover pa-1" @dragstart="startDrag(item.id)">
                            <div class="text-dots text-caption" style="max-width: 160px;">{{ item.name }}</div>
                            <v-img
                                cover
                                :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                                :lazy-src="imgUrlS"
                                :width="160"
                                :height="80"/>
                        </div>
                    </div>
                </div>

                <div style="width: 70%;">
                    <div v-for="(ts, idx) in tags" :key="'tags_'+idx">
                        <v-divider v-if="idx > 0" class="mt-2 mb-2"></v-divider>
                        <div class="d-flex align-end" @dragover="e => e.preventDefault()" @drop="dropDrag(idx)">
                            <div v-if="itemsAssigned.has(idx)"
                                draggable
                                @dragstart="startDrag(itemsAssigned.get(idx), idx)"
                                class="mr-4 mb-1 prevent-select cursor-grab">
                                <div class="text-dots text-caption" style="max-width: 160px;">{{ getItem(itemsAssigned.get(idx)).name }}</div>
                                <v-img
                                    cover
                                    :src="getItem(itemsAssigned.get(idx)).teaser ? 'teaser/'+getItem(itemsAssigned.get(idx)).teaser : imgUrlS"
                                    :lazy-src="imgUrlS"
                                    :width="160"
                                    :height="80"/>
                            </div>
                            <div v-else @dragover="e => e.preventDefault()" @drop="dropDrag(idx)">
                                <v-card  min-width="160" min-height="100"  color="surface-light" class="d-flex align-center justify-center mr-4 mb-1 prevent-select">
                                    <v-icon size="large">mdi-image-area</v-icon>
                                </v-card>
                            </div>
                            <div>
                                <MiniTree v-if="idx === 0" :node-width="5" :selectable="false" @hover="t => setHoverTag(t ? t.id : null)"/>
                                <BarCode
                                    :data="barData[idx]"
                                    :domain="barDomain"
                                    :selected="hoverSet"
                                    binary
                                    hideHighlight
                                    id-attr="0"
                                    name-attr="1"
                                    value-attr="2"
                                    selected-color="red"
                                    :binary-color-fill="settings.lightMode ? '#000000' : '#ffffff'"
                                    :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                                    @hover="t => setHoverTag(t ? t[0] : null)"
                                    :width="5"
                                    :height="20"/>
                                <div>
                                    <span v-for="(t, i) in ts" class="text-caption mr-1 mb-1 prevent-select">
                                        <span v-if="i > 0">~ </span>
                                        <span
                                            @pointerenter="setHoverTag(t.id)"
                                            @pointerleave="setHoverTag(null)"
                                            :class="[hoverTag === t.id ? 'font-weight-bold' : '', 'no-break']">
                                            {{ t.name }}
                                        </span>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <v-btn size="x-large"
                :color="itemsAssigned.size < items.length ? 'default' : 'primary'"
                class="mt-8"
                @click="stopGame"
                :disabled="itemsAssigned.size < items.length">
                submit
            </v-btn>

        </div>

        <div v-else-if="state === STATES.END" class="d-flex flex-column justify-center align-center">
            <div class="mt-4 mb-4">
                <div>{{ correct.size }} / {{ items.length }}</div>
            </div>

            <div style="width: 70%;">
                <div v-for="(ts, idx) in tags" :key="'c_tags_'+idx" class="d-flex align-center prevent-select">
                    <v-icon
                        size="60"
                        class="mr-8"
                        :icon="correct.has(items[shuffling[idx]].id) ? 'mdi-check-bold' : 'mdi-close-circle-outline'"
                        :color="correct.has(items[shuffling[idx]].id) ? 'primary' : 'error'"/>
                    <div>
                        <v-divider v-if="idx > 0" class="mt-2 mb-2"></v-divider>
                        <div class="d-flex">
                            <div class="mr-4 mb-1">
                                <div class="text-dots text-caption" style="max-width: 160px;">{{ getItem(itemsAssigned.get(idx)).name }}</div>
                                <v-img
                                    cover
                                    :src="getItem(itemsAssigned.get(idx)).teaser ? 'teaser/'+getItem(itemsAssigned.get(idx)).teaser : imgUrlS"
                                    :lazy-src="imgUrlS"
                                    :width="160"
                                    :height="80"/>
                            </div>
                            <div class="mr-4 mb-1">
                                <div class="text-dots text-caption" style="max-width: 160px;">{{ items[shuffling[idx]].name }}</div>
                                <v-img
                                    cover
                                    :src="items[shuffling[idx]].teaser ? 'teaser/'+items[shuffling[idx]].teaser : imgUrlS"
                                    :lazy-src="imgUrlS"
                                    :width="160"
                                    :height="80"/>
                            </div>
                            <div>
                                <div class="text-caption" style="min-height: 1.5em;"></div>
                                <BarCode
                                    :data="barData[idx]"
                                    :domain="barDomain"
                                    :selected="hoverSet"
                                    binary
                                    hideHighlight
                                    id-attr="0"
                                    name-attr="1"
                                    value-attr="2"
                                    selected-color="red"
                                    :binary-color-fill="settings.lightMode ? '#000000' : '#ffffff'"
                                    :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                                    @hover="t => setHoverTag(t ? t[0] : null)"
                                    :width="5"
                                    :height="20"/>
                                <div>
                                    <span v-for="(t, i) in ts" class="text-caption mr-1 mb-1">
                                        <span v-if="i > 0">~ </span>
                                        <span
                                            @pointerenter="setHoverTag(t.id)"
                                            @pointerleave="setHoverTag(null)"
                                            :class="[hoverTag === t.id ? 'font-weight-bold' : '', 'no-break']">
                                            {{ t.name }}
                                        </span>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="d-flex align-center justify-center mt-4">
                <v-btn class="mr-1" size="x-large" color="error" @click="close">close</v-btn>
                <v-btn class="ml-1" size="x-large" color="primary" @click="startGame">play again</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager'
    import { range } from 'd3'
    import { computed, onMounted, reactive, watch } from 'vue'
    import imgUrlS from '@/assets/__placeholder__s.png'
    import { DIFFICULTY, SOUND, useGames } from '@/store/games'
    import Timer from './Timer.vue'
    import BarCode from '../vis/BarCode.vue'
    import { useSettings } from '@/store/settings'
    import MiniTree from '../vis/MiniTree.vue'
    import { randomChoice, randomShuffle } from '@/use/random'

    const STATES = Object.freeze({
        START: 0,
        LOADING: 1,
        INGAME: 2,
        END: 3
    })

    const props = defineProps({
        difficulty: {
            type: Number,
            required: true
        },
    })

    const emit = defineEmits(["end", "close"])

    // stores
    const games = useGames()
    const settings = useSettings()

    // difficulty settings
    const timeInSec = computed(() => {
        switch (props.difficulty) {
            case DIFFICULTY.EASY: return 300;
            case DIFFICULTY.NORMAL: return 180;
            case DIFFICULTY.HARD: return 60;
        }
    })
    const numItems = computed(() => {
        switch (props.difficulty) {
            case DIFFICULTY.EASY: return 4;
            case DIFFICULTY.NORMAL: return 5;
            case DIFFICULTY.HARD: return 6;
        }
    })

    // game related stuff
    const state = ref(STATES.START)
    const items = ref([])
    const tags = ref([])
    const shuffling = ref([])
    const barData = ref([])
    const barDomain = ref([])

    const itemsAssigned = reactive(new Map())
    const itemsReverse = computed(() => {
        const m = new Map()
        itemsAssigned.forEach((v, k) => m.set(v, k))
        return m
    })
    const itemsLeft = computed(() => {
        if (itemsAssigned.size === 0) return items.value
        const ids = new Set(Array.from(itemsReverse.value.keys()))
        return items.value.filter(d => !ids.has(d.id))
    })

    const dragItem = ref(-1)
    const dragIndex = ref(-1)
    const hoverTag = ref(-1)
    const hoverSet = computed(() => new Set(hoverTag.value > 0 ? [hoverTag.value] : []))

    const timer = ref(null)

    const correct = reactive(new Set())

    function setHoverTag(tag) {
        hoverTag.value = tag ? tag : -1
    }
    function startDrag(id, index=-1) {
        dragItem.value = id;
        dragIndex.value = index;
    }
    function dropDrag(index) {
        if (dragItem.value > 0) {
            if (dragIndex.value >= 0) {
                itemsAssigned.delete(dragIndex.value)
            }
            const target = itemsAssigned.get(index)
            if (target && dragIndex.value >= 0) {
                itemsAssigned.set(dragIndex.value, target)
            }
            itemsAssigned.set(index, dragItem.value)
            dragItem.value = -1;
            dragIndex.value = -1;
            games.play(SOUND.PLOP)
        }
    }

    function getItem(id) {
        return items.value.find(d => d.id === id)
    }

    function calculateStats() {
        itemsAssigned.forEach((id, idx) => {
            if (items.value[shuffling.value[idx]].id === id) {
                correct.add(id)
            }
        })

        if (correct.size === items.value.length) {
            games.play(SOUND.WIN)
        } else if (correct.size < Math.floor(items.value.length / 3)) {
            games.play(SOUND.FAIL)
        } else {
            games.play(SOUND.MEH)
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
        games.playSingle(SOUND.START)
        state.value = STATES.LOADING

        clear()

        const allItems = DM.getData("items", false)
        const subset = randomChoice(allItems, numItems.value)
        items.value = subset;

        const tmp = subset.map(d => d.allTags.slice())
        shuffling.value = randomShuffle(range(tmp.length))
        tags.value = shuffling.value.map(i => tmp[i])

        barDomain.value = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
        barData.value = tags.value.map(list => list.map(t => ([t.id, t.name, 1])))

        setTimeout(() => {
            state.value = STATES.INGAME
            startTimer()
        }, Date.now() - starttime < 500 ? 1000 : 50)
    }

    function stopGame() {
        timer.value.stop()
        calculateStats()
        state.value = STATES.END
        emit("end", correct.size === items.value.length, items.value.map(d => d.id))
    }

    function close() {
        emit("close")
        reset()
    }

    function clear() {
        hoverTag.value = -1
        items.value = []
        tags.value = []
        shuffling.value = []
        barData.value = []
        itemsAssigned.clear()
        correct.clear()
    }
    function reset() {
        state.value = STATES.START
        clear()
    }

    onMounted(function() {
        reset()
        startGame()
    })

    watch(props, function() {
        reset()
        startGame()
    }, { deep: true })
</script>

<style scoped>
.no-break {
    text-wrap: nowrap;
}
</style>
