<template>
    <div v-if="!loading && active">
        <div v-if="activeGame === null" style="height: 80vh;" class="d-flex flex-column align-center justify-center ma-4">
            <div v-for="g in GAMELIST" :key="'game_'+g" class="mb-3">
                <v-sheet
                    width="400"
                    height="180"
                    rounded
                    @click="setActiveGame(GAMES[g])"
                    class="d-flex align-center justify-center pa-2 mb-1 text-h3"
                    color="surface-light">
                    {{ GAMES[g] }}
                </v-sheet>
                <div class="d-flex justify-space-between" style="width: 400px;">
                    <v-btn class="hover-sat" variant="outlined" color="#47ad13" @click="setActiveGame(GAMES[g], DIFFICULTY.EASY)">
                        <v-icon size="small">mdi-star</v-icon>
                        <v-icon size="small">mdi-star-outline</v-icon>
                        <v-icon size="small">mdi-star-outline</v-icon>
                        easy
                    </v-btn>
                    <v-btn class="hover-sat" variant="outlined" color="#eba605" @click="setActiveGame(GAMES[g], DIFFICULTY.NORMAL)">
                        <v-icon size="small">mdi-star</v-icon>
                        <v-icon size="small">mdi-star</v-icon>
                        <v-icon size="small">mdi-star-outline</v-icon>
                        normal
                    </v-btn>
                    <v-btn class="hover-sat" variant="outlined" color="#d11706" @click="setActiveGame(GAMES[g], DIFFICULTY.HARD)">
                        <v-icon size="small">mdi-star</v-icon>
                        <v-icon size="small">mdi-star</v-icon>
                        <v-icon size="small">mdi-star</v-icon>
                        hard
                    </v-btn>
                </div>
            </div>
        </div>
        <div v-else>
            <div>
                <v-btn color="secondary" prepend-icon="mdi-keyboard-backspace" @click="onEndGame" style="position: absolute; top: 0; left: 0;">back to games</v-btn>
                <div style="position: absolute; top: 0; right: 0;">
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
            <MatchingGame v-if="activeGame === GAMES.MATCHING" :difficulty="difficulty" @end="onEndGame"/>
            <GeoGuesser v-else-if="activeGame === GAMES.GEOGUESSER" :difficulty="difficulty" @end="onEndGame"/>
            <WhoAmI v-else-if="activeGame === GAMES.WHOAMI" :difficulty="difficulty" @end="onEndGame"/>
        </div>
    </div>
</template>

<script setup>
    import MatchingGame from '../games/MatchingGame.vue'
    import GeoGuesser from '../games/GeoGuesser.vue'
    import WhoAmI from '../games/WhoAmI.vue'

    import { useSettings } from '@/store/settings'
    import { computed, onMounted } from 'vue'
    import { DIFFICULTY, GAMELIST, GAMES, useGames } from '@/store/games'
    import { storeToRefs } from 'pinia'

    const games = useGames()
    const settings = useSettings()

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const active = computed(() => settings.activeTab === "games")

    const { activeGame, difficulty } = storeToRefs(games)

    function setDifficulty(diff) {
        difficulty.value = Math.max(DIFFICULTY.EASY, Math.min(diff, DIFFICULTY.HARD))
    }
    function setActiveGame(game, diff=DIFFICULTY.EASY) {
        setDifficulty(diff)
        activeGame.value = game;
    }
    function onEndGame() {
        activeGame.value = null;
    }

    onMounted(function() { games.loadSounds() })
</script>