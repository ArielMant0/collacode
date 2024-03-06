// Utilities
import DM from '@/use/data-manager';
import * as d3 from 'd3'
import { defineStore } from 'pinia'

export const useApp = defineStore('app', {
  state: () => ({
    initialized: false,
    needsDataReload: null,
    dataReloaded: null,

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

    needsReload() {
      this.needsDataReload = Date.now();
    },

    setReloaded() {
      this.dataReloaded = Date.now();
    },

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

    getUserName(id) {
      const u = this.users.find(d => d.id === id);
      return u ? u.name : null;
    },

    setActiveCode(id) {
      this.activeCode = id;
      this.codes = DM.getData("codes", false);
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
