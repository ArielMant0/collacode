// Utilities
import * as d3 from 'd3'
import { defineStore } from 'pinia'

export const useApp = defineStore('app', {
  state: () => ({
    ds: null,
    datasets: [],

    users: [],
    userColorScale: d3.schemeTableau10,
    userColors: d3.scaleOrdinal()
  }),

  getters: {
    dataset: state => state.ds ? state.datasets.find(d => d.id === state.ds) : null,
  },

  actions: {
    setDatasets(list) {
      this.datasets = list;
      this.ds = list[0].id
    },

    setUsers(users) {
      this.users = users;
      this.userColors
        .domain(users.map(d => d.id))
        .range(this.userColorScale)
      this.users.forEach(d => d.color = this.userColors(d.id))
    }
  }
})
