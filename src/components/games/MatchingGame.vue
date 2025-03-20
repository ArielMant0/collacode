<template>
    <div>
        <div v-if="state === STATES.START" class="d-flex align-center justify-center" style="height: 80vh;">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>

        <div v-else-if="state === STATES.LOADING"class="d-flex align-center justify-center">
            <LoadingScreen
                :messages="[
                    'drag item images to assign them to a set of tags',
                    'hover over tags to highlight them in all tag sets',
                    'click on a tag to highlight it permanently',
                    'you can see select tag descriptions in the box at the bottom'
                ]"/>
        </div>

        <div v-else-if="state === STATES.EXCLUDE" class="d-flex flex-column align-center">

            <v-sheet style="font-size: x-large;" class="mb-8 pt-4 pb-4 pr-8 pl-8" rounded="sm" color="surface-light">
                {{ excluded.size }} / {{ numExcludes }} {{ app.itemName }} exclusions used
            </v-sheet>

            <h4>{{ capitalize(app.itemName+'s') }} for this round</h4>
            <div class="d-flex flex-wrap">
                <v-sheet v-for="item in itemsShuffled" :key="'exct_'+item.id" class="pa-1 secondary-on-hover mr-1 mb-1">
                    <ItemTeaser :item="item" :width="160" :height="80" show-name prevent-open @click="excludeItem(item.id)"/>
                </v-sheet>
            </div>

            <h4 class="mt-8">Excluded {{ app.itemName }}s</h4>
            <div class="d-flex flex-wrap">
                <v-sheet v-for="id in excluded" :key="'exc_'+id" class="pa-1 mr-1 mb-1" color="error">
                    <ItemTeaser :id="id" :width="160" :height="80" show-name prevent-click/>
                </v-sheet>
            </div>

            <v-btn size="x-large" color="primary" class="mt-4" @click="startRound">start</v-btn>
        </div>

        <div v-else-if="state === STATES.INGAME" class="d-flex flex-column align-center">

            <Timer ref="timer" :time-in-sec="timeInSec" @end="stopGame"/>

            <div class="d-flex justify-center">
                <div
                    style="margin-right: 25px; min-width: 170px; border-radius: 5px;"
                    class="pa-1 d-flex flex-column justify-center align-end prevent-select bordered-grey"
                    >
                    <div class="d-flex align-center mt-1 mb-1" v-for="(item, idx) in itemsLeft" :key="item.id+':'+idx">
                        <v-sheet draggable class="cursor-grab secondary-on-hover pa-1" @dragstart="startDrag(item.id)">
                            <div class="text-dots text-caption" style="max-width: 160px;">{{ item.name }}</div>
                            <v-img
                                cover
                                :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                                :lazy-src="imgUrlS"
                                :width="160"
                                :height="80"/>
                        </v-sheet>
                    </div>
                </div>

                <div style="width: 70%;">
                    <div v-for="(ts, idx) in tags" :key="'tags_'+idx" style="width:fit-content;">

                        <v-divider v-if="idx > 0" class="mt-3 mb-3" style="width: 100%;"></v-divider>

                        <div class="d-flex align-start" @dragover="e => e.preventDefault()" @drop="dropDrag(idx)">
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
                                <BarCode
                                    :item-id="itemsAssigned.get(idx)"
                                    :data="barData[idx]"
                                    :domain="barDomain"
                                    :selected="hoverSet"
                                    :hidden="tagExts.hidden"
                                    selectable
                                    hide-highlight
                                    categorical
                                    :color-domain="[1, 2]"
                                    :color-scale="[
                                        settings.lightMode ? 'black' : 'white',
                                        settings.lightMode ? '#0ad39f' : '#078766',
                                    ]"
                                    id-attr="0"
                                    name-attr="1"
                                    value-attr="2"
                                    :desc-attr="showDesc ? '3' : undefined"
                                    selected-color="red"
                                    :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                                    @hover="t => setHoverTag(t ? t[0] : null)"
                                    @click="t => toggleSelectedTag(t[0])"
                                    @right-click="t => toggleHiddenTag(t[0])"
                                    :width="nodeWidth"
                                    :height="20"/>

                                <div style="width: 100%;">
                                    <span v-for="(t, i) in ts" class="text-caption mr-1 mb-1 prevent-select">
                                        <span v-if="i > 0">~ </span>
                                        <span
                                            @pointerenter="setHoverTag(t.id)"
                                            @pointerleave="setHoverTag(null)"
                                            @click="toggleSelectedTag(t.id)"
                                            @contextmenu="e => toggleHiddenTag(t.id, e)"
                                            :class="[
                                                isSelectedTag(t.id) || hoverTag === t.id ? 'font-weight-bold' : '',
                                                isHiddenTag(t.id) ? 'tag-hidden' : '',
                                                'no-break', 'cursor-pointer'
                                            ]">
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

            <div style="text-align: center;" class="mb-1 mt-8">
                <v-btn
                    :prepend-icon="tagExts.show ? 'mdi-eye-off' : 'mdi-eye'"
                    density="compact"
                    class="mr-1"
                    @click="tagExts.show = !tagExts.show"
                    variant="tonal">
                    {{ tagExts.show ? 'hide' : 'show' }} selected tags
                </v-btn>
                <v-btn
                    prepend-icon="mdi-delete"
                    :color="tagExts.selected.size > 0 ? 'error' : 'default'"
                    density="compact"
                    class="ml-1"
                    :disabled="tagExts.selected.size === 0"
                    @click="tagExts.selected.clear()"
                    variant="tonal">
                    clear selected tags
                </v-btn>
            </div>

            <v-sheet v-if="tagExts.show" color="surface-light" class="pa-2 mt-1 text-caption" :class="!showDesc ? ['d-flex', 'flex-wrap'] : []" rounded="sm" style="width: 50%;">
                <span v-if="tagExts.selected.size === 0">no selected tags</span>
                <div v-for="([tid, tag]) in tagExts.selected" :key="'texts_'+tid" class="mr-1 mb-1">
                    <v-btn
                        icon="mdi-close"
                        color="error"
                        class="mr-1"
                        @click="toggleSelectedTag(tid, tag)"
                        size="sm"
                        density="compact"
                        rounded="sm"
                        variant="tonal"
                        />
                    <b>{{ tag.name }}</b>
                    <span v-if="showDesc && tag.description">: {{ tag.description }}</span>
                </div>
            </v-sheet>

        </div>

        <div v-else-if="state === STATES.END" class="d-flex flex-column justify-center align-center">

            <div class="mt-4 mb-4 d-flex align-center justify-center">
                <GameResultIcon
                    :result="gameResult"
                    :score-text="correct.size+' / '+items.length"
                    show-text
                    show-effects/>
            </div>

            <div class="d-flex align-center justify-center mb-8">
                <v-btn class="mr-1" size="large" color="error" @click="close">close game</v-btn>
                <v-btn class="ml-1" size="large" color="primary" @click="startGame">play again</v-btn>
            </div>

            <div>
                <div v-for="(ts, idx) in tags" :key="'c_tags_'+idx" class="d-flex align-center justify-center prevent-select">
                    <GameResultIcon :result="correct.has(items[shuffling[idx]].id)" class="mr-8"/>

                    <div>
                        <v-divider v-if="idx > 0" class="mt-3 mb-3" style="width: 100%;"></v-divider>

                        <div class="d-flex align-start">
                            <div v-if="hasAssignedItem(idx)" class="mr-4 mb-1">
                                <div class="text-dots text-caption" style="max-width: 120px;">{{ getAssignedItem(idx).name }}</div>
                                <ItemTeaser :item="getAssignedItem(idx)" :width="120" :height="60"/>
                            </div>
                            <div v-else class="mr-4 mb-1">
                                <v-card  min-width="160" min-height="100"  color="surface-light" class="d-flex align-center justify-center mr-4 mb-1 prevent-select">
                                    <v-icon size="large">mdi-image-area</v-icon>
                                </v-card>
                            </div>

                            <div class="mr-4 mb-1">
                                <div class="text-dots text-caption" style="max-width: 120px;">{{ items[shuffling[idx]].name }}</div>
                                <ItemTeaser :item="items[shuffling[idx]]" :width="120" :height="60"/>
                            </div>

                            <div :style="{ maxWidth: (nodeWidth*barDomain.length)+'px' }">
                                <BarCode
                                    :item-id="items[shuffling[idx]].id"
                                    :data="barData[idx]"
                                    :domain="barDomain"
                                    :selected="hoverSet"
                                    :hidden="tagExts.hidden"
                                    hide-highlight
                                    categorical
                                    selectable
                                    :color-domain="[1, 2]"
                                    :color-scale="[
                                        settings.lightMode ? 'black' : 'white',
                                        settings.lightMode ? '#0ad39f' : '#078766',
                                    ]"
                                    id-attr="0"
                                    name-attr="1"
                                    value-attr="2"
                                    desc-attr="3"
                                    selected-color="red"
                                    :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                                    @hover="t => setHoverTag(t ? t[0] : null)"
                                    @click="t => toggleSelectedTag(t[0])"
                                    @right-click="(t, e, has) => openTagContextBar(items[shuffling[idx]].id, t, e, has)"
                                    :width="nodeWidth"
                                    :height="20"/>

                                <div style="width: 100%;">
                                    <span v-for="(t, i) in ts" class="text-caption mr-1 mb-1">
                                        <span v-if="i > 0">~ </span>
                                        <span
                                            @pointerenter="setHoverTag(t.id)"
                                            @pointerleave="setHoverTag(null)"
                                            @click="toggleSelectedTag(t.id)"
                                            @contextmenu="e => openTagContext(items[shuffling[idx]].id, t, e, true)"
                                            :class="[
                                                isSelectedTag(t.id) || hoverTag === t.id ? 'font-weight-bold' : '',
                                                isHiddenTag(t.id) ? 'tag-hidden' : '',
                                                'no-break', 'cursor-pointer'
                                            ]">
                                            {{ t.name }}
                                        </span>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager'
    import { pointer, range } from 'd3'
    import { computed, onMounted, reactive, watch } from 'vue'
    import imgUrlS from '@/assets/__placeholder__s.png'
    import { DIFFICULTY, GAME_RESULT, STATES, useGames } from '@/store/games'
    import Timer from './Timer.vue'
    import BarCode from '../vis/BarCode.vue'
    import { CTXT_OPTIONS, useSettings } from '@/store/settings'
    import { randomChoice, randomShuffle } from '@/use/random'
    import { OBJECTION_ACTIONS, useApp } from '@/store/app'
    import ItemTeaser from '../items/ItemTeaser.vue'
    import { useSounds, SOUND } from '@/store/sounds';
    import { useWindowSize } from '@vueuse/core'
    import { storeToRefs } from 'pinia'
    import { capitalize } from '@/use/utility'
    import { POSITION, useToast } from 'vue-toastification'
    import GameResultIcon from './GameResultIcon.vue'
