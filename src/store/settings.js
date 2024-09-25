// Utilities
import { defineStore } from 'pinia'

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
    }),

    actions: {
        setView(which) {
            this.addTagsView = which;
        }
    }
})
