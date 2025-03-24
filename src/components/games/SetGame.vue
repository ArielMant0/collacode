<template>
    <div style="width: 100%;">

        <div v-if="state === STATES.START" class="d-flex flex-column justify-center align-center" style="height: 80vh;">

            <div style="width: 100%; max-width: 800px;">
                <div class="d-flex align-center">
                    <v-text-field v-model="myName"
                        label="Name"
                        density="compact"
                        style="width: 100%"
                        hide-details
                        hide-spin-buttons
                        @update:model-value="n => setName(n)"
                        variant="outlined"/>
                    <v-btn variant="text" density="comfortable" rounded="0" icon="mdi-restart" class="ml-1" @click="setName(app.activeUser.name)"/>
                </div>
                <div class="d-flex justify-space-between align-center mt-2" style="width: 100%;">
                    <v-btn size="large" variant="tonal" style="width: 49%;" :disabled="!myName" @click="hostGame">Host Game</v-btn>
                    <v-btn size="large" variant="tonal" style="width: 49%;" :disabled="!myName" @click="joinGame">Join Game</v-btn>
                </div>
            </div>

        </div>

        <div v-else-if="state === STATES.CONNECT" class="d-flex flex-column justify-center align-center" style="height: 80vh;">

            <div style="width: max-content;">

                <div class="d-flex align-center" style="width: 100%;">
                    <v-text-field v-model="myName"
                        label="Your name"
                        density="compact"
                        hide-details
                        hide-spin-buttons
                        @update:model-value="n => setName(n)"
                        variant="outlined"/>
                    <v-btn variant="text" density="comfortable" rounded="0" icon="mdi-restart" class="ml-1" @click="setName(app.activeUser.name)"/>
                </div>

                <v-sheet v-if="app.static" class="mt-2 mb-2 pa-4" rounded="sm" color="surface-light">
                    <div>
                        Loobies are not available in static mode. To connect to a hosting player, you must:
                        <ol class="pl-8">
                            <li>get their room ID (e.g., using text messaging)</li>
                            <li>directly paste their room ID into the box below</li>
                            <li>click the conntect buttong on the right side of the box</li>
                        </ol>
                    </div>
                </v-sheet>

                <table v-else :class="[settings.lightMode ? 'light' : 'dark', 'lobbies mt-8']" style="display:block; min-height: 300px;">
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

                <div class="d-flex align-center mt-2 mb-2" style="width: 100%;">
                    <v-text-field v-model="mp.gameId"
                        label="Room ID"
                        density="compact"
                        placeholder="connect to room manually"
                        hide-details
                        hide-spin-buttons
                        variant="outlined"/>
                    <v-btn
                        variant="text"
                        density="comfortable"
                        :disabled="!mp.gameId"
                        rounded="0"
                        icon="mdi-location-enter"
                        class="ml-1"
                        @click="joinLobby(mp.gameId)"/>
                </div>

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
                    label="Room ID"
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
                    <v-btn class="mt-8" color="warning" style="width: 49%;" @click="leaveLobby(STATES.START)">exit room</v-btn>
                    <v-btn class="mt-8" color="primary" style="width: 49%;" :disabled="numPlayers < 1" @click="startGame">start game</v-btn>
                </div>
                <div v-else>
                    <v-btn class="mt-8" color="warning" block @click="leaveLobby(STATES.CONNECT)">exit room</v-btn>
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
            <div class="d-flex align-center justify-center" style="width: 100%;">
                <LoadingScreen
                    height="70vh"
                    :messages="[
                        'click on an item image to take an item',
                        'clicking on a wrong item deducts 1 point',
                        'as long as you have the <b>most</b> points, you win',
                        'all player names are visible in the top left corner of the screen',
                    ]"/>
            </div>
        </div>

        <div v-if="state === STATES.INGAME" style="width: 100%;" class="d-flex flex-column align-center justify-start mt-4">

            <div style="position: relative; width: 100%;">
                <div style="position: absolute; left: 0; top: 0;"  class="text-caption">
                    <div>
                        <v-icon :color="getPlayerColor(lobby.id)" icon="mdi-circle"/>
                        <span class="ml-1">{{ myNameDisplay }} (you)</span>
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

            <div class="d-flex justify-space-between mt-4 mb-4" style="font-size: x-large;">
                <div v-if="lobby.id"
                    :style="{
                        color: getPlayerColor(lobby.id),
                        border: '2px solid '+getPlayerColor(lobby.id),
                        borderRadius: '5px'
                    }"
                    class="mr-2 ml-2 pt-1 pl-2 pr-2 pb-1">
                    {{ gameData.points.get(lobby.id) }}
                </div>
                <div v-for="([p, _]) in mp.players"
                    :key="'player_'+p"
                    class="mr-2 ml-2 pt-1 pl-2 pr-2 pb-1"
                    :style="{
                        color: getPlayerColor(p),
                        border: '2px solid '+getPlayerColor(p),
                        borderRadius: '5px'
                    }">
                    {{ gameData.points.get(p)}}
                </div>
            </div>

            <h3 class="mt-2 mb-4">{{ gameData.tag ? gameData.tag.name : '?' }}</h3>
            <div v-if="showDesc" class="mb-2 text-caption" style="max-width: 70%; min-width: 100px; text-align: center;">
                {{ gameData.tag ? gameData.tag.description : 'no description' }}
            </div>

            <div class="mt-2 mb-4 d-flex align-center">
                <v-icon v-for="i in numMatches" class="ml-1 mr-1"
                    :color="getNumTakenColor(i-1)"
                    :icon="areNumTaken(i) ? 'mdi-circle-slice-8' : 'mdi-circle-outline'"/>
            </div>

            <div ref="el" style="width: 90%; height: 70vh;" class="d-flex justify-center align-start">
                <div class="item-container" @pointerleave="onCursorLeave" :style="{ maxWidth: ((imageWidth+15)*itemsPerRow)+'px' }">
                    <v-sheet v-for="item in items" :key="item.id"
                        class="mr-1 mb-1 pa-1 cursor-pointer prevent-select"
                        @pointerenter="onCursorEnter(item.id)"
                        @pointerleave="onCursorLeave"
                        rounded="sm"
                        @pointerdown="takeItem(item)"
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
                                draggable="false"
                                :style="{ opacity: gameData.taken.has(item.id) ? 0.1 : 1 }"
                                :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                                :lazy-src="imgUrlS"
                                :width="imageWidth"
                                :height="Math.floor(imageWidth*0.5)"/>

                            <div v-if="gameData.taken.has(item.id)"
                                style="position: absolute; top:0; left:0; width: 100%;"
                                :style="{ height: Math.floor(imageWidth*0.5)+'px'}"
                                class="d-flex align-center justify-center">
                                <GameResultIcon :result="gameData.correct.has(item.id)"/>
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

            <div class="d-flex align-center justify-center">
                <GameResultIcon v-if="gameData.result !== null" :result="gameData.result" :text="getResultText()" show-effects show-text/>
            </div>

            <h3 class="mt-2 mb-4">{{ gameData.tag ? gameData.tag.name : '?' }}</h3>
            <div v-if="showDesc" class="mb-6 text-caption" style="max-width: 80%; text-align: center;">
                {{ gameData.tag ? gameData.tag.description : 'no description' }}
            </div>

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
                            <div v-for="item in myItems" :key="'me_'+item.id" class="mr-1 mb-1">
                                <v-sheet  class="pa-1" rounded="sm" :color="gameData.correct.has(item.id) ? 'primary' : 'error'">
                                    <div class="text-dots text-caption" style="max-width: 100px;">{{ item.name }}</div>
                                    <ItemTeaser :item="item" :width="100" :height="50"/>

                                </v-sheet>
                                <div style="text-align: center;">
                                    <ObjectionButton class="mt-1"
                                        :item-id="item.id"
                                        :tag-id="gameData.tag.id"
                                        :action="gameData.correct.has(item.id) ? OBJECTION_ACTIONS.REMOVE : OBJECTION_ACTIONS.ADD"/>
                                </div>
                            </div>
                        </td>
                    </tr>

                    <tr v-for="(p, idx) in playerList" :key="'res_'+p">
                        <td><v-icon :color="getPlayerColor(p)" icon="mdi-circle"/></td>
                        <td>{{ getPlayerName(p) }}</td>
                        <td>{{ gameData.points.get(p) }}</td>
                        <td class="d-flex flex-wrap">
                            <div v-for="item in otherItems.get(p)" :key="idx+'_it_'+item.id" class="mr-1 mb-1" >
                                <v-sheet class="pa-1" rounded="sm" :color="gameData.correct.has(item.id) ? 'primary' : 'error'">
                                    <div class="text-dots text-caption" style="max-width: 100px;">{{ item.name }}</div>
                                    <ItemTeaser :item="item" :width="100" :height="50"/>
                                </v-sheet>
                                <div style="text-align: center;">
                                    <ObjectionButton class="mt-1"
                                        :item-id="item.id"
                                        :tag-id="gameData.tag.id"
                                        :action="gameData.correct.has(item.id) ? OBJECTION_ACTIONS.REMOVE : OBJECTION_ACTIONS.ADD"/>
                                </div>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div class="d-flex align-center justify-center mt-4 mb-4">
                <v-btn class="mr-1" size="large" color="error" @click="close">close game</v-btn>
                <v-btn class="ml-1 mr-1" size="large" color="warning" @click="leaveLobby(STATES.START)">exit room</v-btn>
                <v-btn v-if="mp.hosting"
                    class="ml-1"
                    size="large"
                    :color="readyToPlay ? 'primary' : 'default'"
                    :disabled="!readyToPlay"
                    @click="startGame">play again</v-btn>
            </div>

            <v-btn
                @click="showDetails = !showDetails"
                variant="tonal"
                density="comfortable"
                class="text-caption">
                {{ showDetails ? 'hide' : 'show' }} {{ app.itemName }} details
            </v-btn>

            <v-sheet v-if="showDetails" class="d-flex align-center justify-center flex-column pa-2 mt-4 mb-2" rounded>
                <ItemSummary v-for="item in items"
                    class="mb-2"
                    :key="'detail_'+item.id"
                    :id="item.id"
                    :teaser-border="gameData.correct.has(item.id) ? theme.current.value.colors.primary : theme.current.value.colors.error"
                    show-all-users
                    show-evidence
                    :teaser-width="100"
                    :teaser-height="50"
                    :evidence-size="80"
                    :tag-id="gameData.tag.id"/>
            </v-sheet>

        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { DIFFICULTY, GAME_RESULT, GAMES, STATES, useGames } from '@/store/games'
    import { ref, onMounted, reactive, computed, watch, onUnmounted, toRaw } from 'vue'
    import { useElementSize } from '@vueuse/core';
    import DM from '@/use/data-manager';
    import Chance from 'chance';
    import { OBJECTION_ACTIONS, useApp } from '@/store/app';
    import Multiplayer from '@/use/multiplayer';
    import { useToast } from 'vue-toastification';
    import { capitalize, joinRoom, leaveRoom, loadGameRooms, openRoom, updateRoom } from '@/use/utility';
    import { useSettings } from '@/store/settings';
    import { useTheme } from 'vuetify/lib/framework.mjs';
    import Cookies from 'js-cookie';
    import { validate as uuidValidate } from 'uuid';

    import imgUrlS from '@/assets/__placeholder__s.png'
    import { DateTime } from 'luxon';
    import DifficultyIcon from './DifficultyIcon.vue';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import ObjectionButton from '../objections/ObjectionButton.vue';
    import { useSounds, SOUND } from '@/store/sounds';
    import { storeToRefs } from 'pinia';
    import ItemSummary from '../items/ItemSummary.vue';
    import GameResultIcon from './GameResultIcon.vue';
    import LoadingScreen from './LoadingScreen.vue';

    const props = defineProps({
        maxPlayers: {
            type: Number,
            default: 5
        },
    })

    const emit = defineEmits(["end", "close"])

    // stores
    const sounds = useSounds()
    const app = useApp()
    const toast = useToast()
    const settings = useSettings()
    const theme = useTheme()
    const games = useGames()

    const hoverColor = computed(() => theme.current.value.colors.secondary)

    // elements
    const el = ref(null)

    const elSize = useElementSize(el)

    const itemsPerRow = ref(3)
    const imageWidth = computed(() => {
        const w = Math.floor(elSize.width.value / itemsPerRow.value)
        const h = Math.floor(elSize.height.value / itemsPerRow.value)
        return Math.max(80, Math.min(360, Math.min(w, h) - 15))
    })

    // difficulty settings
    const { difficulty } = storeToRefs(games)
    const numItems = computed(() => Math.max(9, numPlayers.value * itemsPerRow.value))
    const numMatches = computed(() => {
        switch(difficulty.value) {
            case DIFFICULTY.EASY: return Math.max(1, Math.round(numItems.value * 0.5))
            case DIFFICULTY.NORMAL: return Math.max(1, Math.round(numItems.value * 0.4))
            case DIFFICULTY.HARD: return Math.max(1, Math.round(numItems.value * 0.3))
        }
    })
    const showDesc = computed(() => difficulty.value !== DIFFICULTY.HARD)

    // multiplayer related stuff
    let lobbyInt, toastId = null;
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

    const showDetails = ref(false)

    // game related stuff
    const state = ref(STATES.START)
    const readyToPlay = ref(true)
    const waiting = ref(false)

    const items = ref([])
    const gameData = reactive({
        tag: null,
        taken: new Map(),
        takenOrder: [],
        hovered: new Map(),
        points: new Map(),
        correct: new Set(),
        result: null
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


    function areNumTaken(n) {
        return numFound.value >= n
    }
    function getNumTakenColor(index) {
        if (index < 0 || index >= gameData.takenOrder.length) return 'default'
        const pid = gameData.taken.get(gameData.takenOrder[index])
        return pid ? getPlayerColor(pid) : 'default'
    }

    function getResultText() {
        if (winner.value === lobby.id) {
            return "You won!"
        } else if (Array.isArray(winner)) {
            return `It's a draw (${winner.value.map(w => getPlayerName(w)).join(", ")})`
        } else {
            return getPlayerName(winner.value) + " won"
        }
    }
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
            sounds.play(SOUND.PLOP)
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
        if (gameData.correct.has(item)) {
            gameData.takenOrder.push(item)
        }
        // update points
        const diff = gameData.correct.has(item) ? 1 : -1
        gameData.points.set(user, (gameData.points.get(user) || 0) + diff)
        if (user === lobby.id) {
            sounds.play(diff > 0 ? SOUND.WIN_MINI : SOUND.FAIL_MINI)
        } else {
            sounds.play(SOUND.PLOP)
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

        if (toastId !== null) {
            toast.dismiss(toastId)
            toastId = null
        }

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
            if (mp.hosting && !app.static) {
                updateRoom(GAMES.SET, mp.gameId)
            }

            waiting.value = false
            gameData.taken.clear()
            gameData.points.clear()
            gameData.points.set(lobby.id, 0)
            mp.players.forEach((_, id) => gameData.points.set(id, 0))

            countdown.value = 3
            sounds.play(SOUND.TICK)
            countdownInt = setInterval(() => {
                countdown.value--
                if (countdown.value === 0) {
                    clearInterval(countdownInt)
                    countdownInt = null
                    readyToPlay.value = false;
                    sounds.play(SOUND.START)
                    state.value = STATES.INGAME
                } else {
                    sounds.play(SOUND.TICK)
                }
            }, 900)
        }
    }

    function stopGame() {
        state.value = STATES.END

        if (winner.value === lobby.id) {
            sounds.play(SOUND.WIN)
            gameData.result = GAME_RESULT.WIN
        } else if (Array.isArray(winner.value) && winner.value.includes(lobby.id)) {
            sounds.play(SOUND.MEH)
            gameData.result = GAME_RESULT.DRAW
        } else {
            sounds.play(SOUND.FAIL)
            gameData.result = GAME_RESULT.LOSS
        }

        if (mp.hosting) {
            lobby.setVote("end")
            lobby.send("end_confirm", winner.value)
        } else {
            lobby.send("end", lobby.id)
        }

        if (numPlayers.value > 1) {
            emit("end", winner.value === lobby.id)
        }
    }

    function isState(s) {
        return Object.values(STATES).includes(s)
    }

    async function leaveLobby(screen=STATES.START) {
        if (lobby) {
            if (mp.gameId !== null) {
                try {
                    if (!app.static) {
                        await leaveRoom(GAMES.SET, mp.gameId, lobby.id)
                    }
                    mp.gameId = null
                    mp.peerId = null
                } catch(e) {
                    console.error(e.toString())
                    toast.error("error leaving lobby")
                }
            }
            lobby.send(mp.hosting ? "close" : "leave")
            lobby.clear()

            setName(myName.value)
        }
        reset()
        state.value = isState(screen) ? screen : STATES.START
    }

    function close() {
        leaveLobby()
        emit("close")
    }

    function clear() {
        items.value = []
        gameData.tag = null
        gameData.result = null
        gameData.taken.clear()
        gameData.takenOrder = []
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
        if (app.static) return

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
        sounds.play(SOUND.TRANSITION)
        try {
            if (app.static) {
                mp.gameId = lobby.id
                mp.peerId = lobby.id
            } else {
                const room = await openRoom(
                    GAMES.SET,
                    lobby.id,
                    myName.value,
                    {
                        difficulty: difficulty.value,
                        max_players: props.maxPlayers
                    }
                )
                mp.gameId = room.id;
                mp.peerId = room.peer
            }
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

        if (app.static) {
            mp.rooms = []
        } else {
            loadLobbies()
            lobbyInt = setInterval(loadLobbies, 10000)
        }
    }
    async function joinLobby(id) {
        if (lobby && id) {

            if (!uuidValidate(id)) {
                return toast.error("invalid room id")
            }

            if (id === lobby.id) {
                return toast.warning("you cannot connect to yourself :(")
            }

            if (lobbyInt !== null) {
                clearInterval(lobbyInt)
                lobbyInt = null
            }

            try {
                if (app.static) {
                    mp.gameId = id;
                    mp.peerId = id;
                    lobby.connectTo(id, true)
                } else {
                    const room = await joinRoom(GAMES.SET, id, lobby.id, myName.value)
                    mp.gameId = room.id;
                    mp.peerId = room.peer
                    lobby.connectTo(room.peer, true)
                }
                if (toastId === null) {
                    toastId = toast("trying to connect...", { timeout: false })
                    setTimeout(() => {
                        if (toastId !== null) {
                            toast.dismiss(toastId)
                            toastId = null
                        }
                    }, 5000)
                }
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
                sounds.play(SOUND.TRANSITION)
                toast.info(mp.players.get(id) + " joined the lobby")
                lobby.sendTo(id, "handshake", handshakeData())
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
            const isFirst = !mp.hosting && mp.players.size === 0
            // look for players who left
            mp.players.forEach((n, p) => {
                if (!data.find(d => d[0] === p)) {
                    toast.info(`${n} left the lobby`)
                }
            })
            // look for new players
            if (!isFirst) {
                data.forEach(d => {
                    if (d[0] === lobby.id) {
                        myNameDisplay.value = d[1]
                    } else if (!mp.players.has(d[0])) {
                        toast.info(`${d[1]} joined the lobby`)
                    }
                })
            }
            mp.players = new Map(data.filter(d => d[0] !== lobby.id))
        }
    }

    function handshakeData() {
        return {
            id: lobby.id,
            name: myName.value,
            dataset: app.ds,
            code: app.activeCode,
            difficulty: difficulty.value,
            players: getPlayers()
        }
    }

    function initMultiplayer() {

        reset()

        const savedName = Cookies.get("set-mp-name")
        setName(savedName ? savedName : app.activeUser.name)

        // create the "lobby"
        lobby = new Multiplayer(handshakeData)

        lobby.onConnectError(async (id) => {
            if (id === mp.peerId) {
                toast.error("could not connect to lobby")
                if (toastId !== null) {
                    toast.dismiss(toastId)
                    toastId = null
                }
                // await closeRoom(GAMES.SET, mp.gameId)
                leaveLobby(STATES.CONNECT)
                // mp.peerId = null;
                // mp.gameId = null;
                // state.value = STATES.CONNECT
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
                    if (toastId !== null) {
                        toast.dismiss(toastId)
                        toastId = null
                        toast.success("connected to lobby")
                    }
                    if (state.value === STATES.CONNECT) {
                        state.value = STATES.LOBBY
                        sounds.play(SOUND.TRANSITION)
                    }
                    difficulty.value = data.difficulty;
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

        lobby.onReceive("difficulty", diff => {
            if (!mp.hosting) {
                difficulty.value = diff
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

    watch(difficulty, function() {
        if (lobby.id && mp.hosting) {
            lobby.send("difficulty", difficulty.value)
        }
    })
    watch(props, reset, { deep: true })

    watch(numPlayers, function(newNum, oldNum) {
        if (mp.hosting && newNum === 1 && oldNum > 1) {
            setName(myName.value)
            state.value = STATES.LOBBY
            reset()
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
    display: flex;
    align-items: center;
    justify-content: center;
    align-content: start;
    flex-wrap: wrap;
}
</style>