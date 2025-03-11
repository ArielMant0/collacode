<template>
    <div class="d-flex justify-center align-center flex-column">
        <StackedBarChart v-if="barData.length > 0"
            class="mt-8"
            :data="barData"
            :x-domain="allGameNames"
            x-attr="name"
            :y-attrs="['losses', 'wins']"
            color-legend
            :color-scale="colorScale"
            :padding="25"
            :height="150"
            :width="allGameNames.length*100"/>

        <div v-if="scores.length > 0" style="max-width: 1200px; width: 100%;">
            <h4>Overall Stats</h4>
            <v-data-table density="compact" :headers="headers" :items="scores">
                <template v-slot:item.user_id="{ value }">
                    <span>{{ app.getUserName(value) }}</span>
                </template>

                <template v-slot:item.difficulty="{ value }">
                    <div>
                        <DifficultyIcon :value="value"/>
                    </div>
                </template>
            </v-data-table>
        </div>

        <div v-if="itemGroups.length > 0" style="max-width: 1200px; width: 100%;" class="mt-2">
            <h4>{{ capitalize(app.itemName) }} Stats</h4>
            <v-text-field v-model="searchItems"
                label="Search"
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="compact"
                class="mb-1"
                clearable
                hide-details
                single-line/>
            <v-data-table density="compact"  :headers="itemHeaders" :items="itemGroups" :search="searchItems">
                <template v-slot:item="{ item }">
                    <tr>
                        <td>{{ item.name }}</td>
                        <td class="pt-1 pb-1"><ItemTeaser :item="item" :width="100" :height="50"/></td>
                        <td>{{ item.global.percent }}% ({{ item.global.value }} / {{ item.global.total }})</td>
                        <td v-for="name in allGameNames" :key="name+'_'+item.id">
                            <span v-if="item[name]">
                                {{ item[name].percent }}% ({{ item[name].value }} / {{ item[name].total }})
                            </span>
                            <span v-else>-</span>
                        </td>
                    </tr>
                </template>
            </v-data-table>
        </div>

        <div v-if="tagGroups.length > 0" style="max-width: 1200px; width: 100%;" class="mt-2">
            <h4>Tag Stats</h4>
            <v-text-field v-model="searchTags"
                label="Search"
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="compact"
                class="mb-1"
                clearable
                hide-details
                single-line/>
            <v-data-table density="compact"  :headers="tagHeaders" :items="tagGroups" :search="searchTags">
                <template v-slot:item="{ item }">
                    <tr>
                        <td @contextmenu="e => rightClickTag(item, e)">{{ item.name }}</td>
                        <td>{{ item.parent }}</td>
                        <td>{{ item.global.percent }}% ({{ item.global.value }} / {{ item.global.total }})</td>
                        <td v-for="name in allGameNames" :key="name+'_'+item.id">
                            <span v-if="item[name]">
                                {{ item[name].percent }}% ({{ item[name].value }} / {{ item[name].total }})
                            </span>
                            <span v-else>-</span>
                        </td>
                    </tr>
                </template>
            </v-data-table>
        </div>

    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { DIFF_COLOR, DIFFICULTY, GAMELIST, useGames } from '@/store/games';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { sortObjByString } from '@/use/sorting';
    import { computed, onMounted } from 'vue';
    import StackedBarChart from '../vis/StackedBarChart.vue';
    import { useTheme } from 'vuetify/lib/framework.mjs';
    import { group, pointer } from 'd3';
    import { capitalize } from '@/use/utility';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
