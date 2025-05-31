<template>
  <v-app>
    <v-main>
        <v-overlay v-if="allowOverlay && inMainView" :model-value="showOverlay" class="d-flex justify-center align-center" persistent>
            <v-progress-circular indeterminate size="64" color="white"></v-progress-circular>
        </v-overlay>
        <IdentitySelector v-if="loadedUsers" v-model="askUserIdentity"/>
        <GlobalTooltip/>
        <EvidenceToolTip/>

        <SideNavigation :size="navSize"/>

        <div :style="{
            position: 'relative',
            width: (width - (showNavTop ? 0 : navSize-10))+'px',
            left: (showNavTop ? 0 : navSize)+'px',
            top: (showNavTop ? 45 : 0)+'px',
            maxWidth: '100dvw',
            maxHeight: (height - (showNavTop ? 46 : 0))+'px',
            overflow: 'auto'
        }">
            <router-view />
        </div>
    </v-main>
  </v-app>
</template>

<script setup>

    import { useLoader } from '@/use/loader';
    import { OBJECTION_STATUS, useApp } from '@/store/app'
    import { useToast } from "vue-toastification";
    import { storeToRefs } from 'pinia'
    import { ref, onMounted, watch, computed } from 'vue'
    import DM from '@/use/data-manager'
    import * as api from '@/use/data-api';

    import { useSettings } from '@/store/settings';
    import { group } from 'd3';
    import { useTimes } from '@/store/times';
    import { sortObjByString } from '@/use/sorting';
    import IdentitySelector from '@/components/IdentitySelector.vue';
    import GlobalTooltip from '@/components/GlobalTooltip.vue';
    import EvidenceToolTip from './components/evidence/EvidenceToolTip.vue';
    import { useSounds } from './store/sounds';
    import { toTreePath } from './use/utility';
    import { useWindowSize } from '@vueuse/core';
    import { useRoute } from 'vue-router';
    import SideNavigation from './components/SideNavigation.vue';
    import { useDisplay } from 'vuetify';

    const toast = useToast();
    const loader = useLoader()
    const settings = useSettings();
    const app = useApp()
    const times = useTimes()
    const sounds = useSounds()
    const route = useRoute()

    const { width, height } = useWindowSize()
    const navSize = ref(60)

    const { mdAndDown } = useDisplay()

    const loadedUsers = ref(false)

    const {
        ds,
        activeUserId,
        activeTransition,
        initialized,
        fetchUpdateTime,
        updateItemsTime
    } = storeToRefs(app);

    const {
        isLoading,
        inMainView,
        activeTab,
        askUserIdentity,
        showNavTop
    } = storeToRefs(settings)

    const allowOverlay = ref(false)
    const showOverlay = computed(() => allowOverlay.value && inMainView.value && isLoading.value)

    async function init(force) {
        if (!initialized.value) {
            await loadUsers();
            loadedUsers.value = true
            await loadAllDatasets()
            askUserIdentity.value = activeUserId.value === null;
            if (!askUserIdentity.value) {
                app.setActiveUser(app.activeUserId)
            }
        } else if (force) {
            await loadData();
        }
    }

    async function loadData() {
        if (app.activeUserId === null) { return }

        isLoading.value = true;
        await loadUsers()
        await loadCodes()
        await loadCodeTransitions()
        await loadAllTags(false)
        await loadExtCategories()
        await loadExtGroups()

        await Promise.all([
            loadDataTags(false),
            loadEvidence(false),
            loadExtAgreements(false),
            loadExternalizations(false),
            loadTagAssignments(),
            loadGameExpertise(false),
            loadGameScores(),
            loadObjections(false)
        ])

        // add data to games
        await loadGames();

        if (!initialized.value) {
            initialized.value = true;
        }
        isLoading.value = false;
    }

    async function loadAllDatasets() {
        const list = await api.loadDatasets()
        app.setDatasets(list)
        times.reloaded("datasets")
    }

    async function loadUsers() {
        try {
            const list = await api.loadAllUsers()
            app.setGlobalUsers(list)
        } catch {
            toast.error("error loading users")
        }

        if (ds.value) {
            try {
                const list = await api.loadUsersByDataset(ds.value)
                app.setUsers(list)
            } catch (e) {
                console.error(e.toString())
                toast.error("error loading users for dataset")
            }
        }
        times.reloaded("users")
    }

    async function loadCodes() {
        if (!ds.value) return;
        try {
            const data = await api.loadCodesByDataset(ds.value)
            DM.setData("codes", data);
            app.setCodes(data)
        } catch {
            toast.error("error loading codes for dataset")
        }
        times.reloaded("codes")
    }
    async function loadGames() {
        if (!ds.value) return;
        try {
            const result = await api.loadItemsByDataset(ds.value)
            updateAllItems(result);
        } catch (e) {
            console.error(e.toString())
            toast.error("error loading items for dataset")
        }
        times.reloaded("items")
    }
    async function loadAllTags() {
        return Promise.all([loadTags(), loadOldTags()])
    }
    async function loadOldTags() {
        if (!activeTransition.value || !app.oldCode) return;
        try {
            const result = await api.loadTagsByCode(app.oldCode)
            result.forEach(t => {
                t.parent = t.parent === null ? -1 : t.parent;
                t.path = toTreePath(t, result);
                t.pathNames = t.path.map(dd => result.find(tmp => tmp.id === dd).name).join(" / ")
            });
            result.sort(sortObjByString("name"))
            DM.setData("tags_old", result)
            DM.setDerived("tags_old_path", "tags", d => ({ id: d.id, path: toTreePath(d, result) }))
            DM.setData("tags_old_name", new Map(result.map(d => ([d.id, d.name]))))
        } catch {
            toast.error("error loading old tags")
        }
        times.reloaded("tags_old")
    }
    async function loadTags() {
        if (!app.currentCode) return;
        try {
            const [result, irr] = await Promise.all([api.loadTagsByCode(app.currentCode), api.loadIrrTagsByCode(app.currentCode)])
            DM.setData("tags_irr", new Map(irr.map(d => ([d.tag_id, d.alpha]))))

            result.forEach(t => {
                t.parent = t.parent === null ? -1 : t.parent;
                t.path = toTreePath(t, result);
                t.pathNames = t.path.map(dd => result.find(tmp => tmp.id === dd).name).join(" / ")
                t.valid = true

                if (app.editTag === t.id) {
                    app.editTagObj = t
                }
            });
            result.sort(sortObjByString("name"))

            const sortByTree = result.map(d => Object.assign({}, d))
            sortByTree.sort((a, b) => {
                const l = Math.min(a.path.length, b.path.length);
                for (let i = 0; i < l; ++i) {
                    if (a.path[i] !== b.path[i]) return a.path[i]-b.path[i]
                }
                return a.path.length-b.path.length
            });
            DM.setData("tags_tree", sortByTree)

            DM.setData("tags", result)
            DM.setDerived("tags_path", "tags", d => ({ id: d.id, path: toTreePath(d, result) }))
            DM.setData("tags_name", new Map(result.map(d => ([d.id, d.name ? d.name : '']))))
            DM.setData("tags_desc", new Map(result.map(d => ([d.id, d.description ? d.description : 'no description']))))
        } catch {
            toast.error("error loading tags")
        }
        times.reloaded("tags")
    }
    async function loadDataTags(update=true) {
        if (!app.currentCode) return;
        try {
            const result = await api.loadDataTagsByCode(app.currentCode)
            const irr = await api.loadIrrItemsByCode(app.currentCode)
            DM.setData("items_irr", new Map(irr.map(d => ([d.item_id, d.alpha]))))

            if (update && DM.hasData("items") && DM.hasData("tags")) {
                const data = DM.getData("items", false)
                const tags = DM.getData("tags", false)

                const sortFunc = sortObjByString("name")
                const groupDT = group(result, d => d.item_id)

                const tagCounts = new Map()
                const userTagCounts = new Map()

                tags.forEach(t => {
                    tagCounts.set(t.id, 0)
                    userTagCounts.set(t.id, new Map())
                })

                data.forEach(g => {
                    g.tags = [];
                    g.allTags = [];
                    g.coders = []
                    g.numCoders = 0;

                    if (groupDT.has(g.id)) {
                        const array = groupDT.get(g.id)
                        const m = new Set()
                        const coders = new Set()
                        array.forEach(dt => {
                            const t = tags.find(d => d.id === dt.tag_id)
                            if (!t) return;

                            // count tags (per user)
                            const pu = userTagCounts.get(t.id)
                            pu.set(dt.created_by, (pu.get(dt.created_by) || 0) + 1)
                            // save user/coder
                            coders.add(dt.created_by)

                            if (!m.has(t.id)) {
                                // count tags (overall)
                                tagCounts.set(t.id, tagCounts.get(t.id)+1)
                                g.allTags.push({
                                    id: t.id,
                                    name: t.name,
                                    created_by: t.created_by,
                                    path: t.path ? t.path : toTreePath(t, tags),
                                    pathNames: t.pathNames
                                });
                            }
                            m.add(t.id)
                            dt.name = t.name
                            dt.path = t.path ? t.path : toTreePath(t, tags)
                            dt.pathNames = t.pathNames
                        })

                        g.tags = array.filter(d => d.pathNames !== undefined)
                        g.tags.sort(sortFunc)
                        g.allTags.sort(sortFunc)
                        g.numTags = g.allTags.length
                        g.numCoders = coders.size;
                        g.coders = Array.from(coders.values())
                        g.coders.sort()
                    }
                });
                tags.forEach(t => {
                    t.valid = (t.parent !== null && t.parent !== -1) && t.is_leaf === 1 ?
                        tagCounts.get(t.id) > 0:
                        tagCounts.get(t.id) === 0
                })

                DM.setData("tags_counts", tagCounts)
                DM.setData("tags_user_counts", userTagCounts)
            }

            DM.setData("datatags", result)
        } catch (e) {
            console.error(e.toString())
            toast.error("error loading datatags")
        }
        times.reloaded("datatags")
    }
    async function loadEvidence(update=true) {
        if (!app.currentCode) return;
        try {
            const result = await api.loadEvidenceByCode(app.currentCode)
            if (update && DM.hasData("items")) {
                const data = DM.getData("items", false)
                const g = group(result, d => d.item_id)
                data.forEach(d => {
                    d.evidence = g.has(d.id) ? g.get(d.id) : []
                    d.numEvidence = d.evidence.length
                    if (app.showEv === d.id) {
                        app.showEvObj = d;
                    }
                });
            }
            DM.setData("evidence", result)
        } catch {
            toast.error("error loading evidence")
        }
        times.reloaded("evidence")
    }
    async function loadTagAssignments() {
        if (!app.activeTransition) return;
        try {
            const result = await api.loadTagAssignmentsByCodes(app.oldCode, app.newCode);
            DM.setData("tag_assignments", result);
        } catch {
            toast.error("error loading tag assignments")
        }
        times.reloaded("tag_assignments")
    }
    async function loadCodeTransitions() {
        if (!ds.value) return;
        try {
            const result = await api.loadCodeTransitionsByDataset(ds.value);
            result.forEach(d => d.name = `${app.getCodeName(d.old_code)} to ${app.getCodeName(d.new_code)}`)
            result.sort((a, b) => a.id - b.id)
            DM.setData("code_transitions", result);
            app.setTransitions(result);

        } catch {
            toast.error("error loading code transitions")
        }
        times.reloaded("code_transitions")
    }
    async function loadExtGroups() {
        if (!app.currentCode) return;
        try{
            const result = await api.loadExtGroupsByCode(app.currentCode);
            DM.setData("meta_groups", result);
            if (app.showExtGroup) {
                app.showExtGroupObj = result.find(d => d.id === app.showExtGroup)
            }
        } catch {
            toast.error("error loading ext groups")
        }
        times.reloaded("meta_groups")
    }
    async function loadExternalizations(update=true) {
        if (!app.currentCode) return;
        try {
            const [result, [catc, tagc, evc]] = await Promise.all([
                api.loadExternalizationsByCode(app.currentCode),
                api.loadExtConnectionsByCode(app.currentCode)
            ]);

            DM.setData("meta_cat_connections", catc);
            DM.setData("meta_tag_connections", tagc);
            DM.setData("meta_ev_connections", evc);

            const clusters = new Set()
            const agree = DM.getData("meta_agreements", false)
            const groups = DM.getData("meta_groups")

            result.forEach(d => {
                clusters.add(d.cluster)
                if (groups) {
                    d.item_id = groups.find(g => g.id === d.group_id).item_id
                }
                d.code_id = app.currentCode;
                d.categories = catc.filter(c => c.meta_id === d.id);
                d.tags = tagc.filter(t => t.meta_id === d.id);
                d.evidence = evc.filter(t => t.meta_id === d.id);
                const ld = agree.filter(dd => dd.meta_id === d.id)
                d.likes = ld ? ld.filter(dd => dd.value > 0) : []
                d.dislikes = ld ? ld.filter(dd => dd.value < 0) : []

                if (app.showExt === d.id) {
                    app.showExtObj = d
                }
            });
            if (update && DM.hasData("items")) {
                const data = DM.getData("items", false)
                const g = group(result, d => d.item_id)
                data.forEach(d => {
                    d.metas = g.has(d.id) ? g.get(d.id) : []
                    d.numMeta = d.metas.length
                });
            }
            DM.setData("meta_items", result);
            DM.setData("meta_clusters", Array.from(clusters.values()));
        } catch {
            toast.error("error loading meta items")
        }
        times.reloaded("meta_items")
    }
    async function loadExtCategories() {
        if (!app.currentCode) return;
        try {
            const result = await api.loadExtCategoriesByCode(app.currentCode)
            result.forEach(d => {
                d.parent = d.parent ? d.parent : -1;
                d.is_leaf = result.find(dd => dd.parent === d.id) === undefined
            });
            DM.setData("meta_categories", result);
            DM.setDerived("meta_cats_path", "meta_categories", d => ({ id: d.id, path: toTreePath(d, result) }))
        } catch {
            toast.error("error loading externalization categories")
        }
        times.reloaded("meta_categories")
    }
    async function loadExtAgreements(update=true) {
        if (!app.currentCode) return;
        try {
            const result = await api.loadExtAgreementsByCode(app.currentCode)
            if (update && DM.hasData("meta_items")) {
                const exts = DM.getData("meta_items", false)
                exts.forEach(d => {
                    const ld = result.filter(dd => dd.meta_id === d.id)
                    d.likes = ld ? ld.filter(dd => dd.value > 0) : []
                    d.dislikes = ld ? ld.filter(dd => dd.value < 0) : []
                });
            }
            DM.setData("meta_agreements", result);
        } catch {
            toast.error("error loading externalization agreements")
        }
        times.reloaded("meta_agreements")
    }

    async function loadGameExpertise(update=true) {
        if (!ds.value) return;
        try {
            const result = await api.loadItemExpertiseByDataset(ds.value)
            if (update && DM.hasData("items")) {
                const items = DM.getData("items", false)
                items.forEach(d => d.expertise = result.filter(e => e.item_id === d.id));
                DM.setData("items_name", new Map(result.map(d => ([d.id, d.name ? d.name : '']))))
                DM.setData("items", items)
            }
            DM.setData("item_expertise", result);
        } catch {
            toast.error("error loading game expertise")
        }
        times.reloaded("item_expertise")
    }
    async function loadObjections(update=true) {
        if (!app.currentCode) return;
        try {
            const result = await api.loadObjectionsByCode(app.currentCode)
            result.forEach(o => {
                o.item_name = ""
                if (o.item_id > 0) {
                    const it = DM.getDataItem("items", o.item_id)
                    o.item_name = it ? it.name : ""
                }
                o.tag_name = o.tag_id ? DM.getDataItem("tags_name", o.tag_id) : ""
            });
            if (result.length > 0) {
                const byItem = group(result.filter(d => d.item_id !== null), d => d.item_id)
                const byTag = group(result.filter(d => d.tag_id !== null), d => d.tag_id)
                DM.setData("objections_items", new Map(byItem.entries()))
                DM.setData("objections_tags", new Map(byTag.entries()))
                if (update && DM.hasData("items")) {
                    const data = DM.getData("items", false)
                    data.forEach(d => {
                        d.numObjs = byItem.has(d.id) ?
                            byItem.get(d.id).filter(d => d.status === OBJECTION_STATUS.OPEN).length :
                            0
                    })
                }
            } else {
                DM.setData("objections_items", new Map())
                DM.setData("objections_tags", new Map())
                if (update && DM.hasData("items")) {
                    const data = DM.getData("items", false)
                    data.forEach(d => d.numObjs = 0)
                }
            }
            DM.setData("objections", result);
        } catch {
            toast.error("error loading objections")
        }
        times.reloaded("objections")
    }

    async function loadGameScores() {
        if (!app.currentCode) return;
        try {
            const [r1, r2, r3] = await Promise.all([
                api.loadGameScoresByCode(app.currentCode),
                api.loadGameScoresItemsByCode(app.currentCode),
                api.loadGameScoresTagsByCode(app.currentCode)
            ])
            DM.setData("game_scores", r1);
            DM.setData("game_scores_items", r2);
            DM.setData("game_scores_tags", r3);
        } catch {
            toast.error("error loading game scores")
        }
        times.reloaded("game_scores")
    }


    function updateAllItems(passed=null) {
        if (!Array.isArray(passed) && !DM.hasData("items")) return console.warn("missing data")

        const data = Array.isArray(passed) ? passed : DM.getData("items", false)

        const tags = DM.getData("tags", false);
        const dts = DM.getData("datatags", false)

        const tagCounts = new Map()
        const userTagCounts = new Map()
        tags.forEach(t => {
            tagCounts.set(t.id, 0)
            userTagCounts.set(t.id, new Map())
        })

        const groupDT = group(dts, d => d.item_id)
        const groupExp = group(DM.getData("item_expertise", false), d => d.item_id)
        const groupEv = group(DM.getData("evidence", false), d => d.item_id)
        const groupExt = group(DM.getData("meta_items", false), d => d.item_id)

        const sortFunc = sortObjByString("name")

        data.forEach(g => {
            g.expertise = groupExp.has(g.id) ? groupExp.get(g.id) : [];
            g.tags = [];
            g.allTags = [];
            g.evidence = groupEv.has(g.id) ? groupEv.get(g.id) : []
            g.metas = groupExt.has(g.id) ? groupExt.get(g.id) : []
            g.numEvidence = g.evidence.length
            g.numMeta = g.metas.length
            g.numCoders = 0;
            g.coders = [];
            const objs = DM.getDataItem("objections_items", g.id)
            g.numObjs = objs ? objs.filter(d => d.status === OBJECTION_STATUS.OPEN).length : 0

            if (groupDT.has(g.id)) {
                const array = groupDT.get(g.id)
                const m = new Set()
                const coders = new Set()
                array.forEach(dt => {
                    const t = tags.find(d => d.id === dt.tag_id)
                    if (!t) return;

                    // count tags (per user)
                    const pu = userTagCounts.get(t.id)
                    pu.set(dt.created_by, (pu.get(dt.created_by) || 0) + 1)
                    // save user/coder
                    coders.add(dt.created_by)

                    if (!m.has(t.id)) {
                        // count tags (overall)
                        tagCounts.set(t.id, tagCounts.get(t.id)+1)
                        g.allTags.push({
                            id: t.id,
                            name: t.name,
                            created_by: t.created_by,
                            path: t.path ? t.path :toTreePath(t, tags),
                            pathNames: t.pathNames
                        });
                    }
                    m.add(t.id)
                    dt.name = t.name
                    dt.path = t.path ? t.path :toTreePath(t, tags)
                    dt.pathNames = t.pathNames
                })

                g.tags = array.filter(d => d.name !== undefined)
                g.tags.sort(sortFunc)
                g.allTags.sort(sortFunc)
                g.numTags = g.allTags.length
                g.numCoders = coders.size
                g.coders = Array.from(coders.values())
                g.coders.sort()
            }

            if (app.showGame === g.id) {
                app.showGameObj = g
            }
        });

        tags.forEach(t => {
            t.valid = (t.parent !== null && t.parent !== -1) && t.is_leaf === 1 ?
                tagCounts.get(t.id) > 0:
                tagCounts.get(t.id) === 0
        })

        DM.setData("tags_counts", tagCounts)
        DM.setData("tags_user_counts", userTagCounts)

        if (passed !== null) {
            DM.setData("items_name", new Map(data.map(d => ([d.id, d.name]))))
            DM.setData("items", data)
        }
    }

    async function fetchServerUpdate(giveToast=false) {
        if (app.static) return
        if (app.noUpdate) return

        try {
            const resp = await loader.get(`/lastupdate/dataset/${ds.value}`)
            if (resp.length > 0 && initialized.value) {
                const updates = []
                resp.forEach(d => {
                    if (d.timestamp > times.getTime(d.name)) {
                        updates.push(d.name)
                        times.needsReload(d.name)
                    }
                });

                if (updates.length > 0) {
                    toast.info("loading updates for: " + updates.join(", "))
                } else if (giveToast) {
                    toast.info("no server update available")
                }
            }
        } catch {
            toast.error("could not fetch server update")
        }
    }
    function startPolling(immediate=false) {
        if (immediate) fetchServerUpdate();
        return setInterval(fetchServerUpdate, 30000)
    }
    function stopPolling(handler) {
        clearInterval(handler)
    }

    onMounted(async () => {
        allowOverlay.value = true
        if (!app.static) {
            let handler = startPolling()
            document.addEventListener("visibilitychange", () => {
                if (document.hidden) {
                    stopPolling(handler)
                } else {
                    handler = startPolling(true);
                }
            });
            init()
        } else {
            app.setActiveUser(-1)
            init()
        }

        window.addEventListener("click", () => sounds.loadSounds(), { once: true })
    });

    watch(() => times.n_all, async function() {
        const showToast = initialized.value
        if (showToast) toast.info("reloading all data..")
        allowOverlay.value = true
        await loadData();
        allowOverlay.value = false
        if (showToast) toast.success("reloaded data")
        times.reloaded("all")
    });

    // only watch for reloads when data is not served statically
    if (!app.static) {

        watch(() => times.n_tagging, async function() {
            if (activeTab.value === "transition") {
                await loadAllTags()
                await loadTagAssignments()
            } else {
                await loadTags();
            }
            await loadDataTags();
            times.reloaded("tagging")
        });

        watch(() => times.n_transitioning, async function() {
            await Promise.all([loadCodes(), loadCodeTransitions()])
            times.reloaded("transitioning")
        });

        watch(() => times.n_datasets, loadAllDatasets);
        watch(() => times.n_users, loadUsers);
        watch(() => times.n_items, loadGames);
        watch(() => times.n_item_expertise, loadGameExpertise);
        watch(() => times.n_codes, loadCodes);
        watch(() => times.n_tags, loadTags);
        watch(() => times.n_tags_old, loadOldTags);
        watch(() => times.n_datatags, loadDataTags);
        watch(() => times.n_evidence, loadEvidence);
        watch(() => times.n_tag_assignments, loadTagAssignments);
        watch(() => times.n_code_transitions, loadCodeTransitions);
        watch(() => times.n_meta_items, loadExternalizations);
        watch(() => times.n_meta_groups, loadExtGroups);
        watch(() => times.n_meta_categories, loadExtCategories);
        watch(() => times.n_meta_agreements, loadExtAgreements);
        watch(() => times.n_objections, loadObjections);

        watch(() => times.n_game_scores, loadGameScores);

        watch(activeUserId, now => askUserIdentity.value = now === null);
        watch(fetchUpdateTime, () => fetchServerUpdate(true))
        watch(updateItemsTime, () => updateAllItems())
    }

    watch(() => route.path, function() {
        settings.pathSegments = route.path.split("/").filter(d => d)
        const first = settings.pathSegments.length > 0 ? settings.pathSegments[0] : ""
        if (!first || first.length === 0) {
            inMainView.value = true
        } else {
            inMainView.value = first !== "admin" && first !== "import" && first !== "export"
        }
    })

</script>

<style>
body {
    width: 100%;
}
.topnav {
    background-color: #333;
    position: sticky;
    top: 0;
    left: 0;
    width: 100dvw;
    z-index: 2;
    font-size: smaller;
}

</style>
