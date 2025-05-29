<template>
    <div ref="el" style="width: 100%;">
        <div v-if="state === STATES.START" class="d-flex align-center justify-center" style="height: 80vh;">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>

        <div v-else-if="state === STATES.LOADING"class="d-flex align-center justify-center">
            <LoadingScreen
                :messages="[
                    'ask about tags to find the target item',
                    'you can also about parent tags (intermediate nodes)',
                    'right-click items or tags to de-emphasize them',
                    'click on a tag in the treemap and then use the <b>ask</b> button to ask about tags',
                    'in hard mode, sibling information is not available',
                ]"/>
        </div>


        <div v-else-if="state === STATES.EXCLUDE" class="d-flex flex-column align-center">
            <v-sheet style="font-size: x-large;" class="mb-8 pt-4 pb-4 pr-8 pl-8" rounded="sm" color="surface-light">
                {{ excluded.size }} / {{ numExcludes }} {{ app.itemName }} exclusions used
            </v-sheet>

            <h4>{{ capitalize(app.itemName+'s') }} for this round</h4>
            <div class="d-flex flex-wrap justify-center" :style="{ width: (Math.floor(numItems/3)*170)+'px', minWidth: '335px', maxWidth: '95%' }">
                <v-sheet v-for="item in items" :key="'exct_'+item.id" class="pa-1 secondary-on-hover mr-1 mb-1">
                    <ItemTeaser :item="item" :width="160" :height="80" show-name prevent-open @click="excludeItem(item.id)"/>
                </v-sheet>
            </div>

            <h4 class="mt-8">Excluded {{ app.itemName }}s</h4>
            <div class="d-flex flex-wrap justify-center" :style="{ width: (Math.floor(numItems/3)*170)+'px', minWidth: '335px', maxWidth: '95%' }">
                <v-sheet v-for="id in excluded" :key="'exc_'+id" class="pa-1 mr-1 mb-1" color="error">
                    <ItemTeaser :id="id" :width="160" :height="80" show-name prevent-click/>
                </v-sheet>
            </div>

            <v-btn size="x-large" color="primary" class="mt-4" @click="startRound">start</v-btn>
        </div>

        <div v-else-if="state === STATES.INGAME" class="d-flex flex-column align-center">

            <div class="d-flex justify-center align-center mb-4">

                <div class="d-flex flex-column justify-center align-end mr-4" style="width: 200px;">

                    <div class="d-flex align-center text-caption">
                        <span><i>reset hidden {{ app.itemName }}s</i></span>
                        <v-tooltip :text="'clear hidden '+app.itemName+'s'" location="top" open-delay="300">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props"
                                    icon="mdi-delete"
                                    class="ml-2"
                                    color="error"
                                    size="sm"
                                    rounded="sm"
                                    variant="text"
                                    density="compact"
                                    @click="logic.excluded.clear()"/>
                            </template>
                        </v-tooltip>
                    </div>

                    <div class="d-flex align-center text-caption">
                        <span><i>reset hidden tags</i></span>
                        <v-tooltip text="reset hidden tags" location="top" open-delay="300">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props"
                                    icon="mdi-delete"
                                    class="ml-2"
                                    size="sm"
                                    color="error"
                                    rounded="sm"
                                    variant="text"
                                    density="compact"
                                    @click="logic.hiddenTags.clear()"/>
                            </template>
                        </v-tooltip>
                    </div>
                </div>

                <v-sheet
                    style="font-size: large;"
                    class=" pt-4 pb-4 pr-8 pl-8"
                    rounded="sm"
                    :color="numQuestion === maxQuestions ? '#ed5a5a' : 'surface-light'">

                    <span v-if="numQuestion <= maxQuestions" :style="{ color: numQuestion > maxQuestions ? 'lightgrey' : 'inherit' }">Question {{ numQuestion }} / {{ maxQuestions }}</span>
                    <span v-else>Make Your Guess</span>
                </v-sheet>

                <div class="d-flex flex-column align-start text-ww text-caption ml-4" style="width: 200px; font-style: italic;">
                    <div>
                        <v-icon :color="GR_COLOR.RED" icon="mdi-chart-tree" class="mr-1"/> {{ app.itemName }} does <b>not</b> have tag
                    </div>
                    <div v-if="difficulty !== DIFFICULTY.HARD">
                        <v-icon :color="GR_COLOR.YELLOW" icon="mdi-chart-tree" class="mr-1"/> {{ app.itemName }} has sibling tag
                    </div>
                    <div>
                        <v-icon :color="GR_COLOR.GREEN" icon="mdi-chart-tree" class="mr-1"/> {{ app.itemName }} has tag
                    </div>
                </div>
            </div>


            <div class="d-flex flex-column align-center" style="width: 100%;">

                <div class="d-flex justify-space-between" style="width: 100%;">

                    <div>
                        <div class="d-flex justify-space-between align-center pa-2 pl-4 pr-4 mb-2 bordered-grey-light" style="border-radius: 5px;">
                            <div>Your Guess:  <b>{{ logic.askItem ? logic.askItem.name : '...' }}</b></div>
                            <v-btn class="ml-4" :color="logic.askItem?'primary':'default'" :disabled="!logic.askItem" @click="stopGame">submit</v-btn>
                        </div>

                        <v-text-field v-model="search"
                            :label="'Search for '+app.itemName+'s'"
                            prepend-inner-icon="mdi-magnify"
                            variant="outlined"
                            density="compact"
                            class="mb-1"
                            clearable
                            hide-details
                            single-line/>

                        <div class="d-flex flex-wrap"  :style="{ maxWidth: (itemsWidth+10)+'px', overflowY: 'auto' }">
                            <v-sheet v-for="item in items" :key="item.id" class="mr-1 mb-1 pa-1 cursor-pointer secondary-on-hover" rounded
                                @click="setAskItem(item)"
                                @contextmenu="e => onRightClickItem(item, e)"
                                :style="{
                                    opacity: !isChosen(item.id) && logic.excluded.has(item.id) ? 0.15 : 1,
                                    border: '2px solid ' + (matches.has(item.id) ? 'red' : borderColor),
                                    backgroundColor: isChosen(item.id) ? primaryColor : null
                                }">
                                <div class="text-dots text-caption" :style="{ maxWidth: imageWidth+'px', color: isChosen(item.id) ? 'white' : 'inherit' }">{{ item.name }}</div>
                                <v-img
                                    cover
                                    :src="item.teaser ? mediaPath('teaser', item.teaser) : imgUrlS"
                                    :lazy-src="imgUrlS"
                                    :width="imageWidth"
                                    :height="Math.floor(imageWidth*0.5)"/>
                            </v-sheet>
                        </div>
                    </div>

                    <div>
                        <div class="d-flex justify-space-between align-center mb-2 pa-2 pl-4 pr-4 bordered-grey-light" style="border-radius: 5px;">
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
                            :selected="logic.askTag ? [logic.askTag.id] : []"
                            :hidden="logic.hiddenTags"
                            collapsible
                            color-attr="color"
                            icon-attr="icon"
                            :icon-scale="0.75"
                            frozen-color="#e02d2d"
                            :color-map="treeColorScale"
                            hide-color-filter
                            @click="setAskTag"
                            @right-click="toggleHideTag"
                            />
                    </div>
                </div>
            </div>
        </div>

        <div v-else-if="state === STATES.END" class="d-flex flex-column align-center justify-center mt-8" style="min-height: 50vh;">

            <v-sheet class="mt-2 mb-4 d-flex align-center">
                <GameResultIcon :result="answerCorrect" show-effects show-text/>
            </v-sheet>

            <div class="d-flex justify-center align-center">
                <div v-if="logic.askItem">
                    <div><b>Your Guess:</b></div>
                    <v-sheet class="ma-1" rounded="sm">
                        <ItemTeaser :item="logic.askItem" :width="imageWidth*2" :height="imageWidth"/>
                        <div class="text-dots" :style="{ maxWidth: (imageWidth*2)+'px' }">{{ logic.askItem.name }}</div>
                    </v-sheet>
                </div>

                <div>
                    <b>The Solution:</b>
                    <v-sheet class="ma-1" rounded="sm">
                        <ItemTeaser :item="gameData.target" :width="imageWidth*2" :height="imageWidth"/>
                        <div class="text-dots" :style="{ maxWidth: (imageWidth*2)+'px' }">{{ gameData.target.name }}</div>
                    </v-sheet>
                </div>
            </div>

            <div class="d-flex align-center justify-center mt-8 mb-8">
                <v-btn class="mr-1" size="large" color="error" @click="close">close</v-btn>
                <v-btn class="ml-1" size="large" color="primary" @click="startGame">play again</v-btn>
            </div>

            <div class="d-flex flex-column justify-center">
                <div style="text-align: right;">
                    <span style="width: 150px;" class="mr-2"></span>
                    <MiniTree :node-width="5" :selectable="false"
                        value-attr="from_id"
                        value-agg="none"
                        categorical
                        :value-data="barData.questions"
                        :value-domain="[0, 1, 2, 3]"
                        :value-scale="[
                            settings.lightMode ? 'black' : 'white',
                            GR_COLOR.GREEN,
                            GR_COLOR.YELLOW,
                            GR_COLOR.RED
                        ]"/>
                </div>
                <div v-if="!answerCorrect" style="text-align: right;" class="d-flex align-center mb-2">
                    <span style="width: 150px;" class="mr-2 text-caption">{{ logic.askItem.name }}</span>
                    <BarCode
                        :item-id="logic.askItem.id"
                        :data="barData.guess"
                        :domain="barData.domain"
                        categorical
                        hide-highlight
                        hide-value
                        selectable
                        @right-click="(t, e, has) => openTagContext(logic.askItem.id, t, e, has)"
                        id-attr="0"
                        value-attr="2"
                        name-attr="1"
                        selected-color="red"
                        :color-domain="[1, 2]"
                        :color-scale="[
                            settings.lightMode ? 'black' : 'white',
                            GR_COLOR.GREEN
                        ]"
                        :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                        :width="5"
                        :height="20"/>
                </div>
                <div style="text-align: right;" class="d-flex align-center">
                    <span style="width: 150px;" class="mr-2 text-caption">{{ gameData.target.name }}</span>
                    <BarCode
                        :item-id="gameData.target.id"
                        :data="barData.target"
                        :domain="barData.domain"
                        categorical
                        hide-highlight
                        selectable
                        hide-value
                        @right-click="(t, e, has) => openTagContext(gameData.target.id, t, e, has)"
                        id-attr="0"
                        value-attr="2"
                        name-attr="1"
                        selected-color="red"
                        :color-domain="[1, 2]"
                        :color-scale="[
                            settings.lightMode ? 'black' : 'white',
                            GR_COLOR.GREEN
                        ]"
                        :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                        :width="5"
                        :height="20"/>
                </div>
            </div>

            <v-sheet class="mt-4 d-flex flex-column align-center" style="min-width: 500px;">
                <h2>Questions & Answers</h2>
                <table style="width: 100%;" class="mt-2 mb-1">
                    <tbody>
                        <tr v-for="(q, idx) in logic.history" :key="'q_'+idx">
                            <td>
                                <ObjectionButton
                                    :item-id="gameData.target.id"
                                    :tag-id="q.id"
                                    :action="getQuestionAction(q)"/>
                            </td>
                            <td>
                                <TagText :id="q.id" :item-id="gameData.target.id"></TagText>
                            </td>
                            <td>
                                <v-icon :icon="q.icon" :color="q.color" size="small"/>
                            </td>
                            <td>
                                <span v-if="q.result === GAME_RESULT.WIN">correct</span>
                                <span v-else-if="q.result === GAME_RESULT.DRAW">sibling</span>
                                <span v-else>wrong</span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </v-sheet>
        </div>
    </div>
