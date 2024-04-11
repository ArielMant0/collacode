// Utilities
import { defineStore } from 'pinia'

export const useSettings = defineStore('settings', {
  state: () => ({
    addTagsView: "list",
    showUsers: true,
    showActiveCode: true,
    showTransitionCode: true,
    showTagChips: true,
  }),

  actions: {
    setView(which) {
        this.addTagsView = which === 'list' || which === 'cards' ? which : this.addTagsView;
    }
  }
})
