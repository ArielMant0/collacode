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
            <div v-if="activeGame === null" class="d-flex justify-center" style="max-height: 85vh; overflow-y: auto;">
                <div style="min-width: 320px; max-width: 100%; height: 80vh;" :style="{ width: viewWidth }" class="d-flex flex-wrap align-center justify-center ma-4">
                    <div v-for="g in GAMELIST" :key="'game_'+g.id" class="mb-3 ml-6 mr-6">
                        <v-sheet
                            width="300"
                            height="180"
                            rounded
                            style="font-size: 28px"
                            class="d-flex align-center justify-center flex-column pa-2 mb-1 hover-bold cursor-pointer"
                            @click="setActiveGame(g)"
                            color="surface-light">

                            <div class="d-flex align-center">
                                <div>{{ g.name }}</div>
                                <v-icon v-if="g.multiplayer" class="ml-1" size="sm">mdi-account-multiple</v-icon>
                            </div>
                            <div>
                                <v-icon size="50" class="mt-1 mb-1">{{ GAME_ICON[g.id] }}</v-icon>
                            </div>
                            <DifficultyIcon :value="DIFFICULTY.EASY" size="14px" no-color/>
                        </v-sheet>

                        <div class="d-flex justify-space-between">

                            <v-tooltip location="bottom" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-btn v-bind="props"
                                        class="hover-sat"
                                        variant="outlined"
                                        style="width: 32%;"
                                        :color="DIFF_COLOR.EASY"
                                        @click="setActiveGame(g, DIFFICULTY.EASY)">
                                        <DifficultyIcon :value="DIFFICULTY.EASY"/>
                                    </v-btn>
                                </template>

                                <template v-slot:default>
                                    <div v-for="d in g.desc[DIFFICULTY.EASY]" v-html="d"></div>
                                </template>
                            </v-tooltip>

                            <v-tooltip location="bottom" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-btn v-bind="props"
                                        class="hover-sat"
                                        variant="outlined"
                                        style="width: 32%;"
                                        :color="DIFF_COLOR.NORMAL"
                                        @click="setActiveGame(g, DIFFICULTY.NORMAL)">
                                        <DifficultyIcon :value="DIFFICULTY.NORMAL"/>
                                    </v-btn>
                                </template>

                                <template v-slot:default>
                                    <div v-for="d in g.desc[DIFFICULTY.NORMAL]" v-html="d"></div>
                                </template>
                            </v-tooltip>

                            <v-tooltip location="bottom" open-delay="300">
                                <template v-slot:activator="{ props }">
                                    <v-btn v-bind="props"
                                        class="hover-sat"
                                        variant="outlined"
                                        style="width: 32%;"
                                        :color="DIFF_COLOR.HARD"
                                        @click="setActiveGame(g, DIFFICULTY.HARD)">
                                        <DifficultyIcon :value="DIFFICULTY.HARD"/>
                                    </v-btn>
                                </template>

                                <template v-slot:default>
                                    <div v-for="d in g.desc[DIFFICULTY.HARD]" v-html="d"></div>
                                </template>
                            </v-tooltip>
                        </div>
                    </div>
                </div>
            </div>
            <div v-else style="width: 100%;">
                <div class="d-flex align-center justify-space-between mb-2">
                    <v-btn color="secondary" prepend-icon="mdi-keyboard-backspace" density="comfortable" @click="close">back to games</v-btn>
                    <div class="d-flex align-center justify-end">
                        <v-btn
                            :icon="sounds.getVolumeIcon()"
                            class="mr-2"
                            rounded
                            variant="text"
                            @click="sounds.toggleMuted()"
                            density="compact"/>
                        <div v-if="!activeGame.multiplayer">
                            <v-btn class="hover-sat" variant="outlined" density="comfortable"  :color="difficulty === DIFFICULTY.EASY?DIFF_COLOR.EASY:'default'" @click="setDifficulty(DIFFICULTY.EASY)">
                                <DifficultyIcon :value="DIFFICULTY.EASY" no-color/>
                            </v-btn>
                            <v-btn class="hover-sat ml-1 mr-1" density="comfortable" variant="outlined" :color="difficulty === DIFFICULTY.NORMAL?DIFF_COLOR.NORMAL:'default'" @click="setDifficulty(DIFFICULTY.NORMAL)">
                                <DifficultyIcon :value="DIFFICULTY.NORMAL" no-color/>
                            </v-btn>
                            <v-btn class="hover-sat" variant="outlined" density="comfortable" :color="difficulty === DIFFICULTY.HARD?DIFF_COLOR.HARD:'default'" @click="setDifficulty(DIFFICULTY.HARD)">
                                <DifficultyIcon :value="DIFFICULTY.HARD" no-color/>
                            </v-btn>
                        </div>
                    </div>
                </div>
                <MatchingGame v-if="activeGame.id === GAMES.MATCHING" @end="onEndGame" @close="close"/>
                <GeoGuesser v-else-if="activeGame.id === GAMES.GEOGUESSER" @end="onEndGame" @close="close"/>
                <WhoAmI v-else-if="activeGame.id === GAMES.WHOAMI" @end="onEndGame" @close="close"/>
                <TriviaGame v-else-if="activeGame.id === GAMES.TRIVIA" @round="onRoundEnd" @end="onEndGame" @close="close"/>
                <SetMultiplayer v-else-if="activeGame.id === GAMES.SET" @end="onEndGame" @close="close"/>
            </div>
        </div>
        <div v-else>
            <GameStats/>
        </div>
    </div>
