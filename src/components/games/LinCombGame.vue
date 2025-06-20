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
                    'click on a tag to highlight it permanently'
                ]"/>
        </div>

        <div v-else-if="state === STATES.INGAME || state === STATES.END" class="d-flex flex-column align-center" style="max-height: 80vh;">

            <div v-if="state === STATES.END" class="mt-4 mb-4 d-flex align-center justify-center">
                <GameResultIcon :result="gameResult" show-text show-effects/>
            </div>

            <h3>model this {{ app.itemName }} as a combination of other {{ app.itemName+'s' }}</h3>

            <div style="text-align: center;" class="mt-2 mb-4">
                <div style="max-width: 200px;" class="text-dots">{{ gameData.target.name }}</div>
                <ItemTeaser
                    :item="gameData.target"
                    :width="200"
                    :height="100"
                    prevent-click
                    prevent-open
                    prevent-context
                    class="mb-4"/>
            </div>

            <div>Overlap: {{ Math.round(gameData.resultOverlap*100) }}% ({{ gameData.resultOverlapAbs }})</div>
            <div>Extra: {{ Math.round(gameData.resultDiff*100) }}% ({{ gameData.resultDiffAbs }})</div>

            <BarCode v-show="showBarCodes"
                :item-id="gameData.target.id"
                :data="gameData.target.allTags"
                :domain="gameData.tagDomain"
                hide-value
                hide-highlight
                binary
                binaryColorFill="black"
                :selectable="false"
                id-attr="id"
                name-attr="name"
                value-attr="id"
                desc-attr="description"
                :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                :width="nodeSize"
                :height="20"/>

            <BarCode v-show="showBarCodes"
                :data="gameData.resultTags"
                :domain="gameData.tagDomain"
                hide-value
                hide-highlight
                binary
                binaryColorFill="black"
                :selectable="false"
                id-attr="id"
                name-attr="name"
                value-attr="id"
                desc-attr="description"
                :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                :width="nodeSize"
                :height="20"/>

            <div style="max-height: 80vh; overflow-y: auto;">
                <ItemSimilaritySelector v-if="difficulty === DIFFICULTY.EASY" :node-size="nodeSize" @update="setResultTags" :target="gameData.target.id"/>
                <ItemGraphPath v-else :node-size="nodeSize" @update="setResultTags" :target="gameData.target.id"/>
            </div>

            <v-btn v-if="state === STATES.INGAME"
                size="x-large"
                color="primary"
                class="mt-8"
                @click="stopGame">
                submit
            </v-btn>
            <div v-else class="d-flex align-center justify-center">
                <v-btn class="mr-1" size="large" color="error" @click="close">close game</v-btn>
                <v-btn class="ml-1" size="large" color="primary" @click="startGame">play again</v-btn>
            </div>

        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager'
    import { computed, onMounted, reactive, watch } from 'vue'
    import { DIFFICULTY, GAME_RESULT, STATES, useGames } from '@/store/games'
    import { useSettings } from '@/store/settings'
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
    import { useApp } from '@/store/app'
import ItemGraphPath from '../items/ItemGraphPath.vue'

    const emit = defineEmits(["end", "close"])

    // stores
    const app = useApp()
    const sounds = useSounds()
    const settings = useSettings()
    const games = useGames()

    const { smAndDown } = useDisplay()

    const { barCodeNodeSize } = storeToRefs(settings)
    const wSize = useWindowSize()
    const nodeSize = computed(() => {
        if (gameData.tagDomain.length === 0) {
            return barCodeNodeSize.value
        }
        return Math.max(2, Math.floor((wSize.width.value * 0.6) / gameData.tagDomain.length))
    })

    const showBarCodes = computed(() => !smAndDown.value)

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
        resultDiffAbs: 0
    })

    let targetTagSet = new Set()
    const resultScore = computed(() => gameData.resultOverlap - gameData.resultDiff)
    const gameResult = computed(() => {
        if (resultScore.value >= 0.75) {
            return GAME_RESULT.WIN
        } else if (resultScore.value <= 0.25) {
            return GAME_RESULT.LOSS
        }
        return GAME_RESULT.DRAW
    })

    // ---------------------------------------------------------------------
    // Functions
    // ---------------------------------------------------------------------

    function setResultTags(tags) {
        const s = new Set(tags.map(d => d.id))
        gameData.resultOverlapAbs = s.intersection(targetTagSet).size
        gameData.resultOverlap = gameData.resultOverlapAbs/ targetTagSet.size
        gameData.resultDiffAbs = s.difference(targetTagSet).size
        gameData.resultDiff = s.size > 0 ? gameData.resultDiffAbs / s.size : 0
        gameData.resultTags = tags
    }

    function startRound() {
        state.value = STATES.LOADING
        sounds.play(SOUND.START_SHORT)
        setTimeout(() => state.value = STATES.INGAME, 1000)
    }
    function tryStartRound() {
        gameData.target = randomItems(1, 5)
        gameData.resultTags = []
        targetTagSet = new Set(gameData.target.allTags.map(d => d.id))
        startRound()
    }
    function startGame() {
        sounds.stopAll()
        sounds.play(SOUND.START)
        state.value = STATES.LOADING
        // clear previous data
        clear()
        // get bar code domain
        gameData.tagDomain = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
        // try to start the round
        tryStartRound()
    }

    function stopGame() {
        if (state.value === STATES.END) return
        state.value = STATES.END
    }

    function close() {
        emit("close")
        reset()
    }

    function clear() {
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

<style scoped>
.no-break {
    text-wrap: nowrap;
}
.tag-hidden {
    opacity: 0.15;
}
</style>
