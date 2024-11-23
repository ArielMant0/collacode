// Utilities
import { defineStore } from 'pinia'

export const CTXT_OPTIONS = Object.freeze({
    tag: ["edit tag", "delete tag", "add tag"],
    evidence: ["edit evidence", "delete evidence"],
    evidence_add: ["add evidence"],
    externalization: ["edit externalization", "delete externalization"],
    externalization_add: ["add externalization"],
    ext_category: ["edit ext category", "delete ext category", "add ext category"],
})

export const ALL_ADD_OPTIONS = Object.keys(CTXT_OPTIONS)
    .reduce((all, d) => all.concat(d.endsWith("_add") ? CTXT_OPTIONS[d] : []), []);

export const ALL_GAME_OPTIONS = CTXT_OPTIONS.tag
    .concat(CTXT_OPTIONS.evidence_add)
    .concat(CTXT_OPTIONS.externalization_add)

export const ALL_OPTIONS = Object.values(CTXT_OPTIONS)
    .reduce((all, d) => all.concat(d), []);

export const useSettings = defineStore('settings', {
    state: () => ({
        activeTab: "coding",
        showTable: true,
        showBarCodes: false,
        showEvidenceTiles: false,
        showExtTiles: false,

        addTagsView: "tree",
        expandNavDrawer: false,
        showUsers: true,
        showActiveCode: true,
        showTransition: true,
        exSortBy: "evidence count",
        exSortHow: "dsc",
        treeLayout: "cluster",

        clickTarget: null,
        clickTargetId: null,
        clickData: null,
        clickOptions: [],
        clickX: 0,
        clickY: 0,

        treeHidden: new Set(),

        tableHeaders: {}
    }),

    actions: {

        setView(which) {
            this.addTagsView = which;
        },

        setHeaders(headers) {
            this.tableHeaders = {};
            headers.forEach(d => this.tableHeaders[d] = true)
        },

        hasHeader(header) {
            return this.tableHeaders[header] !== undefined
        },

        toggleHeader(header) {
            if (this.tableHeaders[header]) {
                this.tableHeaders[header] = false
            } else {
                this.tableHeaders[header] = true
            }
        },

        setRightClick(target, id, x, y, data=null, options=ALL_OPTIONS) {
            if (target === null || this.clickTarget === target && this.clickTargetId === id) {
                this.clickTarget = null;
                this.clickTargetId = null;
                this.clickData = null;
            } else {
                this.clickX = x;
                this.clickY = y;
                this.clickOptions = options;
                this.clickData = data;
                this.clickTarget = target;
                this.clickTargetId = id;
            }
        },

        toggleTreeHidden(id) {
            if (this.treeHidden.has(id)) {
                this.treeHidden.delete(id)
            } else {
                this.treeHidden.add(id)
            }
        }
    }
})
