<template>
    <div style="width: 100%;">

        <div v-if="state === STATES.START" class="d-flex flex-column justify-center align-center" style="height: 80vh;">

            <div style="width: 100%; max-width: 800px;">
                <v-text-field v-model="myName"
                    label="Your name"
                    density="compact"
                    style="width: 100%"
                    hide-details
                    hide-spin-buttons
                    @update:model-value="n => setName(n)"
                    variant="outlined"/>
                <div class="d-flex justify-space-between align-center mt-2" style="width: 100%;">
                    <v-btn size="large" variant="tonal" style="width: 49%;" :disabled="!myName" @click="hostGame">Host Game</v-btn>
                    <v-btn size="large" variant="tonal" style="width: 49%;" :disabled="!myName" @click="joinGame">Join Game</v-btn>
                </div>
            </div>

        </div>

        <div v-else-if="state === STATES.CONNECT" class="d-flex flex-column justify-center align-center" style="height: 80vh;">

            <div style="width: max-content;">

                <div style="width: 100%;">
                    <v-text-field v-model="myName"
                        label="Your name"
                        density="compact"
                        class="mb-8"
                        hide-details
                        hide-spin-buttons
                        @update:model-value="n => setName(n)"
                        variant="outlined"/>
                </div>

                <table :class="[settings.lightMode ? 'light' : 'dark', 'lobbies']" style="display:block; min-height: 300px;">
                    <thead>
                        <tr>
                            <th>Host Name</th>
                            <th>Difficulty</th>
                            <th>Players</th>
                            <th>Max. Players</th>
                            <th>Last Update</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="room in mp.rooms" :key="room.id">
                            <td>{{ room.name }}</td>
                            <td><DifficultyIcon :value="room.data.difficulty"/></td>
                            <td>{{ room.players.length }}</td>
                            <td>{{ maxPlayers }}</td>
                            <td>{{ DateTime.fromMillis(room.last_update).toFormat("dd.MM.yyyy HH:mm") }}</td>
                            <td>
                                <v-btn
                                    prepend-icon="mdi-location-enter"
                                    class="ml-4"
                                    density="compact"
                                    variant="tonal"
                                    color="primary"
                                    @click="joinLobby(room.id)">
                                    join
                                </v-btn>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <div style="width: 100%;">
                    <v-btn class="mt-2" size="large" variant="tonal" block @click="leaveLobby">Go Back</v-btn>
                </div>

            </div>
        </div>
        <div v-else-if="state === STATES.LOBBY" style="width: 100%; height: 80vh;" class="d-flex flex-column align-center mt-8">

            <div v-if="waiting" class="d-flex justify-center align-center mb-8 pa-4">
                <v-progress-circular indeterminate color="primary"></v-progress-circular>
                <div class="ml-4">waiting for round to end</div>
            </div>

            <div class="d-flex justify-center align-center mb-4">
                <v-text-field :model-value="mp.gameId"
                    label="Game Code"
                    readonly
                    density="compact"
                    style="min-width: 400px"
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

            <div style="width: max-content; min-width: 400px">

                <div style="position: relative;">
                    <div style="position:absolute; top:0;right:0;">{{ numPlayers }} / {{ maxPlayers }}</div>
                </div>

                <table :class="[settings.lightMode ? 'light' : 'dark']">
                    <tbody>
                        <tr>
                            <td><v-icon size="small" :color="getPlayerColor(lobby.id)">mdi-circle</v-icon></td>
                            <td>{{ myNameDisplay }}</td>
                        </tr>

                        <tr v-for="i in d3.range(0, maxPlayers-1)">
                            <td><v-icon size="small" :color="i < playerList.length ? getPlayerColor(playerList[i]) : 'default'">mdi-circle</v-icon></td>
                            <td>{{ i < playerList.length ? getPlayerName(playerList[i]) : '' }}</td>
                        </tr>
                    </tbody>
                </table>

                <div v-if="mp.hosting" class="d-flex justify-space-between">
                    <v-btn class="mt-8" color="warning" style="width: 49%;" @click="leaveLobby">exit lobby</v-btn>
                    <v-btn class="mt-8" color="primary" style="width: 49%;" :disabled="numPlayers < 2" @click="startGame">start game</v-btn>
                </div>
                <div v-else>
                    <v-btn class="mt-8" color="warning" block @click="leaveLobby(STATES.CONNECT)">exit lobby</v-btn>
                </div>
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

            <div style="position: relative; width: 100%;">
                <div style="position: absolute; left: 0; top: 0;"  class="text-caption">
                    <div>
                        <v-icon :color="getPlayerColor(lobby.id)" icon="mdi-circle"/>
                        <span class="ml-1">{{ myNameDisplay }}</span>
                    </div>
                    <div v-for="([p, n]) in mp.players" :key="'i_'+p">
                        <v-icon :color="getPlayerColor(p)" icon="mdi-circle"/>
                        <span class="ml-1">{{ n }}</span>
                    </div>
                    <div v-for="p in mp.waitingList" :key="'wi_'+p.id">
                        <v-icon color="surface-light" icon="mdi-circle-slice-8"/>
                        <span class="ml-1">{{ p.name }}</span>
                    </div>
                </div>
            </div>

            <div class="d-flex justify-space-between mt-4 mb-4 text-caption">
                <v-sheet class="pt-2 pb-2 pr-4 pl-4" rounded="sm" :color="getPlayerColor(lobby.id)" style="font-weight: bold;">
                    {{ myNameDisplay }} (you): {{ lobby ? gameData.points.get(lobby.id) : 0 }}
                </v-sheet>
                <v-sheet v-for="([p, name]) in mp.players" :key="'player_'+p" class="pt-2 pb-2 pr-4 pl-4 ml-1" rounded="sm" :color="getPlayerColor(p)">
                    {{ name }}: {{ gameData.points.get(p) }}
                </v-sheet>
            </div>

            <h4 class="mt-2 mb-4">{{ gameData.tag ? gameData.tag.name : '?' }}</h4>

            <div style="width: 90%; height: 80vh; position: relative;">

                <div ref="el" class="item-container" @pointerleave="onCursorLeave">
                    <v-sheet v-for="item in items" :key="item.id"
                        class="mr-1 mb-1 pa-1 cursor-pointer"
                        @pointerenter="onCursorEnter(item.id)"
                        @pointerleave="onCursorLeave"
                        rounded="sm"
                        @click="takeItem(item)"
                        :style="{
                            width: 'max-content',
                            height: 'max-content',
                            cursor: gameData.taken.has(item.id) ? 'default' : 'pointer',
                            backgroundColor: isTaken(item.id) ? getTakenColor(item.id) : (isHovered(item.id) ? getHoverColor(item.id) : null)
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
            </div>
        </div>

        <div v-else-if="state === STATES.END" class="d-flex flex-column align-center mt-8" style="min-height: 80vh;">

            <div style="position: relative; width: 100%;">
                <div style="position: absolute; left: 0; top: 0;"  class="text-caption">
                    <div>
                        <v-icon :color="getPlayerColor(lobby.id)" icon="mdi-circle"/>
                        <span class="ml-1">{{ myNameDisplay }}</span>
                    </div>
                    <div v-for="([p, n]) in mp.players" :key="'i_'+p">
                        <v-icon :color="getPlayerColor(p)" icon="mdi-circle"/>
                        <span class="ml-1">{{ n }}</span>
                    </div>
                    <div v-for="p in mp.waitingList" :key="'wi_'+p.id">
                        <v-icon color="surface-light" icon="mdi-circle-slice-8"/>
                        <span class="ml-1">{{ p.name }}</span>
                    </div>
                </div>
            </div>

            <div v-if="winner === lobby.id" class="d-flex align-center justify-center">
                <v-icon
                    size="60"
                    class="mr-4"
                    icon="mdi-check-bold"
                    color="primary"/>
                <span>You won!</span>
            </div>
            <div v-else-if="Array.isArray(winner)" class="d-flex align-center justify-center">
                <v-icon
                    size="60"
                    class="mr-4"
                    icon="mdi-equal"
                    color="default"/>
                <span>It's a draw ({{ winner.map(w => getPlayerName(w)).join(", ") }})</span>
            </div>
            <div v-else class="d-flex align-center justify-center">
                <v-icon
                    size="60"
                    class="mr-4"
                    icon="mdi-close-circle-outline"
                    color="error"/>
                <span>{{ getPlayerName(winner) }} won</span>
            </div>

            <h4 class="mt-8">{{ gameData.tag ? gameData.tag.name : '?' }}</h4>

            <table :class="[settings.lightMode ? 'light' : 'dark']">
                <thead style="text-align: left;">
                    <tr>
                        <th></th>
                        <th>Player</th>
                        <th>Points</th>
                        <th>{{ capitalize(app.itemName+'s') }}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><v-icon :color="getPlayerColor(lobby.id)" icon="mdi-circle"/></td>
                        <td>{{ myNameDisplay }} (you)</td>
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
                        <td><v-icon :color="getPlayerColor(p)" icon="mdi-circle"/></td>
                        <td>{{ getPlayerName(p) }}</td>
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
                <v-btn v-if="mp.hosting"
                    class="ml-1"
                    size="x-large"
                    :color="readyToPlay ? 'primary' : 'default'"
                    :disabled="!readyToPlay"
                    @click="startGame">play again</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { DIFFICULTY, GAMES, SOUND, useGames } from '@/store/games'
    import { ref, onMounted, reactive, computed, watch, onUnmounted, onUpdated, toRaw } from 'vue'
    import { useElementSize } from '@vueuse/core';
    import DM from '@/use/data-manager';
    import Chance from 'chance';
    import { useApp } from '@/store/app';
    import Multiplayer from '@/use/multiplayer';
    import { useToast } from 'vue-toastification';
    import { capitalize, closeRoom, joinRoom, leaveRoom, loadGameRooms, openRoom, updateRoom } from '@/use/utility';
    import { useSettings } from '@/store/settings';
    import { useTheme } from 'vuetify/lib/framework.mjs';
    import Cookies from 'js-cookie';

    import imgUrlS from '@/assets/__placeholder__s.png'
    import { DateTime } from 'luxon';
