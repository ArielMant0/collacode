<template>
    <div style="width: 100%;">

        <div v-if="state === STATES.START" class="d-flex flex-column justify-center align-center" style="height: 80vh;">
            <div style="width: 50%">
                <v-text-field v-model="myName"
                    label="Your name"
                    density="compact"
                    style="width: 100%"
                    hide-details
                    hide-spin-buttons
                    variant="outlined"/>
            </div>
            <div class="d-flex justify-space-between align-center mt-1" style="width: 50%;">
                <v-btn size="x-large" style="width: 49%;" :disabled="!myName" @click="hostGame">Host Game</v-btn>
                <v-btn size="x-large" style="width: 49%;" :disabled="!myName" @click="joinGame">Join Game</v-btn>
            </div>

        </div>

        <div v-else-if="state === STATES.CONNECT">
            <div class="d-flex justify-center align-center"  style="height: 80vh;">
                <v-text-field v-model="mp.gameId"
                    label="Connect to a game"
                    placeholder="Game Id"
                    density="compact"
                    style="max-width: 600px;"
                    autofocus
                    hide-details
                    hide-spin-buttons
                    variant="outlined"/>
                <v-btn variant="tonal"
                    :disabled="!mp.gameId"
                    class="ml-1"
                    @click="connectToPeer"
                    :color="mp.gameId ? 'primary' : 'default'">
                    connect
                </v-btn>
            </div>
        </div>
        <div v-else-if="state === STATES.LOBBY" style="width: 100%; height: 80vh;" class="d-flex flex-column align-center mt-8">

            <div class="d-flex justify-center align-center mb-4">
                <v-text-field :model-value="mp.gameId"
                    label="Game Code"
                    readonly
                    density="compact"
                    style="min-width: 600px;"
                    hide-details
                    hide-spin-buttons
                    variant="outlined"/>
                <v-btn
                    icon="mdi-content-copy"
                    class="ml-1"
                    :disabled="!mp.gameId"
                    density="compact"
                    variant="text"
                    @click="copyToClipboard(mp.gameId)"/>
            </div>

            <div style="width: 60%;">

                <div style="position: relative;">
                    <div style="position:absolute; top:0;right:0;">{{ numPlayers }} / {{ maxPlayers }}</div>
                </div>

                <table :class="[settings.lightMode ? 'light' : 'dark']">
                    <tbody>
                        <tr>
                            <td><v-icon size="small" :color="getPlayerColor(lobby.id)">mdi-circle</v-icon></td>
                            <td>{{ myName }}</td>
                        </tr>

                        <tr v-for="i in d3.range(0, maxPlayers-1)">
                            <td><v-icon size="small" :color="i < playerList.length ? getPlayerColor(playerList[i]) : 'default'">mdi-circle</v-icon></td>
                            <td>{{ i < playerList.length ? mp.names.get(playerList[i]) : '' }}</td>
                        </tr>
                    </tbody>
                </table>

                <v-btn v-if="mp.hosting" class="mt-8" color="primary" block :disabled="numPlayers < 2" @click="startGame">start game</v-btn>
            </div>
        </div>

        <div v-else-if="state === STATES.LOADING" class="d-flex flex-column align-center justify-center">
            <v-sheet
                style="font-size: 40px; font-weight: bold; width: 200px; text-align: center;"
                class="mt-8 pa-4"
                border
                rounded="sm">
                {{ countdown }}
            </v-sheet>
            <div class="d-flex align-center justify-center" style="height: 60vh;">
                <div class="game-loader"></div>
            </div>
        </div>

        <div v-if="state === STATES.INGAME" style="width: 100%;" class="d-flex flex-column align-center mt-4">

            <div class="d-flex justify-space-between mt-4 mb-4 text-caption">
                <v-sheet class="pt-2 pb-2 pr-4 pl-4" rounded="sm" :color="getPlayerColor(lobby.id)" style="font-weight: bold;">
                    {{ myName }} (you): {{ lobby ? gameData.points.get(lobby.id) : 0 }}
                </v-sheet>
                <v-sheet v-for="p in mp.players" :key="'player_'+p" class="pt-2 pb-2 pr-4 pl-4 ml-1" rounded="sm" :color="getPlayerColor(p)">
                    {{ mp.names.get(p) }}: {{ gameData.points.get(p) }}
                </v-sheet>
            </div>

            <div>Tag: {{ gameData.tag ? gameData.tag.name : '?' }}</div>

            <div style="width: 90%; height: 80vh; position: relative;">

                <div ref="el" style="height: 80vh;" @pointermove="onMove" class="d-flex flex-wrap align-start align-content-start">
                    <v-sheet v-for="item in items" :key="item.id"
                        class="mr-1 mb-1 pa-1 cursor-pointer secondary-on-hover"
                        rounded="sm"
                        @click="takeItem(item)"
                        :style="{
                            cursor: gameData.taken.has(item.id) ? 'default' : 'pointer',
                            backgroundColor: isTakenByMe(item.id) ? '#078766 !important' : null
                        }">
                        <div class="text-dots text-caption" :style="{ maxWidth: imageWidth+'px', opacity: gameData.taken.has(item.id) ? 0.1 : 1 }">{{ item.name }}</div>
                        <div style="position: relative;">
                            <v-img
                                cover
                                :style="{ opacity: gameData.taken.has(item.id) ? 0.1 : 1 }"
                                :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                                :lazy-src="imgUrlS"
                                :width="imageWidth"
                                :height="Math.floor(imageWidth*0.5)"/>

                            <div v-if="gameData.taken.has(item.id)"
                                style="position: absolute; top:0; left:0; width: 100%;"
                                :style="{ height: Math.floor(imageWidth*0.5)+'px'}"
                                class="d-flex align-center justify-center">
                                <v-icon
                                    size="60"
                                    :icon="gameData.correct.has(item.id) ? 'mdi-check-bold' : 'mdi-close-circle-outline'"
                                    :color="gameData.correct.has(item.id) ? 'primary' : 'error'"/>
                            </div>
                        </div>
                    </v-sheet>
                </div>

                <svg ref="overlay" :width="elSize.width.value" :height="elSize.height.value" style="pointer-events: none; position: absolute; top: 0; left: 0;"></svg>
            </div>
        </div>

        <div v-else-if="state === STATES.END" class="d-flex flex-column align-center mt-8" style="min-height: 80vh;">

            <div v-if="winner === lobby.id" class="d-flex align-center justify-center">
                <v-icon
                    size="60"
                    class="mr-4"
                    icon="mdi-check-bold"
                    color="primary"/>
                <span>You won!</span>
            </div>
            <div v-else-if="winner !== null" class="d-flex align-center justify-center">
                <v-icon
                    size="60"
                    class="mr-4"
                    icon="mdi-close-circle-outline"
                    color="error"/>
                <span>{{ winner }}</span>
            </div>
            <div v-else class="d-flex align-center justify-center">
                <v-icon
                    size="60"
                    class="mr-4"
                    icon="mdi-equal"
                    color="default"/>
                <span>It's a draw</span>
            </div>

            <div class="mt-8">Tag: {{ gameData.tag ? gameData.tag.name : '?' }}</div>

            <table :class="[settings.lightMode ? 'light' : 'dark']">
                <thead style="text-align: left;">
                    <tr>
                        <th>Player</th>
                        <th>Points</th>
                        <th>{{ capitalize(app.itemName+'s') }}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{{ myName }} (you)</td>
                        <td>{{ gameData.points.get(lobby.id) }}</td>
                        <td class="d-flex flex-wrap">
                            <v-sheet v-for="item in myItems" :key="'me_'+item.id" class="pa-1 mr-1 mb-1" rounded="sm" :color="gameData.correct.has(item.id) ? 'primary' : 'error'">
                                <div class="text-dots text-caption" style="max-width: 100px;">{{ item.name }}</div>
                                <v-img
                                    cover
                                    :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                                    :lazy-src="imgUrlS"
                                    :width="100"
                                    :height="50"/>
                            </v-sheet>
                        </td>
                    </tr>

                    <tr v-for="(p, idx) in playerList" :key="'res_'+p">
                        <td>{{ mp.names.get(p) }}</td>
                        <td>{{ gameData.points.get(p) }}</td>
                        <td class="d-flex flex-wrap">
                            <v-sheet v-for="item in otherItems.get(p)" :key="idx+'_it_'+item.id" class="pa-1 mr-1 mb-1" rounded="sm" :color="gameData.correct.has(item.id) ? 'primary' : 'error'">
                                <div class="text-dots text-caption" style="max-width: 100px;">{{ item.name }}</div>
                                <v-img
                                    cover
                                    :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                                    :lazy-src="imgUrlS"
                                    :width="100"
                                    :height="50"/>
                            </v-sheet>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div class="d-flex align-center justify-center mt-8" style="margin-top: 200px;">
                <v-btn class="mr-1" size="x-large" color="error" @click="close">close game</v-btn>
                <v-btn class="ml-1 mr-1" size="x-large" color="warning" @click="leaveLobby">exit lobby</v-btn>
                <v-btn v-if="mp.hosting" class="ml-1" size="x-large" color="primary" @click="startGame">play again</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { SOUND, useGames } from '@/store/games'
    import { ref, onMounted, reactive, computed } from 'vue'
    import { useElementSize } from '@vueuse/core';
    import DM from '@/use/data-manager';
    import Chance from 'chance';
    import { useApp } from '@/store/app';
    import Multiplayer from '@/use/multiplayer';
    import { POSITION, useToast } from 'vue-toastification';
    import { capitalize } from '@/use/utility';
    import { useSettings } from '@/store/settings';

    import imgUrlS from '@/assets/__placeholder__s.png'

    const STATES = Object.freeze({
        START: 0,
        CONNECT: 1,
        LOBBY: 2,
        LOADING: 3,
        INGAME: 4,
        END: 5,
    })

    const props = defineProps({
        difficulty: {
            type: Number,
            required: true
        },
        maxPlayers: {
            type: Number,
            default: 5
        },
    })

    const emit = defineEmits(["end", "close"])

    // stores
    const games = useGames()
    const app = useApp()
    const toast = useToast()
    const settings = useSettings()

    // elements
    const el = ref(null)
    const overlay = ref(null)

    const elSize = useElementSize(el)
    const imageWidth = computed(() => Math.max(80, Math.floor(elSize.width.value / 4) - 15))

    // difficulty settings
    const numItems = computed(() => {
        return Math.max(9, numPlayers.value * 3)
    })

    // multiplayer related stuff
    const positions = reactive(new Map())
    const countdown = ref(-1)

    let lobby, countdownInt;
    const myName = ref(app.activeUser.name)

    const mp = reactive({
        hosting: false,
        gameId: null,
        players: new Set(),
        names: new Map()
    })
    const playerList = computed(() => {
        const list = Array.from(mp.players.values())
        list.sort()
        return list
    })
    const playerColors = computed(() => {
        const list = [lobby.id].concat(playerList.value)
        list.sort()
        return d3.scaleOrdinal(d3.schemeCategory10)
            .domain(list)
    })

    // game related stuff
    const state = ref(STATES.START)
    const items = ref([])
    const gameData = reactive({
        tag: null,
        taken: new Map(),
        points: new Map(),
        correct: new Set()
    })
    const numPlayers = computed(() => mp.players.size + 1)
    const numMatches = computed(() => Math.floor(numItems.value * 0.5))
    const numFound = computed(() => {
        let num = 0;
        gameData.taken.forEach((_, id) => {
            if (gameData.correct.has(id)) {
                num++
            }
        })
        return num
    })

    const winner = computed(() => {
        let wid;
        let max = Number.MIN_SAFE_INTEGER;
        const counts = new Map()
        gameData.points.forEach((value, id) => {
            if (value > max) {
                wid = id;
                max = value
            } else if (value === max) {
                counts.set(value, (counts.get(value) || 0)+1)
            }
        })
        return counts.has(max) ? null : wid
    })

    const myItems = computed(() => {
        return items.value.filter(d => {
            const t = gameData.taken.get(d.id)
            return t && t.id === lobby.id
        })
    })
    const otherItems = computed(() => {
        const map = new Map()
        mp.players.forEach(p => {
            map.set(p, items.value.filter(d => {
                const t = gameData.taken.get(d.id)
                return t && t.id === p
            }))
        })
        return map
    })


    function copyToClipboard(str) {
        navigator.clipboard.writeText(str)
    }
    function isTakenByMe(id) {
        return gameData.taken.get(id) === lobby.id
    }
    function takeItem(item) {
        if (!gameData.taken.has(item.id)) {
            games.play(SOUND.PLOP)
            const data = { item: item.id, user: lobby.id, time: Date.now() }
            lobby.setVote("take", lobby.id, data)
            lobby.send("take", data)
        }
    }
    function confirmTaken(item, user, time) {
        gameData.taken.set(item, { id: user, time: time })
        if (numFound.value === numMatches.value) {
            stopGame()
        }
    }
    function getPlayerColor(id) {
        return playerColors.value(id)
    }
    function playerNameExists(name) {
        return myName.value === name || mp.names.has(name)
    }

    function startGame() {
        state.value = STATES.LOADING
        // clear previous data
        clear()

        if (mp.hosting) {
            const minCount = numMatches.value
            const tags = DM.getDataBy("tags", d => d.is_leaf === 1 && DM.getDataItem("tags_counts", d.id) > minCount)

            const chance = new Chance()
            gameData.tag = chance.pickone(tags)

            const tid = gameData.tag.id
            const allItems = DM.getData("items", false)
            const withTag = chance.pickset(
                allItems.filter(d => d.allTags.find(t => t.id === tid)),
                minCount
            )
            const withoutTag = chance.pickset(
                allItems.filter(d => !d.allTags.find(t => t.id === tid)),
                numItems.value-minCount
            )

            items.value = chance.shuffle(withTag.concat(withoutTag))
            gameData.correct = new Set(withTag.map(d => d.id))

            lobby.setVote("start_game")
            lobby.send("dataset", {
                tag: tid,
                items: items.value.map(d => d.id)
            })
        }
    }
    function stopGame() {
        state.value = STATES.END
        if (winner.value === lobby.id) {
            games.playSingle(SOUND.WIN)
        } else if (winner.value !== null) {
            games.playSingle(SOUND.FAIL)
        } else {
            games.playSingle(SOUND.MEH)
        }
        emit("end", winner.value === lobby.id)
    }
    function leaveLobby() {
        state.value = STATES.START
        reset()
    }

    function close() {
        reset()
        emit("close")
    }

    function clear() {
        items.value = []
        gameData.tag = null
        gameData.taken.clear()
        gameData.correct.clear()
        gameData.points.clear()
    }
    function reset() {
        clear()
        positions.clear()
        mp.players.clear();
        mp.names.clear();
        if (lobby) {
            lobby.clear()
        }
    }

    function drawCursor() {

        const data = []
        mp.players.forEach(id => {
            const pos = positions.get(id)
            if (pos) {
                data.push({
                    id: id,
                    x: pos[0],
                    y: pos[1],
                })
            }
        })

        const svg = d3.select(overlay.value)

        svg.selectAll(".bg")
            .data(data, d => d.id)
            .join("circle")
            .classed("bg", true)
            .attr("cx", d => d.x * elSize.width.value)
            .attr("cy", d => d.y * elSize.height.value)
            .attr("r", 15)
            .attr("fill", "white")
            .attr("fill-opacity", 0.5)
            .style("filter", "blur(5px)")
            .attr("stroke", "none")

        svg.selectAll(".cursor")
            .data(data, d => d.id)
            .join("circle")
            .classed("cursor", true)
            .attr("cx", d => d.x * elSize.width.value)
            .attr("cy", d => d.y * elSize.height.value)
            .attr("r", 6)
            .attr("fill", d => getPlayerColor(d.id))
            .attr("stroke", "black")

    }

    function onMove(event) {
        if (lobby) {
            const [mx, my] = d3.pointer(event, el.value)
            lobby.send("cursor", {
                id: lobby.id,
                data: [mx/elSize.width.value, my/elSize.height.value]
            })
        }
    }

    function hostGame() {
        mp.hosting = true;
        mp.gameId = lobby.id
        state.value = STATES.LOBBY
        games.playSingle(SOUND.TRANSITION)

    }
    function joinGame() {
        mp.hosting = false;
        mp.gameId = null
        state.value = STATES.CONNECT
    }

    function connectToPeer() {
        if (lobby && mp.gameId) {
            state.value = STATES.LOBBY
            lobby.connect(mp.gameId)
            games.playSingle(SOUND.TRANSITION)
        }
    }

    function initMultiplayer() {

        reset()

        // create the "lobby"
        lobby = new Multiplayer(() => {
            return {
                id: lobby.id,
                name: myName.value,
                dataset: app.ds,
                code: app.activeCode,
                difficulty: props.difficulty
            }
        })

        // handle handshake
        lobby.onReceive("handshake", data => {
            if (data.dataset === app.ds && data.code === app.activeCode) {
                mp.players.add(data.id)
                if (!playerNameExists(data.name)) {
                    mp.names.set(data.id, data.name)
                } else {
                    let nr = 1;
                    let name = `${data.name} (${nr})`
                    do {
                        nr++;
                        name = `${data.name} (${nr})`
                    } while (playerNameExists(name))
                    mp.names.set(data.id, name)
                }
                positions.set(data.id, [0, 0])
            } else {
                toast.error("data mismatch")
            }
        })
        lobby.onReceive("start_game", (_d, _t, conn) => {
            if (state.value === STATES.LOBBY || state.value === STATES.END) {
                lobby.setVote("start_game", conn.peer)
            }
        })
        lobby.onReceive("dataset", (data, _t, conn) => {
            state.value = STATES.LOADING
            // get tag
            gameData.tag = DM.getDataItem("tags", data.tag)
            // get matching items
            const set = new Set(data.items)
            const tmp = DM.getDataBy("items", d => set.has(d.id))
            tmp.sort((a, b) => data.items.indexOf(a.id)-data.items.indexOf(b.id))
            items.value = tmp;
            // save correct games
            gameData.correct.clear()
            tmp.forEach(d => {
                if (d.allTags.find(t => t.id === data.tag)) {
                    gameData.correct.add(d.id)
                }
            })
            lobby.setVote("start_game")
            lobby.setVote("start_game", conn.peer)
            // lobby.send("start_game", lobby.id)
            lobby.send("dataset_confirm", {
                tag: gameData.tag.id,
                items: tmp.map(d => d.id)
            })
        })
        lobby.onReceive("dataset_confirm", (data, _t, conn) => {
            if (mp.hosting) {
                if (data.tag === gameData.tag.id) {
                    if (items.value.every((d,i) => data.items[i] === d.id)) {
                        lobby.setVote("start_game", conn.peer)
                    } else {
                        console.error("items mismatch", data.items, items.value)
                        toast.error("data mismatch", { position: POSITION.TOP_CENTER, timeout: 2000 })
                    }
                } else {
                    console.error("tag mismatch", data.tag, gameData.tag.id)
                    toast.error("data mismatch", { position: POSITION.TOP_CENTER, timeout: 2000 })
                }
            }
        })
        lobby.onReceive("cursor", data => {
            if (state.value === STATES.INGAME) {
                positions.set(data.id, data.data)
                drawCursor()
            }
        })
        lobby.onReceive("take", (data, _time, conn) => {
            if (state.value === STATES.INGAME) {
                const existing = gameData.taken.get(data.item)
                if (!existing || existing.time > data.time) {
                    lobby.setVote("take", lobby.id, data)
                    lobby.setVote("take", conn.peer, data)
                    lobby.send("take_confirm", data)
                }
            }
        })
        lobby.onReceive("take_confirm", (data, _time, conn) => {
            if (state.value === STATES.INGAME) {
                lobby.setVote("take", conn.peer, data)
            }
        })

        lobby.onVote("start_game", () => {
            gameData.taken.clear()
            gameData.points.clear()
            gameData.points.set(lobby.id, 0)
            mp.players.forEach(id => gameData.points.set(id, 0))

            countdown.value = 3
            games.playSingle(SOUND.TICK)
            countdownInt = setInterval(() => {
                countdown.value--
                if (countdown.value === 0) {
                    games.playSingle(SOUND.START)
                    clearInterval(countdownInt)
                    countdownInt = null
                    state.value = STATES.INGAME
                } else {
                    games.playSingle(SOUND.TICK)
                }
            }, 900)
        })
        lobby.onVote("take", data => {
            confirmTaken(data.item, data.user, data.time)
            const diff = gameData.correct.has(data.item) ? 1 : -1
            gameData.points.set(data.user, gameData.points.get(data.user) + diff)
            if (data.user === lobby.id) {
                games.play(diff > 0 ? SOUND.WIN_MINI : SOUND.FAIL_MINI)
            } else {
                games.play(SOUND.PLOP)
            }
        })
        lobby.onVote("end", stopGame)

        state.value = STATES.START
    }

    onMounted(initMultiplayer)

</script>

<style scoped>
table { border-collapse: collapse; }
table td, table th {
    border: 1em;
    padding: 8px;
}

table.light td, table.light th {
    border-color: black;
}
table.dark td, table.light th  {
    border-color: white;
}
</style>