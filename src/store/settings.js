// Utilities
import { defineStore } from 'pinia'

const ALL_OPTIONS = ["edit tag", "add evidence", "add externalization"];

export const useSettings = defineStore('settings', {
    state: () => ({
        activeTab: "coding",
        addTagsView: "tree",
        expandNavDrawer: false,
        showUsers: false,
        showActiveCode: false,
        showTransition: false,
        showTagChips: true,
        exSortBy: "name",
        exSortHow: "asc",
        treeLayout: "cluster",

        rightClickTag: null,
        rightClickGame: null,
        rightClickOptions: [],
        rightClickX: 0,
        rightClickY: 0,

    }),

    actions: {

        setView(which) {
            this.addTagsView = which;
        },

        setRightClick(game_id, tag_id, x, y, options=ALL_OPTIONS) {
            if (this.rightClickGame === game_id && this.rightClickTag === tag_id) {
                this.rightClickTag = null;
                this.rightClickGame = null;
            } else {
                this.rightClickX = x;
                this.rightClickY = y;
                this.rightClickOptions = options;
                this.rightClickGame = game_id;
                this.rightClickTag = tag_id;
            }
        }
    }
})
