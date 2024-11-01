// Utilities
import { defineStore } from 'pinia'

const ALL_OPTIONS = ["edit tag", "delete tag", "add evidence", "add externalization"];

export const useSettings = defineStore('settings', {
    state: () => ({
        activeTab: "coding",
        addTagsView: "tree",
        expandNavDrawer: false,
        showUsers: true,
        showActiveCode: true,
        showTransition: true,
        exSortBy: "name",
        exSortHow: "asc",
        treeLayout: "cluster",

        rightClickEv: null,
        rightClickTag: null,
        rightClickGame: null,
        rightClickOptions: [],
        rightClickX: 0,
        rightClickY: 0,

        treeHidden: new Set()
    }),

    actions: {

        setView(which) {
            this.addTagsView = which;
        },

        setRightClick(game_id, tag_id, ev_id, x, y, options=ALL_OPTIONS) {
            if (this.rightClickGame === game_id && this.rightClickTag === tag_id) {
                this.rightClickTag = null;
                this.rightClickGame = null;
                this.rightClickEv = null;
            } else {
                this.rightClickX = x;
                this.rightClickY = y;
                this.rightClickOptions = options;
                this.rightClickGame = game_id;
                this.rightClickTag = tag_id;
                this.rightClickEv = ev_id;
            }
        },

        toggleTreeHidden(id) {
            if (this.treeHidden.has(id)) {
                this.treeHidden.delete(id)
            } else {
                this.treeHidden.add(id)
            }
        }
    }
})
