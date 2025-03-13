import { randomChoice } from "@/use/random";
import { defineStore } from "pinia";
import { Howl, Howler } from 'howler';

const SOUNDFILES = [
    {
        name: "START",
        file: "level-up-191997.mp3",
        volume: 1,
    },{
        name: "PLOP",
        file: "happy-pop-2-185287.mp3",
        volume: 1
    },{
        name: "WIN",
        file: "success-1-6297.mp3",
        volume: 0.75
    },{
        name: "WIN_MINI",
        file: "beep-6-96243.mp3",
        volume: 1
    },{
        name: "FAIL",
        file: "failfare-86009.mp3",
        volume: 0.75
    },{
        name: "FAIL_MINI",
        file: "error-8-206492.mp3",
        volume: 1
    },{
        name: "MEH",
        file: "weak-clapping-103333.mp3",
        volume: 0.75
    },{
        name: "TICK",
        file: "tick-single.mp3",
        volume: 0.75
    },{
        name: "TRANSITION",
        file: "intro-sound-2-269294.mp3",
        volume: 1
    },{
        name: "OBJECTION",
        file: "objection-english.mp3",
        volume: 0.5
    },{
        name: "OBJECTION",
        file: "objection-judge.mp3",
        volume: 0.5
    },{
        name: "OBJECTION",
        file: "objection-french.mp3",
        volume: 0.25
    }
]

export const SOUND = Object.freeze({
    START: 0,
    PLOP: 1,
    WIN: 2,
    WIN_MINI: 3,
    FAIL: 4,
    FAIL_MINI: 5,
    MEH: 6,
    TICK: 7,
    TRANSITION: 8,
    OBJECTION: [9, 10, 11]
})

export const SOUNDNAMES = Object.keys(SOUND)
export const SOUNDIDS = Object.values(SOUND)

export const useSounds = defineStore('sounds', {
    state: () => ({
        sounds: new Map(),
        playing: new Map(),
        volume: 0.75
    }),

    actions: {

        loadSounds() {
            this.sounds.clear()
            this.setVolume(this.volume)
            SOUNDFILES.forEach((s, i) => {
                const a = new Howl({
                    src: [`sounds/${s.file}`],
                    volume: s.volume
                })
                a.on("fade", id => {
                    if (a.volume(id) <= 0.0001) {
                        a.stop(id)
                    }
                })
                this.sounds.set(i, a)
            })
        },

        isPlaying(name) {
            name = Array.isArray(name) ? name : [name];
            return name.some(n => this.playing.has(n))
        },

        play(name) {
            const n = Array.isArray(name) ? randomChoice(name) : name;
            if (!this.sounds.has(n)) return
            const s = this.sounds.get(n)
            const id = s.play()
            s.fade(0, SOUNDFILES[n].volume, 500, id)
            this.playing.set(n, id)
        },

        stop(name) {
            name = Array.isArray(name) ? name : [name];
            name.forEach(n => {
                const id = this.playing.get(n)
                if (id) {
                    const s = this.sounds.get(n)
                    s.fade(SOUNDFILES[n].volume, 0, 500, id)
                    this.playing.delete(n)
                }
            })
        },

        toggle(name) {
            name = Array.isArray(name) ? name : [name];
            name.forEach(n => {
                const id = this.playing.get(n)
                if (id) {
                    const s = this.sounds.get(n)
                    if (s.playing(id)) {
                        s.pause(id)
                    } else {
                        s.play(id)
                    }
                }
            })
        },

        stopAll() {
            Howler.stop()
        },

        fadeAll(duration=500) {
            this.playing.forEach((id, n) => {
                const s = this.sounds.get(n)
                s.fade(SOUNDFILES[n].volume, 0, duration, id)
            })
            this.playing.clear()
        },

        setVolume(volume) {
            this.volume = volume
            Howler.volume(volume)
        }

    }
})