import LoadingScreen from './LoadingScreen.vue'

    const emit = defineEmits(["end", "close"])

    // stores
    const sounds = useSounds()
    const settings = useSettings()
    const games = useGames()
    const app = useApp()
    const toast = useToast()

    // sizing
    const wSize = useWindowSize()
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

    // difficulty settings
    const { difficulty } = storeToRefs(games)
    const timeInSec = computed(() => {
        switch (difficulty.value) {
            case DIFFICULTY.EASY: return 300;
            case DIFFICULTY.NORMAL: return 180;
            case DIFFICULTY.HARD: return 120;
        }
    })
    const numItems = computed(() => {
        switch (difficulty.value) {
            case DIFFICULTY.EASY: return 4;
            case DIFFICULTY.NORMAL: return 5;
            case DIFFICULTY.HARD: return 6;
        }
    })
    const allowExclude = computed(() => difficulty.value !== DIFFICULTY.HARD)
    const numExcludes = computed(() => {
        switch (difficulty.value) {
            case DIFFICULTY.EASY: return 3;
            case DIFFICULTY.NORMAL: return 1;
            case DIFFICULTY.HARD: return 0;
        }
    })
    const showDesc = computed(() => difficulty.value !== DIFFICULTY.HARD)

    // game related stuff
    const state = ref(STATES.START)
    const items = ref([])
    const tags = ref([])
    const shuffling = ref([])
    const barData = ref([])
    const barDomain = ref([])

    const itemsAssigned = reactive(new Map())
    const itemsShuffled = computed(() => shuffling.value.map(i => items.value[i]))
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

    const tagExts = reactive({
        show: false,
        selected: new Map(),
        hidden: new Set()
    })

    const dragItem = ref(-1)
    const dragIndex = ref(-1)
    const hoverTag = ref(-1)
    const hoverSet = computed(() => new Set(hoverTag.value > 0 ? [hoverTag.value] : []))

    const timer = ref(null)

    const correct = reactive(new Set())
    const excluded = reactive(new Set())
    const gameResult = computed(() => correct.size === items.value.length ? GAME_RESULT.WIN : GAME_RESULT.LOSS)

    // ---------------------------------------------------------------------
    // Functions
    // ---------------------------------------------------------------------

    function isSelectedTag(id) { return tagExts.selected.has(id) }
    function isHiddenTag(id) { return tagExts.hidden.has(id) }

    function hasAssignedItem(index) {
        return itemsAssigned.has(index)
    }
    function getAssignedItem(index) {
        const id = itemsAssigned.get(index)
        return id ? getItem(id) : null
    }

    function toggleSelectedTag(id, obj=null) {
        sounds.play(SOUND.PLOP)
        if (tagExts.selected.has(id)) {
            tagExts.selected.delete(id)
        } else {
            tagExts.selected.set(id, obj ? obj : DM.getDataItem("tags", id))
        }
        updateBarData()
    }
    function toggleHiddenTag(tag, event) {
        if (event) event.preventDefault()

        if (tagExts.hidden.has(tag)) {
            sounds.play(SOUND.PLOP)
            tagExts.hidden.delete(tag)
        } else {
            sounds.play(SOUND.CLICK_REVERB)
            tagExts.hidden.add(tag)
        }
    }
    function openTagContext(itemId, tag, event, has) {
        event.preventDefault()
        const [x, y] = pointer(event, document.body)
        const action = has ? OBJECTION_ACTIONS.REMOVE : OBJECTION_ACTIONS.ADD
        settings.setRightClick(
            "tag", tag.id,
            x, y,
            tag.name,
            { item: itemId, action: action },
            CTXT_OPTIONS.items_tagged
        )
    }
    function openTagContextBar(itemId, tag, event, has) {
        event.preventDefault()
        const [x, y] = pointer(event, document.body)
        const action = has ? OBJECTION_ACTIONS.REMOVE : OBJECTION_ACTIONS.ADD
        settings.setRightClick(
            "tag", tag[0],
            x, y,
            tag[1],
            { item: itemId, action: action },
            CTXT_OPTIONS.items_tagged
        )
    }
    function updateBarData() {
        barData.value = tags.value.map(list => {
            return list.map(t => ([t.id, t.name, tagExts.selected.has(t.id) ? 2 : 1, DM.getDataItem("tags_desc", t.id)]))
        })
    }

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
            sounds.play(SOUND.PLOP)
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
            sounds.play(SOUND.WIN)
        } else if (correct.size < Math.floor(items.value.length / 3)) {
            sounds.play(SOUND.FAIL)
        } else {
            sounds.play(SOUND.MEH)
        }
    }

    function startTimer() {
        if (timer.value) {
            timer.value.start()
        } else {
            setTimeout(startTimer, 50)
        }
    }

    function excludeItem(id) {
        if (excluded.size < numExcludes.value) {
            excluded.add(id)
            const idx = items.value.findIndex(d => d.id === id)
            if (idx >= 0) {
                const existing = new Set(items.value.map(d => d.id))
                const allItems = DM.getDataBy("items", d => !existing.has(d.id) && !excluded.has(d.id))
                const replace = randomChoice(allItems, 1)
                items.value[idx] = replace
                const tmp = items.value.map(d => d.allTags.slice())
                tags.value = shuffling.value.map(i => tmp[i])
            } else {
                console.error("cannot find item with id:", id)
            }
        } else {
            toast.warning("you used up all your exclusions", { position: POSITION.TOP_CENTER, timeout: 2000 })
        }
    }

    function startRound() {
        state.value = STATES.LOADING
        setTimeout(() => {
            state.value = STATES.INGAME
            startTimer()
        }, 1000)
    }
    function tryStartRound() {
        let allItems;
        if (allowExclude.value && excluded.size > 0) {
            allItems = DM.getDataBy("items", d => !excluded.has(d.id))
        } else {
            allItems = DM.getData("items", false)
        }

        const subset = randomChoice(allItems, numItems.value)
        items.value = subset;

        const tmp = subset.map(d => d.allTags.slice())
        shuffling.value = randomShuffle(range(tmp.length))
        tags.value = shuffling.value.map(i => tmp[i])

        updateBarData()

        if (!allowExclude.value) {
            startRound()
        } else {
            state.value = STATES.EXCLUDE
        }
    }
    function startGame() {
        sounds.play(SOUND.START)
        state.value = STATES.LOADING
        // clear previous data
        clear()
        // get bar code domain
        barDomain.value = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
        // try to start the round
        tryStartRound()
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
        tagExts.selected.clear()
        tagExts.hidden.clear()
        excluded.clear()
    }
    function reset() {
        state.value = STATES.START
        clear()
    }

    function init () {
        reset()
        startGame()
    }

    onMounted(init)

    watch(difficulty, init)

</script>

<style scoped>
.no-break {
    text-wrap: nowrap;
}
.tag-hidden {
    opacity: 0.15;
}
</style>
