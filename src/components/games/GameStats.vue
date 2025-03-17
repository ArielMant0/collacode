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

        <div v-if="scores.length > 0" style="width: 100%;">
            <h4>Overall Stats</h4>
            <v-data-table density="compact" :headers="headers" :items="scores" multi-sort>
                <template v-slot:item.user_id="{ value }">
                    <v-chip
                        :color="app.getUserColor(value)"
                        variant="flat"
                        size="small"
                        :title="app.getUserName(value)">
                        {{ app.getUserShort(value) }}
                    </v-chip>
                </template>

                <template v-slot:item.difficulty="{ value }">
                    <div>
                        <DifficultyIcon :value="value"/>
                    </div>
                </template>
            </v-data-table>
        </div>

        <div class="mt-4">
            <div>Worst {{ app.itemNameCaptial }}</div>
            <div v-if="worst.item !== null" class="d-flex align-start justify-center">

                <ItemTeaser v-if="worst.item !== null" :id="worst.item.id" class="mr-1"/>

                <v-sheet class="ml-4 text-subtitle-1">
                    <div>Winrate: <b>{{ worst.item.global.percent }}%</b></div>
                    <div>Times Played: <b>{{ worst.item.global.total }}</b></div>
                    <div>Times Won: <b>{{ worst.item.global.value }}</b></div>
                </v-sheet>

                <WinrateOverTime class="ml-4"
                    :id="worst.item.id"
                    :width="180"
                    :height="80"
                    source="game_scores_items"
                    id-attr="item_id"/>

            </div>
            <v-card v-else width="160" height="80"  color="surface-light" class="d-flex align-center justify-center prevent-select">
                <v-icon size="large">mdi-image-area</v-icon>
            </v-card>
        </div>
        <div v-if="itemGroups.length > 0" style="width: 100%;" class="mt-2">
            <h4>{{ app.itemNameCaptial }} Stats</h4>
            <v-text-field v-model="searchItems"
                label="Search"
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="compact"
                class="mb-1"
                clearable
                hide-details
                single-line/>
            <v-data-table density="compact"  :headers="itemHeaders" :items="itemGroups" :search="searchItems" multi-sort>
                <template v-slot:item="{ item }">
                    <tr>
                        <td>{{ item.name }}</td>
                        <td class="pt-1 pb-1"><ItemTeaser :item="item" :width="100" :height="50"/></td>
                        <td>{{ item.global.percent }}% ({{ item.global.value }} / {{ item.global.total }})</td>
                        <td>{{ item.global.total }}</td>
                        <td><WinrateOverTime :id="item.id" source="game_scores_items" id-attr="item_id"/></td>
                        <template v-for="name in tableGameNames" :key="name+'_'+item.id">
                            <td>
                                <span v-if="item[name]">
                                    {{ item[name].percent }}% ({{ item[name].value }} / {{ item[name].total }})
                                </span>
                                <span v-else>-</span>
                            </td>
                        </template>
                    </tr>
                </template>
            </v-data-table>
        </div>

        <div class="mt-4">
            <div>Worst Tag</div>
            <div v-if="worst.tag !== null" class="d-flex align-start justify-center">

                <v-card width="160" height="80"  color="surface-light"
                    class="d-flex align-center justify-center text-ww">
                    <span>{{ worst.tag.name }}</span>
                </v-card>

                <v-sheet class="ml-4 text-subtitle-1">
                    <div>Winrate: <b>{{ worst.tag.global.percent }}%</b></div>
                    <div>Times Played: <b>{{ worst.tag.global.total }}</b></div>
                    <div>Times Won: <b>{{ worst.tag.global.value }}</b></div>
                </v-sheet>

                <WinrateOverTime
                    class="ml-4"
                    :id="worst.tag.id"
                    :width="180"
                    :height="80"
                    source="game_scores_tags"
                    id-attr="tag_id"/>
            </div>
            <span v-else>none</span>
        </div>
        <div v-if="tagGroups.length > 0" style="width: 100%;" class="mt-2">
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
            <v-data-table density="compact"  :headers="tagHeaders" :items="tagGroups" :search="searchTags" multi-sort>
                <template v-slot:item="{ item }">
                    <tr>
                        <td @contextmenu="e => rightClickTag(item, e)">{{ item.name }}</td>
                        <td>{{ item.parent }}</td>
                        <td>
                            <span v-if="item.items.length > 5">
                                <v-btn
                                    :icon="item.showItems ? 'mdi-menu-down' : 'mdi-menu-right'"
                                    @click="item.showItems = !item.showItems"
                                    density="compact"
                                    rounded="sm"
                                    class="mr-1"
                                    variant="text"/>
                                {{ item.items.length }}
                            </span>

                            <div v-if="item.items.length <= 5 || item.showItems" class="d-flex flex-wrap mt-1">
                                <ItemTeaser v-for="it in item.items"
                                    :key="'ti_'+it.id"
                                    :id="it.id"
                                    class="mr-1 mb-1"
                                    :style="{ padding: '2px', border: '2px solid '+getBorderColor(it.win) }"
                                    :width="80"
                                    :height="40"/>
                            </div>
                        </td>
                        <td>{{ item.global.percent }}% ({{ item.global.value }} / {{ item.global.total }})</td>
                        <td>{{ item.global.total }}</td>
                        <td><WinrateOverTime :id="item.id" source="game_scores_tags" id-attr="tag_id"/></td>
                    </tr>
                </template>
            </v-data-table>
        </div>

    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { GAMELIST, GAMES, useGames } from '@/store/games';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { sortObjByString } from '@/use/sorting';
    import { computed, onMounted, reactive } from 'vue';
    import StackedBarChart from '../vis/StackedBarChart.vue';
    import { useTheme } from 'vuetify/lib/framework.mjs';
    import { group, pointer } from 'd3';
    import { capitalize } from '@/use/utility';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import DifficultyIcon from './DifficultyIcon.vue';
    import WinrateOverTime from './WinrateOverTime.vue';

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
        const list = tableGameNames.value.map(d => {
            const n = capitalize(d)
            return {
                key: d+".percent",
                title: n+" %",
                value: dd => dd[d] ? dd[d].percent : 0
            }
        })

        return [
            { key: "name", title: "Name", maxWidth: 250 },
            { key: "teaser", title: "Teaser", sortable: false },
            { key: "global.percent", title: "Overall %", minWidth: 150 },
            { key: "global.total", title: "Rounds", minWidth: 150 },
            { key: "global.value", title: "Winrate", minWidth: 120 },
        ].concat(list)
    })
    const tagHeaders =  [
        { key: "name", title: "Name", maxWidth: 250 },
        { key: "parent", title: "Parent" },
        { key: "items", title: app.itemNameCaptial+"s", value: dd => dd.items.length, minWidth: 300 },
        { key: "global.percent", title: "Overall %", minWidth: 150 },
        { key: "global.total", title: "Rounds", minWidth: 150 },
        { key: "global.value", title: "Winrate", minWidth: 120 },
    ]

    const worst = reactive({
        item: null,
        tag: null
    })

    const searchItems = ref("")
    const searchTags = ref("")

    const allGameNames = ref([])
    const tableGameNames = ref([])
    const colorScale = computed(() => ([
        theme.current.value.colors.primary,
        theme.current.value.colors.secondary
    ]))

    const barData = ref([])

    const scores = ref([])
    const itemGroups = ref([])
    const tagGroups = ref([])
    const recentWindow = ref(20)


    function getBorderColor(win) {
        return win ?
            theme.current.value.colors.primary :
            theme.current.value.colors.error
    }

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

    function findWorst(data) {
        let w = null
        let percent = 2;
        let total = Number.MIN_SAFE_INTEGER;

        for (let i = 0; i < data.length; ++i) {
            const d = data[i]
            if (d.recent.percent < percent ||
                (d.recent.percent === percent && d.recent.total > total)
            ) {
                w = d
                percent = d.recent.percent
                total = d.recent.total
            }
        }
        return w
    }

    function loadScores() {
        tableGameNames.value = GAMELIST
            .filter(d => !d.multiplayer)
            .map(d => d.name)

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
                global: { percent: 0, value: 0, total: 0 },
                recent: { percent: 0, value: 0, total: 0 },
            }

            if (list.length > recentWindow.value) {
                const recent = list.slice(list.length - recentWindow.value)
                const wins = recent.reduce((acc, v) => acc + v.win, 0)
                obj.recent.percent = Math.round((wins / recent.length) * 100),
                obj.recent.value = wins
                obj.recent.total = recent.length
            }

            GAMELIST.forEach(d => {
                const l = list.filter(dd => dd.game_id === d.id)
                if (l.length > 0) {
                    const wins = l.reduce((acc, v) => acc + v.win, 0)
                    obj[d.name] = {
                        percent: Math.round((wins / l.length) * 100),
                        value: wins,
                        total: l.length
                    }
                    obj.global.value += wins
                    obj.global.total += l.length
                }
            })
            obj.global.percent = Math.round((obj.global.value / obj.global.total) * 100)

            if (list.length <= recentWindow.value) {
                obj.recent.value = obj.global.value
                obj.recent.percent = obj.global.percent
                obj.recent.total = obj.global.total
            }

            tmp.push(obj)
        })
        worst.item = findWorst(tmp)
        tmp.sort((a, b) => b.global.total - a.global.total)
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

            const relatedItems = list.filter(d => d.item_id !== null).map(d => ({
                id: d.item_id,
                win: d.win
            }))

            const obj = {
                id: it.id,
                name: it.name,
                parent: parent,
                items: relatedItems,
                showItems: false,
                global: { percent: 0, value: 0, total: 0 },
                recent: { percent: 0, value: 0, total: 0 },
            }

            if (list.length > recentWindow.value) {
                const recent = list.slice(list.length - recentWindow.value)
                const wins = recent.reduce((acc, v) => acc + v.win, 0)
                obj.recent.percent = Math.round((wins / recent.length) * 100),
                obj.recent.value = wins
                obj.recent.total = recent.length
            }

            GAMELIST.forEach(d => {
                const l = list.filter(dd => dd.game_id === d.id)
                if (l.length > 0) {
                    const wins = l.reduce((acc, v) => acc + v.win, 0)
                    obj[d.name] = {
                        percent: Math.round((wins / (l.length)) * 100),
                        value: wins,
                        total: l.length
                    }
                    obj.global.value += wins
                    obj.global.total += l.length
                }
            })

            obj.global.percent = Math.round((obj.global.value / obj.global.total) * 100)

            if (list.length <= recentWindow.value) {
                obj.recent.value = obj.global.value
                obj.recent.percent = obj.global.percent
                obj.recent.total = obj.global.total
            }

            tmp.push(obj)
        })
        worst.tag = findWorst(tmp)
        tmp.sort((a, b) => b.global.total - a.global.total)
        tagGroups.value = tmp
    }

    onMounted(loadScores)

    watch(() => Math.max(times.all, times.game_scores), loadScores)
    watch(() => app.activeUserId, loadScores)
    watch(() => app.showAllUsers, loadScores)
</script>