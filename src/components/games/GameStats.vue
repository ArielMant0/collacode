<template>
    <div ref="el" class="d-flex justify-center align-center flex-column">

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


        <div v-if="showAllUsers" style="width: 100%;" class="mt-4 text-caption d-flex align-center justify-center">
            <div>filter by user:</div>
            <div class="d-flex flex-wrap">
                <v-chip v-for="u in app.users"
                    class="text-caption ml-1"
                    :color="app.getUserColor(u.id)"
                    :variant="filterUser.has(u.id) ? 'flat' : 'outlined'"
                    @click="toggleUserFilter(u.id)"
                    density="compact">
                    {{ app.getUserName(u.id) }}
                </v-chip>
                <v-chip
                    class="text-caption ml-1"
                    :variant="filterUser.has(-1) ? 'flat' : 'outlined'"
                    color="default"
                    @click="toggleUserFilter(-1)"
                    density="compact">
                    {{ app.getUserName(-1) }}
                </v-chip>
            </div>
        </div>

        <div v-if="showAllUsers" style="width: 100%;" class="mt-2 text-caption d-flex align-center justify-center">
            <div>filter by game:</div>
            <div class="d-flex flex-wrap">
                <template v-for="g in GAMELIST">
                    <v-chip v-if="!g.multiplayer"
                        class="text-caption ml-1"
                        :prepend-icon="GAME_ICON[g.id]"
                        :variant="filterGame.has(g.id) ? 'flat' : 'outlined'"
                        @click="toggleGameFilter(g.id)"
                        density="compact">
                        {{ g.name }}
                    </v-chip>
                </template>

            </div>
        </div>

        <div v-if="scores.length > 0" style="width: 100%;">

            <h4>Overall Stats</h4>
            <v-data-table density="compact" :headers="headers" :items="scores" multi-sort>
                <template v-slot:item.user_id="{ value }">
                    <v-chip
                        :color="app.getUserColor(value)"
                        variant="flat"
                        density="comfortable"
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

                <template v-slot:item.avg_score="{ value, item }">
                    <div>
                        {{ value }}
                        <span v-if="item.game_id !== GAMES.SET">/ {{ games.getMaxScore(item.game_id, item.difficulty) }}</span>
                        <span class="ml-1" style="font-size: smaller;">({{ games.getScoreDesc(item.game_id) }})</span></div>
                </template>
            </v-data-table>
        </div>

        <div v-if="scores.length > 0" class="mt-4 d-flex align-center">
            <div class="mr-4">
                <div>Worst {{ app.itemNameCaptial }} <span class="text-caption">(in its last {{ recentWindow }} games)</span></div>
                <div v-if="worst.item !== null" class="d-flex align-start justify-center">

                    <ItemTeaser v-if="worst.item !== null" :id="worst.item.id" class="mr-1"/>

                    <v-sheet class="ml-4 text-subtitle-1">
                        <div>Recent Winrate: <b>{{ worst.item.recent.percent }}%</b></div>
                        <div>Recent Times Played: <b>{{ worst.item.recent.total }}</b></div>
                        <div>Recent Times Won: <b>{{ worst.item.recent.value }}</b></div>
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

            <div class="ml-4">
                <div>Best {{ app.itemNameCaptial }} <span class="text-caption">(in its last {{ recentWindow }} games)</span></div>
                <div v-if="best.item !== null" class="d-flex align-start justify-center">

                    <ItemTeaser v-if="best.item !== null" :id="best.item.id" class="mr-1"/>

                    <v-sheet class="ml-4 text-subtitle-1">
                        <div>Recent Winrate: <b>{{ best.item.recent.percent }}%</b></div>
                        <div>Recent Times Played: <b>{{ best.item.recent.total }}</b></div>
                        <div>Recent Times Won: <b>{{ best.item.recent.value }}</b></div>
                    </v-sheet>

                    <WinrateOverTime class="ml-4"
                        :id="best.item.id"
                        :width="180"
                        :height="80"
                        source="game_scores_items"
                        id-attr="item_id"/>

                </div>
                <v-card v-else width="160" height="80"  color="surface-light" class="d-flex align-center justify-center prevent-select">
                    <v-icon size="large">mdi-image-area</v-icon>
                </v-card>
            </div>
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
                        <td v-if="showAllUsers">
                            <div class="d-flex">
                                <v-chip v-for="uid in item.users" :key="'iu_'+uid"
                                    :color="app.getUserColor(uid)"
                                    variant="flat"
                                    density="comfortable"
                                    size="small"
                                    class="mr-1 mb-1"
                                    :title="app.getUserName(uid)">
                                    {{ app.getUserShort(uid) }}
                                </v-chip>
                            </div>
                        </td>
                        <td>{{ item.global.percent }}% ({{ item.global.value }} / {{ item.global.total }})</td>
                        <td><WinrateOverTime :id="item.id" source="game_scores_items" id-attr="item_id"/></td>
                        <td>{{ item.global.total }}</td>
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

        <div v-if="itemGroups.length > 0" class="mt-4 d-flex align-center">
            <div class="mr-4">
                <div>Worst Tag <span class="text-caption">(in its last {{ recentWindow }} games)</span></div>
                <div v-if="worst.tag !== null" class="d-flex align-start justify-center">

                    <v-card width="160" height="80"  color="surface-light"
                        class="d-flex align-center justify-center text-ww">
                        <span>{{ worst.tag.name }}</span>
                    </v-card>

                    <v-sheet class="ml-4 text-subtitle-1">
                        <div>Recent Winrate: <b>{{ worst.tag.recent.percent }}%</b></div>
                        <div>Recent Times Played: <b>{{ worst.tag.recent.total }}</b></div>
                        <div>Recent Times Won: <b>{{ worst.tag.recent.value }}</b></div>
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

            <div class="ml-4">
                <div>Best Tag <span class="text-caption">(in its last {{ recentWindow }} games)</span></div>
                <div v-if="best.tag !== null" class="d-flex align-start justify-center">

                    <v-card width="160" height="80"  color="surface-light"
                        class="d-flex align-center justify-center text-ww">
                        <span>{{ best.tag.name }}</span>
                    </v-card>

                    <v-sheet class="ml-4 text-subtitle-1">
                        <div>Recent Winrate: <b>{{ best.tag.recent.percent }}%</b></div>
                        <div>Recent Times Played: <b>{{ best.tag.recent.total }}</b></div>
                        <div>Recent Times Won: <b>{{ best.tag.recent.value }}</b></div>
                    </v-sheet>

                    <WinrateOverTime
                        class="ml-4"
                        :id="best.tag.id"
                        :width="180"
                        :height="80"
                        source="game_scores_tags"
                        id-attr="tag_id"/>
                </div>
                <span v-else>none</span>
            </div>
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
                        <td v-if="showAllUsers">
                            <div class="d-flex">
                                <v-chip v-for="uid in item.users" :key="'tu_'+uid"
                                    :color="app.getUserColor(uid)"
                                    variant="flat"
                                    density="comfortable"
                                    class="mr-1 mb-1"
                                    size="small"
                                    :title="app.getUserName(uid)">
                                    {{ app.getUserShort(uid) }}
                                </v-chip>
                            </div>
                        </td>
                        <td>
                            <div class="d-flex align-center">
                                <v-btn v-if="item.items.length > itemListLimit"
                                    :icon="item.showItems ? 'mdi-menu-down' : 'mdi-menu-right'"
                                    @click="item.showItems = !item.showItems"
                                    density="compact"
                                    rounded="sm"
                                    class="mr-1"
                                    variant="text"/>

                                <div v-if="item.showItems || item.items.length <= itemListLimit" class="d-flex flex-wrap mt-1">
                                    <span v-if="item.items.length <= itemListLimit" style="width: 32px;"></span>
                                    <ItemTeaser v-for="it in item.items"
                                        :key="'ti_'+it.id"
                                        :id="it.id"
                                        class="mr-1 mb-1"
                                        :style="{ padding: '2px', border: '2px solid '+getBorderColor(it.win) }"
                                        :width="80"
                                        :height="40"/>
                                </div>
                                <div v-else-if="!item.showItems && item.items.length > itemListLimit" class="d-flex align-center">
                                    <div class="d-flex flex-wrap mt-1">
                                        <ItemTeaser v-for="it in item.items.slice(0, itemListLimit)"
                                            :key="'ti_'+it.id"
                                            :id="it.id"
                                            class="mr-1 mb-1"
                                            :style="{ padding: '2px', border: '2px solid '+getBorderColor(it.win) }"
                                            :width="80"
                                            :height="40"/>
                                    </div>
                                    <span class="ml-1 text-caption">+ {{ item.items.length-itemListLimit }} more</span>
                                </div>
                            </div>

                        </td>
                        <td>{{ item.global.percent }}% ({{ item.global.value }} / {{ item.global.total }})</td>
                        <td><WinrateOverTime :id="item.id" source="game_scores_tags" id-attr="tag_id"/></td>
                        <td>{{ item.global.total }}</td>
                    </tr>
                </template>
            </v-data-table>
        </div>

    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { GAME_ICON, GAMELIST, GAMES, useGames } from '@/store/games';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { sortObjMultiple } from '@/use/sorting';
    import { computed, onMounted, reactive } from 'vue';
    import StackedBarChart from '../vis/StackedBarChart.vue';
    import { useTheme } from 'vuetify/lib/framework.mjs';
    import { group, pointer } from 'd3';
    import { capitalize } from '@/use/utility';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import DifficultyIcon from './DifficultyIcon.vue';
    import WinrateOverTime from './WinrateOverTime.vue';
    import { storeToRefs } from 'pinia';
    import { useElementSize } from '@vueuse/core';

    const app = useApp()
    const games = useGames()
    const times = useTimes()
    const theme = useTheme()
    const settings = useSettings()

    const { showAllUsers, activeUserId } = storeToRefs(app)

    const el = ref(null)
    const size = useElementSize(el)
    const itemListLimit = computed(() => Math.max(2, Math.min(10, Math.floor((size.width.value * 0.25) / 90))))

    const filterUser = reactive(new Set())
    const filterGame = reactive(new Set())

    const headers = computed(() => {
        const list = [
            { key: "name", title: "Game" },
            { key: "difficulty", title: "Difficulty" },
            { key: "played", title: "#Played" },
            { key: "wins", title: "#Wins" },
            { key: "avg_score", title: "Avg. Score", value: d => d.avg_score.toFixed(2) },
            { key: "streak_current", title: "Current Streak" },
            { key: "streak_highest", title: "Highest Streak" },
        ]
        return showAllUsers.value ?
            list.slice(0, 2).concat([{ key: "user_id", title: "User" }]).concat(list.slice(2)) :
            list
    })
    const itemHeaders = computed(() => {
        const glist = tableGameNames.value.map(d => {
            const n = capitalize(d)
            return {
                key: d+".percent",
                title: n+" %",
                value: dd => dd[d] ? dd[d].percent : 0
            }
        })
        const list = [
            { key: "name", title: "Name", maxWidth: 250 },
            { key: "teaser", title: "Teaser", sortable: false },
            { key: "global.percent", title: "Overall %", minWidth: 150 },
            { key: "global.value", title: "Winrate", minWidth: 120 },
            { key: "global.total", title: "Rounds", minWidth: 150 },
        ]

        return !showAllUsers.value ?
            list.concat(glist) :
            list.slice(0, 2)
                .concat([{ key: "users", title: "Users" }])
                .concat(list.slice(2))
                .concat(glist)

    })
    const tagHeaders = computed(() => {
        const list = [
            { key: "name", title: "Name", maxWidth: 250 },
            { key: "parent", title: "Parent" },
            { key: "items", title: app.itemNameCaptial+"s", value: dd => dd.items.map(i => i.name), minWidth: 300 },
            { key: "global.percent", title: "Overall %", minWidth: 150 },
            { key: "global.value", title: "Winrate", minWidth: 120 },
            { key: "global.total", title: "Rounds", minWidth: 150 },
        ]
        return !showAllUsers.value ?
            list :
            list.slice(0, 2)
                .concat([{ key: "users", title: "Users" }])
                .concat(list.slice(2))
    })

    const worst = reactive({
        item: null,
        tag: null
    })
    const best = reactive({
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
    const recentWindow = ref(25)

    const scoreTime = ref(0)

    function getBorderColor(win) {
        return win ?
            theme.current.value.colors.primary :
            theme.current.value.colors.error
    }

    function toggleUserFilter(uid) {
        if (filterUser.has(uid)) {
            filterUser.delete(uid)
        } else {
            filterUser.add(uid)
        }
        loadScores()
    }
     function toggleGameFilter(gid) {
        if (filterGame.has(gid)) {
            filterGame.delete(gid)
        } else {
            filterGame.add(gid)
        }
        loadScores()
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

    function findBest(data) {
        let w = null
        let percent = 0;
        let total = 0;

        for (let i = 0; i < data.length; ++i) {
            const d = data[i]
            if (d.recent.percent > percent ||
                (d.recent.percent === percent && d.recent.total > total)
            ) {
                w = d
                percent = d.recent.percent
                total = d.recent.total
            }
        }
        return w
    }
    function findWorst(data) {
        let w = null
        let percent = 2;
        let total = 0;

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

    function matchesFilter(d) {
        return (filterUser.size === 0 || filterUser.has(d.user_id)) &&
            (filterGame.size === 0 || filterGame.has(d.game_id))
    }

    function loadScores() {
        tableGameNames.value = GAMELIST
            .filter(d => !d.multiplayer)
            .map(d => d.name)

        allGameNames.value = GAMELIST.map(d => d.name)

        const tmpScores = showAllUsers.value ?
            DM.getDataBy("game_scores", matchesFilter) :
            DM.getDataBy("game_scores", d => d.user_id === activeUserId.value && matchesFilter(d))

        tmpScores.forEach(d => {
            d.name = games.gameName(d.game_id)
            d.losses = d.played - d.wins;
        })
        tmpScores.sort(sortObjMultiple([
            { name: "name", type: "string" },
            { name: "difficulty", type: "number" },
        ]))

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

        const tmpItems = showAllUsers.value ?
            DM.getDataBy("game_scores_items", d => matchesFilter(d, true)) :
            DM.getDataBy("game_scores_items", d => d.user_id === activeUserId.value && matchesFilter(d))

        g = group(tmpItems, d => d.item_id)
        tmp = []
        g.forEach((lf, item_id) => {
            const it = DM.getDataItem("items", item_id)

            const users = Array.from(new Set(lf.map(d => d.user_id)))
            users.sort()

            const obj = {
                id: it.id,
                name: it.name,
                teaser: it.teaser,
                users: users,
                global: { percent: 0, value: 0, total: 0 },
                recent: { percent: 0, value: 0, total: 0 },
            }

            if (lf.length > recentWindow.value) {
                const recent = lf.slice(lf.length - recentWindow.value)
                const wins = recent.reduce((acc, v) => acc + v.win, 0)
                obj.recent.percent = Math.round((wins / recent.length) * 100),
                obj.recent.value = wins
                obj.recent.total = recent.length
            }

            GAMELIST.forEach(d => {
                const l = lf.filter(dd => dd.game_id === d.id)
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

            if (lf.length <= recentWindow.value) {
                obj.recent.value = obj.global.value
                obj.recent.percent = obj.global.percent
                obj.recent.total = obj.global.total
            }

            tmp.push(obj)
        })
        worst.item = findWorst(tmp)
        best.item = findBest(tmp)
        tmp.sort((a, b) => b.global.total - a.global.total)
        itemGroups.value = tmp

        const tmpTags = showAllUsers.value ?
            DM.getDataBy("game_scores_tags", matchesFilter) :
            DM.getDataBy("game_scores_tags", d => d.user_id === activeUserId.value && matchesFilter(d))

        g = group(tmpTags, d => d.tag_id)
        tmp = []
        g.forEach((lf, tag_id) => {
            const it = DM.getDataItem("tags", tag_id)
            const parent = it.parent !== null && it.parent > 0 ?
                DM.getDataItem("tags_name", it.parent) :
                ""

            const relatedItems = lf.filter(d => d.item_id !== null).map(d => ({
                id: d.item_id,
                win: d.win,
                name: DM.getDataItem("items_name", d.item_id),
            }))

            const users = Array.from(new Set(lf.map(d => d.user_id)))
            users.sort()

            const obj = {
                id: it.id,
                name: it.name,
                parent: parent,
                items: relatedItems,
                showItems: false,
                users: users,
                global: { percent: 0, value: 0, total: 0 },
                recent: { percent: 0, value: 0, total: 0 },
            }

            if (lf.length > recentWindow.value) {
                const recent = lf.slice(lf.length - recentWindow.value)
                const wins = recent.reduce((acc, v) => acc + v.win, 0)
                obj.recent.percent = Math.round((wins / recent.length) * 100),
                obj.recent.value = wins
                obj.recent.total = recent.length
            }

            GAMELIST.forEach(d => {
                const l = lf.filter(dd => dd.game_id === d.id)
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

            if (lf.length <= recentWindow.value) {
                obj.recent.value = obj.global.value
                obj.recent.percent = obj.global.percent
                obj.recent.total = obj.global.total
            }

            tmp.push(obj)
        })
        worst.tag = findWorst(tmp)
        best.tag = findBest(tmp)
        tmp.sort((a, b) => b.global.total - a.global.total)
        tagGroups.value = tmp

        scoreTime.value = Date.now()
    }

    onMounted(loadScores)

    watch(() => Math.max(times.all, times.game_scores), loadScores)
    watch(activeUserId, loadScores)
    watch(showAllUsers, loadScores)
</script>