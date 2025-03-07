<template>
    <div v-if="!loading && active">
        <div v-if="activeGame === null" style="height: 80vh;" class="d-flex flex-column align-center justify-center ma-4">
            <v-sheet v-for="(g, idx) in GAMELIST" :key="'game_'+g"
                width="400"
                height="200"
                rounded
                @click="setActiveGame(GAMES[g])"
                class="cursor-pointer d-flex align-center justify-center pa-2 mr-2 mb-2 text-h2 hover-sat hover-bold"
                :color="schemeObservable10[idx]">
                {{ GAMES[g] }}
            </v-sheet>
        </div>
        <div v-else>
            <v-btn color="secondary" prepend-icon="mdi-keyboard-backspace" @click="onEndGame" style="position: absolute; top: 0; left: 0;">back to games</v-btn>
            <MatchingGame v-if="activeGame === GAMES.MATCHING" @end="onEndGame"/>
            <GeoGuesser v-else-if="activeGame === GAMES.GEOGUESSER" @end="onEndGame"/>
            <WhoAmI v-else-if="activeGame === GAMES.WHOAMI" @end="onEndGame"/>
        </div>
    </div>
</template>

<script setup>
    import { schemeObservable10 } from 'd3'
    import MatchingGame from '../games/MatchingGame.vue'
    import GeoGuesser from '../games/GeoGuesser.vue'
    import WhoAmI from '../games/WhoAmI.vue'

    import { useSettings } from '@/store/settings'
    import { computed, onMounted } from 'vue'
    import { GAMELIST, GAMES, useGames } from '@/store/games'
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

    const { activeGame } = storeToRefs(games)

    function setActiveGame(game) {
        activeGame.value = game;
    }
    function onEndGame() {
        activeGame.value = null;
    }

    onMounted(function() { games.loadSounds() })
</script>