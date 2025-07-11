import { defineStore } from "pinia";

export const DIFFICULTY = Object.freeze({
    EASY: 1,
    NORMAL: 2,
    HARD: 3
})
export const DIFF_COLOR = Object.freeze({
    EASY: "#47ad13",
    NORMAL: "#FFC107",
    HARD: "#d11706"
})

export const GAMES = Object.freeze({
    MATCHING: 1,
    WHEREAMI: 2,
    WHOAMI: 3,
    TRIVIA: 4,
    SET: 5,
    LINCOMB: 6,
})

export const GAME_ICON = Object.freeze({
    1: "cst:game-matching",
    2: "cst:game-where",
    3: "cst:game-who",
    4: "cst:game-trivia",
    5: "cst:game-set",
    6: "mdi-crowd",
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
    GREEN: "#078766",
    YELLOW: "#FFC107",
    RED: "#b61431",
}

export const GR_ICON = Object.freeze({
    WIN: "mdi-check-bold",
    DRAW: "mdi-approximately-equal",
    LOSS: "mdi-close-circle-outline",
})

export const GAMELIST = [
    {
        id: 2,
        name: "Where Am I?",
        multiplayer: false,
        desc: {
            1: ["<b>5 min</b> time limit", "<b>infinite</b> exclusions"],
            2: ["<b>3 min</b> time limit", "<b>infinite</b> exclusions"],
            3: ["<b>2 min</b> time limit", "<b>no</b> exclusions", "can only view items <b>once</b>"],
        }
    },{
        id: 3,
        name: "Who Am I?",
        multiplayer: false,
        desc: {
            1: ["up <b>20</b> items", "up to <b>10</b> exclusions", "<b>extra</b> sibling feedback"],
            2: ["up <b>24</b> items", "up to <b>5</b> exclusions"],
            3: ["up <b>32</b> items", "<b>no</b> exclusions", "<b>no</b> sibling feedback"],
        }
    },{
        id: 1,
        name: "Matching",
        multiplayer: false,
        desc: {
            1: ["<b>4</b> items", "<b>5 min</b> time limit", "<b>3</b> exclusions"],
            2: ["<b>5</b> items", "<b>3 min</b> time limit", "<b>1</b> exclusion"],
            3: ["<b>6</b> items", "<b>2 min</b> time limit", "<b>no</b> exclusions", "<b>no</b> tag descriptions"],
        }
    },{
        id: 4,
        name: "Trivia",
        multiplayer: false,
        desc: {
            1: ["<b>4</b> questions", "<b>4</b> answer options", "<b>40</b> sec per question"],
            2: ["<b>5</b> questions", "<b>4</b> answer options", "<b>30</b> sec per question"],
            3: ["<b>6</b> questions", "<b>6</b> answer options", "<b>20</b> sec per question", "<b>no</b> tag descriptions"],
        },
    },{
        id: 5,
        name: "Set",
        multiplayer: true,
        desc: {
            1: ["<b>~50%</b> matching items"],
            2: ["<b>~40%</b> matching items"],
            3: ["<b>~30%</b> matching items", "<b>no</b> tag descriptions"],
        }
    },{
        id: 6,
        name: "LinComb",
        multiplayer: false,
        desc: {
            1: ["<b>~50%</b> matching items"],
            2: ["<b>~40%</b> matching items"],
            3: ["<b>~30%</b> matching items", "<b>no</b> tag descriptions"],
        }
    }
]

export const useGames = defineStore('games', {
    state: () => ({
        activeGame: null,
        difficulty: DIFFICULTY.EASY,
        sounds: new Map(),
        volume: 1,
        themeColors: {
            primary: "#078766",
            secondary: "#0ad39f",
            background: "#FFFFFF",
            onBackground: "#000000",
            error: "#b61431"
        }
    }),

    actions: {

        setThemeColors(colors) {
            this.themeColors = colors
        },

        gameName(id) {
            const g = GAMELIST.find(d => d.id === id)
            return g ? g.name : null
        },

        resultColor(result) {
            if (typeof result === "boolean") {
                result = result ? GAME_RESULT.WIN : GAME_RESULT.LOSS
            }
            switch(result) {
                case GAME_RESULT.LOSS: return this.themeColors.error
                case GAME_RESULT.DRAW: return this.themeColors.onBackground
                case GAME_RESULT.WIN: return this.themeColors.primary
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
                    return "M18.9 9.2C18.1 10.1 16.6 11 15 11C13.5 11 12.6 10.5 11.8 10.1C11 9.8 10.2 9.3 8.9 9.3C7.7 9.3 6.6 10 6 10.6L5 9.1C5.9 8.2 7.3 7.2 8.9 7.2C10.4 7.2 11.3 7.8 12.1 8.1C12.9 8.4 13.7 9 15 9C16.2 9 17.3 8.2 17.9 7.6L18.9 9.2M19 14.1C18.1 15 16.7 16 15.1 16C13.6 16 12.7 15.5 11.9 15.1C11.1 14.8 10.3 14.2 9 14.2C7.8 14.2 6.7 15 6.1 15.6L5.1 14C6 13.1 7.4 12.1 9 12.1C10.5 12.1 11.4 12.6 12.2 13C13 13.3 13.8 13.8 15.1 13.8C16.3 13.8 17.4 13 18 12.4L19 14.1Z"
                case GAME_RESULT.WIN:
                    return "M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z"
            }
        },

        getMaxScore(game, difficulty) {
            switch(game) {
                case GAMES.MATCHING:
                case GAMES.TRIVIA: {
                    switch(difficulty) {
                        case DIFFICULTY.EASY: return 4
                        case DIFFICULTY.NORMAL: return 5
                        case DIFFICULTY.HARD: return 6
                    }
                }
                case GAMES.WHEREAMI: return 100
                case GAMES.WHOAMI: return 10
                case GAMES.SET: return NaN
                default: return 1
            }
        },

        getScoreDesc(game) {
            switch(game) {
                default:
                case GAMES.MATCHING:
                case GAMES.TRIVIA:
                case GAMES.SET: return "higher better"
                case GAMES.WHEREAMI:
                case GAMES.WHOAMI: return "lower better"
            }
        },
    }
})
