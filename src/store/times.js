// Utilities
import { defineStore } from 'pinia'

export const useTimes = defineStore('times', {
    state: () => ({
        n_all: 0,
        n_coding: 0,
        n_transition: 0,
        n_exploration: 0,
        n_tagging: 0,

        n_datasets: 0,
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
        coding: 0,
        transition: 0,
        exploration: 0,
        tagging: 0,

        datasets: 0,
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
        }
    }

})