import DifficultyIcon from './DifficultyIcon.vue';

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
    const theme = useTheme()

    const hoverColor = computed(() => theme.current.value.colors.secondary)

    // elements
    const el = ref(null)

    const elSize = useElementSize(el)

    const itemsPerRow = ref(3)
    const imageWidth = computed(() => {
        const w = Math.floor(elSize.width.value / itemsPerRow.value)
        const h = Math.floor(elSize.height.value / itemsPerRow.value)
        return Math.max(80, Math.min(360, w - 15))
    })

    // difficulty settings
    const numItems = computed(() => Math.max(9, numPlayers.value * 3))
    // const numMatches = computed(() => {
    //     const mul = props.difficulty === DIFFICULTY.HARD ? 0.6 : 0.4
    //     return Math.max(1, Math.floor(numItems.value * mul))
    // })
    const numMatches = computed(() => Math.max(1, Math.floor(numItems.value * 0.5)))

    // multiplayer related stuff
    let lobbyInt;
    let lobby, countdownInt;

    const myName = ref("")
    const myNameDisplay = ref("")
    const countdown = ref(-1)

    const mp = reactive({
        rooms: [],
        hosting: false,
        gameId: null,
        peerId: null,
        players: new Map(),
        waitingList: []
    })
    const playerList = computed(() => {
        const list = Array.from(mp.players.keys())
        list.sort()
        return list
    })
    const playerColors = computed(() => {
        const list = [lobby.id].concat(playerList.value)
        list.sort()
        return d3.scaleOrdinal(d3.schemeCategory10).domain(list)
    })

    // game related stuff
    const state = ref(STATES.START)
    const readyToPlay = ref(true)
    const waiting = ref(false)

    const items = ref([])
    const gameData = reactive({
        tag: null,
        taken: new Map(),
        hovered: new Map(),
        points: new Map(),
        correct: new Set()
    })
    const numPlayers = computed(() => mp.players.size + 1)
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
        if (gameData.points.size === 0) return null
        let max = Number.MIN_SAFE_INTEGER;
        let winners = []
        gameData.points.forEach((value, id) => {
            if (value > max) {
                max = value
                winners = [id]
            } else if (value === max) {
                winners.push(id)
            }
        })
        return winners.length > 1 ? winners : winners[0]
    })

    const myItems = computed(() => {
        return items.value.filter(d => {
            const t = gameData.taken.get(d.id)
            return t && t === lobby.id
        })
    })
    const otherItems = computed(() => {
        const map = new Map()
        mp.players.forEach((_, p) => {
            map.set(p, items.value.filter(d => {
                const t = gameData.taken.get(d.id)
                return t  && t === p
            }))
        })
        return map
    })


    function setName(name, setDisplay=true) {
        myName.value = name;
        if (setDisplay) {
            myNameDisplay.value = name;
        }
        saveName(name)
    }
    function saveName() {
        Cookies.set("set-mp-name", myName.value)
    }

    function copyToClipboard(str) {
        navigator.clipboard.writeText(str)
    }
    function isHovered(id) {
        return new Set(gameData.hovered.values()).has(id)
    }
    function getHoverColor(id) {
        let me = false;
        let hc = hoverColor.value
        gameData.hovered.forEach((item, user) => {
            if (!me && item === id) {
                const tmp = d3.color(getPlayerColor(user))
                tmp.opacity = 0.25
                hc = tmp.formatRgb()
                me = user === lobby.id
            }
        })
        return hc
    }
    function isTaken(id) {
        return gameData.taken.has(id)
    }
    function getTakenColor(id) {
        const user = gameData.taken.get(id)
        if (!user) return null
        const tmp = d3.color(getPlayerColor(user))
        tmp.opacity = 0.25
        return tmp.formatRgb()
    }
    function takeItem(item) {
        if (!gameData.taken.has(item.id)) {
            games.play(SOUND.PLOP)
            if (mp.hosting) {
                confirmTaken(item.id, lobby.id)
            } else {
                lobby.send("take", { item: item.id, user: lobby.id })
            }
        }
    }
    function confirmTaken(item, user) {
        // set item as taken
        gameData.taken.set(item, user)
        // update points
        const diff = gameData.correct.has(item) ? 1 : -1
        gameData.points.set(user, (gameData.points.get(user) || 0) + diff)
        if (user === lobby.id) {
            games.play(diff > 0 ? SOUND.WIN_MINI : SOUND.FAIL_MINI)
        } else {
            games.play(SOUND.PLOP)
        }

        // if host - tell other players
        if (mp.hosting) {
            lobby.send("take_confirm", { item: item, user: user })
            if (numFound.value === numMatches.value) {
                stopGame()
            }
        }
    }
    function getPlayerColor(id) {
        return playerColors.value(id)
    }
    function playerNameExists(name) {
        return myName.value === name || Array.from(mp.players.values()).includes(name)
    }
    function getPlayerName(id) {
        if (lobby && id === lobby.id) {
            return myName.value
        }
        return mp.players.get(id)
    }

    function startGame() {
        state.value = STATES.LOADING
        // clear previous data
        clear()

        if (mp.hosting) {
            mp.waitingList.forEach(d => addPlayer(d.id, d.name))
            mp.waitingList = []

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

            lobby.setVote("start")
            lobby.send("dataset", {
                tag: tid,
                items: items.value.map(d => d.id)
            })
        } else {
            mp.waitingList = []
        }
    }
    function startRound() {
        if (lobby) {

            // tell the server we are still playing
            if (mp.hosting) {
                updateRoom(GAMES.SET, mp.gameId)
            }

            waiting.value = false
            gameData.taken.clear()
            gameData.points.clear()
            gameData.points.set(lobby.id, 0)
            mp.players.forEach((_, id) => gameData.points.set(id, 0))

            countdown.value = 3
            games.playSingle(SOUND.TICK)
            countdownInt = setInterval(() => {
                countdown.value--
                if (countdown.value === 0) {
                    clearInterval(countdownInt)
                    countdownInt = null
                    readyToPlay.value = false;
                    games.playSingle(SOUND.START)
                    state.value = STATES.INGAME
                } else {
                    games.playSingle(SOUND.TICK)
                }
            }, 900)
        }
    }

    function stopGame() {
        state.value = STATES.END
        if (winner.value === lobby.id) {
            games.playSingle(SOUND.WIN)
        } else if (Array.isArray(winner.value) && winner.value.includes(lobby.id)) {
            games.playSingle(SOUND.MEH)
        } else {
            games.playSingle(SOUND.FAIL)
        }

        if (mp.hosting) {
            lobby.setVote("end")
            lobby.send("end_confirm", winner.value)
        } else {
            lobby.send("end", lobby.id)
        }

        emit("end", winner.value === lobby.id)
    }

    function isState(s) {
        return Object.values(STATES).includes(s)
    }

    async function leaveLobby(screen=STATES.START) {
        if (lobby) {
            if (mp.gameId !== null) {
                try {
                    await leaveRoom(GAMES.SET, mp.gameId, lobby.id)
                    mp.gameId = null
                    mp.peerId = null
                } catch(e) {
                    console.error(e.toString())
                    toast.error("error leaving lobby")
                }
            }
            lobby.send(mp.hosting ? "close" : "leave")
            lobby.disconnect()
            setName(myName.value)
        }
        state.value = isState(screen) ? screen : STATES.START
        reset()
    }

    function close() {
        leaveLobby()
        emit("close")
    }

    function clear() {
        items.value = []
        gameData.tag = null
        gameData.taken.clear()
        gameData.hovered.clear()
        gameData.correct.clear()
        gameData.points.clear()
        readyToPlay.value = true
        if (lobbyInt) {
            clearInterval(lobbyInt)
            lobbyInt = null
        }
        if (countdownInt) {
            clearInterval(countdownInt)
            countdownInt = null;
        }
        if (lobby) lobby.clearVotes()
    }
    function reset() {
        clear()
        mp.players.clear();
        if (lobby) {
            lobby.clear()
        }
    }

    function sendItemHover() {
        if (lobby) {
            const list = []
            gameData.hovered.forEach((item, id) => list.push([id, item]))
            lobby.send("item_hover", list)
        }
    }

    function onCursorEnter(id) {
        if (lobby && state.value === STATES.INGAME) {
            if (mp.hosting) {
                gameData.hovered.set(lobby.id, id)
                sendItemHover()
            } else {
                lobby.send("cursor_enter", { user: lobby.id, item: id })
            }
        }
    }
    function onCursorLeave() {
        if (lobby && state.value === STATES.INGAME) {
            if (mp.hosting) {
                gameData.hovered.delete(lobby.id)
                sendItemHover()
            } else {
                const item = gameData.hovered.get(lobby.id)
                if (item) {
                    lobby.send("cursor_leave", { user: lobby.id, item: item })
                }
            }
        }
    }

    async function loadLobbies() {
        try {
            mp.rooms = await loadGameRooms(GAMES.SET)
        } catch(e) {
            console.error(e.toString())
            toast.error("could not load lobbies")
        }
    }

    async function hostGame() {
        mp.hosting = true;
        mp.gameId = null
        mp.peerId = null
        state.value = STATES.LOBBY
        games.playSingle(SOUND.TRANSITION)
        try {
            const room = await openRoom(
                GAMES.SET,
                lobby.id,
                myName.value,
                {
                    difficulty: props.difficulty,
                    max_players: props.maxPlayers
                }
            )
            mp.gameId = room.id;
            mp.peerId = room.peer
        } catch (e) {
            console.error(e.toString())
            toast.error("could not host lobby")
        }
    }
    function joinGame() {
        mp.hosting = false;
        mp.gameId = null
        mp.peerId = null
        mp.rooms = []
        state.value = STATES.CONNECT
        loadLobbies()
        lobbyInt = setInterval(loadLobbies, 10000)
    }
    async function joinLobby(id) {
        if (lobby && id) {
            if (lobbyInt) {
                clearInterval(lobbyInt)
                lobbyInt = null
            }
            try {
                const room = await joinRoom(GAMES.SET, id, lobby.id, myName.value)
                mp.gameId = room.id;
                mp.peerId = room.peer
                lobby.connectTo(room.peer)
            } catch (e) {
                console.error(e.toString())
                toast.error("could not join lobby")
            }
        }
    }

    function addPlayer(id, name) {
        if (mp.hosting && numPlayers.value <= props.maxPlayers) {
            if (!mp.players.has(id)) {
                if (!playerNameExists(name)) {
                    mp.players.set(id, name)
                } else {
                    let nr = 1;
                    let newName;
                    do {
                        newName = `${name} (${nr})`
                        nr++;
                    } while (playerNameExists(newName))
                    mp.players.set(id, newName)
                }
                games.play(SOUND.TRANSITION)
                toast.info(mp.players.get(id) + " joined the lobby")
                lobby.send("players", getPlayers())
            } else {
                console.debug("player", name, "already in game")
            }
        }
    }
    function addPlayerToWaitingList(id, name) {
        if (mp.hosting && (numPlayers.value + mp.waitingList.length + 1) <= props.maxPlayers) {
            if (mp.waitingList.find(d => d.id === id) === undefined) {
                mp.waitingList.push({ id: id, name: name })
                lobby.send("players_wait", toRaw(mp.waitingList))
                lobby.sendTo(id, "wait")
                lobby.sendTo(id, "players", getPlayers())
            } else {
                console.debug("player", name, "already on waiting list")
            }
        }
    }

    function removePlayer(id) {
        if (mp.hosting) {
            if (mp.players.has(id)) {
                toast.info(mp.players.get(id) + " left the lobby")
                mp.players.delete(id)
                lobby.disconnectFrom(id)

                if (mp.players.size === 0) {
                    toast.info("no other players in lobby")
                    state.value = STATES.LOBBY
                } else {
                    lobby.send("players", getPlayers())
                }
            } else {
                removePlayerFromWaitingList(id)
            }
        }
    }
    function removePlayerFromWaitingList(id) {
        if (mp.hosting) {
            const idx = mp.waitingList.findIndex(d => d.id === id)
            if (idx >= 0) {
                mp.waitingList.splice(idx, 1)
                lobby.disconnectFrom(id)
                lobby.send("players_wait", toRaw(mp.waitingList))
            }
        }
    }

    function getPlayers() {
        const list = [[lobby.id, myName.value]]
        mp.players.forEach((name, id) => list.push([id, name]))
        return list
    }

    function readPlayers(data) {
        if (!mp.hosting) {
            // look for players who left
            mp.players.forEach((n, p) => {
                if (!data.find(d => d[0] === p)) {
                    toast.info(`${n} left the lobby`)
                }
            })
            // look for new players
            data.forEach(d => {
                if (d[0] === lobby.id) {
                    myNameDisplay.value = d[1]
                } else if (!mp.players.has(d[0])) {
                    toast.info(`${d[1]} joined the lobby`)
                }
            })
            mp.players = new Map(data.filter(d => d[0] !== lobby.id))
        }
    }

    function initMultiplayer() {

        reset()

        const savedName = Cookies.get("set-mp-name")
        setName(savedName ? savedName : app.activeUser.name)

        // create the "lobby"
        lobby = new Multiplayer(() => {
            return {
                id: lobby.id,
                name: myName.value,
                dataset: app.ds,
                code: app.activeCode,
                difficulty: props.difficulty,
                players: getPlayers()
            }
        })

        lobby.onCreate(() => state.value = STATES.START)
        lobby.onConnectError(async (id) => {
            if (id === mp.peerId) {
                toast.error("could not connect to lobby")
                // await closeRoom(GAMES.SET, mp.gameId)
                leaveLobby(STATES.CONNECT)
                loadLobbies()
            }
        })

        // handle handshake
        lobby.onReceive("handshake", data => {
            if (data.dataset == app.ds && data.code == app.activeCode) {
                if (mp.hosting) {
                    if (state.value === STATES.INGAME) {
                        addPlayerToWaitingList(data.id, data.name)
                    } else {
                        addPlayer(data.id, data.name)
                    }
                } else {
                    if (state.value === STATES.CONNECT) {
                        state.value = STATES.LOBBY
                        games.play(SOUND.TRANSITION)
                    }
                    readPlayers(data.players)
                }

            } else {
                toast.error("data mismatch")
                toast.error("player data mismatch")
            }
        })
        lobby.onReceive("players", data => {
            if (!mp.hosting) {
                readPlayers(data)
            }
        })
        lobby.onReceive("players_wait", data => {
            if (!mp.hosting) {
                mp.waitingList = data;
            }
        })

        lobby.onReceive("start", (_d, _t, conn) => {
            if (mp.hosting && (state.value === STATES.LOBBY || state.value === STATES.END)) {
                lobby.setVote("start", conn.peer)
            }
        })
        lobby.onReceive("start_confirm", () => {
            if (!mp.hosting && (state.value === STATES.LOADING || state.value === STATES.END)) {
                startRound()
            }
        })

        lobby.onReceive("wait",() => {
            if (!mp.hosting) {
                waiting.value = true
            }
        })

        lobby.onReceive("dataset", data => {
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

            lobby.send("dataset_confirm", {
                tag: gameData.tag.id,
                items: tmp.map(d => d.id)
            })
        })

        lobby.onReceive("dataset_confirm", (data, _t, conn) => {
            if (mp.hosting && state.value === STATES.LOADING) {
                let error = false
                if (data.tag === gameData.tag.id) {
                    if (items.value.every((d,i) => data.items[i] === d.id)) {
                        lobby.setVote("start", conn.peer)
                    } else {
                        console.error("items mismatch", data.items, items.value)
                        toast.error("data mismatch", { timeout: 2000 })
                        error = true
                    }
                } else {
                    console.error("tag mismatch", data.tag, gameData.tag.id)
                    toast.error("data mismatch", { timeout: 2000 })
                    error = true
                }

                // send data again if there is an error
                if (error) {
                    lobby.send("dataset", {
                        tag: gameData.tag.id,
                        items: items.value.map(d => d.id)
                    })
                }
            }
        })

        lobby.onReceive("cursor_enter", data => {
            if (mp.hosting && state.value === STATES.INGAME) {
                gameData.hovered.set(data.user, data.item)
                sendItemHover()
            }
        })
        lobby.onReceive("cursor_leave", data => {
            if (mp.hosting && state.value === STATES.INGAME) {
                gameData.hovered.delete(data.user)
                sendItemHover()
            }
        })
        lobby.onReceive("item_hover", data => {
            if (!mp.hosting && state.value === STATES.INGAME) {
                gameData.hovered = new Map(data)
            }
        })
        lobby.onReceive("take", data => {
            if (mp.hosting && state.value === STATES.INGAME) {
                const existing = gameData.taken.get(data.item)
                if (!existing) {
                    confirmTaken(data.item, data.user)
                }
            }
        })
        lobby.onReceive("take_confirm", data => {
            if (state.value === STATES.INGAME) {
                confirmTaken(data.item, data.user, data.time)
            }
        })
        lobby.onReceive("end", user => {
            if (mp.hosting && state.value === STATES.END) {
                lobby.setVote("end", user)
            }
        })
        lobby.onReceive("end_confirm", () => {
            if (!mp.hosting && state.value === STATES.INGAME) {
                stopGame()
            }
        })

        lobby.onReceive("close", () => {
            if (!mp.hosting) {
                toast.info("host closed the lobby", { timeout: 2000 })
                leaveLobby()
            }
        })
        lobby.onReceive("leave", (_d, _t, conn) => {
            if (mp.hosting) {
                removePlayer(conn.peer)
            }
        })


        // voting callbacks

        lobby.onVote("start", () => {
            if (mp.hosting) {
                lobby.send("start_confirm")
                startRound()
            }
        })

        lobby.onVoteUpdate("end", set => readyToPlay.value = set.size === numPlayers.value)
    }

    onMounted(initMultiplayer)
    onUnmounted(leaveLobby)

    watch(() => app.activeUserId, () => setName(app.activeUser.name))

    watch(props, reset, { deep: true })

    watch(numPlayers, function() {
        if (numPlayers.value === 1) {
            leaveLobby(mp.hosting ? STATES.LOBBY : STATES.CONNECT)
        }
    })

</script>

<style scoped>
table {
    border-collapse: collapse;
    text-align: left;
}
table td, table th {
    border: 1em;
    padding: 8px;
    padding-right: 2em;
}

table.light td, table.light th {
    border-color: black;
}
table.dark td, table.light th  {
    border-color: white;
}

table.lobbies td, table.lobbies th {
    margin-right: 4em;
}

.break {
  flex-basis: 100%;
  height: 0;
}

.item-container {
    width: 100%;
    height: 80vh;
    display: flex;
    align-items: center;
    justify-content: center;
    align-content: start;
    flex-wrap: wrap;
}
</style>