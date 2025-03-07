import { defineStore } from "pinia";

const SOUNDFILES = [
    "level-up-191997.mp3",
    "happy-pop-2-185287.mp3",
    "success-1-6297.mp3",
    "failfare-86009.mp3",
    "weak-clapping-103333.mp3"
]

export const SOUND = Object.freeze({
    START: 0,
    PLOP: 1,
    WIN: 2,
    FAIL: 3,
    MEH: 4,
})
export const GAMES = Object.freeze({
    MATCHING: "Matching",
    GEOGUESSER: "Geo Guesser",
    WHOAMI: "Who Am I?"
})
export const GAMELIST = Object.keys(GAMES)

export const SOUNDNAMES = Object.values(SOUND)
export const SOUNDIDS = Object.values(SOUND)

function isSoundPlaying(s) {
    return s.currentTime > 0 && !s.paused
}

export const useGames = defineStore('games', {
    state: () => ({
        activeGame: null,
        sounds: new Map(),
    }),

    actions: {

        loadSounds() {
            this.sounds.clear()
            SOUNDIDS.forEach(i => this.sounds.set(i, new Audio(`sounds/${SOUNDFILES[i]}`)))
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
