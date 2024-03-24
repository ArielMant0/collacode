// Utilities
import { defineStore } from 'pinia'

export const useSettings = defineStore('settings', {
  state: () => ({
    addTagsView: "list",
  }),

  actions: {
    setView(which) {
        this.addTagsView = which === 'list' || which === 'cards' ? which : this.addTagsView;
    }
  }
})
