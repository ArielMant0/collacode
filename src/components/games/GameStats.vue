<template>
    <div class="d-flex justify-center align-center flex-column">
        <StackedBarChart v-if="scores"
            class="mt-8 mb-2"
            :data="scores"
            :x-domain="allGameNames"
            x-attr="name"
            :y-attrs="['losses', 'wins']"
            color-legend
            :color-scale="colorScale"
            :height="200"
            :width="allGameNames.length*100"/>
        <v-data-table style="max-width: 900px;" :headers="headers" :items="scores"></v-data-table>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { GAMELIST, useGames } from '@/store/games';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { sortObjByString } from '@/use/sorting';
    import { computed, onMounted } from 'vue';
    import StackedBarChart from '../vis/StackedBarChart.vue';
    import { useTheme } from 'vuetify/lib/framework.mjs';
import { color } from 'd3';

    const app = useApp()
    const games = useGames()
    const times = useTimes()
    const theme = useTheme()

    const headers = [
        { key: "name", title: "Game" },
        { key: "played", title: "#Played" },
        { key: "wins", title: "#Wins" },
        { key: "streak_current", title: "Current Streak" },
        { key: "streak_highest", title: "Highest Streak" },
    ]
    const scores = ref([])
    const allGameNames = ref([])
    const colorScale = computed(() => ([
        theme.current.value.colors.primary,
        theme.current.value.colors.secondary
    ]))

    function loadScores() {
        allGameNames.value = GAMELIST.map(d => d.name)

        const tmp = DM.getDataBy("game_scores", d => d.user_id === app.activeUserId)
        tmp.forEach(d => {
            d.name = games.gameName(d.game_id)
            d.losses = d.played - d.wins;
        })
        tmp.sort(sortObjByString("name"))
        scores.value = tmp
    }

    onMounted(loadScores)

    watch(() => Math.max(times.all, times.game_scores), loadScores)
    watch(() => app.activeUserId, loadScores)
</script>