import DifficultyIcon from './DifficultyIcon.vue';

    const app = useApp()
    const games = useGames()
    const times = useTimes()
    const theme = useTheme()
    const settings = useSettings()

    const headers = computed(() => {
        const list = [
            { key: "name", title: "Game" },
            { key: "difficulty", title: "Difficulty" },
            { key: "played", title: "#Played" },
            { key: "wins", title: "#Wins" },
            { key: "streak_current", title: "Current Streak" },
            { key: "streak_highest", title: "Highest Streak" },
        ]
        return app.showAllUsers ?
            list.slice(0, 2).concat([{ key: "user_id", title: "User" }]).concat(list.slice(2)) :
            list
    })
    const itemHeaders = computed(() => {
        return [
            { key: "name", title: "Name", maxWidth: 250 },
            { key: "teaser", title: "Teaser", sortable: false },
            { key: "global", title: "Overall", minWidth: 150 ,value: d => d.global.percent },
        ].concat(allGameNames.value.map(d => ({ key: d, title: capitalize(d), value: dd => dd[d] ? dd[d].percent : 0 })))
    })
    const tagHeaders = computed(() => {
        return [
            { key: "name", title: "Name", maxWidth: 250 },
            { key: "parent", title: "Parent" },
            { key: "global", title: "Overall",  minWidth: 150, value: d => d.global.percent },
        ].concat(allGameNames.value.map(d => ({ key: d, title: capitalize(d), value: dd => dd[d] ? dd[d].percent : 0 })))
    })

    const searchItems = ref("")
    const searchTags = ref("")

    const allGameNames = ref([])
    const colorScale = computed(() => ([
        theme.current.value.colors.primary,
        theme.current.value.colors.secondary
    ]))

    const barData = ref([])

    const scores = ref([])
    const itemGroups = ref([])
    const tagGroups = ref([])

    function rightClickTag(tag, event) {
        event.preventDefault()
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "tag",
            tag.id,
            mx, my,
            tag.name,
            null,
            CTXT_OPTIONS.tag
        )
    }

    function loadScores() {
        allGameNames.value = GAMELIST.map(d => d.name)

        const tmpScores = app.showAllUsers ?
            DM.getData("game_scores", false) :
            DM.getDataBy("game_scores", d => d.user_id === app.activeUserId)

        tmpScores.forEach(d => {
            d.name = games.gameName(d.game_id)
            d.losses = d.played - d.wins;
        })
        tmpScores.sort(sortObjByString("name"))

        let tmp = []
        let g = group(tmpScores, d => d.name)
        g.forEach((list, name) => {
            const played = list.reduce((acc, d) => acc + d.played, 0)
            const wins = list.reduce((acc, d) => acc + d.wins, 0)
            tmp.push({
                name: name,
                wins: wins,
                losses: played - wins
            })
        })
        barData.value = tmp
        scores.value = tmpScores

        const tmpItems = app.showAllUsers ?
            DM.getData("game_scores_items", false) :
            DM.getDataBy("game_scores_items", d => d.user_id === app.activeUserId)

        g = group(tmpItems, d => d.item_id)
        tmp = []
        g.forEach((list, item_id) => {
            const it = DM.getDataItem("items", item_id)

            const obj = {
                id: it.id,
                name: it.name,
                teaser: it.teaser,
                global: { percent: 0, value: 0, total: 0 }
            }
            GAMELIST.forEach(d => {
                const l = list.find(dd => dd.game_id === d.id)
                if (l) {
                    obj[d.name] = {
                        percent: Math.round((l.right / (l.right + l.wrong)) * 100),
                        value: l.right,
                        total: l.right + l.wrong
                    }
                    obj.global.value += l.right
                    obj.global.total += l.right + l.wrong
                }
            })
            obj.global.percent = Math.round((obj.global.value / obj.global.total) * 100)
            tmp.push(obj)
        })
        itemGroups.value = tmp

        const tmpTags = app.showAllUsers ?
            DM.getData("game_scores_tags", false) :
            DM.getDataBy("game_scores_tags", d => d.user_id === app.activeUserId)

        g = group(tmpTags, d => d.tag_id)
        tmp = []
        g.forEach((list, tag_id) => {
            const it = DM.getDataItem("tags", tag_id)
            const parent = it.parent !== null && it.parent > 0 ?
                DM.getDataItem("tags_name", it.parent) :
                ""

            const obj = {
                id: it.id,
                name: it.name,
                parent: parent,
                global: { percent: 0, value: 0, total: 0 }
            }

            GAMELIST.forEach(d => {
                const l = list.find(dd => dd.game_id === d.id)
                if (l) {
                    obj[d.name] = {
                        percent: Math.round((l.right / (l.right + l.wrong)) * 100),
                        value: l.right,
                        total: l.right + l.wrong
                    }
                    obj.global.value += l.right
                    obj.global.total += l.right + l.wrong
                }
            })
            obj.global.percent = Math.round((obj.global.value / obj.global.total) * 100)
            tmp.push(obj)
        })
        tagGroups.value = tmp

    }

    onMounted(loadScores)

    watch(() => Math.max(times.all, times.game_scores), loadScores)
    watch(() => app.activeUserId, loadScores)
    watch(() => app.showAllUsers, loadScores)
</script>