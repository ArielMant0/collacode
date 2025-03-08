<template>
    <div>
        <div v-if="state === STATES.START" class="d-flex align-center justify-center" style="height: 80vh;">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>

        <div v-else-if="state === STATES.LOADING" class="d-flex align-center justify-center" style="height: 80vh;">
            <div class="game-loader"></div>
        </div>

        <div v-else-if="state === STATES.INGAME" class="d-flex flex-column align-center">

            <v-sheet
                style="font-size: x-large;"
                class="mt-8 mb-4 pt-4 pb-4 pr-8 pl-8"
                rounded="sm"
                :color="timer.seconds < 10 ? '#ed5a5a' : 'surface-light'">
                {{ timer.toFormat("mm:ss") }}
            </v-sheet>

            <div class="d-flex justify-space-around">
                <div style="width: 20%;" class="d-flex flex-column align-end prevent-select">
                    <div class="d-flex align-center mt-1 mb-1" v-for="(item, idx) in itemsLeft" :key="item.id+':'+idx">
                        <div draggable class="cursor-grab" @dragstart="startDrag(item.id)">
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

                <div style="width: 60%;">
                    <div v-for="(ts, idx) in tags" :key="'tags_'+idx">
                        <v-divider v-if="idx > 0" class="mt-2 mb-2"></v-divider>
                        <div class="d-flex" @dragover="e => e.preventDefault()" @drop="dropDrag(idx)">
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
                                <span v-for="(t, i) in ts" class="text-caption mr-1 mb-1 prevent-select">
                                    <span v-if="i > 0">~</span>
                                    {{ t.name }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <v-btn size="x-large" color="primary" class="mt-4" @click="stopGame" :disabled="itemsAssigned.size < items.length">submit</v-btn>

        </div>

        <div v-else-if="state === STATES.END" class="d-flex flex-column align-center">
            <div class="mt-4 mb-4">
                <div>{{ correct.size }} / {{ items.length }}</div>
            </div>

            <div style="width: 75%;">
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
                                <span v-for="(t, i) in ts" class="text-caption mr-1 mb-1">
                                    <span v-if="i > 0">~</span>
                                    {{ t.name }}
                                </span>
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
    import { Chance } from 'chance'
    import { range } from 'd3'
    import { DateTime } from 'luxon'
    import { computed, onMounted, reactive, watch } from 'vue'
    import imgUrlS from '@/assets/__placeholder__s.png'
    import { DIFFICULTY, SOUND, useGames } from '@/store/games'

    const STATES = Object.freeze({
        START: 0,
        LOADING: 1,
        INGAME: 2,
        END: 3
    })

    const games = useGames()

    const props = defineProps({
        difficulty: {
            type: Number,
            required: true
        },
    })

    const emit = defineEmits(["end"])

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

    const timeEnd = ref(DateTime.local())
    const timer = ref(DateTime.local())

    const correct = reactive(new Set())

    let int;

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

    function checkTimer() {
        timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
        if (timer.value.seconds <= 0) {
            stopGame()
        }
    }

    function startGame() {
        const starttime = Date.now()
        games.playSingle(SOUND.START)
        state.value = STATES.LOADING
        const chance = new Chance()
        const allItems = DM.getData("items", false)
        const subset = chance.pickset(allItems, numItems.value)
        items.value = subset;
        const tmp = subset.map(d => d.allTags.slice())
        shuffling.value = chance.shuffle(range(tmp.length))
        tags.value = shuffling.value.map(i => tmp[i])

        itemsAssigned.clear()
        correct.clear()

        setTimeout(() => {
            timeEnd.value =  DateTime.local().plus({ seconds: timeInSec.value })
            timer.value = timeEnd.value.diffNow(["minutes", "seconds"])
            state.value = STATES.INGAME
            int = setInterval(checkTimer, 500)
        }, Date.now() - starttime < 500 ? 1000 : 50)
    }

    function stopGame() {
        if (int) clearInterval(int)
        calculateStats()
        state.value = STATES.END
    }

    function close() {
        reset()
        emit("end")
    }

    function reset() {
        if (int) clearInterval(int)
        state.value = STATES.START
        items.value = []
        tags.value = []
        shuffling.value = []
        itemsAssigned.clear()
        correct.clear()
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
