// Utilities
import DM from '@/use/data-manager';
import { FILTER_TYPES } from '@/use/filters';
import * as d3 from 'd3'
import { defineStore } from 'pinia'

export const useApp = defineStore('app', {
    state: () => ({
        static: false,
        initialized: false,
        showAllUsers: false,
        fetchUpdateTime: 0,

        ds: null,
        datasets: [],

        users: [],
        userColorScale: d3.schemeTableau10,
        userColors: d3.scaleOrdinal(),

        activeUser: null,
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
        allowEdit: state => state.static ? false : state.activeUserId > 0,
        dataset: state => state.ds ? state.datasets.find(d => d.id === state.ds) : null,
        code:  state => state.activeCode ? state.codes.find(d => d.id === state.activeCode) : null,
        newCode: state => state.transitionData ? state.transitionData.new_code : null,
        oldCode: state => state.transitionData ? state.transitionData.old_code : null,
        currentCode: state => state.useActive || !state.transitionData ? state.activeCode : state.transitionData.new_code
    },

    actions: {

        fetchUpdate() {
            this.fetchUpdateTime = Date.now()
        },

        setDatasets(list) {
            this.datasets = list;
            if (list.length > 0 && this.ds === null) {
                this.setDataset(list[0].id)
            }
        },

        setDataset(id) {
            this.ds = id;
        },

        setCodes(codes) {
            this.codes = codes;
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
            if (id !== this.activeUserId) {
                this.activeUser = id < 0 ? { name: "guest", id: -1 } : this.users.find(d => d.id === id)
                if (id < 0) { this.showAllUsers = true; }
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

        getUserColor(id) {
            const u = this.users.find(d => d.id === id);
            return u ? u.color : "black";
        },

        setActiveCode(id) {
            this.activeCode = id;
            this.codes = DM.getData("codes", false);
        },

        setActiveTransition(id) {
            this.transitions = DM.getData("code_transitions", false);
            this.transitionData = id ? this.transitions.find(d => d.id === id) : null;
            this.activeTransition = id;
        },

        getCodeName(id) {
            return this.codes.find(d => d.id === id).name
        },

        setInitialized() {
            this.initialized = true;
        },

        selectById(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("games");
                DM.removeFilter("externalizations");
            } else {
                DM.setFilter("games", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter("externalizations", "game_id", values, FILTER_TYPES.SET_OR);
            }
        },
        toggleSelectById(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("games");
                DM.removeFilter("externalizations");
            } else {
                DM.toggleFilter("games", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter("externalizations", "game_id", DM.getSelectedIds("games"), FILTER_TYPES.SET_OR);
            }
        },
        selectSelectByGameValue(attr, access, values=null, filterType=FILTER_TYPES.SET_OR) {
            if (values === null || Array.isArray(values) && values.length === 0) {
                DM.removeFilter("games");
                DM.removeFilter("externalizations");
            } else {
                DM.setFilter("games", attr, values, filterType, access);
                DM.setFilter(
                    "externalizations", "game_id",
                    DM.getIds("games"),
                    FILTER_TYPES.SET_OR
                );
            }
        },
        toggleSelectByGameValue(attr, access, values=null, filterType=FILTER_TYPES.SET_OR) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("games");
                DM.removeFilter("externalizations");
            } else {
                DM.toggleFilter("games", attr, values, filterType, access);
                DM.setFilter(
                    "externalizations", "game_id",
                    DM.getIds("games"),
                    FILTER_TYPES.SET_OR
                );
            }
        },

        selectByTag(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("tags", "id");
                DM.removeFilter("games", "tags");
                DM.removeFilter("externalizations", "tags");
            } else {
                DM.setFilter("tags", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter(
                    "games", "tags",
                    values,
                    FILTER_TYPES.SET_AND,
                    d => d.tags.map(d => [d.tag_id].concat(d.path)).flat()
                );
                const paths = DM.getDerived("tags_path")
                DM.setFilter(
                    "externalizations", "tags",
                    values,
                    FILTER_TYPES.SET_AND,
                    d => d.tags.map(d => [d.tag_id].concat(paths.find(dd => dd.id === d.tag_id).path)).flat()
                )
            }
        },
        toggleSelectByTag(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("tags", "id");
                DM.removeFilter("games", "tags");
                DM.removeFilter("externalizations", "tags");
            } else {
                DM.toggleFilter("tags", "id", values, FILTER_TYPES.SET_OR);
                const set = DM.getIds("tags")
                if (set.size === 0) {
                    DM.removeFilter("games", "tags")
                    DM.removeFilter("externalizations", "tags");
                } else {
                    DM.setFilter(
                        "games", "tags",
                        set,
                        FILTER_TYPES.SET_AND,
                        d => d.tags.map(d => [d.tag_id].concat(d.path)).flat()
                    );
                    const paths = DM.getDerived("tags_path")
                    DM.setFilter(
                        "externalizations", "tags",
                        set,
                        FILTER_TYPES.SET_AND,
                        d => d.tags.map(d => [d.tag_id].concat(paths.find(dd => dd.id === d.tag_id).path)).flat()
                    )
                }
            }
        },
        selectByExternalization(values=null) {
            if (values === null || Array.isArray(values) && values.length === 0) {
                DM.removeFilter("externalizations");
                DM.removeFilter("games");
            } else {
                DM.setFilter("externalizations", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter(
                    "games", "exts",
                    values,
                    FILTER_TYPES.SET_OR,
                    d => d.exts.map(d => d.id)
                );
            }
        },
        toggleSelectByExternalization(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("externalizations");
                DM.removeFilter("games");
            } else {
                DM.toggleFilter("externalizations", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter(
                    "games", "exts",
                    DM.getIds("externalizations"),
                    FILTER_TYPES.SET_OR,
                    d => d.exts.map(d => d.id)
                );
            }
        },

        selectSelectByExtValue(attr, access, values=null, filterType=FILTER_TYPES.SET_OR) {
            if (values === null || Array.isArray(values) && values.length === 0) {
                DM.removeFilter("externalizations");
                DM.removeFilter("games");
            } else {
                DM.setFilter("externalizations", attr, values, filterType, access);
                DM.setFilter(
                    "games", "exts",
                    DM.getIds("externalizations"),
                    FILTER_TYPES.SET_OR,
                    d => d.exts.map(d => d.id)
                );
            }
        },
        toggleSelectByExtValue(attr, access, values=null, filterType=FILTER_TYPES.SET_OR) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("externalizations");
                DM.removeFilter("games");
            } else {
                DM.toggleFilter("externalizations", attr, values, filterType, access);
                DM.setFilter(
                    "games", "exts",
                    DM.getIds("externalizations"),
                    FILTER_TYPES.SET_OR,
                    d => d.exts.map(d => d.id)
                );
            }
        },

        selectByExtCategory(values=null) {
            if (values === null || (Array.isArray(values) && values.length === 0)) {
                DM.removeFilter("ext_categories", "id");
                DM.removeFilter("externalizations", "categories");
                DM.removeFilter("games", "exts")
            } else {
                DM.setFilter("ext_categories", "id", values, FILTER_TYPES.SET_OR);
                DM.setFilter(
                    "externalizations", "categories",
                    values,
                    FILTER_TYPES.SET_AND,
                    d => d.categories.map(d => d.cat_id)
                );
                DM.setFilter(
                    "games", "exts",
                    DM.getIds("externalizations"),
                    FILTER_TYPES.SET_OR,
                    d => d.exts.map(d => d.id)
                );
            }
        },
        toggleSelectByExtCategory(values=null) {
            if (values === null || values.length === 0) {
                DM.removeFilter("ext_categories", "id");
                DM.removeFilter("externalizations", "categories");
                DM.removeFilter("games", "exts")
            } else {
                DM.toggleFilter("ext_categories", "id", values, FILTER_TYPES.SET_OR);
                const set = DM.getIds("ext_categories")
                if (set.size === 0) {
                    DM.removeFilter("externalizations", "categories")
                    DM.removeFilter("games", "exts")
                } else {
                    DM.setFilter(
                        "externalizations", "categories",
                        set,
                        FILTER_TYPES.SET_AND,
                        d => d.categories.map(d => d.cat_id)
                    );
                    DM.setFilter(
                        "games", "exts",
                        DM.getIds("externalizations"),
                        FILTER_TYPES.SET_OR,
                        d => d.exts.map(d => d.id)
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

        setShowGame(id) {
            this.showGame = id;
            this.showGameObj = id !== null ? DM.getDataItem("games", id) : null
        },
        toggleShowGame(id) {
            this.setShowGame(this.showGame === id ? null : id)
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
        setEditTag(id) {
            this.editTag = id
            this.editTagObj = id !== null ? DM.getDataItem("tags", id) : null;
        },

        toggleEditTag(id) {
            if (this.editTag === id) {
                this.setEditTag(null)
            } else {
                this.setEditTag(id)
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

        setDeleteExtCategory(id) {
            this.delExtCat = id
            this.delExtCatObj = id !== null ? DM.getDataItem("ext_categories", id) : null;
        },
        toggleDeleteExtCategory(id) {
            if (this.delExtCat === id) {
                this.setDeleteExtCategory(null)
            } else {
                this.setDeleteExtCategory(id)
            }
        },

        setDeleteExternalization(id) {
            this.delExt = id
            this.delExtObj = id !== null ? DM.getDataItem("externalizations", id) : null;
        },
        toggleDeleteExternalization(id) {
            if (this.delExt === id) {
                this.setDeleteExternalization(null)
            } else {
                this.setDeleteExternalization(id)
            }
        },

        setAddEvidence(id, tag=null, image=null) {
            if (!this.allowEdit) {
                this.addEv = null;
                return;
            }
            this.addEv = id;
            this.addEvObj = id !== null ? DM.getDataItem("games", id) : null;
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

        setAddExternalization(id, group=null, tag=null, evidence=null) {
            if (!this.allowEdit) {
                this.addExtObj = null;
                return;
            }
            if (!id) { this.addExt = id; }
            this.addExtObj = id !== null ? DM.getDataItem("games", id) : null;
            this.addExtTag = tag;
            this.addExtGroup = group
            this.addExtEv = evidence
            if (id) { this.addExt = id; }
        },

        toggleAddExternalization(id, group=null, tag=null, evidence=null) {
            if (this.addExt === id) {
                this.setAddExternalization(null)
            } else {
                this.setAddExternalization(id, group, tag, evidence)
            }
        },

        setAddExtCategory(id=-1, parent=null) {
            if (!this.allowEdit) {
                this.addExtCatP = null;
                return;
            }
            if (!id) { this.addExtCat = id; }
            this.addExtCatP = parent;
            if (id) { this.addExtCat = id; }
        },
        toggleAddExtCategory(id=-1, parent=null) {
            this.setAddExtCategory(this.addExtCat !== null ? null : id, parent)
        },

        setShowEvidence(id) {
            if (!id) { this.showEv = id; }
            this.showEvObj = id !== null ? DM.getDataItem("evidence", id) : null;
            this.showEvTags = this.showEvObj ? DM.getDataItem("games", this.showEvObj.game_id).allTags : null;
            if (id) { this.showEv = id; }
        },

        toggleShowEvidence(id) {
            this.setShowEvidence(this.showEv === id ? null : id)
        },

        setShowExtGroup(id, extId=null) {
            if (!id) { this.showExtGroup = id; }
            this.showExtGroupExt = id !== null ? extId : null;
            this.showExtGroupObj = id !== null ? DM.getDataItem("ext_groups", id) : null;
            if (id) { this.showExtGroup = id; }
        },

        toggleShowExtGroup(id, extId=null) {
            this.setShowExternalization(this.showExtGroup === id ? null : id, extId)
        },

        setShowExternalization(id) {
            if (!id) { this.showExt = id; }
            this.showExtObj = id !== null ? DM.getDataItem("externalizations", id) : null;
            if (id) { this.showExt = id; }
        },

        toggleShowExternalization(id) {
            this.setShowExternalization(this.showExt === id ? null : id)
        },

        setShowExtCategory(id) {
            if (!id) { this.showExtCat = id; }
            this.showExtCatObj = id !== null ? DM.getDataItem("ext_categories", id) : null;
            if (id) { this.showExtCat = id; }
        },

        toggleShowExtCategory(id) {
            this.setShowExtCategory(this.showExtCat === id ? null : id)
        },
    }
})