</template>

<script setup>
    import MatchingGame from '../games/MatchingGame.vue'
    import GeoGuesser from '../games/GeoGuesser.vue'
    import WhoAmI from '../games/WhoAmI.vue'
    import TriviaGame from '../games/TriviaGame.vue'

    import { useSettings } from '@/store/settings'
    import { computed } from 'vue'
    import { DIFF_COLOR, DIFFICULTY, GAMELIST, GAMES, GAME_ICON, useGames } from '@/store/games'
    import { storeToRefs } from 'pinia'
    import SetMultiplayer from '../games/SetMultiplayer.vue'
    import { addGameScores, addGameScoresItems, addGameScoresTags } from '@/use/utility'
    import { useToast } from 'vue-toastification'
    import { useTimes } from '@/store/times'
    import { useApp } from '@/store/app'
    import GameStats from '../games/GameStats.vue'
    import { useWindowSize } from '@vueuse/core'
    import { useSounds } from '@/store/sounds'
    import DifficultyIcon from '../games/DifficultyIcon.vue'

    const app = useApp()
    const games = useGames()
    const settings = useSettings()
    const toast = useToast()
    const times = useTimes()
    const sounds = useSounds()

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const { activeGame, difficulty } = storeToRefs(games)

    const view = ref("games")
    const active = computed(() => settings.activeTab === "games")

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

    function setDifficulty(diff) {
        difficulty.value = Math.max(DIFFICULTY.EASY, Math.min(diff, DIFFICULTY.HARD))
    }
    function setActiveGame(game, diff=DIFFICULTY.EASY) {
        setDifficulty(diff)
        activeGame.value = game;
    }

    async function addScoresItems(win, items) {
        if (!items || items.length === 0) return
        return addGameScoresItems(items.map(id => ({
            code_id: app.currentCode,
            user_id: app.activeUserId,
            item_id: id,
            game_id: activeGame.value.id,
            difficulty: difficulty.value,
            created: Date.now(),
            win: win
        })))
    }
    async function addScoresTags(win, tags) {
        if (!tags || tags.length === 0) return
        return  addGameScoresTags(tags.map(d => ({
            code_id: app.currentCode,
            user_id: app.activeUserId,
            tag_id: d.tag_id,
            item_id: d.item_id,
            game_id: activeGame.value.id,
            difficulty: difficulty.value,
            created: Date.now(),
            win: win,
        })))
    }
    async function addScore(win) {
        return addGameScores([{
            code_id: app.currentCode,
            user_id: app.activeUserId,
            game_id: activeGame.value.id,
            difficulty: difficulty.value,
            win: win
        }])
    }
    async function onRoundEnd(win, items=null, tags=null) {
        try {
            await addScoresItems(win, items)
            await addScoresTags(win, tags)
            times.needsReload("game_scores")
        } catch(e) {
            console.error(e.toString())
            toast.error("error updating game scores")
        }
    }
    async function onEndGame(win, items=null, tags=null) {
        try {
            await addScore(win)
            await addScoresItems(win, items)
            await addScoresTags(win, tags)
            times.needsReload("game_scores")
        } catch(e) {
            console.error(e.toString())
            toast.error("error updating game scores")
        }
    }
    function close() {
        sounds.fadeAll()
        activeGame.value = null;
    }
</script>
