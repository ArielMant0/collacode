// Utilities
import DM from '@/use/data-manager';
import { FILTER_TYPES } from '@/use/filters';
import * as d3 from 'd3'
import Cookies from 'js-cookie';
import { defineStore } from 'pinia'

export const useApp = defineStore('app', {
    state: () => ({
        static: APP_BUILD_STATIC,
        anonymous: APP_ANONYMOUS,
        initialized: false,
        showAllUsers: false,
        fetchUpdateTime: 0,
        updateItemsTime: 0,

        ds: null,
        datasets: [],

        globalUsers: [],
        users: [],
        userColorScale: d3.schemeTableau10,
        userColors: d3.scaleOrdinal(),

        activeUserId: null,

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

        addTag: null,
        addTagObj: null,
        addTagP: null,

        editTag: null,
        editTagObj: null,
        delTag: null,
        delTagObj: null,

        addEv: null,
        addEvObj: null,
        addEvTag: null,
        addEvImg: null,

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
        showEvTags: null,

        showExt: null,
        showExtObj: null,

        showExtCat: null,
        showExtCatObj: null,

        showExtGroup: null,
        showExtGroupObj: null,
        showExtGroupExt: null
    }),

    getters: {
        activeUser: state => {
            if (state.activeUserId === null) return null
            return state.activeUserId < 0 ? { name: "guest", id: -1 } : state.users.find(d => d.id === state.activeUserId)
        },
        allowEdit: state => state.static ? false : state.activeUserId > 0,
        dataset: state => state.ds ? state.datasets.find(d => d.id === state.ds) : null,
        scheme: state => state.dataset ? state.dataset.scheme : null,
        schemeItemName: state => state.scheme ? state.scheme.item_name : "Item",
        schemeMetaItemName: state => state.scheme ? state.scheme.meta_item_name : "Meta Item",
        code:  state => state.activeCode ? state.codes.find(d => d.id === state.activeCode) : null,
        newCode: state => state.transitionData ? state.transitionData.new_code : null,
        oldCode: state => state.transitionData ? state.transitionData.old_code : null,
        currentCode: state => state.useActive || state.transitionData === null ? state.activeCode : state.newCode
    },

    actions: {

        fetchUpdate() {
            this.fetchUpdateTime = Date.now()
        },

        updateItems() {
            this.updateItemsTime = Date.now()
        },

        setDatasets(list) {
            this.datasets = list;
        },

        setDataset(id) {
            this.ds = id;
        },

        setCodes(codes) {
            this.codes = codes;
        },

        setGlobalUsers(users) {
            this.globalUsers = users;
            const colors = d3.scaleOrdinal()
                .domain(users.map(d => d.id))
                .unknown("black")
                .range(users.map(d => this.userColorScale[d.id-1]))
            this.globalUsers.forEach(d => d.color = colors(d.id))
        },


        setUsers(users) {
            this.users = users;
            this.userColors
                .domain(users.map(d => d.id))
                .unknown("black")
                .range(users.map(d => this.userColorScale[d.id-1]))
            this.users.forEach(d => d.color = this.userColors(d.id))
            this.userTime = Date.now();
        },

        setActiveUser(id) {
            if (id < 0) { this.showAllUsers = true; }
            if (id !== this.activeUserId) {
                this.activeUserId = id;
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

        getUserShort(id) {
            const u = this.users.find(d => d.id === id);
            return u ? u.short : null;
        },

        getUserColor(id) {
            const u = this.users.find(d => d.id === id);
            return u ? u.color : "black";
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
            return this.codes.find(d => d.id === id).name
        },

        setInitialized() {
            this.initialized = true;
        },

        resetSelections() {
            DM.clearFilters()
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

        selectByTag(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("tags", "id");
                DM.removeFilter("items", "tags");
                DM.removeFilter("meta_items", "tags");
            } else {
                DM.setFilter("tags", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter(
                    "items", "tags",
                    values,
                    FILTER_TYPES.SET_OR,
                    d => d.tags.map(d => [d.tag_id].concat(d.path)).flat()
                );
                const paths = DM.getDerived("tags_path")
                DM.setFilter(
                    "meta_items", "tags",
                    values,
                    FILTER_TYPES.SET_OR,
                    d => d.tags.map(d => [d.tag_id].concat(paths.find(dd => dd.id === d.tag_id).path)).flat()
                )
            }
        },
        toggleSelectByTag(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("tags", "id");
                DM.removeFilter("items", "tags");
                DM.removeFilter("meta_items", "tags");
            } else {
                DM.toggleFilter("tags", "id", values, FILTER_TYPES.SET_OR);
                const set = DM.getIds("tags")
                if (set.size === 0) {
                    DM.removeFilter("items", "tags")
                    DM.removeFilter("meta_items", "tags");
                } else {
                    DM.setFilter(
                        "items", "tags",
                        set,
                        FILTER_TYPES.SET_OR,
                        d => d.tags.map(d => [d.tag_id].concat(d.path)).flat()
                    );
                    const paths = DM.getDerived("tags_path")
                    DM.setFilter(
                        "meta_items", "tags",
                        set,
                        FILTER_TYPES.SET_OR,
                        d => d.tags.map(d => [d.tag_id].concat(paths.find(dd => dd.id === d.tag_id).path)).flat()
                    )
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
                    "items", "exts",
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
                    "items", "exts",
                    DM.getIds("meta_items"),
                    FILTER_TYPES.SET_OR,
                    d => d.metas.map(d => d.id)
                );
            }
        },

        selectSelectByExtValue(attr, access, values=null, filterType=FILTER_TYPES.SET_OR) {
            if (values === null || Array.isArray(values) && values.length === 0) {
                DM.removeFilter("meta_items");
                DM.removeFilter("items");
            } else {
                DM.setFilter("meta_items", attr, values, filterType, access);
                DM.setFilter(
                    "items", "exts",
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
                    "items", "exts",
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
                DM.removeFilter("items", "exts")
            } else {
                DM.setFilter("meta_categories", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter(
                    "meta_items", "categories",
                    values,
                    FILTER_TYPES.SET_AND,
                    d => d.categories.map(d => d.cat_id)
                );
                DM.setFilter(
                    "items", "exts",
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
                DM.removeFilter("items", "exts")
            } else {
                DM.toggleFilter("meta_categories", "id", values, FILTER_TYPES.SET_OR);
                const set = DM.getIds("meta_categories")
                if (set.size === 0) {
                    DM.removeFilter("meta_items", "categories")
                    DM.removeFilter("items", "exts")
                } else {
                    DM.setFilter(
                        "meta_items", "categories",
                        set,
                        FILTER_TYPES.SET_AND,
                        d => d.categories.map(d => d.cat_id)
                    );
                    DM.setFilter(
                        "items", "exts",
                        DM.getIds("meta_items"),
                        FILTER_TYPES.SET_OR,
                        d => d.metas.map(d => d.id)
                    );
                }
            }
        },

        startCodeTransition() {
            this.useActive = false;
        },

        cancelCodeTransition() {
            this.useActive = true;
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
            this.showGame = id;
            this.showGameObj = id !== null ? DM.getDataItem("items", id) : null
        },
        toggleShowItem(id) {
            this.setShowItem(this.showGame === id ? null : id)
        },

        setAddTag(id) {
            if (!this.allowEdit) {
                this.addTag = null;
                return;
            }
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

        setAddEvidence(id, tag=null, image=null) {
            if (!this.allowEdit) {
                this.addEv = null;
                return;
            }
            this.addEv = id;
            this.addEvObj = id !== null ? DM.getDataItem("items", id) : null;
            this.addEvTag = tag;
            this.addEvImg = image;
        },

        toggleAddEvidence(id, tag=null, image=null) {
            if (this.addEv === id) {
                this.setAddEvidence(null)
            } else {
                this.setAddEvidence(id, tag, image)
            }
        },

        setAddMetaItem(id, group=null, tag=null, evidence=null) {
            if (!this.allowEdit) {
                this.addExtObj = null;
                return;
            }
            if (!id) { this.addExt = id; }
            this.addExtObj = id !== null ? DM.getDataItem("items", id) : null;
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
            if (!this.allowEdit) {
                this.addExtCatP = null;
                return;
            }
            if (!id) { this.addExtCat = id; }
            this.addExtCatP = parent;
            if (id) { this.addExtCat = id; }
        },
        toggleAddMetaCategory(id=-1, parent=null) {
            this.setAddMetaCategory(this.addExtCat !== null ? null : id, parent)
        },

        setShowEvidence(id) {
            if (!id) { this.showEv = id; }
            this.showEvObj = id !== null ? DM.getDataItem("evidence", id) : null;
            this.showEvTags = this.showEvObj ? DM.getDataItem("items", this.showEvObj.item_id).allTags : null;
            if (id) { this.showEv = id; }
        },

        toggleShowEvidence(id) {
            this.setShowEvidence(this.showEv === id ? null : id)
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
    }
})
