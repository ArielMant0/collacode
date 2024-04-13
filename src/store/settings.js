// Utilities
import { defineStore } from 'pinia'

export const useSettings = defineStore('settings', {
  state: () => ({
    addTagsView: "list",
    expandNavDrawer: true,
    showUsers: true,
    showActiveCode: true,
    showTransitionCode: true,
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
