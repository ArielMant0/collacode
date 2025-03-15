<template>
    <div v-if="!loading && active">

        <div v-if="activeGame === null" style="width: 100%; text-align: center;">
            <v-btn-toggle v-model="view" rounded="sm" border divided mandatory density="comfortable" variant="text" color="primary">
                <v-btn value="games" icon="mdi-controller"></v-btn>
                <v-btn value="scores" icon="mdi-chart-line"></v-btn>
            </v-btn-toggle>
        </div>

        <div v-if="view === 'games'">
            <div v-if="activeGame === null" class="d-flex justify-center" style="max-height: 85vh; overflow-y: auto;">
                <div style="min-width: 320px; max-width: 100%; height: 80vh;" :style="{ width: viewWidth }" class="d-flex flex-wrap align-center justify-center ma-4">
                    <div v-for="g in GAMELIST" :key="'game_'+g.id" class="mb-3 ml-6 mr-6">
                        <v-sheet
                            width="300"
                            height="150"
                            rounded
                            class="d-flex align-center justify-center pa-2 mb-1 text-h4 hover-bold cursor-pointer hover-border"
                            @click="setActiveGame(g)"
                            color="surface-light">
                            <span>{{ g.name }}</span> <v-icon v-if="g.multiplayer" size="sm" class="ml-1">mdi-account-multiple</v-icon>
                        </v-sheet>
                        <div class="d-flex justify-space-between">
                            <v-btn class="hover-sat" variant="outlined" style="width: 32%;" color="#47ad13" @click="setActiveGame(g, DIFFICULTY.EASY)">
                                <v-icon size="small">mdi-star</v-icon>
                                <v-icon size="small">mdi-star-outline</v-icon>
                                <v-icon size="small">mdi-star-outline</v-icon>
                            </v-btn>
                            <v-btn class="hover-sat" variant="outlined" style="width: 32%;" color="#eba605" @click="setActiveGame(g, DIFFICULTY.NORMAL)">
                                <v-icon size="small">mdi-star</v-icon>
                                <v-icon size="small">mdi-star</v-icon>
                                <v-icon size="small">mdi-star-outline</v-icon>
                            </v-btn>
                            <v-btn class="hover-sat" variant="outlined" style="width: 32%;" color="#d11706" @click="setActiveGame(g, DIFFICULTY.HARD)">
                                <v-icon size="small">mdi-star</v-icon>
                                <v-icon size="small">mdi-star</v-icon>
                                <v-icon size="small">mdi-star</v-icon>
                            </v-btn>
                        </div>
                    </div>
                </div>
            </div>
            <div v-else style="width: 100%;">
                <div class="d-flex align-center justify-space-between mb-2">
                    <v-btn color="secondary" prepend-icon="mdi-keyboard-backspace" density="comfortable" @click="close">back to games</v-btn>
                    <div v-if="!activeGame.multiplayer">
                        <v-btn class="hover-sat" variant="outlined" density="comfortable"  :color="difficulty === DIFFICULTY.EASY?DIFF_COLOR.EASY:'default'" @click="setDifficulty(DIFFICULTY.EASY)">
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star-outline</v-icon>
                            <v-icon size="small">mdi-star-outline</v-icon>
                        </v-btn>
                        <v-btn class="hover-sat ml-1 mr-1" density="comfortable" variant="outlined" :color="difficulty === DIFFICULTY.NORMAL?DIFF_COLOR.NORMAL:'default'" @click="setDifficulty(DIFFICULTY.NORMAL)">
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star-outline</v-icon>
                        </v-btn>
                        <v-btn class="hover-sat" variant="outlined" density="comfortable" :color="difficulty === DIFFICULTY.HARD?DIFF_COLOR.HARD:'default'" @click="setDifficulty(DIFFICULTY.HARD)">
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star</v-icon>
                        </v-btn>
                    </div>
                </div>
                <MatchingGame v-if="activeGame.id === GAMES.MATCHING" @end="onEndGame" @close="close"/>
                <GeoGuesser v-else-if="activeGame.id === GAMES.GEOGUESSER" @end="onEndGame" @close="close"/>
                <WhoAmI v-else-if="activeGame.id === GAMES.WHOAMI" @end="onEndGame" @close="close"/>
                <TriviaGame v-else-if="activeGame.id === GAMES.TRIVIA" @end="onEndGame" @close="close"/>
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
    import { computed, onMounted } from 'vue'
    import { DIFF_COLOR, DIFFICULTY, GAMELIST, GAMES, useGames } from '@/store/games'
    import { storeToRefs } from 'pinia'
    import SetMultiplayer from '../games/SetMultiplayer.vue'
    import { addGameScores, addGameScoresItems, addGameScoresTags } from '@/use/utility'
    import { useToast } from 'vue-toastification'
    import { useTimes } from '@/store/times'
    import { useApp } from '@/store/app'
    import GameStats from '../games/GameStats.vue'
    import { useWindowSize } from '@vueuse/core'
    import { useSounds } from '@/store/sounds'

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
    function setActiveGame(game, diff=DIFFICULTY.NORMAL) {
        setDifficulty(diff)
        activeGame.value = game;
    }
    async function onEndGame(win, items=null, tags=null) {
        try {
            await addGameScores([{
                code_id: app.currentCode,
                user_id: app.activeUserId,
                game_id: activeGame.value.id,
                difficulty: difficulty.value,
                win: win
            }])
            if (items) {
                await addGameScoresItems(items.map(id => ({
                    code_id: app.currentCode,
                    user_id: app.activeUserId,
                    item_id: id,
                    game_id: activeGame.value.id,
                    difficulty: difficulty.value,
                    win: win
                })))
            }
            if (tags) {
                await addGameScoresTags(tags.map(d => ({
                    code_id: app.currentCode,
                    user_id: app.activeUserId,
                    tag_id: d.tag_id,
                    item_id: d.item_id,
                    game_id: activeGame.value.id,
                    difficulty: difficulty.value,
                    win: win
                })))
            }
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