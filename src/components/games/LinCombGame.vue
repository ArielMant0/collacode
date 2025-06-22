<template>
    <div style="max-height: 90vh; overflow-y: auto;">
        <div v-if="state === STATES.START" class="d-flex align-center justify-center">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>

        <div v-else-if="state === STATES.LOADING"class="d-flex align-center justify-center">
            <LoadingScreen
                :messages="[
                    'drag item images to assign them to a set of tags',
                    'hover over tags to highlight them in all tag sets',
                    'click on a tag to highlight it permanently'
                ]"/>
        </div>

        <div v-else-if="state === STATES.INGAME || state === STATES.END" class="d-flex flex-column align-center">

            <div class="mt-2 mb-2 d-flex align-end justify-center">
                <GameResultIcon v-if="state === STATES.END"
                    :result="gameResult"
                    :score-text="gameData.scoreText"
                    show-text
                    show-effects
                    :effects-width="180"
                    :effects-height="90"/>
                <div class="ml-2 mr-2 mb-2 d-flex align-center">
                    <div style="text-align: center;">
                        <div style="max-width: 200px;" class="text-dots">{{ gameData.target.name }}</div>
                            <ItemTeaser
                            :item="gameData.target"
                            :width="180"
                            :height="90"
                            :prevent-click="state !== STATES.END"
                            :prevent-open="state !== STATES.END"
                            :prevent-context="state !== STATES.END"/>
                    </div>
                    <v-btn variant="outlined" class="ml-2" icon="mdi-sync" density="comfortable" @click="reroll(false)"/>
                </div>
            </div>

            <div v-if="state === STATES.END">
                <div>ground truth</div>
                <BarCode v-show="showBarCodes"
                    :item-id="gameData.target.id"
                    :data="gameData.target.allTags"
                    :domain="gameData.tagDomain"
                    hide-value
                    hide-highlight
                    binary
                    :binary-color-fill="lightMode ? '#000' : '#fff'"
                    id-attr="id"
                    name-attr="name"
                    value-attr="id"
                    desc-attr="description"
                    @right-click="rightClickTag"
                    :no-value-color="lightMode ? '#f2f2f2' : '#333333'"
                    :width="nodeSize"
                    :height="20"/>

                <div>your solution</div>
                <BarCode v-show="showBarCodes"
                    :data="gameData.resultTags"
                    :domain="gameData.tagDomain"
                    hide-value
                    hide-highlight
                    categorical
                    :binary-color-fill="lightMode ? '#000' : '#fff'"
                    id-attr="id"
                    name-attr="name"
                    value-attr="value"
                    desc-attr="description"
                    :color-domain="[1, 2, 3]"
                    :color-scale="[
                        GR_COLOR.GREEN,
                        GR_COLOR.RED,
                        lightMode ? '#666' : '#aaa'
                    ]"
                    :no-value-color="lightMode ? '#f2f2f2' : '#333333'"
                    :width="nodeSize"
                    :height="20"/>
            </div>

            <div>
                <ItemSimilaritySelector v-if="difficulty === DIFFICULTY.EASY"
                    :node-size="nodeSize"
                    @update="setResultTags"
                    @step="s => step = s"
                    :target="gameData.target.id"/>
                <ItemGraphPath v-else-if="difficulty === DIFFICULTY.NORMAL"
                    :node-size="nodeSize"
                    @update="setResultTags"
                    @step="s => step = s"
                    :target="gameData.target.id"/>
                <ItemBinarySearch v-else
                    :node-size="nodeSize"
                    @update="setResultTags"
                    @step="s => step = s"
                    :target="gameData.target.id"/>
            </div>

            <v-btn v-if="state === STATES.INGAME && step > 1" class="ml-1" size="large" color="primary" @click="stopGame">submit</v-btn>
            <div v-if="state === STATES.END" class="d-flex align-center justify-center">
                <v-btn class="mr-1" size="large" color="error" @click="close">close game</v-btn>
                <v-btn class="ml-1" size="large" color="primary" @click="startGame">play again</v-btn>
            </div>

        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager'
    import { pointer } from 'd3'
    import { computed, onMounted, reactive, watch } from 'vue'
    import { DIFFICULTY, GAME_RESULT, GR_COLOR, STATES, useGames } from '@/store/games'
    import { CTXT_OPTIONS, useSettings } from '@/store/settings'
    import { randomItems } from '@/use/random'
    import { useSounds, SOUND } from '@/store/sounds';
    import { storeToRefs } from 'pinia'
    import GameResultIcon from './GameResultIcon.vue'
    import LoadingScreen from './LoadingScreen.vue'
    import { useDisplay } from 'vuetify'
    import { useWindowSize } from '@vueuse/core'
    import ItemSimilaritySelector from '../items/ItemSimilaritySelector.vue'
    import ItemTeaser from '../items/ItemTeaser.vue'
    import BarCode from '../vis/BarCode.vue'
    import ItemGraphPath from '../items/ItemGraphPath.vue'
    import { OBJECTION_ACTIONS } from '@/store/app'
