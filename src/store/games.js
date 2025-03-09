import { defineStore } from "pinia";

const SOUNDFILES = [
    "level-up-191997.mp3",
    "happy-pop-2-185287.mp3",
    "success-1-6297.mp3",
    "beep-6-96243.mp3",
    "failfare-86009.mp3",
    "error-8-206492.mp3",
    "weak-clapping-103333.mp3",
    "tick-single.mp3",
    "intro-sound-2-269294.mp3"
]
const SOUND_VOLUME = Object.freeze({
    START: 0.7,
    PLOP: 0.7,
    WIN: 0.7,
    WIN_MINI: 0.7,
    FAIL: 0.7,
    FAIL_MINI: 0.7,
    MEH: 0.7,
    TICK: 0.7,
    TRANSITION: 1
})

export const SOUND = Object.freeze({
    START: 0,
    PLOP: 1,
    WIN: 2,
    WIN_MINI: 3,
    FAIL: 4,
    FAIL_MINI: 5,
    MEH: 6,
    TICK: 7,
    TRANSITION: 8
})

export const DIFFICULTY = Object.freeze({
    EASY: 1,
    NORMAL: 2,
    HARD: 3
})
export const DIFF_COLOR = Object.freeze({
    EASY: "#47ad13",
    NORMAL: "#eba605",
    HARD: "#d11706"
})

export const GAMES = Object.freeze({
    MATCHING: 1,
    GEOGUESSER: 2,
    WHOAMI: 3,
    TRIVIA: 4,
    SET: 5
})

export const GAMELIST = [
    {
        id: 1,
        name: "Matching"
    },{
        id: 2,
        name: "Geo Guesser"
    },{
        id: 3,
        name: "Who Am I?"
    },{
        id: 4,
        name: "Trivia"
    },{
        id: 5,
        name: "Set (Multiplayer)"
    },
]

export const SOUNDNAMES = Object.values(SOUND)
export const SOUNDIDS = Object.values(SOUND)

function isSoundPlaying(s) {
    return s.currentTime > 0 && !s.paused
}

export const useGames = defineStore('games', {
    state: () => ({
        activeGame: null,
        difficulty: DIFFICULTY.EASY,
        sounds: new Map(),
        volume: 1
    }),

    actions: {

        gameName(id) {
            const g = GAMELIST.find(d => d.id === id)
            return g ? g.name : null
        },

        loadSounds() {
            this.sounds.clear()
            SOUNDIDS.forEach(i => {
                const a = new Audio(`sounds/${SOUNDFILES[i]}`)
                a.volume = this.volume * (SOUND_VOLUME[i] ? SOUND_VOLUME[i] : 1)
                this.sounds.set(i, a)
            })
        },

        isPlaying(name) {
            if (!this.sounds.has(name)) return false
            const s = this.sounds.get(name)
            return isSoundPlaying(s)
        },

        play(name) {
            if (!this.sounds.has(name)) return
            this.stop(name)
            this.sounds.get(name).play()
        },

        playSingle(name) {
            if (!this.sounds.has(name)) return
            SOUNDNAMES.forEach(n => this.stop(n))
            this.sounds.get(name).play()
        },

        togglePlay(name) {
            if (!this.sounds.has(name)) return
            const s = this.sounds.get(name)
            if (isSoundPlaying(s)) {
                s.pause()
            } else {
                s.play()
            }
        },

        stop(name) {
            if (!this.sounds.has(name) || !this.isPlaying(name)) return
            const s = this.sounds.get(name)
            s.pause()
            s.currentTime = 0;
        }

    }
})
