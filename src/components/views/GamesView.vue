<template>
    <div v-if="!loading && active">
        <div v-if="activeGame === null" style="width: 100%; text-align: center;">
            <v-btn-toggle v-model="view"
                rounded="sm" border
                divided mandatory
                density="comfortable"
                variant="text"
                color="primary">

                <v-btn value="games" prepend-icon="mdi-controller">games</v-btn>
                <v-btn value="scores" prepend-icon="mdi-chart-line">stats</v-btn>

            </v-btn-toggle>
        </div>

        <div v-if="view === 'games'">
            <div v-if="activeGame === null" class="d-flex justify-center">
                <div style="min-width: 250px; max-width: 100%; height: 80vh;" :style="{ width: viewWidth }" class="d-flex flex-wrap align-center justify-center ma-4">
                    <div v-for="g in GAMELIST" :key="'game_'+g.id" class="mb-3 ml-6 mr-6">

                        <div v-if="mobile && !canPlayMobile(g.id)" class="text-caption" style="width: 100%; text-align: center;">
                            <span class="text-red text-decoration-underline"><b>cannot</b></span> be played on mobile
                        </div>

                        <v-hover>
                            <template v-slot:default="{ isHovering, props }">
                                <v-btn v-bind="props"
                                    rounded="0"
                                    stacked
                                    style="font-size: 24px; height: fit-content; width: 100%;"
                                    class="pa-3 hover-bold rounded-t-lg"
                                    variant="tonal"
                                    :disabled="!canPlayGame(g.id)"
                                    @click="setActiveGame(g)">

                                    <div class="d-flex align-center">
                                        <div>{{ g.name }}</div>
                                        <v-icon v-if="g.multiplayer" class="ml-1" size="sm">mdi-account-multiple</v-icon>
                                    </div>
                                    <div>
                                        <v-icon size="50" :class="['mt-1', 'mb-1', isHovering ? 'always-wobble' : '']">{{ GAME_ICON[g.id] }}</v-icon>
                                    </div>
                                </v-btn>
                            </template>
                        </v-hover>


                        <div class="rounded-b-lg d-flex align-center" style="width: 100%;">

                            <v-tooltip location="bottom" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-btn v-bind="props"
                                        class="hover-sat rounded-b-lg holo"
                                        variant="flat"
                                        rounded="0"
                                        :value="DIFFICULTY.EASY"
                                        :color="diffPerGame[g.id] === DIFFICULTY.EASY ? DIFF_COLOR.EASY : 'default'"
                                        @click="setDifficulty(g.id, DIFFICULTY.EASY)">
                                        <DifficultyIcon :value="DIFFICULTY.EASY" :no-color="diffPerGame[g.id] === DIFFICULTY.EASY"/>
                                    </v-btn>
                                </template>

                                <template v-slot:default>
                                    <div>
                                        <div style="text-align: center;" class="text-uppercase">easy mode</div>
                                        <div v-for="d in g.desc[DIFFICULTY.EASY]" v-html="d"></div>
                                    </div>
                                </template>
                            </v-tooltip>

                            <v-tooltip location="bottom" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-btn v-bind="props"
                                        class="hover-sat rounded-b-lg holo"
                                        variant="flat"
                                        rounded="0"
                                        :value="DIFFICULTY.NORMAL"
                                        :color="diffPerGame[g.id] === DIFFICULTY.NORMAL ? DIFF_COLOR.NORMAL : 'default'"
                                        @click="setDifficulty(g.id, DIFFICULTY.NORMAL)">
                                        <DifficultyIcon :value="DIFFICULTY.NORMAL" :no-color="diffPerGame[g.id] === DIFFICULTY.NORMAL"/>
                                    </v-btn>
                                </template>

                                <template v-slot:default>
                                    <div>
                                        <div style="text-align: center;" class="text-uppercase">normal mode</div>
                                        <div v-for="d in g.desc[DIFFICULTY.NORMAL]" v-html="d"></div>
                                    </div>
                                </template>
                            </v-tooltip>

                            <v-tooltip location="bottom" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-btn v-bind="props"
                                        class="hover-sat rounded-b-lg holo"
                                        variant="flat"
                                        rounded="0"
                                        :value="DIFFICULTY.HARD"
                                        :color="diffPerGame[g.id] === DIFFICULTY.HARD ? DIFF_COLOR.HARD : 'default'"
                                        @click="setDifficulty(g.id, DIFFICULTY.HARD)">
                                        <DifficultyIcon :value="DIFFICULTY.HARD" :no-color="diffPerGame[g.id] === DIFFICULTY.HARD"/>
                                    </v-btn>
                                </template>

                                <template v-slot:default>
                                    <div>
                                        <div style="text-align: center;" class="text-uppercase">hard mode</div>
                                        <div v-for="d in g.desc[DIFFICULTY.HARD]" v-html="d"></div>
                                    </div>
                                </template>
                            </v-tooltip>
                        </div>

                    </div>
                </div>
            </div>
            <div v-else style="width: 100%;" :style="{ maxHeight: verticalLayout || wSize.height.value < 600 ? null : '87vh' }">
                <div class="d-flex align-center justify-space-between mb-2">
                    <v-btn color="secondary" prepend-icon="mdi-keyboard-backspace" density="comfortable" @click="close">go back</v-btn>
                    <div class="d-flex align-center justify-end">
                        <v-btn
                            :icon="sounds.getVolumeIcon()"
                            class="mr-2"
                            rounded
                            :size="mdAndUp ? 'normal' : 'small'"
                            variant="text"
                            @click="sounds.toggleMuted()"
                            density="compact"/>
                        <div v-if="!activeGame.multiplayer && mdAndUp">
                            <v-btn class="hover-sat" variant="outlined" density="comfortable"  :color="difficulty === DIFFICULTY.EASY?DIFF_COLOR.EASY:'default'" @click="setDifficulty(activeGame.id, DIFFICULTY.EASY)">
                                <DifficultyIcon :value="DIFFICULTY.EASY" no-color/>
                            </v-btn>
                            <v-btn class="hover-sat ml-1 mr-1" density="comfortable" variant="outlined" :color="difficulty === DIFFICULTY.NORMAL?DIFF_COLOR.NORMAL:'default'" @click="setDifficulty(activeGame.id, DIFFICULTY.NORMAL)">
                                <DifficultyIcon :value="DIFFICULTY.NORMAL" no-color/>
                            </v-btn>
                            <v-btn class="hover-sat" variant="outlined" density="comfortable" :color="difficulty === DIFFICULTY.HARD?DIFF_COLOR.HARD:'default'" @click="setDifficulty(activeGame.id, DIFFICULTY.HARD)">
                                <DifficultyIcon :value="DIFFICULTY.HARD" no-color/>
                            </v-btn>
                        </div>
                    </div>
                </div>
                <MatchingGame v-if="activeGame.id === GAMES.MATCHING" @end="onEndGame" @close="close"/>
                <WhereAmI v-else-if="activeGame.id === GAMES.WHEREAMI" @end="onEndGame" @close="close"/>
                <WhoAmI v-else-if="activeGame.id === GAMES.WHOAMI" @end="onEndGame" @close="close"/>
                <TriviaGame v-else-if="activeGame.id === GAMES.TRIVIA" @round="onRoundEnd" @end="onEndGame" @close="close"/>
                <SetGame v-else-if="activeGame.id === GAMES.SET" @end="onEndGame" @close="close"/>
            </div>
        </div>
        <div v-else>
            <GameStats/>
        </div>
    </div>
