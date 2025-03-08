<template>
    <div style="width: 100%;">
        <div class="d-flex justify-space-between align-center">
            <div class="d-flex align-center">
                <span>you: </span>
                <v-sheet class="ml-2 pa-2" rounded color="surface-light">
                    <span>{{ mp.peer ? mp.peer : '..' }}</span>
                    <v-btn
                        icon="mdi-content-copy"
                        size="small"
                        class="ml-1"
                        :disabled="!mp.peer"
                        density="compact"
                        variant="text"
                        @click="copyToClipboard(mp.peer)"/>
                </v-sheet>
            </div>
            <div class="d-flex align-center">
                <span>other player: </span>
                <v-sheet class="ml-2 pa-2" rounded color="surface-light">
                    <span>{{ mp.otherPeer ? mp.otherPeer : '..' }}</span>
                    <v-btn
                        icon="mdi-content-copy"
                        size="small"
                        class="ml-1"
                        :disabled="!mp.otherPeer"
                        density="compact"
                        variant="text"
                        @click="copyToClipboard(mp.otherPeer)"/>
                </v-sheet>
            </div>
        </div>

        <div v-if="state === STATES.CONNECT" class="d-flex align-center justify-center" style="height: 80vh;">
            <div class="d-flex justify-center align-center">
                <v-text-field v-model="mp.otherPeer"
                    label="Connect to another player"
                    placeholder="Peer Id"
                    density="compact"
                    style="min-width: 300px;"
                    hide-details
                    hide-spin-buttons
                    variant="outlined"/>
                <v-btn variant="tonal"
                    :disabled="!mp.otherPeer"
                    @click="connectToPeer"
                    :color="mp.otherPeer ? 'primary' : 'default'">
                    connect
                </v-btn>
            </div>
        </div>

        <div v-else-if="state === STATES.LOADING" class="d-flex align-center justify-center" style="height: 80vh;">
            <div class="game-loader"></div>
        </div>

        <div v-else-if="state === STATES.INGAME" style="width: 100%;" class="d-flex flex-column align-center mt-4">

            <div class="d-flex justify-space-between mt-4 mb-4">
                <v-sheet style="font-size: large;" class="pt-4 pb-4 pr-8 pl-8" rounded="sm">
                    You: {{ mp.peer ? gameData.points.get(mp.peer) : 0 }}
                </v-sheet>
                <v-sheet style="font-size: large;" class="pt-4 pb-4 pr-8 pl-8" rounded="sm">
                    Enemy: {{ mp.peer ? gameData.points.get(mp.otherPeer) : 0 }}
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

            <div v-if="gameData.points.get(mp.peer) > gameData.points.get(mp.otherPeer)" class="d-flex align-center justify-center">
                <v-icon
                    size="60"
                    class="mr-4"
                    icon="mdi-check-bold"
                    color="primary"/>
                <span>You won!</span>
            </div>
            <div v-else-if="gameData.points.get(mp.peer) < gameData.points.get(mp.otherPeer)" class="d-flex align-center justify-center">
                <v-icon
                    size="60"
                    class="mr-4"
                    icon="mdi-close-circle-outline"
                    color="error"/>
                <span>You lost :(</span>
            </div>
            <div v-else class="d-flex align-center justify-center">
                <v-icon
                    size="60"
                    class="mr-4"
                    icon="mdi-equal"
                    color="default"/>
                <span>It's a draw</span>
            </div>

            <div>Tag: {{ gameData.tag ? gameData.tag.name : '?' }}</div>

            <div>Your {{ capitalize(app.itemName+'s') }}</div>
            <div class="d-flex flex-wrap mb-4">
                <v-sheet v-for="item in myItems" :key="'me_'+item.id" class="pa-1 mr-1 mb-1" rounded="sm" :color="gameData.correct.has(item.id) ? 'primary' : 'error'">
                    <div class="text-dots text-caption" style="max-width: 100px;">{{ item.name }}</div>
                    <v-img
                        cover
                        :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                        :lazy-src="imgUrlS"
                        :width="100"
                        :height="50"/>
                </v-sheet>
            </div>

            <div>Enemy {{ capitalize(app.itemName+'s') }}</div>
            <div class="d-flex flex-wrap">
                <v-sheet v-for="item in enemyItems" :key="'en_'+item.id" class="pa-1 mr-1 mb-1" rounded="sm" :color="gameData.correct.has(item.id) ? 'primary' : 'error'">
                    <div class="text-dots text-caption" style="max-width: 100px;">{{ item.name }}</div>
                    <v-img
                        cover
                        :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                        :lazy-src="imgUrlS"
                        :width="100"
                        :height="50"/>
                </v-sheet>
            </div>

            <div class="d-flex align-center justify-center mt-8" style="margin-top: 200px;">
                <v-btn class="mr-1" size="x-large" color="error" @click="close">close</v-btn>
                <v-btn class="ml-1" size="x-large" color="primary" @click="startGame">play again</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { SOUND, useGames } from '@/store/games'
    import Peer from 'peerjs'
    import { ref, onMounted, reactive, computed } from 'vue'
    import { v4 as uuidv4 } from 'uuid';
    import { useElementSize } from '@vueuse/core';
    import DM from '@/use/data-manager';
    import Chance from 'chance';
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';

    import imgUrlS from '@/assets/__placeholder__s.png'
    import { useToast } from 'vue-toastification';
    import { capitalize } from '@/use/utility';

    const STATES = Object.freeze({
        START: 0,
        CONNECT: 1,
        LOADING: 2,
        INGAME: 3,
        END: 4
    })

    const props = defineProps({
        difficulty: {
            type: Number,
            required: true
        },
    })

    const emit = defineEmits(["end"])

    // stores
    const games = useGames()
    const app = useApp()
    const settings = useSettings()
    const toast = useToast()

    // elements
    const el = ref(null)
    const overlay = ref(null)

    const elSize = useElementSize(el)
    const imageWidth = computed(() => Math.max(80, Math.floor(elSize.width.value / 4) - 15))

    // difficulty settings
    const numItems = ref(9)

    // multiplayer related stuff
    const mp = reactive({
        peer: null,
        otherPeer: null,
        otherPos: [0, 0],
        otherHover: null,
        voting: new Map(),
        initiator: false
    })

    let PEER, THECONN;

    // game related stuff
    const state = ref(STATES.START)
    const items = ref([])
    const gameData = reactive({
        tag: null,
        taken: new Map(),
        points: new Map(),
        correct: new Set()
    })

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

    const myItems = computed(() => {
        return items.value.filter(d => {
            const t = gameData.taken.get(d.id)
            return t && t.id === mp.peer
        })
    })
    const enemyItems = computed(() => {
        return items.value.filter(d => {
            const t = gameData.taken.get(d.id)
            return t && t.id === mp.otherPeer
        })
    })


    function copyToClipboard(str) {
        navigator.clipboard.writeText(str)
    }
    function isTakenByMe(id) {
        return gameData.taken.get(id) === mp.peer
    }
    function takeItem(item) {
        if (!gameData.taken.has(item.id)) {
            sendMessage("take", { item: item.id, user: mp.peer })
        }
    }
    function confirmTaken(item, user, time) {
        gameData.taken.set(item, { id: user, time: time })
        if (numFound.value === numMatches.value) {
            stopGame()
        }
    }

    function startGame() {
        games.playSingle(SOUND.START)
        state.value = STATES.LOADING
        // reset these values
        clear()

        if (mp.initiator) {
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

            sendMessage("dataset", {
                tag: tid,
                items: items.value.map(d => d.id)
            })
        }
    }
    function stopGame() {
        state.value = STATES.END
    }

    function close() {
        reset()
        emit("end")
    }

    function clear() {
        items.value = []
        gameData.tag = null
        gameData.taken.clear()
        gameData.correct.clear()
        gameData.points.clear()
    }
    function reset() {
        mp.otherPeer = null
        mp.voting.clear()
    }

    function drawCursor() {
        if (mp.otherPeer) {
            const svg = d3.select(overlay.value)
            svg.selectAll("circle")
                .data([{ id: mp.otherPeer, x: mp.otherPos[0], y: mp.otherPos[1] }])
                .join("circle")
                .classed("cursor", true)
                .attr("cx", d => d.x * elSize.width.value)
                .attr("cy", d => d.y * elSize.height.value)
                .attr("r", 5)
                .attr("fill", "black")
        }
    }

    function onMove(event) {
        if (THECONN) {
            const [mx, my] = d3.pointer(event, el.value)
            sendMessage("cursor", [mx/elSize.width.value, my/elSize.height.value])
        }
    }

    function sendMessage(name, data, conn=THECONN) {
        conn.send({ type: name, data: data, time: Date.UTC() })
    }

    function handleMessage(msg, conn, src=null) {
        if (src) console.log(src, msg.type)
        switch(msg.type) {
            case "handshake":
                if (msg.data.id === mp.otherPeer || !THECONN) {
                    mp.otherPeer = msg.data.id
                    if (msg.data.dataset === app.ds && msg.data.code === app.activeCode) {
                        setVote("start", mp.peer)
                        sendMessage("start", mp.peer)
                    }
                }
            case "start":
                if (state.value !== STATES.INGAME && msg.data === mp.otherPeer) {
                    setVote("start", mp.otherPeer)
                    if (!hasVote("start", mp.peer)) {
                        setVote("start", mp.peer)
                        sendMessage("start", mp.peer)
                    }
                }
                break;
            case "start_game":
                if (state.value !== STATES.INGAME && msg.data === mp.otherPeer) {
                    setVote("start_game", mp.otherPeer)
                    if (!hasVote("start_game", mp.peer)) {
                        setVote("start_game", mp.peer)
                        sendMessage("start_game", mp.peer)
                    }
                }
                break;
            case "dataset": {
                    // get tag
                    gameData.tag = DM.getDataItem("tags", msg.data.tag)
                    // get matching items
                    const set = new Set(msg.data.items)
                    const tmp = DM.getDataBy("items", d => set.has(d.id))
                    tmp.sort((a, b) => msg.data.items.indexOf(a.id)-msg.data.items.indexOf(b.id))
                    items.value = tmp;
                    // save correct games
                    gameData.correct.clear()
                    tmp.forEach(d => {
                        if (d.allTags.find(t => t.id === msg.data.tag)) {
                            gameData.correct.add(d.id)
                        }
                    })
                    setVote("start_game", mp.peer)
                    sendMessage("dataset_confirm", {
                        tag: gameData.tag.id,
                        items: tmp.map(d => d.id)
                    })
                }
                break;
            case "dataset_confirm":
                if (mp.initiator) {
                    if (msg.data.tag === gameData.tag.id) {
                        if (items.value.every((d,i) => msg.data.items[i] === d.id)) {
                            setVote("start_game", mp.peer)
                            sendMessage("start_game", mp.peer)
                        } else {
                            console.error("items mismatch", msg.data.items, items.value)
                            toast.error("data mismatch", { position: POSITION.TOP_CENTER, timeout: 2000 })
                        }
                    } else {
                        console.error("tag mismatch", msg.data.tag, gameData.tag.id)
                        toast.error("data mismatch", { position: POSITION.TOP_CENTER, timeout: 2000 })
                    }
                }
                break;
            case "cursor":
                if (state.value === STATES.INGAME) {
                    mp.otherPos = msg.data;
                    drawCursor()
                }
                break;
            case "take":
                if (state.value === STATES.INGAME) {
                    const existing = gameData.taken.get(msg.data.item)
                    if (!existing || existing.time > msg.time) {
                        confirmTaken(msg.data.item, msg.data.user, msg.time)
                        const diff = gameData.correct.has(msg.data.item) ? 1 : -1
                        gameData.points.set(msg.data.user, gameData.points.get(msg.data.user)+diff)
                        sendMessage("take_confirm", { item: msg.data.item, user: msg.data.user, time: msg.time })
                    }
                }
                break;
            case "take_confirm":
                if (state.value === STATES.INGAME) {
                    confirmTaken(msg.data.item, msg.data.user, msg.data.time)
                    const diff = gameData.correct.has(msg.data.item) ? 1 : -1
                    gameData.points.set(msg.data.user, gameData.points.get(msg.data.user)+diff)
                }
                break;
        }
    }

    function connectToPeer(setInitiate=true) {
        if (mp.otherPeer && PEER) {
            THECONN = PEER.connect(mp.otherPeer)
            THECONN.on("open", () => {
                sendMessage(
                    "handshake",
                    {
                        id: mp.peer,
                        dataset: app.ds,
                        code: app.activeCode,
                        difficulty: props.difficulty
                    }
                )
                // setVote("start", mp.peer)
                // setVote("start", mp.otherPeer)
            });
            if (setInitiate) {
                mp.initiator = true;
            }
        }
    }

    function hasVote(name, id) {
        return mp.voting.has(name) && mp.voting.get(name).has(id)
    }
    function setVote(name, id) {
        if (mp.voting.has(name)) {
            const set = mp.voting.get(name)
            set.add(id)
            // TODO: do sth when both players agree
            if (set.size === 2) {
                switch (name) {
                    case "start":
                        if (state.value !== STATES.INGAME) {
                            startGame()
                        }
                        break;
                    case "start_game":
                        gameData.points.set(mp.peer, 0)
                        gameData.points.set(mp.otherPeer, 0)
                        state.value = STATES.INGAME
                        break;
                    case "end":
                        stopGame()
                        break;
                }
                mp.voting.delete(name)
            }
        } else {
            mp.voting.set(name, new Set([id]))
        }
    }
    function getPeerId() {

        const id = uuidv4()
        PEER = new Peer(id)
        mp.peer = id

        PEER.on("connection", conn => {
            if (!THECONN) {
                mp.otherPeer = conn.peer
                connectToPeer(false)
            }
            sendMessage(
                "handshake",
                {
                    id: mp.peer,
                    dataset: app.ds,
                    code: app.activeCode,
                    difficulty: props.difficulty
                },
            )
            conn.on("data", msg => handleMessage(msg, conn))
        })

        state.value = STATES.CONNECT
    }

    onMounted(() => {
        reset()
        getPeerId()
    })

</script>