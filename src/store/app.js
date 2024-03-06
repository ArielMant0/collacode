// Utilities
import DM from '@/use/data-manager';
import * as d3 from 'd3'
import { defineStore } from 'pinia'

export const useApp = defineStore('app', {
  state: () => ({
    initialized: false,
    ds: null,
    datasets: [],

    activeUser: null,
    users: [],
    userColorScale: d3.schemeTableau10,
    userColors: d3.scaleOrdinal(),

    activeCode: null,
    codes: [],

    selectionTime: null,
  }),

  getters: {
    dataset: state => state.ds ? state.datasets.find(d => d.id === state.ds) : null,
    code:  state => state.activeCode ? state.codes.find(d => d.id === state.activeCode) : null,
    activeUserId: state => state.activeUser ? state.activeUser.id : null,
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
    },

    setActiveUser(id) {
      this.activeUser = this.users.find(d => d.id === id);
    },

    setActiveCode(id) {
      this.activeCode = id;
      this.codes = DM.getData("codes", false);
      DM.setFilter("tags", "code_id", id);
      DM.setFilter("data_tags", "code_id", id);
      this.selectionTime = Date.now();
    },

    setInitialized() {
      this.initialized = true;
    },

    selectByAttr(attr, values) {
      DM.setFilter("raw", attr, values);
      this.selectionTime = Date.now();
    }

  }
})
