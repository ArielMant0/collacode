<template>
    <div v-if="!loading && active">

        <div v-if="activeGame === null" style="width: 100%; text-align: center;">
            <v-btn-toggle v-model="view" rounded="sm" border divided mandatory density="comfortable" variant="text" color="primary">
                <v-btn value="games" icon="mdi-controller"></v-btn>
                <v-btn value="scores" icon="mdi-chart-line"></v-btn>
            </v-btn-toggle>
        </div>

        <div v-if="view === 'games'">
            <div v-if="activeGame === null" style="height: 85vh;" class="d-flex flex-column flex-wrap align-center justify-center ma-4">
                <div v-for="g in GAMELIST" :key="'game_'+g.id" class="mb-3">
                    <v-sheet
                        width="400"
                        height="180"
                        rounded
                        @click="setActiveGame(g)"
                        class="d-flex align-center justify-center pa-2 mb-1 text-h3"
                        color="surface-light">
                        {{ g.name }}
                    </v-sheet>
                    <div class="d-flex justify-space-between" style="width: 400px;">
                        <v-btn class="hover-sat" variant="outlined" color="#47ad13" @click="setActiveGame(g, DIFFICULTY.EASY)">
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star-outline</v-icon>
                            <v-icon size="small">mdi-star-outline</v-icon>
                            easy
                        </v-btn>
                        <v-btn class="hover-sat" variant="outlined" color="#eba605" @click="setActiveGame(g, DIFFICULTY.NORMAL)">
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star-outline</v-icon>
                            normal
                        </v-btn>
                        <v-btn class="hover-sat" variant="outlined" color="#d11706" @click="setActiveGame(g, DIFFICULTY.HARD)">
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star</v-icon>
                            hard
                        </v-btn>
                    </div>
                </div>
            </div>
            <div v-else style="width: 100%;">
                <div class="d-flex align-center justify-space-between mb-2">
                    <v-btn color="secondary" prepend-icon="mdi-keyboard-backspace" @click="close">back to games</v-btn>
                    <div>
                        <v-btn class="hover-sat" variant="outlined" :color="difficulty === DIFFICULTY.EASY?'#47ad13':'default'" @click="setDifficulty(DIFFICULTY.EASY)">
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star-outline</v-icon>
                            <v-icon size="small">mdi-star-outline</v-icon>
                            easy
                        </v-btn>
                        <v-btn class="hover-sat ml-1 mr-1" variant="outlined" :color="difficulty === DIFFICULTY.NORMAL?'#eba605':'default'" @click="setDifficulty(DIFFICULTY.NORMAL)">
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star-outline</v-icon>
                            normal
                        </v-btn>
                        <v-btn class="hover-sat" variant="outlined" :color="difficulty === DIFFICULTY.HARD?'#d11706':'default'" @click="setDifficulty(DIFFICULTY.HARD)">
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star</v-icon>
                            <v-icon size="small">mdi-star</v-icon>
                            hard
                        </v-btn>
                    </div>
                </div>
                <MatchingGame v-if="activeGame.id === GAMES.MATCHING" :difficulty="difficulty" @end="onEndGame" @close="close"/>
                <GeoGuesser v-else-if="activeGame.id === GAMES.GEOGUESSER" :difficulty="difficulty" @end="onEndGame" @close="close"/>
                <WhoAmI v-else-if="activeGame.id === GAMES.WHOAMI" :difficulty="difficulty" @end="onEndGame" @close="close"/>
                <TriviaGame v-else-if="activeGame.id === GAMES.TRIVIA" :difficulty="difficulty" @end="onEndGame" @close="close"/>
                <SetMultiplayer v-else-if="activeGame.id === GAMES.SET" :difficulty="difficulty" @end="onEndGame" @close="close"/>
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
    import { DIFFICULTY, GAMELIST, GAMES, useGames } from '@/store/games'
    import { storeToRefs } from 'pinia'
    import SetMultiplayer from '../games/SetMultiplayer.vue'
    import { addGameScores } from '@/use/utility'
    import { useToast } from 'vue-toastification'
    import { useTimes } from '@/store/times'
    import { useApp } from '@/store/app'
    import GameStats from '../games/GameStats.vue'

    const app = useApp()
    const games = useGames()
    const settings = useSettings()
    const toast = useToast()
    const times = useTimes()

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const active = computed(() => settings.activeTab === "games")

    const view = ref("games")

    const { activeGame, difficulty } = storeToRefs(games)

    function setDifficulty(diff) {
        difficulty.value = Math.max(DIFFICULTY.EASY, Math.min(diff, DIFFICULTY.HARD))
    }
    function setActiveGame(game, diff=DIFFICULTY.EASY) {
        setDifficulty(diff)
        activeGame.value = game;
    }
    async function onEndGame(won) {
        try {
            await addGameScores([{
                code_id: app.currentCode,
                user_id: app.activeUserId,
                game_id: activeGame.value.id,
                difficulty: difficulty.value,
                win: won
            }])
            toast.success("updated game scores")
            times.needsReload("game_scores")
        } catch(e) {
            toast.error("error updating game scores")
        }
    }
    function close() {
        activeGame.value = null;
    }

    onMounted(function() { games.loadSounds() })
</script>