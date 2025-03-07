<template>
    <div v-if="!loading && active">
        <div v-if="activeGame === null" style="height: 80vh;" class="d-flex flex-column align-center ma-4">
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
        <MatchingGame v-else-if="activeGame === GAMES.MATCHING" @end="onEndGame"/>
        <GeoGuesser v-else-if="activeGame === GAMES.GEOGUESSER" @end="onEndGame"/>
    </div>
</template>

<script setup>
    import MatchingGame from '../games/MatchingGame.vue'
    import GeoGuesser from '../games/GeoGuesser.vue'
    import { schemeObservable10 } from 'd3'

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
        console.log(game)
        activeGame.value = game;
    }
    function onEndGame() {
        activeGame.value = null;
    }

    onMounted(function() { games.loadSounds() })
</script>