</template>

<script setup>
    import { pointer } from 'd3';
    import { DIFFICULTY, GAME_RESULT, GR_COLOR, STATES, useGames } from '@/store/games';
    import { computed, onMounted, reactive, watch } from 'vue';
    import imgUrlS from '@/assets/__placeholder__s.png'
    import DM from '@/use/data-manager';
    import { useElementSize, useWindowSize } from '@vueuse/core';
    import TreeMap from '../vis/TreeMap.vue';
    import { OBJECTION_ACTIONS, useApp } from '@/store/app';
    import { POSITION, useToast } from 'vue-toastification';
    import { useTooltip } from '@/store/tooltip';
    import BarCode from '../vis/BarCode.vue';
    import { useTimes } from '@/store/times';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import MiniTree from '../vis/MiniTree.vue';
    import { useTheme } from 'vuetify/lib/framework.mjs';
    import { useSounds, SOUND } from '@/store/sounds';
    import { storeToRefs } from 'pinia';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import { randomChoice, randomInteger, randomShuffle } from '@/use/random';
    import { capitalize, mediaPath } from '@/use/utility';
    import TagText from '../tags/TagText.vue';
    import GameResultIcon from './GameResultIcon.vue';
    import LoadingScreen from './LoadingScreen.vue';
    import ObjectionButton from '../objections/ObjectionButton.vue';

    const emit = defineEmits(["end", "close"])

    // stores
    const sounds = useSounds()
    const toast = useToast()
    const app = useApp()
    const tt = useTooltip()
    const times = useTimes()
    const settings = useSettings()
    const theme = useTheme()
    const games = useGames()

    const primaryColor = computed(() => theme.current.value.colors.primary)
    const borderColor = computed(() => theme.current.value.colors.background)

    // difficulty settings
    const { difficulty } = storeToRefs(games)

    const numItems = computed(() => {
        const size = DM.getSizeBy("items", d => d.allTags.length > 0)
        switch (difficulty.value) {
            case DIFFICULTY.EASY:
                return Math.max(5, Math.min(20, Math.round(size*0.1)));
            case DIFFICULTY.NORMAL:
                return Math.max(5, Math.min(24, Math.round(size*0.15)));
            case DIFFICULTY.HARD:
                return Math.max(5, Math.min(32, Math.round(size*0.2)));
        }
    })
    // const maxQuestions = ref(10)
    const maxQuestions = computed(() => {
        switch (difficulty.value) {
            case DIFFICULTY.EASY:
            case DIFFICULTY.NORMAL:
            case DIFFICULTY.HARD:
                return 10;
        }
    })

    const allowExclude = computed(() => difficulty.value !== DIFFICULTY.HARD)
    const numExcludes = computed(() => {
        switch (difficulty.value) {
            case DIFFICULTY.EASY:
                return Math.min(10, Math.max(1, Math.floor(numItems.value * 0.5)));
            case DIFFICULTY.NORMAL:
                return Math.min(5, Math.max(1, Math.floor(numItems.value * 0.25)));
            case DIFFICULTY.HARD:
                return 0;
        }
    })

    // elements
    const el = ref(null)
    const elSize = useElementSize(el)
    const wSize = useWindowSize()

    const imageWidth = computed(() => Math.max(80, Math.floor(itemsWidth.value / 4)-15))
    const itemsWidth = computed(() => {
        const mul = wSize.width.value <= 1600 ? 0.2 : 0.25
        return Math.max(300, elSize.width.value * mul)
    })
    const treeWidth = computed(() => Math.max(400, elSize.width.value - itemsWidth.value - 30))
    const treeHeight = computed(() => Math.max(800, wSize.height.value * 0.75))

    // optics and settings
    const items = ref([])
    const treeTime = ref(0)
    const excluded = reactive(new Set())

    function treeColorScale(d3obj, h, light) {
        const n = Math.max(3, Math.min(9, h))
        const domain = d3obj.range(1, n+1)
        const scale = d3obj.scaleOrdinal(d3obj.schemeGreys[n]).domain(domain)
        const r = domain.map(scale)
        return light ? r : r.reverse()
    }

    // game related stuff
    const state = ref(STATES.START)
    const gameData = reactive({
        target: null,
        targetIndex: null,
        tagsYes: new Set(),
    })
    const logic = reactive({
        askTag: null,
        askItem: null,
        history: [],
        excluded: new Set(),
        hiddenTags: new Set()
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
        questions: {},
        domain: []
    })

    const needsReload = ref(false)

    const tags = ref([])
    const search = ref("")
    const numQuestion = ref(0)

    ///////////////////////////////////////////////////////////////////////////
    // Functions
    ///////////////////////////////////////////////////////////////////////////

    function getQuestionAction(q) {
        if (q.result === GAME_RESULT.WIN) {
            return OBJECTION_ACTIONS.REMOVE
        }
        return q.leaf ? OBJECTION_ACTIONS.ADD : OBJECTION_ACTIONS.DISCUSS
    }

    function isChosen(id) {
        return logic.askItem && logic.askItem.id === id
    }

    function setAskItem(item) {
        if (item) {
            logic.askItem = logic.askItem && logic.askItem.id === item.id ? null : item;
            sounds.play(SOUND.PLOP)
            if (logic.askItem && logic.excluded.has(item.id)) {
                logic.excluded.delete(item.id)
            }
        }
    }

    function toggleHideTag(tag) {
        if (logic.hiddenTags.has(tag.id)) {
            logic.hiddenTags.delete(tag.id)
            sounds.play(SOUND.PLOP)
        } else {
            logic.hiddenTags.add(tag.id)
            sounds.play(SOUND.CLICK_REVERB)
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
        sounds.play(SOUND.PLOP)
    }
    function askTag() {

        if (logic.askTag !== null && gameData.target !== null) {
            const tid = logic.askTag.id;
            const isLeaf = logic.askTag.is_leaf === 1

            const thetag = tags.value.find(d => d.id === tid)
            const hasTag = gameData.target.allTags.find(d => isLeaf ? d.id === tid : d.path.includes(tid)) !== undefined
            let inParent = false, result, tagColor;

            if (hasTag) {
                thetag.color = GR_COLOR.GREEN
                thetag.icon = [games.resultIconPath(GAME_RESULT.WIN)]
                gameData.tagsYes.add(tid)
                tagColor = thetag.color
                result = GAME_RESULT.WIN
            } else {
                const p = logic.askTag.parent
                inParent = gameData.target.allTags.find(d => d.id !== tid && d.path.includes(p)) !== undefined

                const leafInP = isLeaf && inParent
                if (difficulty.value !== DIFFICULTY.HARD) {
                    thetag.color = leafInP ? GR_COLOR.YELLOW : GR_COLOR.RED
                    thetag.icon = [games.resultIconPath(leafInP ? GAME_RESULT.DRAW : GAME_RESULT.LOSS)]
                    tagColor = thetag.color
                } else {
                    thetag.color = GR_COLOR.RED
                    thetag.icon = [games.resultIconPath(GAME_RESULT.LOSS)]
                    tagColor = leafInP ? GR_COLOR.YELLOW : GR_COLOR.RED
                }

                result = isLeaf && inParent ? GAME_RESULT.DRAW : GAME_RESULT.LOSS
                // when in easy mode, color wrong siblings red too
                if (isLeaf && !inParent && difficulty.value === DIFFICULTY.EASY) {
                    const siblings = tags.value.filter(d => d.is_leaf === 1 && d.id !== tid && d.path.includes(p))
                    siblings.forEach(t => {
                        t.color = GR_COLOR.RED
                        t.icon = [games.resultIconPath(GAME_RESULT.LOSS)]
                    })
                }
            }
            treeTime.value = Date.now()

            logic.history.push({
                id: tid,
                leaf: thetag.is_leaf === 1,
                name: logic.askTag.name,
                result: result,
                icon: games.resultIcon(result),
                color: tagColor,
                value: hasTag ? 1 : (inParent ? 2 : 3)
            })

            logic.askTag = null;
            numQuestion.value++

            if (numQuestion.value > maxQuestions.value) {
                toast.info("No questions left, make your guess", { position: POSITION.TOP_CENTER, timeout: 2000 })
                sounds.play(SOUND.DRAMATIC)
            } else {
                if (numQuestion.value === maxQuestions.value) {
                    sounds.play(SOUND.OBACHT)
                }
                if (hasTag) {
                    toast.success("Correct!", { position: POSITION.TOP_CENTER, timeout: 2000 })
                    sounds.play(SOUND.WIN_MINI)
                } else {
                    toast.error("Wrong!", { position: POSITION.TOP_CENTER, timeout: 2000 })
                    sounds.play(SOUND.FAIL_MINI)
                }
            }
        }
    }

    function excludeItem(id) {
        if (excluded.size < numExcludes.value) {
            excluded.add(id)
            const idx = items.value.findIndex(d => d.id === id)
            if (idx >= 0) {
                sounds.play(SOUND.PLOP)
                const existing = new Set(items.value.map(d => d.id))
                const allItems = DM.getDataBy("items", d => {
                    return d.allTags.length > 0 &&
                        !existing.has(d.id) &&
                        !excluded.has(d.id)
                })
                const replace = randomChoice(allItems, 1)
                items.value[idx] = replace
                if (gameData.targetIndex === idx) {
                    gameData.target = replace;
                }
            } else {
                console.error("cannot find item with id:", id)
            }
        } else {
            toast.warning("you used up all your exclusions", { position: POSITION.TOP_CENTER, timeout: 2000 })
        }
    }
    function startRound() {
        const starttime = Date.now()
        sounds.play(SOUND.START_SHORT)
        state.value = STATES.LOADING

        setTimeout(() => {
            numQuestion.value = 1;
            state.value = STATES.INGAME
        }, Date.now() - starttime > 500 ? 50 : 1000)
    }
    function tryStartRound() {

        let allItems, idx;
        if (allowExclude.value && excluded.size > 0) {
            allItems = DM.getDataBy("items", d => d.allTags.length > 0 && !excluded.has(d.id))
        } else {
            allItems = DM.getDataBy("items", d => d.allTags.length > 0)
        }

        if (tags.value.length === 0 || needsReload.value) {
            tags.value = DM.getData("tags", false).map(d => Object.assign({}, d))
            tags.value.forEach(d => d.icon = [])
            barData.domain = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
            needsReload.value = false
        }


        if (allItems.length > numItems.value) {
            items.value = randomShuffle(randomChoice(allItems, numItems.value))
        } else {
            items.value = allItems
        }
        idx = randomInteger(0, items.value.length-1)

        gameData.target = items.value[idx]
        gameData.targetIndex = idx

        if (allowExclude.value) {
            state.value = STATES.EXCLUDE
        } else {
            startRound()
        }
    }
    function startGame() {
        tt.hide()
        sounds.stopAll()
        sounds.play(SOUND.START)
        state.value = STATES.LOADING
        // reset these values
        clear()

        // start the round / exclusion process
        tryStartRound()
    }

    function stopGame() {
        tt.hide()
        barData.target = makeBarCodeData(gameData.target)
        barData.guess = logic.askItem ? makeBarCodeData(logic.askItem) : []
        barData.questions = {}
        logic.history.forEach(d => barData.questions[d.id] = d.value)

        state.value = STATES.END;
        if (answerCorrect.value) {
            sounds.play(SOUND.WIN)
        } else {
            sounds.play(SOUND.FAIL)
        }
        emit(
            "end",
            answerCorrect.value,
            Math.max(0, numQuestion.value-1),
            [{ id: gameData.target.id, correct: answerCorrect.value }]
        )
    }

    function close() {
        tt.hide()
        emit("close")
        reset()
    }

    function openTagContext(itemId, tag, event, has) {
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
    function makeBarCodeData(item) {
        return item.allTags.map(t => ([
            t.id,
            t.name,
            gameData.tagsYes.has(t.id) ? 2 : 1
        ]))
    }

    function clear() {
        search.value = ""
        items.value = []
        numQuestion.value = 0;
        gameData.target = null
        gameData.targetIndex = null
        gameData.tagsYes.clear()
        logic.askTag = null;
        logic.askItem = null;
        logic.history = []
        logic.hiddenTags.clear()
        logic.excluded.clear()
        tags.value.forEach(t => {
            delete t.color
            t.icon = []
        })
        excluded.clear()
        barData.guess = []
        barData.target = []
    }
    function reset() {
        needsReload.value = false;
        state.value = STATES.START;
        clear()
    }

    function onRightClickItem(item, event) {
        event.preventDefault()
        if (item && (!logic.askItem || logic.askItem.id !== item.id)) {
            if (logic.excluded.has(item.id)) {
                logic.excluded.delete(item.id)
                sounds.play(SOUND.PLOP)
            } else {
                logic.excluded.add(item.id)
                sounds.play(SOUND.CLICK_REVERB)
            }
            treeTime.value = Date.now()
        }
    }

    function init() {
        reset()
        startGame()
    }

    onMounted(init)

    watch(difficulty, init)

    watch(() => Math.max(times.all, times.tags, times.tagging), () => needsReload.value = true)

</script>