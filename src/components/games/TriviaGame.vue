<template>
    <div>
        <div v-if="state === STATES.START" class="d-flex align-center justify-center" style="height: 80vh;">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>

        <div v-else-if="state === STATES.LOADING" class="d-flex align-center justify-center" style="height: 80vh;">
            <div class="game-loader"></div>
        </div>

        <div v-else-if="state === STATES.INGAME" class="d-flex flex-column justify-center align-center">

            <div class="mt-4 mb-4 d-flex justify-space-between" style="width: 50%;">
                <div>Question {{ gameData.qIndex+1 }} / {{ questions.length }}</div>
                <div>Points {{ numCorrect }} / {{ questions.length }}</div>
            </div>

            <Timer ref="timer" :time-in-sec="timeInSec" @end="stopRound"/>

            <div v-if="activeQ" class="d-flex flex-column align-center">
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

                <div v-if="activeQ.itemChoices" class="d-flex flex-wrap align-start align-content-start" :style="{ maxWidth: ((imageWidth+15)*2)+'px' }">
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

                <div v-else-if="activeQ.tagChoices" class="d-flex flex-wrap align-start align-content-start" :style="{ maxWidth: ((imageWidth+15)*2)+'px' }">
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
                            <div class="bg-surface-light d-flex align-center justify-center text-caption"
                                :style="{
                                    opacity: isChosenAnswer(tag.id) || gameData.showCorrect && isCorrectAnswer(tag.id) ? 0.1 : 1,
                                    width: imageWidth+'px',
                                    height: Math.floor(imageWidth*0.5)+'px',
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
                                    border: '2px solid '+theme.current.value.colors.primary
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
            <div class="mt-8 mb-4" style="font-size: 20px; text-align: center; width: 100%;">
                <div><b>Your Score:</b> {{ numCorrect }} / {{ questions.length }}</div>
            </div>

            <div v-for="(q, idx) in questions" :key="'q_res_'+idx" style="width: 100%; max-height: 80vh; overflow-y: auto;" class="d-flex flex-column align-center">
                <div v-html="(idx+1)+'. '+q.text" class="mt-6 mb-2"></div>

                <div class="d-flex align-center">

                    <v-icon
                        size="60"
                        class="mr-2"
                        :icon="gaveCorrectAnswer(idx) ? 'mdi-check-bold' : 'mdi-close-circle-outline'"
                        :color="gaveCorrectAnswer(idx) ? 'primary' :'error'"/>

                    <div v-if="q.item" class="d-flex">
                        <v-sheet class="mr-1 mb-1 pa-1" rounded="sm">
                            <div class="text-dots text-caption" :style="{ maxWidth: imageWidth+'px' }">{{ q.item.name }}</div>
                            <v-img
                                cover
                                :src="q.item.teaser ? 'teaser/'+q.item.teaser : imgUrlS"
                                :lazy-src="imgUrlS"
                                :width="imageWidth"
                                :height="Math.floor(imageWidth*0.5)"/>
                        </v-sheet>
                        <v-divider vertical class="ml-2 mr-2" opacity="1"></v-divider>
                    </div>

                    <div v-if="q.itemChoices" class="d-flex align-center justify-center" style="width: 100%;">
                        <div v-for="(item, iidx) in q.itemChoices" :key="'q_res_'+idx+'_i_'+item.id" class="d-flex">
                            <v-divider v-if="iidx > 0" vertical class="ml-2 mr-2"></v-divider>
                            <v-sheet class="mr-1 mb-1 pa-1" rounded="sm" :style="{ border: '2px solid ' + getBorderColorResult(idx, item.id) }">
                                <div class="text-dots text-caption" :style="{ maxWidth: imageWidth+'px' }">{{ item.name }}</div>
                                <v-img
                                    cover
                                    :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                                    :lazy-src="imgUrlS"
                                    :width="imageWidth"
                                    :height="Math.floor(imageWidth*0.5)"/>
                            </v-sheet>
                        </div>
                    </div>

                    <div v-if="q.tagChoices" class="d-flex align-center justify-center" style="width: 100%;">
                        <div v-for="(tag, tidx) in q.tagChoices" :key="'q_res_'+idx+'_t_'+tag.id" class="d-flex">
                            <v-divider v-if="tidx > 0" vertical class="ml-2 mr-2"></v-divider>
                            <v-sheet
                                class="mr-1 mb-1 pa-1 d-flex align-center justify-center"
                                rounded="sm"
                                color="surface-light"
                                :style="{
                                    width: (imageWidth+10)+'px',
                                    height: (5+Math.floor(imageWidth*0.5))+'px',
                                    border: '2px solid ' + getBorderColorResult(idx, tag.id)
                                }">
                                <div class="text-caption text-ww">
                                    {{ tag.name }}
                                </div>
                            </v-sheet>
                        </div>
                    </div>
                </div>
            </div>

            <div class="d-flex align-center justify-center mt-4">
                <v-btn class="mr-1" size="x-large" color="error" @click="close">close game</v-btn>
                <v-btn class="ml-1" size="x-large" color="primary" @click="startGame">play again</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { range } from 'd3'
    import DM from '@/use/data-manager'
    import { useApp } from '@/store/app'
    import { computed, onMounted, reactive, watch } from 'vue'
    import { DIFFICULTY, SOUND, useGames } from '@/store/games'
    import Timer from './Timer.vue'
    import { randomChoice, randomInteger, randomItems, randomItemsWithoutTags, randomItemsWithTags, randomLeafTags, randomShuffle } from '@/use/random'
    import imgUrlS from '@/assets/__placeholder__s.png'
    import { useTheme } from 'vuetify/lib/framework.mjs'
    import { useSettings } from '@/store/settings'

    const STATES = Object.freeze({
        START: 0,
        LOADING: 1,
        INGAME: 2,
        END: 3
    })

    const QTYPES = Object.freeze({
        GAME_HAS_TAG: 0,
        TAG_HAS_GAME: 1,
        MOST_TAGS: 2,
        // TAG_SAME: 3
    })

    const props = defineProps({
        difficulty: {
            type: Number,
            required: true
        },
        waitTime: {
            type: Number,
            default: 1000
        },
    })

    const emit = defineEmits(["end", "close"])

    const theme = useTheme()

    // stores
    const games = useGames()
    const app = useApp()
    const settings = useSettings()

    // difficulty settings
    const timeInSec = computed(() => {
        switch (props.difficulty) {
            case DIFFICULTY.EASY: return 45;
            case DIFFICULTY.NORMAL: return 30;
            case DIFFICULTY.HARD: return 15;
        }
    })
    const numQuestions = computed(() => {
        switch (props.difficulty) {
            case DIFFICULTY.EASY: return 4;
            case DIFFICULTY.NORMAL: return 5;
            case DIFFICULTY.HARD: return 10;
        }
    })

    const imageWidth = ref(160)

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

        games.play(answeredCorrect.value ? SOUND.WIN_MINI : SOUND.FAIL_MINI)
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
                const other = randomItemsWithoutTags(tag.id, 3)
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
                const tagOther = randomLeafTags(3, 1,item.allTags.map(t => t.id) )
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
                while (chosen.size < 4) {
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
        emit("end", a.correct, items, tags)

    }

    function startGame() {
        const starttime = Date.now()
        games.playSingle(SOUND.START)
        state.value = STATES.LOADING

        // clear previous data
        clear()

        // generate questions
        for (let i = 0; i < numQuestions.value; ++i) {
            questions.value.push(generateQuestion())
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
            games.playSingle(SOUND.FAIL)
        } else if (numCorrect.value === numQuestions.value) {
            games.playSingle(SOUND.WIN)
        } else {
            games.playSingle(SOUND.MEH)
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

    onMounted(function() {
        reset()
        startGame()
    })

    watch(props, function() {
        reset()
        startGame()
    }, { deep: true })
</script>
