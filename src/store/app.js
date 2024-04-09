// Utilities
import DM from '@/use/data-manager';
import * as d3 from 'd3'
import { defineStore } from 'pinia'

export const useApp = defineStore('app', {
  state: () => ({
    initialized: false,
    showAllUsers: false,

    dataNeedsReload: {
      _all: null,
    },
    dataLoading: {
      _all: false
    },

    ds: null,
    datasets: [],

    users: [],
    userColorScale: d3.schemeTableau10,
    userColors: d3.scaleOrdinal(),

    activeUser: null,
    activeUserId: null,
    activeCode: null,
    codes: [],

    transitionCode: null,

    selectionTime: null,
    userTime: null
  }),

  getters: {
    dataset: state => state.ds ? state.datasets.find(d => d.id === state.ds) : null,
    code:  state => state.activeCode ? state.codes.find(d => d.id === state.activeCode) : null,
    currentCode: state => state.transitionCode ? state.transitionCode : state.activeCode
  },

  actions: {

    needsReload(name) {
      if (name) {
        if (Array.isArray(name)) {
          name.forEach(n => {
            this.dataNeedsReload[n] = Date.now();
            this.dataLoading[n] = true;
            console.debug("needs reload", n)
          })
        } else {
          this.dataNeedsReload[name] = Date.now();
          this.dataLoading[name] = true;
          console.debug("needs reload", name)
        }
      } else {
        this.dataNeedsReload._all = Date.now();
        this.dataLoading._all = true;
        console.debug("all needs reload")
      }
    },

    setReloaded(name) {
      if (name) {
        if (Array.isArray(name)) {
          name.forEach(n => {
            this.dataLoading[n] = false
            console.debug("finished loading", n)
          })
        } else {
          this.dataLoading[name] = false;
          console.debug("finished loading", name)
        }
      } else {
        this.dataLoading._all = false;
        console.debug("finished loading all")
      }
    },

    setDatasets(list) {
      this.datasets = list;
      if (list.length > 0) {
        this.setDataset(list[0].id)
      }
    },

    setDataset(id) {
      this.ds = id;
    },

    setUsers(users) {
      this.users = users;
      this.userColors
        .domain(users.map(d => d.id))
        .range(this.userColorScale)
      this.users.forEach(d => d.color = this.userColors(d.id))
      this.userTime = Date.now();

    },

    setActiveUser(id) {
      if (id !== this.activeUserId) {
        this.activeUserId = id;
        this.activeUser = this.users.find(d => d.id === id);
        this.userTime = Date.now();
      }
    },

    setUserVisibility(value) {
      this.showAllUsers = value;
      this.userTime = Date.now();
    },

    toggleUserVisibility() {
      this.setUserVisibility(!this.showAllUsers);
    },

    getDatasetName(id) {
      const ds = this.datasets.find(d => d.id === id)
      return ds ? ds.name : null;
    },

    getUserName(id) {
      const u = this.users.find(d => d.id === id);
      return u ? u.name : null;
    },

    getUserColor(id) {
      const u = this.users.find(d => d.id === id);
      return u ? u.color : "black";
    },

    setActiveCode(id) {
      this.activeCode = id;
      this.codes = DM.getData("codes", false);
    },

    setTransitionCode(id) {
      this.transitionCode = id;
    },

    getCodeName(id) {
      return this.codes.find(d => d.id === id).name
    },

    setInitialized() {
      this.initialized = true;
    },

    selectById(values) {
      DM.setFilter("games", "id", values);
      this.selectionTime = Date.now();
    },
    selectByTag(values) {
      if (!values || values.length === 0) {
        DM.removeFilter("tags", "id");
        DM.removeFilter("games", "tags");
      } else {
        DM.setFilter("tags", "id", values);
        const set = new Set(values);
        DM.setFilter("games", "tags", tags => {
          return set.has(-1) || tags && tags.some(d => set.has(d.tag_id) || d.path.some(p => set.has(p)))
        });
      }
      this.selectionTime = Date.now();
    },

    toggleSelectByTag(values) {
      if (!values || values.length === 0) {
        DM.removeFilter("tags", "id");
        DM.removeFilter("games", "tags");
      } else {
        DM.toggleFilter("tags", "id", values);
        const set = new Set(DM.getFilter("tags", "id"));
        if (set.size === 0) {
          DM.removeFilter("games", "tags")
        } else {
          DM.setFilter("games", "tags", tags => {
            return set.has(-1) || tags && tags.some(d => set.has(d.tag_id) || d.path.some(p => set.has(p)))
          });
        }
      }
      this.selectionTime = Date.now();
    },

    startCodeTransition() {
      DM.clearFilters();
      DM.setFilter("tags", "is_leaf", 1)
      DM.setFilter("tags_old", "is_leaf", 1)
      this.setUserVisibility(true);
    },

    cancelCodeTransition() {
      this.transitionCode = null;
      DM.clearFilters();
      DM.setFilter("tags", "is_leaf", 1)
      DM.setFilter("tags_old", "is_leaf", 1)
      this.setUserVisibility(false);
    },

  }
})
