<template>
    <div>
        <div v-if="state === STATES.START" class="d-flex align-center justify-center" style="height: 80vh;">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>

        <div v-else-if="state === STATES.LOADING" class="d-flex align-center justify-center" style="height: 80vh;">
            <div class="game-loader"></div>
        </div>

        <div v-else-if="state === STATES.INGAME" class="d-flex flex-column justify-center align-center">

            <div class="mt-4 mb-4 d-flex justify-center align-center" style="width: 100%;">
                <div v-for="(_, qi) in questions" :key="'qs_'+qi" class="ml-2 mr-2">
                    <v-icon v-if="qi > gameData.qIndex" color="default">mdi-circle-medium</v-icon>
                    <v-icon v-else-if="qi === gameData.qIndex" :color="answered ? (answeredCorrect ? 'primary' : 'error') :'default'">mdi-circle-slice-8</v-icon>
                    <v-icon v-else-if="gaveCorrectAnswer(qi)" color="primary">mdi-circle</v-icon>
                    <v-icon v-else color="error">mdi-circle</v-icon>
                </div>
            </div>

            <Timer ref="timer" :time-in-sec="timeInSec" @end="stopRound"/>

            <div v-if="activeQ" ref="el" class="d-flex flex-column align-center" style="width: 80%; height: 80vh;">
                <div v-html="activeQ.text" class="mt-8 mb-4"></div>

                <v-sheet v-if="activeQ.item" class="mr-1 mb-1 pa-1" rounded="sm">
                    <div class="text-dots text-caption" :style="{ maxWidth: imageWidth+'px' }">{{ activeQ.item.name }}</div>
                    <v-img
                        cover
                        :src="activeQ.item.teaser ? 'teaser/'+activeQ.item.teaser : imgUrlS"
                        :lazy-src="imgUrlS"
                        :width="imageWidth"
                        :height="Math.floor(imageWidth*0.5)"/>
                </v-sheet>

                <v-sheet v-if="activeQ.tag && showTagDesc" class="mb-6 pa-2 d-flex align-center justify-center text-ww" rounded="sm" color="surface-light">
                    {{ activeQ.tag.description ? activeQ.tag.description : 'no description' }}
                </v-sheet>

                <div v-if="activeQ.itemChoices" class="d-flex flex-wrap align-start align-content-start" :style="{ maxWidth: ((imageWidth+15)*itemsPerRow)+'px' }">
                    <v-sheet v-for="(item, idx) in activeQ.itemChoices" :key="'ai_'+idx+'_'+item.id"
                        class="mr-1 mb-1 pa-1 secondary-on-hover"
                        rounded="sm"
                        @click="chooseAnswer(item.id)"
                        :style="{ cursor: answered ? 'default' : 'pointer' }">
                        <div class="text-dots text-caption" :style="{ maxWidth: imageWidth+'px' }">{{ item.name }}</div>
                        <div style="position: relative;">
                            <v-img
                                cover
                                :style="{ opacity: isChosenAnswer(item.id) || gameData.showCorrect && isCorrectAnswer(item.id) ? 0.1 : 1 }"
                                :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                                :lazy-src="imgUrlS"
                                :width="imageWidth"
                                :height="Math.floor(imageWidth*0.5)"/>

                                <div v-if="gameData.showCorrect && !answeredCorrect && isChosenAnswer(item.id)"
                                    style="position: absolute; top:0; left:0; width: 100%;"
                                    :style="{
                                        height: Math.floor(imageWidth*0.5)+'px',
                                        border: '2px solid '+theme.current.value.colors.error
                                    }"
                                    class="d-flex align-center justify-center">
                                    <v-icon size="60" icon="mdi-close-circle-outline" color="error"/>
                                </div>
                                <div v-else-if="gameData.showCorrect && isCorrectAnswer(item.id)"
                                    style="position: absolute; top:0; left:0; width: 100%;"
                                    :style="{
                                        height: Math.floor(imageWidth*0.5)+'px',
                                        border: '2px solid '+theme.current.value.colors.primary
                                    }"
                                    class="d-flex align-center justify-center">
                                    <v-icon v-if="answeredCorrect" size="60" icon="mdi-check-bold" color="primary"/>
                                </div>
                        </div>
                    </v-sheet>
                </div>

                <div v-else-if="activeQ.tagChoices" class="d-flex flex-wrap align-start justify-center align-content-start" :style="{ maxWidth: ((imageWidth+15)*itemsPerRow)+'px' }">
                    <v-sheet v-for="(tag, idx) in activeQ.tagChoices" :key="'ai_'+idx+'_'+tag.id"
                        class="mr-1 mb-1 pa-1 secondary-on-hover"
                        rounded="sm"
                        @click="chooseAnswer(tag.id)"
                        :style="{
                            cursor: answered ? 'default' : 'pointer',
                            maxWidth: (imageWidth+10)+'px',
                            maxHeight: (Math.floor(imageWidth*0.5)+10)+'px'
                        }">

                        <div style="position: relative;">
                            <div class="bg-surface-light d-flex align-center justify-center text-ww"
                                :title="showTagDesc ? tag.description : ''"
                                :style="{
                                    textAlign: 'center',
                                    opacity: isChosenAnswer(tag.id) || gameData.showCorrect && isCorrectAnswer(tag.id) ? 0.1 : 1,
                                    width: imageWidth+'px',
                                    height: Math.floor(imageWidth*0.5)+'px',
                                    fontSize: fontSize+'px'
                                }">
                                {{ tag.name }}
                            </div>
                            <div v-if="gameData.showCorrect && !answeredCorrect && isChosenAnswer(tag.id)"
                                style="position: absolute; top:0; left:0; width: 100%;"
                                :style="{
                                    height: Math.floor(imageWidth*0.5)+'px',
                                    border: '2px solid '+theme.current.value.colors.error
                                }"
                                class="d-flex align-center justify-center">
                                <v-icon size="60" icon="mdi-close-circle-outline" color="error"/>
                            </div>
                            <div v-else-if="gameData.showCorrect && isCorrectAnswer(tag.id)"
                                style="position: absolute; top:0; left:0; width: 100%;"
                                :style="{
                                    height: Math.floor(imageWidth*0.5)+'px',
                                    border: '2px solid '+theme.current.value.colors.primary,
                                }"
                                class="d-flex align-center justify-center">
                                <v-icon v-if="answeredCorrect" size="60" icon="mdi-check-bold" color="primary"/>
                            </div>
                        </div>
                    </v-sheet>
                </div>
            </div>
        </div>

        <div v-else-if="state === STATES.END" class="d-flex flex-column align-center">

            <div class="mb-4" style="font-size: 20px; text-align: center; width: 100%;">
                <div><b>Your Score:</b> {{ numCorrect }} / {{ questions.length }}</div>
            </div>

            <div class="d-flex align-center justify-center mb-4">
                <v-btn class="mr-1" size="large" color="error" @click="close">close game</v-btn>
                <v-btn class="ml-1" size="large" color="primary" @click="startGame">play again</v-btn>
            </div>


            <div style="padding: 2px;">

                <div v-for="(q, idx) in questions" :key="'q_res_'+idx" class="d-flex flex-column align-start">

                    <div class="d-flex flex-column align-center">

                        <div class="d-flex align-center mt-6 mb-2" style="width: 100%;">
                            <span v-html="(idx+1)+'. '+q.text"></span>
                            <v-tooltip v-if="q.tag" :text="q.tag.description ? q.tag.description : 'no description'" location="top" max-width="300">
                                <template v-slot:activator="{ props }">
                                    <v-icon v-bind="props"
                                    icon="mdi-information"
                                    class="ml-1"
                                    size="sm"
                                    density="compact"/>
                                </template>
                            </v-tooltip>
                        </div>

                        <div class="d-flex align-start justify-start">

                            <div class="mr-4 d-flex align-center flex-column">
                                <v-icon
                                    size="60"
                                    :icon="gaveCorrectAnswer(idx) ? 'mdi-check-bold' : 'mdi-close-circle-outline'"
                                    :color="gaveCorrectAnswer(idx) ? 'primary' :'error'"/>

                                <v-btn v-if="q.item || q.itemChoices"
                                    @click="showDetails[idx] = !showDetails[idx]"
                                    variant="text"
                                    density="compact"
                                    class="text-caption">
                                    {{ showDetails[idx] ? 'hide' : 'show' }} details
                                </v-btn>
                            </div>

                            <div v-if="q.item">
                                <div class="d-flex">
                                    <v-sheet class="mr-1 mb-1 pa-1" rounded="sm">
                                        <div class="text-dots text-caption" :style="{ maxWidth: endImageWidth+'px' }">{{ q.item.name }}</div>
                                        <ItemTeaser :item="q.item" :width="endImageWidth" :height="endImageHeight"/>
                                    </v-sheet>
                                    <v-divider vertical class="ml-2 mr-2" opacity="1"></v-divider>
                                </div>
                                <div style="text-align: center;">
                                    <ObjectionButton class="mt-1" :item-id="q.item.id"/>
                                </div>
                            </div>

                            <div v-if="q.itemChoices" style="width: 100%;" class="d-flex align-center justify-start">

                                <div v-for="(item, iidx) in q.itemChoices" :key="'q_res_'+idx+'_i_'+item.id">
                                    <div class="d-flex">
                                        <v-divider v-if="iidx > 0" vertical class="ml-2 mr-2"></v-divider>
                                        <v-sheet class="mr-1 mb-1 pa-1" rounded="sm" :style="{ border: '2px solid ' + getBorderColorResult(idx, item.id) }">
                                            <div class="text-dots text-caption" :style="{ maxWidth: endImageWidth+'px' }">{{ item.name }}</div>
                                            <ItemTeaser :item="item" :width="endImageWidth" :height="endImageHeight"/>
                                        </v-sheet>
                                    </div>
                                    <div style="text-align: center;">
                                        <ObjectionButton class="mt-1"
                                            :item-id="item.id"
                                            :tag-id="q.tag ? q.tag.id : null"
                                            :action="getObjectionAction(idx, item.id)"
                                            />
                                    </div>
                                </div>

                            </div>

                            <div v-if="q.tagChoices" class="d-flex align-center justify-start" style="width: 100%;">
                                <div v-for="(tag, tidx) in q.tagChoices" :key="'q_res_'+idx+'_t_'+tag.id">
                                    <div class="d-flex" style="margin-top: 1.5em;">
                                        <v-divider v-if="tidx > 0" vertical class="ml-2 mr-2"></v-divider>
                                        <v-sheet
                                            class="mr-1 mb-1 pa-1 d-flex align-center justify-center"
                                            rounded="sm"
                                            color="surface-light"
                                            :title="tag.description"
                                            :style="{
                                                width: (endImageWidth+10)+'px',
                                                height: (5+endImageHeight)+'px',
                                                border: '2px solid ' + getBorderColorResult(idx, tag.id)
                                            }">
                                            <div
                                                class="text-caption text-ww cursor-pointer"
                                                @contextmenu="e => openTagContext(q.item ? q.item.id : null, tag, getObjectionAction(idx, tag.id), e)"
                                                style="text-align: center;">
                                                {{ tag.name }}
                                            </div>
                                        </v-sheet>
                                    </div>
                                    <div style="text-align: center;">
                                        <ObjectionButton class="mt-1"
                                            :item-id="q.item ? q.item.id : null"
                                            :tag-id="tag.id"
                                            :action="getObjectionAction(idx, tag.id)"/>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <v-sheet v-if="q.itemChoices && showDetails[idx]"
                        class="d-flex align-center justify-center flex-column pa-2 mt-4 mb-2"
                        :style="{ border: '2px solid'+theme.current.value.colors.secondary }"
                        rounded>
                        <ItemSummary v-for="item in q.itemChoices"
                            class="mb-2"
                            :key="'q_detail_'+idx+'_i_'+item.id"
                            :id="item.id"
                            show-all-users
                            :teaser-border="getBorderColorResult(idx, item.id)"
                            :show-evidence="q.tag !== undefined"
                            :teaser-width="100"
                            :teaser-height="50"
                            :evidence-size="80"
                            :tag-id="q.tag ? q.tag.id : undefined"/>
                    </v-sheet>

                    <v-sheet v-if="q.item && showDetails[idx]"
                        class="d-flex align-center justify-center flex-column pa-2 mt-4 mb-2"
                        :style="{ border: '2px solid'+theme.current.value.colors.secondary }"
                        rounded>
                        <ItemSummary
                            class="mb-2"
                            :id="q.item.id"
                            show-all-users
                            :show-evidence="q.tag !== undefined"
                            :teaser-width="100"
                            :teaser-height="50"
                            :evidence-size="80"
                            :tag-id="q.tag ? q.tag.id : (q.answer.tag ? q.answer.tag.id : undefined)"/>
                    </v-sheet>

                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { pointer, range } from 'd3'
    import DM from '@/use/data-manager'
    import { OBJECTION_ACTIONS, useApp } from '@/store/app'
    import { computed, onMounted, reactive, watch } from 'vue'
    import { DIFFICULTY, STATES, useGames } from '@/store/games'
    import Timer from './Timer.vue'
    import { randomChoice, randomInteger, randomItems, randomItemsWithoutTags, randomItemsWithTags, randomLeafTags, randomShuffle } from '@/use/random'
    import imgUrlS from '@/assets/__placeholder__s.png'
    import { useTheme } from 'vuetify/lib/framework.mjs'
    import { CTXT_OPTIONS, useSettings } from '@/store/settings'
    import { useElementSize, useWindowSize } from '@vueuse/core'
    import ObjectionButton from '../objections/ObjectionButton.vue'
    import ItemTeaser from '../items/ItemTeaser.vue'
    import { useSounds, SOUND } from '@/store/sounds'
    import { storeToRefs } from 'pinia'
    import ItemSummary from '../items/ItemSummary.vue'

    const QTYPES = Object.freeze({
        GAME_HAS_TAG: 0,
        TAG_HAS_GAME: 1,
        MOST_TAGS: 2,
        // TAG_SAME: 3
    })

    const props = defineProps({
        waitTime: {
            type: Number,
            default: 1000
        },
    })

    const emit = defineEmits(["end", "round", "close"])

    // stores
    const sounds = useSounds()
    const app = useApp()
    const settings = useSettings()
    const theme = useTheme()
    const games = useGames()

    // elements
    const el = ref(null)
    const elSize = useElementSize(el)
    const wSize = useWindowSize()

    const itemsPerRow = computed(() => Math.max(2, Math.round(Math.sqrt(numAnswers.value))))
    const imageWidth = computed(() => {
        const w = Math.floor(elSize.width.value / itemsPerRow.value)
        const h = Math.floor(elSize.height.value / itemsPerRow.value)
        return Math.max(80, Math.min(360, w, h) - 15)
    })
    const endImageWidth = computed(() => wSize.width.value >= 1600 ? 160 : 80)
    const endImageHeight = computed(() => Math.floor(endImageWidth.value*0.5))

    const fontSize = computed(() => {
        if (imageWidth.value <= 100) {
            return 9
        } else if (imageWidth.value <= 200) {
            return 14
        } else {
            return 20
        }
    })

    const showDetails = reactive({})

    // difficulty settings
    const { difficulty } = storeToRefs(games)

    const timeInSec = computed(() => {
        switch (difficulty.value) {
            case DIFFICULTY.EASY: return 45;
            case DIFFICULTY.NORMAL: return 30;
            case DIFFICULTY.HARD: return 15;
        }
    })
    const numAnswers = computed(() => {
        switch (difficulty.value) {
            case DIFFICULTY.EASY:
            case DIFFICULTY.NORMAL:
                return 4;
            case DIFFICULTY.HARD:
                return 6;
        }
    })
    const numQuestions = computed(() => {
        switch (difficulty.value) {
            case DIFFICULTY.EASY: return 4;
            case DIFFICULTY.NORMAL: return 6;
            case DIFFICULTY.HARD: return 8;
        }
    })

    const showTagDesc = computed(() => difficulty.value === DIFFICULTY.EASY)
    // game related stuff
    const state = ref(STATES.START)

    const timer = ref(null)
    const questions = ref([])
    const gameData = reactive({
        qIndex: -1,
        history: [],
        showCorrect: false
    })

    const activeQ = computed(() => {
        if (gameData.qIndex < 0 || gameData.qIndex >= questions.value.length) {
            return null
        }
        return questions.value[gameData.qIndex]
    })
    const activeA = computed(() => activeQ.value ? activeQ.value.answer : null)

    const answered = computed(() => activeQ.value && gameData.history.length >= gameData.qIndex+1)
    const answeredCorrect = computed(() => answered.value && gameData.history.at(-1).correct)
    const numCorrect = computed(() => gameData.history.reduce((acc, d) => acc + (d.correct ? 1 : 0), 0))

    function getObjectionAction(index, answer) {
        if (questions.value[index].type === QTYPES.MOST_TAGS) {
            return OBJECTION_ACTIONS.DISCUSS
        }

        if (wasCorrectAnswer(index, answer)) {
            return OBJECTION_ACTIONS.REMOVE
        }
        return OBJECTION_ACTIONS.ADD
    }
    function getBorderColorResult(index, answer) {
        if (wasChosenAnswer(index, answer)) {
            return gaveCorrectAnswer(index) ?
                theme.current.value.colors.primary :
                theme.current.value.colors.error
        } else if (wasCorrectAnswer(index, answer)) {
            return theme.current.value.colors.primary
        }
        return settings.lightMode ? "white" : "black"
    }
    function wasCorrectAnswer(index, answer) {
        if (index < 0 || index >= questions.value.length) return false
        const q = questions.value[index]
        switch (q.type) {
            case QTYPES.GAME_HAS_TAG:
            case QTYPES.MOST_TAGS:
                return q.answer.item.id == answer
            case QTYPES.TAG_HAS_GAME:
                return q.answer.tag.id == answer
        }
    }
    function wasChosenAnswer(index, answer) {
        if (index < 0 || index >= gameData.history.length) return false
        return gameData.history[index].answer === answer
    }
    function gaveCorrectAnswer(index) {
        if (index < 0 || index >= gameData.history.length) return false
        return gameData.history[index].correct
    }

    function isCorrectAnswer(answer) {
        switch (activeQ.value.type) {
            case QTYPES.GAME_HAS_TAG:
            case QTYPES.MOST_TAGS:
                return activeA.value.item.id == answer
            case QTYPES.TAG_HAS_GAME:
                return activeA.value.tag.id == answer
        }
    }
    function isChosenAnswer(answer) {
        if (answered.value) {
            return gameData.history.at(-1).answer === answer
        }
        return false
    }

    function openTagContext(itemId, tag, action, event) {
        event.preventDefault()
        const [x, y] = pointer(event, document.body)
        settings.setRightClick(
            "tag", tag.id,
            x, y,
            tag.name,
            { item: itemId, action: action },
            CTXT_OPTIONS.items_tagged
        )
    }

    function chooseAnswer(answer) {
        // already answered
        if (answered.value) return;

        // push answer to history
        gameData.history.push({
            correct: isCorrectAnswer(answer),
            answer: answer
        })

        stopRound()
    }
    function stopRound() {
        if (!answered.value) {
            gameData.history.push({
                correct: false,
                answer: null
            })
        }

        emitScoreData()

        sounds.play(answeredCorrect.value ? SOUND.WIN_MINI : SOUND.FAIL_MINI)
        gameData.showCorrect = true

        // transition
        setTimeout(() => {
            gameData.showCorrect = false
            gameData.qIndex++
            if (gameData.qIndex >= questions.value.length) {
                stopGame()
            } else {
                startTimer()
            }
        }, props.waitTime)
    }

    function generateQuestion() {
        const type = randomChoice(Object.values(QTYPES), 1)
        switch (type) {
            case QTYPES.GAME_HAS_TAG:{
                const tag = randomLeafTags(1)
                const target = randomItemsWithTags(tag.id, 1)
                const other = randomItemsWithoutTags(tag.id, numAnswers.value-1)
                return {
                    type: type,
                    text: `Which ${app.itemName} has the tag <b>${tag.name}</b>?`,
                    tag: tag,
                    itemChoices: randomShuffle([target].concat(other)),
                    answer: { item: target }
                }
            }
            case QTYPES.TAG_HAS_GAME: {
                const item = randomItems(1, 5)
                const tag = randomChoice(item.allTags, 1)
                const tagOther = randomLeafTags(numAnswers.value-1, 1, item.allTags.map(t => t.id) )
                return {
                    type: type,
                    text: `Which tag does this <b>${app.itemName}</b> have?`,
                    item: item,
                    tagChoices: randomShuffle([tag].concat(tagOther)),
                    answer: { tag: tag }
                }
            }
            case QTYPES.MOST_TAGS: {
                const items = DM.getDataBy("items", d => d.allTags.length > 1)
                let indices = Array.from(range(0, items.length))
                const chosen = new Set()
                const itemOther = []
                let maxCount = 0, maxIdx = -1;
                while (chosen.size < numAnswers.value) {
                    const idx = randomInteger(0, indices.length)
                    const item = items[indices[idx]]
                    chosen.add(indices[idx])
                    itemOther.push(item)
                    if (item.allTags.length > maxCount) {
                        maxCount = item.allTags.length
                        maxIdx = itemOther.length-1
                    }
                    indices = indices.filter(i => items[i].allTags.length !== item.allTags.length)
                }

                const target = itemOther[maxIdx]
                return {
                    type: type,
                    text: `Which <b>${app.itemName}</b> has the most tags?`,
                    itemChoices: randomShuffle(itemOther),
                    answer: { item: target }
                }
            }

        }
    }

    function startTimer() {
        if (timer.value) {
            timer.value.start()
        } else {
            setTimeout(startTimer, 50)
        }
    }

    function emitScoreData() {
        const idx = gameData.history.length-1
        if (idx <= 0) return

        let items = null, tags = null;
        const q = questions.value[idx]
        const a = gameData.history[idx]

        if (a.answer === null) return

        switch (q.type) {

            case QTYPES.GAME_HAS_TAG:
                items = [a.answer]
                tags = [{
                    item_id: a.answer,
                    tag_id: q.tag.id
                }]
                if (!a.correct) {
                    items.push(q.answer.item.id)
                    tags.push({
                        item_id: q.answer.item.id,
                        tag_id: q.tag.id
                    })
                }
                break;

            case QTYPES.TAG_HAS_GAME:
                items = [q.item.id]
                tags = [{
                    item_id: q.item.id,
                    tag_id: a.answer
                }]
                if (!a.correct) {
                    tags.push({
                        item_id: q.item.id,
                        tag_id: q.answer.tag.id
                    })
                }
                break

            default: return;

        }
        emit("round", a.correct, items, tags)

    }

    function startGame() {
        const starttime = Date.now()
        sounds.play(SOUND.START)
        state.value = STATES.LOADING

        // clear previous data
        clear()

        // generate questions
        for (let i = 0; i < numQuestions.value; ++i) {
            questions.value.push(generateQuestion())
            showDetails[i] = false
        }
        gameData.qIndex = 0;

        setTimeout(() => {
            state.value = STATES.INGAME
            startTimer()
        }, Date.now() - starttime < 500 ? 1000 : 50)
    }

    function stopGame() {
        timer.value.stop()
        state.value = STATES.END
        if (numCorrect.value === 0) {
            sounds.play(SOUND.FAIL)
            emit("end", false)
        } else if (numCorrect.value === numQuestions.value) {
            sounds.play(SOUND.WIN)
            emit("end", true)
        } else {
            sounds.play(SOUND.MEH)
            emit("end", false)
        }
    }

    function close() {
        reset()
        emit("close")
    }

    function clear() {
        questions.value = []
        gameData.history = []
    }
    function reset() {
        clear()
        state.value = STATES.START
    }

    function init() {
        reset()
        startGame()
    }

    onMounted(init)

    watch(difficulty, init)
    watch(props, init, { deep: true })
</script>

<style scoped>
.break {
  flex-basis: 100%;
  height: 0;
}</style>
