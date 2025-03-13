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
                    <div v-for="(ts, idx) in tags" :key="'tags_'+idx" style="max-width: 1920px; width:fit-content;">

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
                                    selected-color="red"
                                    :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                                    @hover="t => setHoverTag(t ? t[0] : null)"
                                    @click="t => toggleSelectedTag(t[0])"
                                    @right-click="t => toggleHiddenTag(t[0])"
                                    :width="5"
                                    :height="20"/>
                                <br/>
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

        </div>

        <div v-else-if="state === STATES.END" class="d-flex flex-column justify-center align-center">
            <div class="mt-4 mb-4">
                <div>{{ correct.size }} / {{ items.length }}</div>
            </div>

            <div style="width: 70%;">
                <div v-for="(ts, idx) in tags" :key="'c_tags_'+idx" class="d-flex align-center prevent-select" style="max-width: 1920px; width:fit-content;">
                    <v-icon
                        size="60"
                        class="mr-8"
                        :icon="correct.has(items[shuffling[idx]].id) ? 'mdi-check-bold' : 'mdi-close-circle-outline'"
                        :color="correct.has(items[shuffling[idx]].id) ? 'primary' : 'error'"/>
                    <div>
                        <v-divider v-if="idx > 0" class="mt-3 mb-3" style="width: 100%;"></v-divider>

                        <div class="d-flex align-start">
                            <div v-if="hasAssignedItem(idx)" class="mr-4 mb-1">
                                <div class="text-dots text-caption" style="max-width: 160px;">{{ getAssignedItem(idx).name }}</div>
                                <ItemTeaser :item="getAssignedItem(idx)" :width="160" :height="80"/>
                            </div>
                            <div v-else class="mr-4 mb-1">
                                <v-card  min-width="160" min-height="100"  color="surface-light" class="d-flex align-center justify-center mr-4 mb-1 prevent-select">
                                    <v-icon size="large">mdi-image-area</v-icon>
                                </v-card>
                            </div>

                            <div class="mr-4 mb-1">
                                <div class="text-dots text-caption" style="max-width: 160px;">{{ items[shuffling[idx]].name }}</div>
                                <ItemTeaser :item="items[shuffling[idx]]" :width="160" :height="80"/>
                            </div>

                            <div style="display: block;">
                                <BarCode
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
                                    selected-color="red"
                                    :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                                    @hover="t => setHoverTag(t ? t[0] : null)"
                                    @click="t => toggleSelectedTag(t[0])"
                                    @right-click="(t, e, has) => openTagContextBar(items[shuffling[idx]].id, t, e, has)"
                                    :width="5"
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

            <div class="d-flex align-center justify-center mt-4">
                <v-btn class="mr-1" size="x-large" color="error" @click="close">close</v-btn>
                <v-btn class="ml-1" size="x-large" color="primary" @click="startGame">play again</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager'
    import { pointer, range } from 'd3'
    import { computed, onMounted, reactive, watch } from 'vue'
    import imgUrlS from '@/assets/__placeholder__s.png'
    import { DIFFICULTY } from '@/store/games'
    import Timer from './Timer.vue'
    import BarCode from '../vis/BarCode.vue'
    import { CTXT_OPTIONS, useSettings } from '@/store/settings'
    import { randomChoice, randomShuffle } from '@/use/random'
    import { OBJECTION_ACTIONS } from '@/store/app'
    import ItemTeaser from '../items/ItemTeaser.vue'
    import { useSounds, SOUND } from '@/store/sounds';

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
    const sounds = useSounds()
    const settings = useSettings()

    // difficulty settings
    const timeInSec = computed(() => {
        switch (props.difficulty) {
            case DIFFICULTY.EASY: return 300;
            case DIFFICULTY.NORMAL: return 150;
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

    const tagExts = reactive({
        selected: new Set(),
        hidden: new Set()
    })

    const dragItem = ref(-1)
    const dragIndex = ref(-1)
    const hoverTag = ref(-1)
    const hoverSet = computed(() => new Set(hoverTag.value > 0 ? [hoverTag.value] : []))

    const timer = ref(null)

    const correct = reactive(new Set())

    function isSelectedTag(id) { return tagExts.selected.has(id) }
    function isHiddenTag(id) { return tagExts.hidden.has(id) }

    function hasAssignedItem(index) {
        return itemsAssigned.has(index)
    }
    function getAssignedItem(index) {
        const id = itemsAssigned.get(index)
        return id ? getItem(id) : null
    }
    function getAssignedItemOr(index, attr, fallback="") {
        const item = getAssignedItem(index)
        return item ? item[attr] : fallback
    }

    function toggleSelectedTag(tag) {
        if (tagExts.selected.has(tag)) {
            tagExts.selected.delete(tag)
        } else {
            tagExts.selected.add(tag)
        }
        updateBarData()
    }
    function toggleHiddenTag(tag, event) {
        if (event) event.preventDefault()

        if (tagExts.hidden.has(tag)) {
            tagExts.hidden.delete(tag)
        } else {
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
            CTXT_OPTIONS.items
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
            CTXT_OPTIONS.items
        )
    }
    function updateBarData() {
        barData.value = tags.value.map(list => {
            return list.map(t => ([t.id, t.name, tagExts.selected.has(t.id) ? 2 : 1]))
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

    function startGame() {
        const starttime = Date.now()
        sounds.play(SOUND.START)
        state.value = STATES.LOADING

        clear()

        const allItems = DM.getData("items", false)
        const subset = randomChoice(allItems, numItems.value)
        items.value = subset;

        const tmp = subset.map(d => d.allTags.slice())
        shuffling.value = randomShuffle(range(tmp.length))
        tags.value = shuffling.value.map(i => tmp[i])

        barDomain.value = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
        updateBarData()

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
        sounds.fadeAll()
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
.tag-hidden {
    opacity: 0.15;
}
</style>
