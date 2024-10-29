// Utilities
import { defineStore } from 'pinia'

export const useTimes = defineStore('times', {
    state: () => ({
        n_all: 0,
        n_tagging: 0,

        n_datasets: 0,
        n_users: 0,
        n_games: 0,
        n_codes: 0,
        n_tags: 0,
        n_tags_old: 0,
        n_datatags: 0,
        n_evidence: 0,
        n_code_transitions: 0,
        n_tag_assignments: 0,
        n_externalizations: 0,
        n_ext_categories: 0,
        n_ext_agreements: 0,

        all: 0,
        tagging: 0,

        datasets: 0,
        users: 0,
        games: 0,
        codes: 0,
        tags: 0,
        tags_old: 0,
        datatags: 0,
        evidence: 0,
        code_transitions: 0,
        tag_assignments: 0,
        externalizations: 0,
        ext_categories: 0,
        ext_agreements: 0,
    }),

    actions: {

        needsReload(key='all') {
            this['n_'+key] = Date.now();
        },

        reloaded(key) {
            this[key] = Date.now();
        },

        getTime(key) {
            switch(key) {
                case "tags": return Math.max(this.all, this.tagging, this.tags)
                case "tags_olds": return Math.max(this.all, this.tagging, this.tags_olds)
                case "datatags": return Math.max(this.all, this.tagging, this.datatags)
                default: return Math.max(this.all, this[key])
            }
        }
    }

})
