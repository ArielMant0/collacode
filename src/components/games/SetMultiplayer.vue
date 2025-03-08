<template>
    <div style="width: 100%;">
        <div v-if="state === STATES.START" class="d-flex align-center justify-center" style="height: 80vh;">
            <v-btn size="x-large" color="primary" class="mt-4" @click="startGame">start</v-btn>
        </div>
        <div v-else class="d-flex justify-space-between align-center">
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

            <div style="width: 90%; height: 80vh; position: relative;">
                <div ref="el" style="height: 80vh; background-color: lightgrey;" @pointermove="onMove">

                </div>
                <svg ref="overlay" :width="elSize.width.value" :height="elSize.height.value" style="pointer-events: none; position: absolute; top: 0; left: 0;"></svg>
            </div>

        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { SOUND, useGames } from '@/store/games'
    import Peer from 'peerjs'
    import { computed, onMounted, reactive } from 'vue'
    import { v4 as uuidv4 } from 'uuid';
    import { useElementSize } from '@vueuse/core';

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

    // elements
    const el = ref(null)
    const overlay = ref(null)

    const elSize = useElementSize(el)

    // multiplayer related stuff
    const mp = reactive({
        peer: null,
        otherPeer: null,
        otherPos: [0, 0],
        voting: new Map()
    })


    let PEER, THECONN;

    // game related stuff
    const state = ref(STATES.START)
    const items = ref([])

    function copyToClipboard(str) {
        navigator.clipboard.writeText(str)
    }

    function startGame() {
        const starttime = Date.now()
        games.playSingle(SOUND.START)
        state.value = STATES.LOADING
        // reset these values
        clear()

        setTimeout(() => {
            state.value = STATES.INGAME
        }, Date.now() - starttime < 500 ? 1000 : 50)
    }
    function stopGame() {

    }

    function close() {
        reset()
        emit("end")
    }

    function clear() {}
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
            THECONN.send({ type: "cursor", data: [mx/elSize.width.value, my/elSize.height.value]})
        }
    }

    function handleMessage(msg, conn, src=null) {
        if (src) console.log(src, msg.type)
        switch(msg.type) {
            case "start":
                if (msg.data === mp.otherPeer || !mp.otherPeer) {
                    mp.otherPeer = msg.data
                    setVote("start", mp.otherPeer)
                    if (!hasVote("start", mp.peer)) {
                        // conn.send({ type: "start", data: mp.peer, time: Date.UTC() })
                        setVote("start", mp.peer)
                    }
                }
                break;
            case "cursor":
                if (state.value === STATES.INGAME) {
                    mp.otherPos = msg.data;
                    drawCursor()
                }
                break;

        }
    }

    function connectToPeer() {
        if (mp.otherPeer && PEER) {
            THECONN = PEER.connect(mp.otherPeer)
            THECONN.on("open", () => {
                THECONN.send({ type: "start", data: mp.peer, time: Date.UTC() })
                setVote("start", mp.peer)
                setVote("start", mp.otherPeer)
                // MPCONN.on("data", msg => handleMessage(msg, MPCONN, "mpconn"))
            });
            console.log("connectToPeer")
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
                        startGame();
                        break;
                    case "end":
                        stopGame()
                        break;
                    case "move":
                        // TODO: do move
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
            if (!mp.otherPeer) {
                mp.otherPeer = conn.peer
                connectToPeer()
            }
            conn.on("data", msg => handleMessage(msg, conn, "peerconn"))
        })

        state.value = STATES.CONNECT
    }

    onMounted(() => {
        reset()
        getPeerId()
    })

</script>