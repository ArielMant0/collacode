<template>
    <div ref="el" style="width: 100%;">
        <div v-if="state === STATES.START" class="d-flex align-center justify-center" style="height: 80vh;">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>

        <div v-else-if="state === STATES.LOADING" class="d-flex align-center justify-center" style="height: 80vh;">
            <div class="game-loader"></div>
        </div>

        <div v-else-if="state === STATES.INGAME" class="d-flex flex-column align-center">

            <div class="d-flex justify-center align-center">
                <v-sheet
                    style="font-size: large;"
                    class="mt-4 mb-4 pt-4 pb-4 pr-8 pl-8"
                    rounded="sm"
                    :style="{ color: numQuestion > maxQuestions ? 'lightgrey' : 'inherit' }"
                    :color="numQuestion <= maxQuestions && maxQuestions-numQuestion < 2 ? '#ed5a5a' : 'surface-light'">
                    Question {{ Math.min(numQuestion, maxQuestions) }} / {{ maxQuestions }}
                </v-sheet>
            </div>


            <div class="d-flex flex-column align-center" style="width: 100%;">

                <div class="d-flex justify-space-between" style="width: 100%;">

                    <div>

                        <div class="d-flex justify-space-between align-center pa-2 pl-4 pr-4 mb-2" style="border: 2px solid #efefef; border-radius: 5px;">
                            <div>Your Guess:  <b>{{ logic.askItem ? logic.askItem.name : '...' }}</b></div>
                            <v-btn class="ml-4" :color="logic.askItem?'primary':'default'" :disabled="!logic.askItem" @click="stopGame">submit</v-btn>
                        </div>

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

                            <v-tooltip text="clear excluded" location="top" open-delay="300">
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
                        </div>

                        <div class="d-flex flex-wrap"  :style="{ maxWidth: (itemsWidth+10)+'px', overflowY: 'auto' }">
                            <v-sheet v-for="item in items" :key="item.id" class="mr-1 mb-1 pa-1 cursor-pointer secondary-on-hover" rounded="sm"
                                @click="setAskItem(item)"
                                :style="{
                                    opacity: logic.excluded.has(item.id) ? 0.15 : 1,
                                    border: '2px solid ' + (matches.has(item.id) ? 'red' : 'white'),
                                    backgroundColor: logic.askItem && logic.askItem.id === item.id ? '#078766 !important' : null
                                }"
                                @contextmenu="e => onRightClickItem(item, e)">
                                <div class="text-dots text-caption" :style="{ maxWidth: imageWidth+'px'}">{{ item.name }}</div>
                                <v-img
                                    cover
                                    :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                                    :lazy-src="imgUrlS"
                                    :width="imageWidth"
                                    :height="Math.floor(imageWidth*0.5)"/>
                            </v-sheet>
                        </div>
                    </div>

                    <div>
                        <div class="d-flex justify-space-between align-center mb-2 pa-2 pl-4 pr-4" style="border: 2px solid #efefef; border-radius: 5px;">
                            <div>
                                Does the {{ app.itemName }} have
                                {{ logic.askTag && logic.askTag.is_leaf == 1 ? 'tag' : 'tags from' }}
                                <b>{{ logic.askTag ? logic.askTag.name : '...' }}</b> ?
                            </div>
                            <v-btn class="ml-4" :color="logic.askTag === null?'default':'primary'" :disabled="logic.askTag === null" @click="askTag">ask</v-btn>
                        </div>

                        <TreeMap v-if="tags.length > 0"
                            :data="tags"
                            :time="treeTime"
                            :width="treeWidth"
                            :height="treeHeight"
                            :selectable="numQuestion <= maxQuestions"
                            :selected="logic.askTag ? [logic.askTag.id] : []"
                            collapsible
                            color-attr="color"
                            frozen-color="#e02d2d"
                            hide-color-filter
                            @click="setAskTag"
                            />
                    </div>
                </div>
            </div>
        </div>

        <div v-else-if="state === STATES.END" class="d-flex flex-column align-center justify-center mt-8" style="min-height: 50vh;">

            <v-sheet class="mt-2 d-flex align-center">
                <v-icon
                    size="60"
                    class="mr-4"
                    :icon="answerCorrect ? 'mdi-check-bold' : 'mdi-close-circle-outline'"
                    :color="answerCorrect ? 'primary' : 'error'"/>

                <span v-if="answerCorrect">Yay, you found the right game!</span>
                <span v-else>Wrong, maybe next time ...</span>
            </v-sheet>

            <div class="d-flex justify-center align-center">
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

            <div class="d-flex flex-column justify-center">
                <div style="text-align: right;">
                    <span style="width: 150px;" class="mr-2"></span>
                    <MiniTree :node-width="5" :selectable="false"/>
                </div>
                <div v-if="!answerCorrect" style="text-align: right;" class="d-flex align-center mb-2">
                    <span style="width: 150px;" class="mr-2 text-caption">{{ logic.askItem.name }}</span>
                    <BarCode
                        :data="barData.guess"
                        :domain="barData.domain"
                        binary
                        hideHighlight
                        id-attr="0"
                        value-attr="2"
                        name-attr="1"
                        selected-color="red"
                        :binary-color-fill="settings.lightMode ? '#000000' : '#ffffff'"
                        :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                        :width="5"
                        :height="20"/>
                </div>
                <div style="text-align: right;" class="d-flex align-center">
                    <span style="width: 150px;" class="mr-2 text-caption">{{ gameData.target.name }}</span>
                    <BarCode
                        :data="barData.target"
                        :domain="barData.domain"
                        binary
                        hideHighlight
                        id-attr="0"
                        value-attr="2"
                        name-attr="1"
                        selected-color="red"
                        :binary-color-fill="settings.lightMode ? '#000000' : '#ffffff'"
                        :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                        :width="5"
                        :height="20"/>
                </div>
                <!-- <div style="text-align: right;">
                    <span style="width: 200px;" class="mr-2 text-caption">questions</span>
                    <BarCode
                        :data="barData.questions"
                        :domain="barData.domain"
                        hideHighlight
                        id-attr="0"
                        value-attr="2"
                        name-attr="1"
                        selected-color="red"
                        categorical
                        :color-scale="[COLOR.GREEN, COLOR.YELLOW, COLOR.RED]"
                        :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                        :width="5"
                        :height="20"/>
                </div> -->
            </div>

            <v-sheet class="mt-4 d-flex flex-column align-center" style="min-width: 500px;">
                <h2>Questions & Answers</h2>
                <table style="width: 100%;" class="mt-2 mb-1">
                    <tbody>
                        <tr v-for="(q, idx) in logic.history" :key="'q_'+idx">
                            <td>{{ q.name }}</td>
                            <td><v-icon icon="mdi-circle" :color="q.color" size="small"/></td>
                            <td>
                                <span v-if="q.result[0] === true">correct</span>
                                <span v-else-if="q.result[1] === true">sibling</span>
                                <span v-else>wrong</span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </v-sheet>

            <div class="d-flex align-center justify-center" style="margin-top: 200px;">
                <v-btn class="mr-1" size="x-large" color="error" @click="close">close</v-btn>
                <v-btn class="ml-1" size="x-large" color="primary" @click="startGame">play again</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { DIFFICULTY, SOUND, useGames } from '@/store/games';
    import { computed, onMounted, reactive, toRaw, watch } from 'vue';
    import { Chance } from 'chance';
    import imgUrlS from '@/assets/__placeholder__s.png'
    import DM from '@/use/data-manager';
    import { useElementSize, useWindowSize } from '@vueuse/core';
    import TreeMap from '../vis/TreeMap.vue';
    import { useApp } from '@/store/app';
    import { POSITION, useToast } from 'vue-toastification';
    import { useTooltip } from '@/store/tooltip';
    import BarCode from '../vis/BarCode.vue';
    import { useTimes } from '@/store/times';
    import { useSettings } from '@/store/settings';
    import MiniTree from '../vis/MiniTree.vue';

    const STATES = Object.freeze({
        START: 0,
        LOADING: 1,
        INGAME: 2,
        END: 3
    })

    const COLOR = Object.freeze({
        GREEN: "#238b45",
        YELLOW: "#e8e120",
        RED: "#e31a1c",
    })

    const props = defineProps({
        difficulty: {
            type: Number,
            required: true
        },
    })

    const emit = defineEmits(["end"])

    // difficulty settings
    const numItems = computed(() => {
        switch (props.difficulty) {
            case DIFFICULTY.EASY: return 25;
            case DIFFICULTY.NORMAL: return 35;
            case DIFFICULTY.HARD: return 50;
        }
    })
    const maxQuestions = ref(10)
    // const maxQuestions = computed(() => {
    //     switch (props.difficulty) {
    //         case DIFFICULTY.EASY: return 15;
    //         case DIFFICULTY.NORMAL: return 10;
    //         case DIFFICULTY.HARD: return 5;
    //     }
    // })

    // stores
    const games = useGames()
    const toast = useToast()
    const app = useApp()
    const tt = useTooltip()
    const times = useTimes()
    const settings = useSettings()

    // elements
    const el = ref(null)
    const elSize = useElementSize(el)
    const wSize = useWindowSize()

    const imageWidth = computed(() => Math.max(80, Math.floor(itemsWidth.value / 5)-15))
    const itemsWidth = computed(() => Math.max(300, elSize.width.value * 0.35))
    const treeWidth = computed(() => Math.max(400, elSize.width.value - itemsWidth.value - 50))
    const treeHeight = computed(() => Math.max(800, wSize.height.value * 0.80))

    // optics and settings
    const items = ref([])
    const treeTime = ref(0)

    // game related stuff
    const state = ref(STATES.START)
    const gameData = reactive({
        target: null,
        targetIndex: null,
        tagsYes: [],
        tagsNo: [],
    })
    const logic = reactive({
        askTag: null,
        askItem: null,
        history: [],
        excluded: new Set()
    })
    const matches = computed(() => {
        if (search.value && search.value.length > 0) {
            const regex = new RegExp(search.value, "gi")
            return new Set(items.value.filter(d =>regex.test(d.name)).map(d => d.id))
        }
        return new Set()
    })

    const answerCorrect = computed(() => logic.askItem && gameData.target ? logic.askItem.id === gameData.target.id : false)
    const barData = reactive({
        guess: [],
        target: [],
        questions: [],
        domain: []
    })

    const needsReload = ref(false)

    const tags = ref([])
    const search = ref("")
    const numQuestion = ref(0)

    ///////////////////////////////////////////////////////////////////////////
    // Functions
    ///////////////////////////////////////////////////////////////////////////

    function setAskItem(item) {
        if (item) {
            logic.askItem = logic.askItem && logic.askItem.id === item.id ? null : item;
            if (logic.askItem && logic.excluded.has(item.id)) {
                logic.excluded.delete(item.id)
            }
            if (numQuestion.value > maxQuestions.value && logic.askItem) {
                stopGame()
            }
        }
    }

    function setAskTag(tag) {
        if (numQuestion.value > maxQuestions.value) {
            return toast.warning("you can no longer ask about tags")
        }
        const asked = logic.history.find(d => d.id === tag.id)
        if (asked) {
            return toast.info("you already asked about " + tag.name)
        }
        logic.askTag = logic.askTag && logic.askTag.id === tag.id ? null : tag;
    }
    function askTag() {
        if (logic.askTag && gameData.target) {
            const tid = logic.askTag.id;
            const isLeaf = logic.askTag.is_leaf === 1

            const thetag = tags.value.find(d => d.id === tid)
            const hasTag = gameData.target.allTags.find(d => isLeaf ? d.id === tid : d.path.includes(tid)) !== undefined
            let inParent = false;

            if (hasTag) {
                thetag.color = COLOR.GREEN
            } else {
                const p = logic.askTag.parent
                inParent = gameData.target.allTags.find(d => d.path.includes(p)) !== undefined
                thetag.color = isLeaf && inParent ? COLOR.YELLOW : COLOR.RED
            }
            treeTime.value = Date.now()

            logic.history.push({
                id: tid,
                name: logic.askTag.name,
                result: [hasTag, inParent],
                color: thetag.color,
                value: hasTag ? 1 : (inParent ? 2 : 3)
            })

            logic.askTag = null;
            numQuestion.value++

            if (numQuestion.value > maxQuestions.value) {
                if (logic.askItem) {
                    stopGame()
                } else {
                    // TODO: play other sound
                    games.playSingle(SOUND.START)
                }
            } else {
                if (hasTag) {
                    toast.success("Correct!", { position: POSITION.TOP_CENTER, timeout: 2000 })
                    games.playSingle(SOUND.WIN)
                } else {
                    toast.error("Wrong!", { position: POSITION.TOP_CENTER, timeout: 2000 })
                    games.playSingle(SOUND.FAIL)
                }
            }
        }
    }

    function startGame() {
        tt.hide()
        const starttime = Date.now()
        games.playSingle(SOUND.START)
        state.value = STATES.LOADING
        // reset these values
        clear()
        // pick data
        readData()

        const chance = new Chance()
        const idx = chance.integer({ min: 0, max: items.value.length-1 })

        gameData.target = items.value[idx]
        gameData.targetIndex = idx

        setTimeout(() => {
            numQuestion.value = 1;
            state.value = STATES.INGAME
        }, Date.now() - starttime < 500 ? 1000 : 50)
    }

    function stopGame() {
        tt.hide()
        barData.target = makeBarCodeData(gameData.target)
        barData.guess = logic.askItem ? makeBarCodeData(logic.askItem) : []
        barData.questions = logic.history.map(d => ([d.id, d.name, d.value]))
        state.value = STATES.END;
        if (answerCorrect.value) {
            games.playSingle(SOUND.WIN)
        } else {
            games.playSingle(SOUND.FAIL)
        }
    }

    function close() {
        tt.hide()
        reset()
        emit("end")
    }

    function makeBarCodeData(item) {
        return item.allTags.map(t => [t.id, t.name, 1])
    }

    function clear() {
        search.value = ""
        numQuestion.value = 0;
        gameData.target = null
        gameData.targetIndex = null
        gameData.tagsYes = []
        gameData.tagsNo = []
        logic.askTag = null;
        logic.askItem = null
        logic.history = []
        logic.excluded.clear()
        tags.value.forEach(t => delete t.color)
    }
    function reset() {
        needsReload.value = false;
        state.value = STATES.START;
        clear()
    }

    function onRightClickItem(item, event) {
        event.preventDefault()
        if (item) {
            if (logic.excluded.has(item.id)) {
                logic.excluded.delete(item.id)
            } else {
                logic.excluded.add(item.id)
            }
            treeTime.value = Date.now()
        }
    }

    function readData() {
        const allItems = DM.getDataBy("items", d => d.allTags.length > 0)
        const chance = new Chance()
        items.value = chance.shuffle(chance.pickset(allItems, numItems.value))
        if (tags.value.length === 0 || needsReload.value) {
            tags.value = DM.getData("tags", false).map(d => Object.assign({}, d))
            barData.domain = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
            needsReload.value = false
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

    watch(() => Math.max(times.all, times.tags, times.tagging), () => needsReload.value = true)

</script>