import { randomChoice } from "@/use/random";
import { defineStore } from "pinia";
import { Howl, Howler } from 'howler';
import { group } from "d3";

const SOUNDFILES = [
    {
        name: "START",
        file: "level-up-191997.mp3",
        volume: 1,
    },{
        name: "PLOP",
        file: "happy-pop-2-185287.mp3",
        volume: 1.5
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
        volume: 0.25
    },{
        name: "OBJECTION",
        file: "objection-judge.mp3",
        volume: 0.25
    },{
        name: "OBJECTION",
        file: "objection-french.mp3",
        volume: 0.25
    },{
        name: "BING",
        file: "bing-298405.mp3",
        volume: 1
    },{
        name: "SOUND_ON",
        file: "ui-sound-on-270295.mp3",
        volume: 1
    },{
        name: "SOUND_OFF",
        file: "ui-sound-off-270300.mp3",
        volume: 2
    },{
        name: "DRAMATIC",
        file: "dramatic-ticking-clock-45736.mp3",
        volume: 0.75
    },{
        name: "CLICK_REVERB",
        file: "click-with-big-reverb-28848-01.mp3",
        volume: 0.5
    },{
        name: "MENU_MUSIC",
        file: "menu-music-251877.mp3",
        volume: 0.33,
        loop: true
    },{
        name: "OBACHT",
        file: "obacht.mp3",
        volume: 1
    }
]

export const SOUND = Object.freeze({
    START: [0],
    PLOP: [1],
    WIN: [2],
    WIN_MINI: [3],
    FAIL: [4],
    FAIL_MINI: [5],
    MEH: [6],
    TICK: [7],
    TRANSITION: [8],
    OBJECTION: [9, 10, 11],
    BING: [12],
    SOUND_ON: [13],
    SOUND_OFF: [14],
    DRAMATIC: [15],
    CLICK_REVERB: [16],
    MENU_MUSIC: [17],
    OBACHT: [18],
})

export const SOUNDNAMES = Object.keys(SOUND)
export const SOUNDIDS = Object.values(SOUND)

export const useSounds = defineStore('sounds', {
    state: () => ({
        sounds: new Map(),
        playing: new Map(),
        volume: 0.75,
        muted: false,
    }),

    actions: {

        loadSounds() {
            this.sounds.clear()
            SOUNDFILES.forEach((s, i) => {
                const a = new Howl({
                    src: [`sounds/${s.file}`],
                    volume: s.volume,
                    loop: s.loop ? s.loop : false
                })
                this.sounds.set(i, a)
            })
            this.setVolume(this.volume, false)
            this.setMuted(this.muted, false)
        },

        getVolumeIcon() {
            if (this.muted) {
                return "mdi-volume-mute"
            } else if (this.volume < 0.333) {
                return "mdi-volume-low"
            } else if (this.volume < 0.66) {
                return "mdi-volume-medium"
            }
            return "mdi-volume-high"
        },

        setMuted(value, play=true) {
            const m = value === true
            if (play) {
                Howler.mute(false)
                this.play(m ? SOUND.SOUND_OFF : SOUND.SOUND_ON, false)
                this.muted = m
                setTimeout(() => Howler.mute(m), 2000)
            } else {
                this.muted = m
                Howler.mute(this.muted)
            }
        },

        toggleMuted() {
            this.setMuted(!this.muted)
        },

        isPlaying(name) {
            return name.some(n => this.playing.has(n))
        },

        play(name, fade=true) {
            if (this.sounds.size === 0) this.loadSounds()
            if (this.muted) return
            const n = Array.isArray(name) ? randomChoice(name) : name[0];
            if (!this.sounds.has(n)) return
            const s = this.sounds.get(n)
            const id = s.play()
            if (fade) {
                this.fadeIn(s, id, SOUNDFILES[n].volume)
            }
            this.playing.set(n, id)
        },

        stop(name, fade=true) {
            if (this.sounds.size === 0) this.loadSounds()
            if (this.muted) return
            name.forEach(n => {
                const id = this.playing.get(n)
                if (id) {
                    const s = this.sounds.get(n)
                    if (fade) {
                        this.fadeOut(s, id, SOUNDFILES[n].volume)
                        this.playing.delete(n)
                    } else {
                        s.stop(id)
                    }
                }
            })
        },

        toggle(name) {
            if (this.sounds.size === 0) this.loadSounds()
            if (this.muted) return
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

        fadeIn(s, id, volume=1, duration=200) {
            s.fade(0, volume, duration, id)
        },

        fadeOut(s, id, volume=1, duration=200) {
            s.fade(volume, 0, duration, id)
            setTimeout(() => s.stop(id), duration)
        },

        stopAll() {
            Howler.stop()
        },

        fadeAll(duration=200) {
            if (this.sounds.size === 0) this.loadSounds()
            this.playing.forEach((id, n) => {
                const s = this.sounds.get(n)
                s.fade(SOUNDFILES[n].volume, 0, duration, id)
            })
            this.playing.clear()
            setTimeout(() => this.stopAll(), duration)
        },

        setVolume(volume, play=true) {
            this.volume = volume
            Howler.volume(volume)
            if (play) this.play(SOUND.BING)
        }

    }
})
