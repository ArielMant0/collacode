// Utilities
import { defineStore } from 'pinia'

export const useSettings = defineStore('settings', {
  state: () => ({
    addTagsView: "list",
    expandNavDrawer: false,
    showUsers: false,
    showActiveCode: false,
    showTransitionCode: false,
    showTagChips: true,
    exSortBy: "name",
    exSortHow: "asc",
  }),

  actions: {
    setView(which) {
        this.addTagsView = which === 'list' || which === 'cards' ? which : this.addTagsView;
    }
  }
})
