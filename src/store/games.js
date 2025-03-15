import { defineStore } from "pinia";

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

export const STATES = Object.freeze({
    START: 0,
    LOADING: 1,
    EXCLUDE: 2,
    INGAME: 3,
    END: 4,
    CONNECT: 5,
    LOBBY: 6,
})

export const GAMELIST = [
    {
        id: 1,
        name: "Matching",
        multiplayer: false
    },{
        id: 2,
        name: "Geo Guesser",
        multiplayer: false
    },{
        id: 3,
        name: "Who Am I?",
        multiplayer: false
    },{
        id: 4,
        name: "Trivia",
        multiplayer: false
    },{
        id: 5,
        name: "Set",
        multiplayer: true
    }
]

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
    }
})
