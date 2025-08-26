// Utilities
import DM from '@/use/data-manager';
import { FILTER_TYPES } from '@/use/filters';
import { capitalize } from '@/use/utility';
import { generateColor, generateColorRGB } from '@marko19907/string-to-color';
import Cookies from 'js-cookie';
import { defineStore } from 'pinia'
import { useTheme } from 'vuetify/lib/framework.mjs';

export const APP_URLS = Object.freeze({
    TEASER: __URL_TEASER__,
    EVIDENCE: __URL_EVIDENCE__,
    DATA: __URL_STATIC_DATA__,
})

export const OBJECTION_ACTIONS = Object.freeze({
    DISCUSS: 0,
    ADD: 1,
    REMOVE: 2
})

export const EVIDENCE_TYPE = Object.freeze({
    POSITIVE: 1,
    NEGATIVE: 2
})

export function getActionColor(action) {
    const theme = useTheme()
    switch(action) {
        case OBJECTION_ACTIONS.DISCUSS:
            return theme.current.value.colors.info
        case OBJECTION_ACTIONS.ADD:
            return theme.current.value.colors.primary
        case OBJECTION_ACTIONS.REMOVE:
            return theme.current.value.colors.error
    }
}

export function getActionName(action) {
    switch(action) {
        case OBJECTION_ACTIONS.DISCUSS: return "discuss"
        case OBJECTION_ACTIONS.ADD: return "add"
        case OBJECTION_ACTIONS.REMOVE: return "remove"
    }
}

export const OBJECTION_STATUS = Object.freeze({
    OPEN: 1,
    CLOSED_APPROVE: 2,
    CLOSED_DENY: 3,
})

export function getActionIcon(action) {
    switch(action) {
        case OBJECTION_ACTIONS.DISCUSS:
            return "mdi-forum"
        case OBJECTION_ACTIONS.ADD:
            return "mdi-plus-circle"
        case OBJECTION_ACTIONS.REMOVE:
            return "mdi-minus-circle"
    }
}

export function getObjectionStatusName(status) {
    switch(status) {
        case OBJECTION_STATUS.OPEN:
            return "open"
        case OBJECTION_STATUS.CLOSED_APPROVE:
            return "approved"
        case OBJECTION_STATUS.CLOSED_DENY:
            return "denied"
    }
}

export function getObjectionStatusIcon(status) {
    switch(status) {
        case OBJECTION_STATUS.OPEN:
            return "mdi-lock-open"
        case OBJECTION_STATUS.CLOSED_APPROVE:
        case OBJECTION_STATUS.CLOSED_DENY:
            return "mdi-lock"
    }
}

export function getObjectionStatusColor(status) {
    const theme = useTheme()
    switch(status) {
        case OBJECTION_STATUS.OPEN:
            return theme.current.value.colors['on-background']
        case OBJECTION_STATUS.CLOSED_APPROVE:
            return theme.current.value.colors.primary
        case OBJECTION_STATUS.CLOSED_DENY:
            return theme.current.value.colors.error
    }
}


export function getEvidenceTypeColor(type) {
    const theme = useTheme()
    switch(type) {
        case EVIDENCE_TYPE.POSITIVE:
            return theme.current.value.colors.primary
        case EVIDENCE_TYPE.NEGATIVE:
            return theme.current.value.colors.error
    }
}

export const GUEST_USER = Object.freeze({
    name: "guest",
    id: -1,
    role: "guest",
    short: "gst",
    color: "grey",
    guid: null,
    warnings: 0
})

