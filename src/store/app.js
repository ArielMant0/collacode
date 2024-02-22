// Utilities
import * as d3 from 'd3'
import { defineStore } from 'pinia'

export const useApp = defineStore('app', {
  state: () => ({
    datasets: [],
    ds: null,

    userColorScale: d3.schemeTableau10,
    userColors: d3.scaleOrdinal()
  }),

  getters: {
    dataset: state => state.ds ? state.datasets.find(d => d.id === state.ds) : null,
    users: state => {
      if (state.ds) {
        return state.dataset.users.map(d => ({ name: d, color: state.userColors(d) }))
      }
      return []
    },
  },

  actions: {
    setDatasets(list) {
      this.datasets = list;
      this.ds = list[0].id
      this.userColors.domain(list[0].users).range(this.userColorScale)
    }
  }
})