import ItemBinarySearch from '../items/ItemBinarySearch.vue'

    const emit = defineEmits(["end", "close"])

    // stores
    const sounds = useSounds()
    const settings = useSettings()
    const games = useGames()

    const { smAndDown } = useDisplay()

    const { barCodeNodeSize, lightMode } = storeToRefs(settings)

    const wSize = useWindowSize()
    const nodeSize = computed(() => {
        if (gameData.tagDomain.length === 0) {
            return barCodeNodeSize.value
        }
        return Math.max(2, Math.floor((wSize.width.value * 0.6) / gameData.tagDomain.length))
    })

    const showBarCodes = computed(() => !smAndDown.value)
    const step = ref(1)

    // difficulty settings
    const { difficulty } = storeToRefs(games)

    // game related stuff
    const state = ref(STATES.START)
    const gameData = reactive({
        target: null,
        tagDomain: [],

        resultTags: [],
        resultOverlap: 0,
        resultOverlapAbs: 0,
        resultDiff: 0,
        resultDiffAbs: 0,
        resultMiss: 0,
        resultMissAbs: 0,
        scoreText: ""
    })

    const targetTagSet = reactive(new Set())
    const gameResult = computed(() => {
        const o = gameData.resultOverlap
        const d = gameData.resultDiffAbs
        const m = gameData.resultMissAbs
        const upper = Math.max(3, Math.min(5, targetTagSet.size*0.1))
        const lower = Math.max(5, Math.min(10, targetTagSet.size*0.25))

        if (o > 0.66 && d < upper && m < upper) {
            return GAME_RESULT.WIN
        } else if (o <= 0.33 || d > lower || m > lower) {
            return GAME_RESULT.LOSS
        }
        return GAME_RESULT.DRAW
    })

    // ---------------------------------------------------------------------
    // Functions
    // ---------------------------------------------------------------------

    function rightClickTag(tag, event) {
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "tag", tag.id,
            mx, my,
            tag.name,
            {
                item: gameData.target.id,
                action: gameData.target.allTags.find(d => d.id === tag.id) ? OBJECTION_ACTIONS.REMOVE : OBJECTION_ACTIONS.ADD
            },
            CTXT_OPTIONS.items_tagged
        )
    }

    function setResultTags(tags) {
        const s = new Set(tags.map(d => d.id))
        const both = s.intersection(targetTagSet)
        gameData.resultOverlapAbs = both.size
        gameData.resultOverlap = gameData.resultOverlapAbs/ targetTagSet.size
        gameData.resultDiffAbs = s.difference(targetTagSet).size
        gameData.resultDiff = s.size > 0 ? gameData.resultDiffAbs / s.size : 0
        const missing = gameData.target.allTags
            .filter(t => !both.has(t.id))
            .map(t => {
                return {
                    id: t.id,
                    name: t.name,
                    description: t.description,
                    parent: t.parent,
                    value: 3
                }
            })
        gameData.resultMissAbs = missing.length
        gameData.resultMiss = missing.length / targetTagSet.size

        gameData.resultTags = tags.map(t => {
            return {
                id: t.id,
                name: t.name,
                description: t.description,
                parent: t.parent,
                value: both.has(t.id) ? 1 : 2
            }
        }).concat(missing)
    }

    function startRound(timestamp=null) {
        state.value = STATES.LOADING
        sounds.play(SOUND.START_SHORT)
        setTimeout(
            () => state.value = STATES.INGAME,
            1000 - (timestamp !== null ? Date.now()-timestamp : 0)
        )
    }
    function tryStartRound(timestamp=null) {
        gameData.target = randomItems(1, 5)
        gameData.resultTags = []
        targetTagSet.clear()
        gameData.target.allTags.forEach(d => targetTagSet.add(d.id))
        startRound(timestamp)
    }
    function startGame() {
        sounds.stopAll()
        sounds.play(SOUND.START)
        state.value = STATES.LOADING
        reroll()
    }
    function reroll(loading=true) {
        const now = Date.now() - (loading ? 0 : 1000)
        // clear previous data
        clear()
        // get bar code domain
        gameData.tagDomain = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
        // try to start the round
        tryStartRound(now)
    }

    function stopGame() {
        if (state.value === STATES.END) return
        gameData.scoreText = Math.round(gameData.resultOverlap*100)+'%</br>' +
            '(+'+gameData.resultDiffAbs+', -'+gameData.resultMissAbs+')</br>'
        state.value = STATES.END
    }

    function close() {
        emit("close")
        reset()
    }

    function clear() {
        step.value = 1
        gameData.target = null
        gameData.resultTags = []
        gameData.resultOverlap = 0
        gameData.resultOverlapAbs = 0
        gameData.resultDiff = 0
        gameData.resultDiffAbs = 0
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

