import { defineStore } from "pinia";
import { useTheme } from "vuetify/lib/framework.mjs";

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

export const GAME_RESULT = Object.freeze({
    LOSS: 0,
    DRAW: 1,
    WIN: 2
})

export const GR_COLOR = {
    GREEN: "#238b45",
    YELLOW: "#f5d407",
    RED: "#e31a1c",
}

export const GR_ICON = Object.freeze({
    WIN: "mdi-check-bold",
    DRAW: "mdi-approximately-equal-box",
    LOSS: "mdi-close-circle-outline",
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

        resultColor(result) {
            const theme = useTheme()
            switch(result) {
                case GAME_RESULT.LOSS: return theme.current.value.colors.error
                case GAME_RESULT.DRAW: return theme.current.value.colors["on-background"]
                case GAME_RESULT.WIN: return theme.current.value.colors.primary
            }
        },

        resultIcon(result) {
            if (typeof result === "boolean") {
                result = result ? GAME_RESULT.WIN : GAME_RESULT.LOSS
            }
            switch(result) {
                case GAME_RESULT.LOSS: return GR_ICON.LOSS
                case GAME_RESULT.DRAW: return GR_ICON.DRAW
                case GAME_RESULT.WIN: return GR_ICON.WIN
            }
        },

        resultIconPath(result) {
            if (typeof result === "boolean") {
                result = result ? GAME_RESULT.WIN : GAME_RESULT.LOSS
            }
            switch(result) {
                case GAME_RESULT.LOSS:
                    return "M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2C6.47,2 2,6.47 2,12C2,17.53 6.47,22 12,22C17.53,22 22,17.53 22,12C22,6.47 17.53,2 12,2M14.59,8L12,10.59L9.41,8L8,9.41L10.59,12L8,14.59L9.41,16L12,13.41L14.59,16L16,14.59L13.41,12L16,9.41L14.59,8Z"
                case GAME_RESULT.DRAW:
                    return "M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3M9.3 8.2C10.6 8.2 11.4 8.7 12.1 9C12.7 9.3 13.4 9.7 14.5 9.7C15.5 9.7 16.5 9 17 8.5L17.8 9.8C17.1 10.6 15.8 11.4 14.4 11.4C13.1 11.4 12.3 10.9 11.7 10.6C11.1 10.3 10.3 9.9 9.2 9.9C8.2 9.9 7.2 10.6 6.7 11.1L6 9.8C6.7 9 8 8.2 9.3 8.2M14.6 15.8C13.3 15.8 12.5 15.3 11.8 15C11.2 14.7 10.4 14.3 9.3 14.3C8.3 14.3 7.3 15 6.8 15.5L6 14.1C6.7 13.3 8 12.5 9.3 12.5C10.6 12.5 11.4 13 12.1 13.3C12.7 13.6 13.4 14 14.6 14C15.6 14 16.6 13.3 17.1 12.8L17.9 14.1C17.3 15 16 15.8 14.6 15.8Z"
                case GAME_RESULT.WIN:
                    return "M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z"
            }
        }
    }
})