export const useApp = defineStore('app', {
    state: () => ({
        static: __APP_STATIC__,
        anonymous: __APP_ANONYMOUS__,
        initialized: false,
        showAllUsers: false,
        fetchUpdateTime: 0,
        updateItemsTime: 0,
        noUpdate: false,

        ds: null,
        dataset: null,
        datasets: [],

        globalUsers: [],
        users: [],
        usersCanEdit: [],
        userColors: {},

        activeUserId: null,
        activeUser: null,
        allowEdit: false,
        warningsEnabled: false,

        crowdFilter: true,

        useActive: true,

        activeCode: null,
        activeTransition: null,
        transitionData: null,

        codes: [],
        transitions: [],

        userTime: null,

        actionQueue: [],

        showGame: null,
        showGameObj: null,
        showGameQueue: [],

        addTag: null,
        addTagObj: null,
        addTagP: null,

        addObj: null,
        addObjTag: null,
        addObjItem: null,
        addObjType: null,

        editTag: null,
        editTagObj: null,
        delTag: null,
        delTagObj: null,

        showTagEx: null,
        showTagObj: null,
        showTagObjItem: null,

        addEv: null,
        addEvObj: null,
        addEvTag: null,
        addEvImg: null,
        addEvType: null,

        delEv: null,
        delEvObj: null,

        addExt: null,
        addExtObj: null,
        addExtTag: null,
        addExtEv: null,
        addExtGroup: null,

        delExt: null,
        delExtObj: null,

        addExtCat: null,
        addExtCatP: null,

        delExtCat: null,
        delExtCatObj: null,

        showEv: null,
        showEvObj: null,
        showEvList: null,
        showEvIdx: null,

        showObjection: null,
        showObjectionObj: null,

        showExt: null,
        showExtObj: null,

        showExtCat: null,
        showExtCatObj: null,

        showExtGroup: null,
        showExtGroupObj: null,
        showExtGroupExt: null
    }),

    getters: {
        isAdmin: state => state.activeUser !== null ? state.activeUser.role === "admin" : false,
        schema: state => state.dataset ? state.dataset.schema : null,
        itemColumns: state => state.schema ? state.schema.columns : [],
        itemName: state => state.dataset ? state.dataset.item_name : "Item",
        itemNameCaptial: state => capitalize(state.itemName),
        metaItemName: state => state.dataset ? state.dataset.meta_item_name : "Meta Item",
        metaItemNameCaptial: state => capitalize(state.metaItemName),

        hasMetaItems: state => state.dataset ?
            state.dataset.meta_item_name !== null && state.dataset.meta_item_name.length > 0 :
            false,
        code:  state => state.activeCode ? state.codes.find(d => d.id === state.activeCode) : null,
        newCode: state => state.transitionData ? state.transitionData.new_code : null,
        oldCode: state => state.transitionData ? state.transitionData.old_code : null,
        currentCode: state => state.activeCode
    },

    actions: {

        fetchUpdate() {
            this.fetchUpdateTime = Date.now()
        },

        setCrowdFilter(value) {
            this.crowdFilter = value === true
            if (this.crowdFilter) {
                this.selectByItemValue("crowdRobust", "crowdRobust", true)
                if (this.showAllUsers && this.allowEdit) {
                    this.setUserVisibility(false)
                }
            } else {
                this.selectByItemValue("crowdRobust", "crowdRobust", null)
            }
        },

        updateItems() {
            this.updateItemsTime = Date.now()
        },

        setDatasets(list) {
            this.datasets = list;
        },

        setDataset(id) {
            const obj = this.datasets.find(d => d.id === id)
            this.dataset = obj !== undefined ? obj : null
            this.ds = id;
        },

        setCodes(codes) {
            this.codes = codes;
        },

        setGlobalUsers(users) {
            this.globalUsers = users;
            this.userColors = {}
            const colorOptions = { saturation: 70, lightness: 50 }
            this.globalUsers.forEach((d, i) => {
                if (d.id > 0) {
                    // const c1 = color(generateColor(d.name, colorOptions).replaceAll(/[\n\s]/gi, ""))
                    // const c2 = color(generateSecondaryColor(d.name, colorOptions).replaceAll(/[\n\s]/gi, ""))
                    // console.log(c1, c2, generateColor(d.name, colorOptions).replaceAll(/[\n\s]/gi, ""))
                    // let minSim1 = Number.MAX_VALUE, minSim2 = Number.MAX_VALUE
                    // const rgb1 = [c1.r, c1.g, c1.b]
                    // const rgb2 = [c2.r, c2.g, c2.b]
                    // for (let j = 0; j < i; ++j) {
                    //     const tmp = color(this.globalUsers[j].color)
                    //     const rgbTmp = [tmp.r, tmp.g, tmp.b]
                    //     const d1 = deltaE(rgb1, rgbTmp)
                    //     if (d1 < minSim1) {
                    //         minSim1 = d1
                    //     }
                    //     const d2 = deltaE(rgb2, rgbTmp)
                    //     if (d2 < minSim1) {
                    //         minSim1 = d2
                    //     }
                    // }
                    // this.userColors[d.id] = minSim1 < minSim2 ? c2.toString() : c1.toString()
                    this.userColors[d.id] = generateColorRGB(d.name, colorOptions)
                    d.color = this.userColors[d.id]
                } else {
                    d.color = "grey"
                }
            })
        },

        setUsers(users) {
            this.users = users
            this.usersCanEdit = users.filter(d => d.id > 0 && d.role !== "guest")
            this.users.forEach(d => d.color = this.getUserColor(d.id))

            if (this.activeUser) {
                this.setActiveUser(this.activeUserId)
            } else {
                this.userTime = Date.now();
            }
        },

        setActiveUser(id) {
            const usr = this.globalUsers.find(d => d.id === id)
            this.activeUser = !usr || id === null || id < 0 ? GUEST_USER : usr
            if (!this.activeUser || this.activeUser.id < 0 || this.activeUser.role === "guest") {
                this.showAllUsers = true
                this.allowEdit = false
            } else {
                this.allowEdit = this.activeUser.id > 0 && this.activeUser.role !== "guest"
                this.showAllUsers = !this.allowEdit
            }
            const prjUser = this.users.find(d => d.id === id)
            this.warningsEnabled = prjUser && prjUser.warnings > 0 && this.activeUser.role !== "guest"
            this.activeUserId = this.activeUser ? this.activeUser.id : null;
            this.userTime = Date.now();
        },

        setUserVisibility(value) {
            if (value === true || this.activeUser.id > 0 && this.activeUser.role !== "guest") {
                this.showAllUsers = value;
                this.userTime = Date.now();
            }
        },

        toggleUserVisibility() {
            this.setUserVisibility(!this.showAllUsers);
        },

        getDatasetName(id) {
            const ds = this.datasets.find(d => d.id === id)
            return ds ? ds.name : null;
        },

        getUser(id) {
            const u = this.globalUsers.find(d => d.id === id);
            return u ? u : null
        },

        hasUserName(name) {
            return this.globalUsers.find(d => d.name === name) !== undefined
        },

        getUserName(id) {
            const u = this.globalUsers.find(d => d.id === id);
            return u ? u.name : GUEST_USER.name
        },

        getUserShort(id) {
            const u = this.globalUsers.find(d => d.id === id);
            return u ? u.short : GUEST_USER.short
        },

        getUserColor(id) {
            const u = this.globalUsers.find(d => d.id === id);
            return u ? u.color : GUEST_USER.color
        },

        setActiveCode(id) {
            this.activeCode = id;
            Cookies.set("code_id", id, { expires: 365 })
            const tOld = this.transitions.find(d => d.old_code === id)
            const tNew = this.transitions.find(d => d.new_code === id)
            if (tNew) {
                this.setActiveTransition(tNew.id)
            } else if (tOld) {
                this.setActiveTransition(tOld.id)
            }
        },

        setTransitions(list) {
            this.transitions = list;
            if (this.activeTransition !== null) {
                this.setActiveTransition(this.activeTransition)
            }
        },

        setActiveTransition(id) {
            this.transitionData = id ? this.transitions.find(d => d.id === id) : null;
            this.activeTransition = this.transitionData !== null ? id : null;
            if (this.transitionData) {
                if (this.activeCode !== this.transitionData.old_code &&
                    this.activeCode !== this.transitionData.new_code
                ) {
                    this.setActiveCode(this.transitionData.new_code)
                }
            }
            Cookies.set("trans_id", this.activeTransition, { expires: 365 })
        },

        getCodeName(id) {
            const code = this.codes.find(d => d.id === id)
            return code ? code.name : "?"
        },

        setInitialized() {
            this.initialized = true;
        },

        resetSelections() {
            DM.clearFilters()
            this.setCrowdFilter(this.crowdFilter)
        },

        selectById(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("items");
                DM.removeFilter("meta_items");
            } else {
                DM.setFilter("items", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter("meta_items", "item_id", values, FILTER_TYPES.SET_OR);
            }
        },
        toggleSelectById(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("items");
                DM.removeFilter("meta_items");
            } else {
                DM.toggleFilter("items", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter("meta_items", "item_id", DM.getSelectedIds("items"), FILTER_TYPES.SET_OR);
            }
        },
        selectByItemValue(attr, access, values=null, filterType=FILTER_TYPES.SET_OR) {
            if (values === null || Array.isArray(values) && values.length === 0) {
                DM.removeFilter("items");
                DM.removeFilter("meta_items");
            } else {
                DM.setFilter("items", attr, values, filterType, access);
                DM.setFilter(
                    "meta_items", "item_id",
                    DM.getIds("items"),
                    FILTER_TYPES.SET_OR
                );
            }
        },
        toggleSelectByItemValue(attr, access, values=null, filterType=FILTER_TYPES.SET_OR) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("items");
                DM.removeFilter("meta_items");
            } else {
                DM.toggleFilter("items", attr, values, filterType, access);
                DM.setFilter(
                    "meta_items", "item_id",
                    DM.getIds("items"),
                    FILTER_TYPES.SET_OR
                );
            }
        },

        selectByTag(values=null, filterType=FILTER_TYPES.SET_OR) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("tags", "id");
                DM.removeFilter("items", "tags");
                DM.removeFilter("meta_items", "item_id");
                DM.removeFilter("objections", "tag_id");
            } else {
                DM.setFilter("tags", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter(
                    "items", "tags",
                    values,
                    filterType,
                    d => d.allTags.map(d => [d.id].concat(d.path)).flat()
                );
                DM.setFilter(
                    "meta_items", "item_id",
                    DM.getIds("items"),
                    FILTER_TYPES.SET_OR
                );
                DM.setFilter(
                    "objections", "tag_id",
                    set,
                    FILTER_TYPES.SET_OR
                );
            }
        },
        toggleSelectByTag(values=null, filterType=FILTER_TYPES.SET_OR) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("tags", "id");
                DM.removeFilter("items", "tags");
                DM.removeFilter("meta_items", "item_id");
                DM.removeFilter("objections", "tag_id");
            } else {
                DM.toggleFilter("tags", "id", values, FILTER_TYPES.SET_OR);
                const set = DM.getIds("tags")
                if (set.size === 0) {
                    DM.removeFilter("items", "tags")
                    DM.removeFilter("meta_items", "item_id");
                    DM.removeFilter("objections", "tag_id");
                } else {
                    DM.setFilter(
                        "items", "tags",
                        set,
                        filterType,
                        d => d.allTags.map(d => [d.id].concat(d.path)).flat()
                    );
                    DM.setFilter(
                        "meta_items", "item_id",
                        DM.getIds("items"),
                        FILTER_TYPES.SET_OR
                    );
                    DM.setFilter(
                        "objections", "tag_id",
                        set,
                        FILTER_TYPES.SET_OR
                    );
                }
            }
        },
        selectByExternalization(values=null) {
            if (values === null || Array.isArray(values) && values.length === 0) {
                DM.removeFilter("meta_items");
                DM.removeFilter("items");
            } else {
                DM.setFilter("meta_items", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter(
                    "items", "metas",
                    values,
                    FILTER_TYPES.SET_OR,
                    d => d.metas.map(d => d.id)
                );
            }
        },
        toggleSelectByExternalization(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("meta_items");
                DM.removeFilter("items");
            } else {
                DM.toggleFilter("meta_items", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter(
                    "items", "metas",
                    DM.getIds("meta_items"),
                    FILTER_TYPES.SET_OR,
                    d => d.metas.map(d => d.id)
                );
            }
        },

        selectByExtValue(attr, access, values=null, filterType=FILTER_TYPES.SET_OR) {
            if (values === null || Array.isArray(values) && values.length === 0) {
                DM.removeFilter("meta_items");
                DM.removeFilter("items");
            } else {
                DM.setFilter("meta_items", attr, values, filterType, access);
                DM.setFilter(
                    "items", "metas",
                    DM.getIds("meta_items"),
                    FILTER_TYPES.SET_OR,
                    d => d.metas.map(d => d.id)
                );
            }
        },
        toggleSelectByExtValue(attr, access, values=null, filterType=FILTER_TYPES.SET_OR) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("meta_items");
                DM.removeFilter("items");
            } else {
                DM.toggleFilter("meta_items", attr, values, filterType, access);
                DM.setFilter(
                    "items", "metas",
                    DM.getIds("meta_items"),
                    FILTER_TYPES.SET_OR,
                    d => d.metas.map(d => d.id)
                );
            }
        },

        selectByExtCategory(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("meta_categories", "id");
                DM.removeFilter("meta_items", "categories");
                DM.removeFilter("items", "metas")
            } else {
                DM.setFilter("meta_categories", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter(
                    "meta_items", "categories",
                    values,
                    FILTER_TYPES.SET_OR,
                    d => d.categories.map(d => d.cat_id)
                );
                DM.setFilter(
                    "items", "metas",
                    DM.getIds("meta_items"),
                    FILTER_TYPES.SET_OR,
                    d => d.metas.map(d => d.id)
                );
            }
        },
        toggleSelectByExtCategory(values=null) {
            if (values === null || values.length === 0) {
                DM.removeFilter("meta_categories", "id");
                DM.removeFilter("meta_items", "categories");
                DM.removeFilter("items", "metas")
            } else {
                DM.toggleFilter("meta_categories", "id", values, FILTER_TYPES.SET_OR);
                const set = DM.getIds("meta_categories")
                if (set.size === 0) {
                    DM.removeFilter("meta_items", "categories")
                    DM.removeFilter("items", "metas")
                } else {
                    DM.setFilter(
                        "meta_items", "categories",
                        set,
                        FILTER_TYPES.SET_OR,
                        d => d.categories.map(d => d.cat_id)
                    );
                    DM.setFilter(
                        "items", "metas",
                        DM.getIds("meta_items"),
                        FILTER_TYPES.SET_OR,
                        d => d.metas.map(d => d.id)
                    );
                }
            }
        },

        addAction(src, action, values) {
            this.actionQueue.push({ src: src, action: action, values: values });
        },

        popAction(src=null) {
            if (src) {
                const idx = this.actionQueue.findLastIndex(d => d.src === src);
                if (idx >= 0) {
                const it = this.actionQueue.splice(idx, 1)[0]
                return it;
                }
                return undefined
            }
            return this.actionQueue.pop()
        },

        setShowItem(id) {
            // works but not sure if this is a good idea
            // if (id !== null && this.showGame !== id) {
            //     this.showGameQueue.push(id)
            // } else if (this.showGameQueue.length > 0) {
            //     id = this.showGameQueue.pop()
            //     if (id === this.showGame) {
            //         id = this.showGameQueue.length > 0 ? this.showGameQueue.pop() : null
            //     }
            // }
            this.showGame = id;
            this.showGameObj = id !== null ? DM.getDataItem("items_id", id) : null
        },
        toggleShowItem(id) {
            this.setShowItem(this.showGame === id ? null : id)
        },

        setAddObjection(tagId=null, itemId=null, action=OBJECTION_ACTIONS.DISCUSS) {
            const set = tagId !== null || itemId !== null
            this.addObjTag = set ? tagId : null
            this.addObjItem = set ? itemId : null
            this.addObjType = set ? action : null
            this.addObj = set ? -1 : null;
        },

        setShowObjection(id=null) {
            const obj = id !== null ? DM.getDataItem("objections", id) : null
            this.showObjectionObj = id !== null && obj ? obj : null
            this.showObjection = id !== null && obj ? id : null;
        },
        toggleShowObjection(id=null) {
            this.setShowObjection(this.showObjection === id ? null : id)
        },

        setAddTag(id) {
            this.addTag = id;
        },
        toggleAddTag(id) {
            this.setAddTag(this.addTag === id ? null : id)
        },
        setShowTag(id) {
            this.editTag = id
            this.editTagObj = id !== null ? DM.getDataItem("tags", id) : null;
        },

        toggleShowTag(id) {
            if (this.editTag === id) {
                this.setShowTag(null)
            } else {
                this.setShowTag(id)
            }
        },

        setDeleteTag(id) {
            this.delTag = id
            this.delTagObj = id !== null ? DM.getDataItem("tags", id) : null;
        },
        toggleDeleteTag(id) {
            if (this.delTag === id) {
                this.setDeleteTag(null)
            } else {
                this.setDeleteTag(id)
            }
        },

        setDeleteEvidence(id) {
            this.delEv = id
            this.delEvObj = id !== null ? DM.getDataItem("evidence", id) : null;
        },
        toggleDeleteEvidence(id) {
            if (this.delEv === id) {
                this.setDeleteEvidence(null)
            } else {
                this.setDeleteEvidence(id)
            }
        },

        setDeleteMetaCategory(id) {
            this.delExtCat = id
            this.delExtCatObj = id !== null ? DM.getDataItem("meta_categories", id) : null;
        },
        toggleDeleteMetaCategory(id) {
            if (this.delExtCat === id) {
                this.setDeleteMetaCategory(null)
            } else {
                this.setDeleteMetaCategory(id)
            }
        },

        setDeleteMetaItem(id) {
            this.delExt = id
            this.delExtObj = id !== null ? DM.getDataItem("meta_items", id) : null;
        },
        toggleDeleteMetaItem(id) {
            if (this.delExt === id) {
                this.setDeleteMetaItem(null)
            } else {
                this.setDeleteMetaItem(id)
            }
        },

        setAddEvidence(id, tag=null, type=EVIDENCE_TYPE.POSITIVE, image=null) {
            this.addEvObj = id !== null ? DM.getDataItem("items_id", id) : null;
            this.addEvTag = tag;
            this.addEvImg = image;
            this.addEvType = type
            this.addEv = id;
        },

        toggleAddEvidence(id, tag=null, type=null, image=null) {
            if (this.addEv === id) {
                this.setAddEvidence(null)
            } else {
                this.setAddEvidence(id, tag, type, image)
            }
        },

        setAddMetaItem(id, group=null, tag=null, evidence=null) {
            if (!id) { this.addExt = id; }
            this.addExtObj = id !== null ? DM.getDataItem("items_id", id) : null;
            this.addExtTag = tag;
            this.addExtGroup = group
            this.addExtEv = evidence
            if (id) { this.addExt = id; }
        },

        toggleAddMetaItem(id, group=null, tag=null, evidence=null) {
            if (this.addExt === id) {
                this.setAddMetaItem(null)
            } else {
                this.setAddMetaItem(id, group, tag, evidence)
            }
        },

        setAddMetaCategory(id=-1, parent=null) {
            if (!id) { this.addExtCat = id; }
            this.addExtCatP = parent;
            if (id) { this.addExtCat = id; }
        },
        toggleAddMetaCategory(id=-1, parent=null) {
            this.setAddMetaCategory(this.addExtCat !== null ? null : id, parent)
        },

        setShowEvidence(id, list=null, index=null) {
            if (!id) { this.showEv = id; }
            this.showEvObj = id !== null ? DM.getDataItem("evidence", id) : null;
            this.showEvList = this.showEvObj ? list : null
            this.showEvIdx = this.showEvObj ? index : null
            if (id) { this.showEv = id; }
        },

        toggleShowEvidence(id, list=null, index=null) {
            this.setShowEvidence(this.showEv === id ? null : id, list, index)
        },

        setShowMetaGroup(id, extId=null) {
            if (!id) { this.showExtGroup = id; }
            this.showExtGroupExt = id !== null ? extId : null;
            this.showExtGroupObj = id !== null ? DM.getDataItem("meta_groups", id) : null;
            if (id) { this.showExtGroup = id; }
        },

        toggleShowMetaGroup(id, extId=null) {
            this.setShowMetaGroup(this.showExtGroup === id ? null : id, extId)
        },

        setShowMetaItem(id) {
            if (!id) { this.showExt = id; }
            this.showExtObj = id !== null ? DM.getDataItem("meta_items", id) : null;
            if (id) { this.showExt = id; }
        },

        toggleShowMetaItem(id) {
            this.setShowMetaItem(this.showExt === id ? null : id)
        },

        setShowMetaCategory(id) {
            if (!id) { this.showExtCat = id; }
            this.showExtCatObj = id !== null ? DM.getDataItem("meta_categories", id) : null;
            if (id) { this.showExtCat = id; }
        },

        toggleShowMetaCategory(id) {
            this.setShowMetaCategory(this.showExtCat === id ? null : id)
        },

        setShowTagExamples(id) {
            this.showTagEx = id;
        },

        toggleShowTagExamples(id) {
            this.setShowTagExamples(this.showTagEx === id ? null : id)
        },

        setShowTagObjections(id, item=null) {
            this.showTagObj = id
            this.showTagObjItem =  id ? item : null
        },

        toggleShowTagObjections(id, item=null) {
            const same = item === this.showTagObjItem && id === this.showTagObj
            this.setShowTagObjections(same ? null : id, item)
        }
    }
})
