// Utilities
import { defineStore } from 'pinia'
import { useApp } from './app';
import { capitalize } from '@/use/utility';
import Cookies from 'js-cookie';
import { schemeBlues, schemeGreens, schemeGreys, schemeOranges, schemePurples, schemeRdPu } from 'd3';

export const CTXT_IDS = Object.freeze({
    TAG_EDIT: 1,
    TAG_DEL: 2,
    TAG_ADD: 3,
    TAG_OBJECT: 4,

    TAG_EX: 5,
    TAG_SHOW_OBJ: 6,
    TAG_TOGGLE: 7,
    ITEM_TAG_OBJECT: 8,
    ITEM_SHOW: 9,

    EV_EDIT: 10,
    EV_DEL: 11,
    EV_ADD: 12,

    META_EDIT: 13,
    META_DEL: 14,
    META_ADD: 15,

    META_CAT_EDIT: 16,
    META_CAT_DEL: 17,
    META_CAT_ADD: 18,

    AGREE_ADD: 19,
    AGREE_DEL: 20,
})

export const CTXT_OPTIONS = Object.freeze({
    tag: [
        [
            { id: CTXT_IDS.TAG_EDIT, text: "edit tag", icon: "mdi-tag" },
            { id: CTXT_IDS.TAG_ADD, text: "add tag", icon: "mdi-plus" },
            { id: CTXT_IDS.TAG_DEL, text: "delete tag", icon: "mdi-close" },
        ],[
            { id: CTXT_IDS.TAG_OBJECT, text: "add objection", icon: "mdi-exclamation-thick" },
        ],[
            { id: CTXT_IDS.TAG_EX, text: "show tag examples", icon: "mdi-view-grid" },
            { id: CTXT_IDS.TAG_SHOW_OBJ, text: "show tag objections", icon: "mdi-exclamation" },
        ]
    ],
    tag_agree: [
        [
            { id: CTXT_IDS.AGREE_ADD, text: "add missing user tag(s)", icon: "mdi-plus" },
            { id: CTXT_IDS.AGREE_DEL, text: "remove user tag(s)", icon: "mdi-close" },

        ],[
            { id: CTXT_IDS.TAG_EDIT, text: "edit tag", icon: "mdi-tag" },
        ],[
            { id: CTXT_IDS.TAG_EX, text: "show tag examples", icon: "mdi-view-grid" },
            { id: CTXT_IDS.TAG_SHOW_OBJ, text: "show tag objections", icon: "mdi-exclamation" },
        ]
    ],
    items: [
        [
            { id: CTXT_IDS.ITEM_SHOW, text: "show item", icon: "mdi-cube-outline" },
        ],[
            { id: CTXT_IDS.ITEM_TAG_OBJECT, text: "add objection", icon: "mdi-exclamation-thick" },
            { id: CTXT_IDS.EV_ADD, text: "add evidence", icon: "mdi-plus" },
            { id: CTXT_IDS.META_ADD, text: "add meta item", icon: "mdi-plus" },
        ]
    ],
    items_tagged: [
        [
            { id: CTXT_IDS.TAG_EDIT, text: "edit tag", icon: "mdi-tag" },
            { id: CTXT_IDS.TAG_ADD, text: "add tag", icon: "mdi-plus" },
            { id: CTXT_IDS.TAG_DEL, text: "delete tag", icon: "mdi-close" },
        ],[
            { id: CTXT_IDS.ITEM_TAG_OBJECT, text: "add objection", icon: "mdi-exclamation-thick" },
            { id: CTXT_IDS.TAG_TOGGLE, text: "toggle tag", icon: "mdi-toggle-switch" },
        ],[
            { id: CTXT_IDS.TAG_EX, text: "show tag examples", icon: "mdi-view-grid" },
            { id: CTXT_IDS.TAG_SHOW_OBJ, text: "show tag objections", icon: "mdi-exclamation" },
        ],[
            { id: CTXT_IDS.EV_ADD, text: "add evidence", icon: "mdi-plus" },
            { id: CTXT_IDS.META_ADD, text: "add meta item", icon: "mdi-plus" },
        ]
    ],
    items_untagged: [
        [
            { id: CTXT_IDS.TAG_EDIT, text: "edit tag", icon: "mdi-tag" },
            { id: CTXT_IDS.TAG_ADD, text: "add tag", icon: "mdi-plus" },
            { id: CTXT_IDS.TAG_DEL, text: "delete tag", icon: "mdi-close" },
        ],[
            { id: CTXT_IDS.ITEM_TAG_OBJECT, text: "add objection", icon: "mdi-exclamation-thick" },
        ],[
            { id: CTXT_IDS.TAG_EX, text: "show tag examples", icon: "mdi-view-grid" },
            { id: CTXT_IDS.TAG_SHOW_OBJ, text: "show tag objections", icon: "mdi-exclamation" },
        ],[
            { id: CTXT_IDS.TAG_TOGGLE, text: "toggle tag", icon: "mdi-toggle-switch" },
        ]
    ],
    evidence: [[
        { id: CTXT_IDS.EV_EDIT, text: "edit evidence", icon: "mdi-image" },
        { id: CTXT_IDS.EV_DEL, text: "delete evidence", icon: "mdi-close" },
        { id: CTXT_IDS.META_ADD, text: "add meta item", icon: "mdi-plus" },
    ]],
    meta_items: [[
        { id: CTXT_IDS.META_EDIT, text: "edit meta item", icon: "mdi-lightbulb" },
        { id: CTXT_IDS.META_ADD, text: "add meta item", icon: "mdi-plus" },
        { id: CTXT_IDS.META_DEL, text: "delete meta item", icon: "mdi-close" },
    ]],
    meta_category: [[
        { id: CTXT_IDS.META_CAT_EDIT, text: "edit meta category", icon: "mdi-lightbulb-group" },
        { id: CTXT_IDS.META_CAT_ADD, text: "add meta category", icon: "mdi-plus" },
        { id: CTXT_IDS.META_CAT_DEL, text: "delete meta category", icon: "mdi-close" },
    ]],

})

