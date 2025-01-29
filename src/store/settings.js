// Utilities
import { defineStore } from 'pinia'
import { useApp } from './app';
import { capitalize } from '@/use/utility';
import Cookies from 'js-cookie';

export const CTXT_OPTIONS = Object.freeze({
    tag: ["edit tag", "delete tag", "add tag"],
    evidence: ["edit evidence", "delete evidence"],
    evidence_add: ["add evidence"],
    meta_items: ["edit meta item", "delete meta item"],
    meta_items_add: ["add meta item"],
    meta_category: ["edit meta category", "delete meta category", "add meta category"],
})

export const ALL_ADD_OPTIONS = Object.keys(CTXT_OPTIONS)
    .reduce((all, d) => all.concat(d.endsWith("_add") ? CTXT_OPTIONS[d] : []), []);

export const ALL_ITEM_OPTIONS = CTXT_OPTIONS.tag
    .concat(CTXT_OPTIONS.evidence_add)
    .concat(CTXT_OPTIONS.meta_items_add)

export const ALL_OPTIONS = Object.values(CTXT_OPTIONS)
    .reduce((all, d) => all.concat(d), []);

export const useSettings = defineStore('settings', {
    state: () => ({
        lightMode: true,
        activeTab: APP_START_PAGE,
        showTable: true,
        showBarCodes: false,
        showScatter: false,
        showEvidenceTiles: false,
        showExtTiles: false,

        addTagsView: "tree",
        expandNavDrawer: false,
        expandComponents: false,
        expandStats: false,
        expandCode: false,
        expandTransition: false,

        exSortBy: "evidence count",
        exSortHow: "dsc",

        treeLayout: "history",
        expandTransTools: false,
        transToolsFree: false,
        tagAssign: false,
        tagAssignMode: false,

        clickTarget: null,
        clickTargetId: null,
        clickData: null,
        clickOptions: [],
        clickX: 0,
        clickY: 0,

        treeHidden: new Set(),

        tableHeaders: {},

        focusTag: null,
        focusTime: null,

        transOld: -1,
        transNew: -1,

        extCatOrder: [
            "mental load",
            "creation effort",
            "level of expression",
            "lifetime",
            "interaction",
            "mechanics coupling",
            "why",
            "what",
            "encoding",
        ],
        clusterOrder: [
            ["hotbar", "location guidance", "organizable inventory", "organizable windows"],
            ["templates", "screenshots", "notes"],
            ["knowledge map", "placeholders", "labeling", "command queue"],
            ["pings", "free expression"],
            ["misc"]
        ]
    }),

    actions: {

        getTabName(tab) {
            const app = useApp()
            switch(tab) {
                case "explore_meta": return capitalize("Explore "+app.schemeMetaItemName+"s")
                case "explore_tags": return "Explore Tags"
                case "explore_ev": return "Explore Evidence"
                case "transition": return "Transition"
                case "agree": return "Agreement"
                default:
                case "coding": return "Coding"
            }
        },

        setView(which) {
            this.addTagsView = which;
        },

        setHeaders(headers) {
            this.tableHeaders = {};
            if (Array.isArray(headers)) {
                headers.forEach(d => this.tableHeaders[d] = true)
            } else {
                for (const h in headers) {
                    this.tableHeaders[h] = headers[h] === true
                }
            }
            Cookies.set("table-headers", JSON.stringify(this.tableHeaders), { expires: 365 })
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
            Cookies.set("table-headers", JSON.stringify(this.tableHeaders), { expires: 365 })
        },

        setRightClick(target, id, x, y, data=null, options=ALL_OPTIONS) {
            const app = useApp()
            if (app.static) return;

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
        },

        getExtCatValueOrder(dim, a, b) {
            switch (dim) {
                case "mechanics coupling":
                    if (a === b) return 0;
                    else if (a === "uncoupled") return -1
                    else if (a === "coupled to optional") return b === "uncoupled" ? 1 : -1;
                    return 1;
                case "interaction":
                    if (a === b) return 0;
                    else if (a === "free") return -1
                    else if (a === "object-related") return b === "free" ? 1 : -1;
                    return 1;
                case "lifetime":
                    if (a === b) return 0;
                    else if (a === "transient") return -1
                    else if (a === "action-based") return b === "transient" ? 1 : -1;
                    return 1;
                case "mental task load":
                case "creation effort":
                case "level of expression":
                    if (a === b) return 0;
                    else if (a === "low") return -1
                    else if (a === "medium") return b === "low" ? 1 : -1;
                    return 1;
                default:
                    if (a < b) { return -1; }
                    if (a > b) { return 1 }
                    return 0;
            }
        },

        moveToTag(id) {
            this.focusTag = id;
            this.focusTime = Date.now()
        }
    }
})
