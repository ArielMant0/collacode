// Utilities
import { defineStore } from 'pinia'

export const useTimes = defineStore('times', {
    state: () => ({
        clipboard: 0,

        n_all: 0,
        n_tagging: 0,
        n_transitioning: 0,

        n_datasets: 0,
        n_users: 0,
        n_items: 0,
        n_items_finalized: 0,
        n_item_expertise: 0,
        n_codes: 0,
        n_tags: 0,
        n_tags_old: 0,
        n_datatags: 0,
        n_evidence: 0,
        n_code_transitions: 0,
        n_tag_assignments: 0,
        n_meta_items: 0,
        n_meta_groups: 0,
        n_meta_categories: 0,
        n_meta_agreements: 0,
        n_objections: 0,

        n_similarity: 0,
        n_game_scores: 0,

        all: 0,
        tagging: 0,
        transitioning: 0,

        datasets: 0,
        users: 0,
        items: 0,
        items_finalized: 0,
        item_expertise: 0,
        codes: 0,
        tags: 0,
        tags_old: 0,
        datatags: 0,
        evidence: 0,
        code_transitions: 0,
        tag_assignments: 0,
        meta_items: 0,
        meta_groups: 0,
        meta_categories: 0,
        meta_agreements: 0,
        objections: 0,

        similarity: 0,
        game_scores: 0,

        f_any: 0,

        f_items: 0,
        f_item_expertise: 0,
        f_codes: 0,
        f_tags: 0,
        f_tags_old: 0,
        f_datatags: 0,
        f_evidence: 0,
        f_code_transitions: 0,
        f_tag_assignments: 0,
        f_meta_items: 0,
        f_meta_groups: 0,
        f_meta_categories: 0,
        f_meta_agreements: 0,
        f_objections: 0,

        actions: {}
    }),

    actions: {

        needsReload(key='all') {
            this['n_'+key] = Date.now();
        },

        reloaded(key) {
            this[key] = Date.now();
            if (this.actions[key]) {
                this.actions[key].forEach(f => f())
                delete this.actions[key]
            }
        },

        filtered(key) {
            this['f_'+key] = Date.now();
            this.f_any = Date.now()
        },

        getTime(key) {
            switch(key) {
                case "tags": return Math.max(this.all, this.tagging, this.tags);
                case "tags_olds": return Math.max(this.all, this.tagging, this.tags_olds);
                case "datatags": return Math.max(this.all, this.tagging, this.datatags);
                default: return Math.max(this.all, this[key]);
            }
        },

        addAction(key, callback) {
            if (!this.actions[key]) this.actions[key] = []
            this.actions[key].push(callback)
        }
    }

})