export const useSettings = defineStore('settings', {
    state: () => ({
        pathSegments: [],
        inMainView: true,
        isLoading: false,
        askUserIdentity: false,
        lightMode: true,
        activeTab: __APP_START_PAGE__,
        showTable: true,
        showBarCodes: false,
        showScatter: false,
        showEvidenceTiles: false,
        showExtTiles: false,

        showNavTop: false,
        verticalLayout: false,

        addTagsView: "tree",
        expandNavDrawer: false,
        expandNav: {
            project: false,
            filters: false,
            account: false,
            settings: false,
            codes: false,
            transitions: false,
            components: false,
            stats: false
        },

        exSortBy: "evidence count",
        exSortHow: "dsc",

        treeLayout: "history",
        expandTransTools: false,
        transToolsFree: false,
        tagAssign: false,
        tagAssignMode: false,

        panelSide: "left",

        clickTarget: null,
        clickTargetId: null,
        clickLabel: null,
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

        barCodeNodeSize: 4,

        extCatTopOrder: [
            "meta",
            "mental load",
            "creation effort",
            "level of expression",
            "lifetime",
            "mechanics coupling",
            "why",
            "what",
            "how",
            "interaction",
            "encoding",
        ],
        extCatOrder: [
            "mental load",
            "creation effort",
            "level of expression",
            "lifetime",
            "mechanics coupling",
            "why",
            "what",
            "interaction",
            "encoding",
        ],
        clusterNames: ["quick access", "storage", "sensemaking", "communication", "other"],
        clusterOrder: [
            ["hotbar", "location guidance", "organizable inventory", "organizable windows"],
            ["templates", "screenshots", "notes"],
            ["knowledge map", "placeholders", "labeling", "command queue"],
            ["pings", "free expression"],
            ["misc"]
        ]
    }),

    getters: {
        tabNames: () => {
            const app = useApp()
            const meta = app.metaItemName ? app.metaItemName+"s" : "?"
            return {
                explore_meta: capitalize(meta),
                explore_tags: "Tags",
                explore_ev: "Evidence",
                transition: "Transition",
                agree: "Agreement",
                coding: "Coding",
                games: "Games",
                objections: "Objections"
            }
        },
        tabIcons: () => {
            return {
                explore_meta: "mdi-magnify",
                explore_tags: "mdi-tag-search",
                explore_ev: "mdi-image-search",
                transition: "mdi-transit-connection-horizontal",
                agree: "mdi-forum",
                coding: "mdi-tag-multiple",
                games: "mdi-controller",
                objections: "mdi-exclamation-thick"
            }
        },
        tabDesc: () => {
            const app = useApp()
            const meta = app.metaItemName ? app.metaItemName+"s" : "?"
            return {
                explore_meta: "explore "+meta,
                explore_tags: "explore tags",
                explore_ev: "explore evidence",
                transition: "create and analyze transitions",
                agree: "analyze and resolve inter-coder disagreement",
                coding: "where you do the coding",
                games: "validate your coding with games",
                objections: "list of all objections"
            }
        },
    },

    actions: {

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

        setRightClick(target, id, x, y, label=target, data=null, options=[]) {
            if (target === null || this.clickTarget === target && this.clickTargetId === id) {
                this.clickTarget = null;
                this.clickTargetId = null;
                this.clickData = null;
                this.clickLabel = null
            } else {
                this.clickX = x;
                this.clickY = y;
                this.clickOptions = options;
                this.clickData = data;
                this.clickLabel = label
                this.clickTarget = target;
                this.clickTargetId = id;
            }
        },

        setPanelSide(side) {
            this.panelSide = side;
            Cookies.set("panel-side", side, { expires: 365 })
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

        getClusterColor(name) {
            const idx = this.clusterNames.indexOf(name)
            switch (idx) {
                case 0: return schemeBlues[6][4]
                case 1: return schemeRdPu[6][4]
                case 2: return schemeGreens[6][4]
                case 3: return schemeOranges[6][4]
                case 4: return schemePurples[6][4]
                default: return schemeGreys[6][4]
            }
        },

        moveToTag(id) {
            this.focusTag = id;
            this.focusTime = Date.now()
        }
    }
})