</template>

<script setup>
    import MatchingGame from '../games/MatchingGame.vue'
    import WhereAmI from '../games/WhereAmI.vue'
    import WhoAmI from '../games/WhoAmI.vue'
    import TriviaGame from '../games/TriviaGame.vue'

    import { useSettings } from '@/store/settings'
    import { computed, onMounted, reactive } from 'vue'
    import { DIFF_COLOR, DIFFICULTY, GAMELIST, GAMES, GAME_ICON, useGames } from '@/store/games'
    import { storeToRefs } from 'pinia'
    import SetGame from '../games/SetGame.vue'
    import { addGameScores, addGameScoresItems, addGameScoresTags } from '@/use/data-api'
    import { useToast } from 'vue-toastification'
    import { useTimes } from '@/store/times'
    import { useApp } from '@/store/app'
    import GameStats from '../games/GameStats.vue'
    import { useWindowSize } from '@vueuse/core'
    import { useSounds } from '@/store/sounds'
    import DifficultyIcon from '../games/DifficultyIcon.vue'
    import Cookies from 'js-cookie'
    import DM from '@/use/data-manager'
    import { useDisplay } from 'vuetify'

    const app = useApp()
    const games = useGames()
    const settings = useSettings()
    const toast = useToast()
    const times = useTimes()
    const sounds = useSounds()

    const { mdAndUp, mobile } = useDisplay()

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const { activeGame, difficulty } = storeToRefs(games)
    const { verticalLayout } = storeToRefs(settings)

    const view = ref("games")
    const active = computed(() => settings.activeTab === "games")
    const diffPerGame = reactive({})

    const wSize = useWindowSize()
    const viewWidth = computed(() => {
        if (wSize.width.value <= 600) {
            return "100%"
        } else if (wSize.width.value <= 1500) {
            return "70%"
        } else {
            return "50%"
        }
    })

    function setDifficulty(gid, diff) {
        if (gid) {
            diffPerGame[gid] = Math.max(diff, Math.min(diff, DIFFICULTY.HARD))
            difficulty.value = diffPerGame[gid]
            saveDiffPerGame()
        }
    }
    function setActiveGame(game) {
        if (game) {
            difficulty.value = diffPerGame[game.id]
            activeGame.value = game;
        }
    }

    function canPlayMobile(id) {
        return id !== GAMES.WHEREAMI
    }
    function canPlayGame(id) {
        const base = DM.getSize("items", false) >= 25 && DM.getSize("tags", false) >= 10
        return base && (!mobile.value || canPlayMobile(id))
    }

    async function addScoresItems(items) {
        if (!items || items.length === 0) return
        const now = Date.now()
        return addGameScoresItems(items.map(d => ({
            code_id: app.currentCode,
            user_id: app.activeUserId,
            item_id: d.id,
            game_id: activeGame.value.id,
            difficulty: difficulty.value,
            created: now,
            win: d.correct
        })))
    }
    async function addScoresTags(tags) {
        if (!tags || tags.length === 0) return
        const now = Date.now()
        return addGameScoresTags(tags.map(d => ({
            code_id: app.currentCode,
            user_id: app.activeUserId,
            tag_id: d.tag_id,
            item_id: d.item_id,
            game_id: activeGame.value.id,
            difficulty: difficulty.value,
            created: now,
            win: d.correct,
        })))
    }
    async function addScore(win, score) {
        return addGameScores([{
            code_id: app.currentCode,
            user_id: app.activeUserId,
            game_id: activeGame.value.id,
            difficulty: difficulty.value,
            win: win,
            score: score
        }])
    }
    async function onRoundEnd(items=null, tags=null) {
        try {
            await addScoresItems(items)
            await addScoresTags(tags)
            times.needsReload("game_scores")
        } catch(e) {
            console.error(e.toString())
            toast.error("error updating game scores")
        }
    }
    async function onEndGame(win, score, items=null, tags=null) {
        try {
            await addScore(win, score)
            await addScoresItems(items)
            await addScoresTags(tags)
            times.needsReload("game_scores")
        } catch(e) {
            console.error(e.toString())
            toast.error("error updating game scores")
        }
    }
    function close() {
        activeGame.value = null;
        sounds.fadeAll()
    }

    function saveDiffPerGame() {
        Cookies.set("game-diffs", JSON.stringify(diffPerGame), { expires: 365 })
    }
    function readDiffPerGame() {
        const fromCookie = Cookies.get("game-diffs")
        const cdiffs = fromCookie ? JSON.parse(fromCookie) : null
        GAMELIST.forEach(d => {
            if (cdiffs && cdiffs[d.id] !== undefined && cdiffs[d.id] !== null) {
                diffPerGame[d.id] = cdiffs[d.id]
            } else {
                diffPerGame[d.id] = DIFFICULTY.EASY
            }
        })
        saveDiffPerGame()
    }

    onMounted(readDiffPerGame)
</script>
