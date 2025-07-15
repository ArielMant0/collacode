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
                <div class="ml-2">
                    <div>
                        <v-btn variant="outlined" size="small" icon="mdi-sync" density="comfortable" @click="reroll(false)"/>
                    </div>
                    <div class="mt-1">
                        <v-btn variant="outlined" size="small" icon="mdi-magnify" density="comfortable" @click="searchItem"/>
                    </div>
                </div>
            </div>

            <div v-if="step <= 1">
                <ItemSimilaritySelector v-if="difficulty === DIFFICULTY.EASY"
                    :node-size="nodeSize"
                    @inventory="items => inventory = items"
                    @submit="setCandidates"
                    :target="gameData.target.id"/>
                <ItemGraphPath v-else-if="difficulty === DIFFICULTY.NORMAL"
                    :node-size="nodeSize"
                    @inventory="items => inventory = items"
                    @submit="setCandidates"
                    :target="gameData.target.id"/>
                <ItemBinarySearch v-else
                    :node-size="nodeSize"
                    @inventory="items => inventory = items"
                    @submit="setCandidates"
                    :target="gameData.target.id"/>
            </div>
            <div v-else-if="step === 2" class="mt-4 mb-8">
                <ItemTagRecommend
                    :item-limit="10"
                    :items="candidates"
                    @update="setResultItems"/>
            </div>
            <div v-else-if="state === STATES.INGAME" class="mt-4 mb-8">
                <ItemCustomRecommend
                    :item-limit="10"
                    :target="gameData.target.id"
                    :items="gameData.resultItems"
                    @update="setAdditionalItems"/>
            </div>


            <div v-if="state === STATES.END" class="mb-8 d-flex flex-column align-center" :style="{ maxWidth: (190*5)+'px' }">
                <div style="max-width: 100%; text-align: center;">
                    <h3>Your Choices</h3>
                    <div class="d-flex flex-wrap justify-center">
                        <ItemTeaser v-for="item in gameData.resultItems"
                            :id="item.id"
                            prevent-click
                            prevent-context
                            class="mr-1 mb-1"/>
                    </div>
                </div>
                <div v-if="gameData.otherItems.length" class="mt-4" style="max-width: 100%; text-align: center;">
                    <h3>Most Common Choices</h3>
                    <div class="d-flex flex-wrap justify-center">
                        <ItemTeaser v-for="item in gameData.otherItems"
                            :id="item.id"
                            :border-size="4"
                            :border-color="item.same ? GR_COLOR.GREEN : 'default'"
                            prevent-click
                            prevent-contex
                            class="mr-1 mb-1"/>
                    </div>
                </div>
            </div>

            <MiniDialog v-model="showSearch" min-width="50%" max-width="55%">
                <template #text>
                    <ItemSelect @submit="setTarget"/>
                </template>
            </MiniDialog>

            <v-btn v-if="state === STATES.INGAME && step === 2" class="ml-1" size="large" color="primary" @click="step = 3">next</v-btn>
            <v-btn v-else-if="state === STATES.INGAME && step === 3" class="ml-1" size="large" color="primary" @click="stopGame">submit</v-btn>
            <div v-if="state === STATES.END" class="d-flex align-center justify-center">
                <v-btn class="mr-1" size="large" color="error" @click="close">close game</v-btn>
                <v-btn class="ml-1" size="large" color="primary" @click="startGame">play again</v-btn>
            </div>

        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager'
    import { cross, pointer } from 'd3'
    import { computed, onMounted, reactive, watch } from 'vue'
    import { DIFFICULTY, GR_COLOR, STATES, useGames } from '@/store/games'
    import { CTXT_OPTIONS, useSettings } from '@/store/settings'
    import { randomItems } from '@/use/random'
    import { useSounds, SOUND } from '@/store/sounds';
    import { storeToRefs } from 'pinia'
    import LoadingScreen from './LoadingScreen.vue'
    import { useWindowSize } from '@vueuse/core'
    import ItemSimilaritySelector from '../items/ItemSimilaritySelector.vue'
    import ItemTeaser from '../items/ItemTeaser.vue'
    import ItemGraphPath from '../items/ItemGraphPath.vue'
    import { OBJECTION_ACTIONS, useApp } from '@/store/app'
    import ItemBinarySearch from '../items/ItemBinarySearch.vue'
    import ItemTagRecommend from '../items/ItemTagRecommend.vue'
    import ItemCustomRecommend from '../items/ItemCustomRecommend.vue'
    import ItemSelect from '../items/ItemSelect.vue'
    import MiniDialog from '../dialogs/MiniDialog.vue'
    import { addSimilarity, getSimilarByTarget } from '@/use/data-api'
    import { useToast } from 'vue-toastification'

    const emit = defineEmits(["end", "close"])

    // stores
    const app = useApp()
    const sounds = useSounds()
    const settings = useSettings()
    const games = useGames()
    const toast = useToast()

    const { barCodeNodeSize } = storeToRefs(settings)

    const wSize = useWindowSize()
    const nodeSize = computed(() => {
        if (gameData.tagDomain.length === 0) {
            return barCodeNodeSize.value
        }
        return Math.max(2, Math.floor((wSize.width.value * 0.6) / gameData.tagDomain.length))
    })

    const showSearch = ref(false)
    const step = ref(1)
    const candidates = ref([])

    // difficulty settings
    const { difficulty } = storeToRefs(games)

    // game related stuff
    const state = ref(STATES.START)
    const inventory = ref([])
    const gameData = reactive({
        target: null,
        tagDomain: [],
        resultItems: [],
        customItems: [],
        otherItems: []
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

    function setTarget(item) {
        gameData.resultItems = []
        gameData.customItems = []
        gameData.otherItems = []
        gameData.target = item
        showSearch.value = false
        startRound(Date.now()-1200)
    }

    function setCandidates(items) {
        candidates.value = items
        step.value = 2
    }

    function setResultItems(items) {
        gameData.resultItems = items
    }
    function setAdditionalItems(items) {
        gameData.customItems = items
    }

    function startRound(timestamp=null) {
        state.value = STATES.LOADING
        step.value = 1
        inventory.value = []
        sounds.play(SOUND.START_SHORT)
        setTimeout(
            () => state.value = STATES.INGAME,
            1000 - (timestamp !== null ? Date.now()-timestamp : 0)
        )
    }
    function tryStartRound(timestamp=null) {
        gameData.resultItems = []
        gameData.customItems = []
        gameData.otherItems = []
        gameData.target = randomItems(1, 5)
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
    function searchItem() {
        showSearch.value = true
    }

    async function stopGame() {
        state.value = STATES.END

        // submit data
        const now = Date.now()
        let guid = localStorage.getItem("crowd-guid")
        if (!guid) {
            guid = self.crypto.randomUUID()
            // TODO: make sure this identifier is unique
            localStorage.setItem("crowd-guid", guid)
        }

        const transform = (d, tid) => ({
            dataset_id: app.ds,
            item_id: d.id,
            target_id: tid,
            game_id: difficulty.value,
            timestamp: now,
            guid: guid,
            value: d.value
        })

        const allItems = gameData.resultItems
            .concat(gameData.customItems)
            .map(d => transform(d, gameData.target.id))

        // get all highly similar items
        const highSim = new Set(allItems.filter(d => d.value > 1).map(d => d.item_id))
        // make the cross product of highly similar items
        const extra = cross(highSim, highSim)
        // add pairwise high similarity for highly similar items
        const submitItems = allItems.concat(extra.map(d => transform({ id: d[0], value: 2 }, d[1])))

        try {
            await addSimilarity(submitItems)
            // fetch common similar items for all players
            const set = new Set(allItems.map(d => d.id))
            const other = await getSimilarByTarget(gameData.target.id)
            gameData.otherItems = other.map(d => ({ id: d["item_id"], same: set.has(d["item_id"]) }))
        } catch(e) {
            console.error(e.toString())
            toast.error("error adding similarity")
        }
    }

    function close() {
        emit("close")
        reset()
    }

    function clear() {
        step.value = 1
        candidates.value = []
        gameData.target = null
        gameData.resultItems = []
        gameData.customItems = []
        gameData.otherItems = []
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

