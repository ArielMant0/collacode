<template>
    <main>
        <ActionContextMenu/>

        <v-overlay v-if="showOverlay" v-model="isLoading" class="d-flex justify-center align-center" persistent>
            <v-progress-circular indeterminate size="64" color="white"></v-progress-circular>
        </v-overlay>
        <GlobalShortcuts/>
        <GlobalTooltip/>

        <IdentitySelector v-if="!app.static" v-model="askUserIdentity"/>

        <v-tabs v-model="activeTab"
            class="main-tabs"
            color="secondary"
            bg-color="surface-variant"
            align-tabs="center"
            density="compact"
            @update:model-value="checkReload"
            >
            <v-tab value="coding">{{ settings.getTabName("coding") }}</v-tab>
            <v-tab value="agree">{{ settings.getTabName("agree") }}</v-tab>
            <v-tab value="transition">{{ settings.getTabName("transition") }}</v-tab>
            <v-divider vertical thickness="2" color="primary" class="ml-1 mr-1" opacity="1"></v-divider>
            <v-tab value="explore_tags">{{ settings.getTabName("explore_tags") }}</v-tab>
            <v-tab value="explore_ev">{{ settings.getTabName("explore_ev") }}</v-tab>
            <v-tab value="explore_meta">{{ settings.getTabName("explore_meta") }}</v-tab>
        </v-tabs>

        <div ref="el" style="width: 100%;">

            <MiniNavBar :hidden="expandNavDrawer"/>

            <div v-if="initialized && !isLoading" class="mb-2 pa-2" style="margin-left: 70px;">

                <div style="text-align: center;">
                    <ItemBarCodes :hidden="!showBarCodes"/>
                </div>

                <div class="d-flex justify-center">
                    <EmbeddingExplorer :hidden="!showScatter" :width="Math.max(400,width*0.85)"/>
                </div>

                <v-tabs-window v-model="activeTab">

                    <v-tabs-window-item value="transition">
                        <TransitionView v-if="activeUserId !== null" :loading="isLoading"/>
                    </v-tabs-window-item>

                    <v-tabs-window-item value="agree">
                        <AgreementView v-if="activeUserId !== null" :loading="isLoading"/>
                    </v-tabs-window-item>

                    <v-tabs-window-item value="explore_meta">
                        <ExploreExtView v-if="activeUserId !== null" :loading="isLoading"/>
                    </v-tabs-window-item>

                    <v-tabs-window-item value="explore_tags">
                        <ExploreTagsView v-if="activeUserId !== null" :loading="isLoading"/>
                    </v-tabs-window-item>

                    <v-tabs-window-item value="explore_ev">
                        <ExploreEvidenceView v-if="activeUserId !== null" :loading="isLoading"/>
                    </v-tabs-window-item>

                </v-tabs-window>

                <v-sheet class="mt-2 pa-2">
                    <RawDataView
                        :hidden="!showTable"
                        selectable
                        :allow-edit="allowEdit"
                        :allow-add="allowEdit"
                        check-assigned/>
                </v-sheet>

                <div style="text-align: center;">
                    <ItemEvidenceTiles :hidden="!showEvidenceTiles" :code="currentCode"/>
                </div>

                <div style="text-align: center;">
                    <MetaItemsList :hidden="!showExtTiles" show-bar-codes/>
                </div>
            </div>
        </div>
    </main>
</template>

<script setup>

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { useToast } from "vue-toastification";
    import TransitionView from '@/components/views/TransitionView.vue'
    import ExploreTagsView from '@/components/views/ExploreTagsView.vue';
    import { storeToRefs } from 'pinia'
    import { ref, onMounted, watch } from 'vue'
    import DM from '@/use/data-manager'
    import { loadAllUsers, loadCodesByDataset, loadCodeTransitionsByDataset, loadDatasets, loadDataTagsByCode, loadEvidenceByCode, loadExtAgreementsByCode, loadExtCategoriesByCode, loadExtConnectionsByCode, loadExternalizationsByCode, loadExtGroupsByCode, loadIrrByCode, loadItemExpertiseByDataset, loadItemsByDataset, loadTagAssignmentsByCodes, loadTagsByCode, loadUsersByDataset, toToTreePath } from '@/use/utility';
    import GlobalShortcuts from '@/components/GlobalShortcuts.vue';
    import IdentitySelector from '@/components/IdentitySelector.vue';
    import ItemEvidenceTiles from '@/components/evidence/ItemEvidenceTiles.vue';
    import RawDataView from '@/components/RawDataView.vue';
    import MetaItemsList from '@/components/meta_items/MetaItemsList.vue';

    import { useSettings } from '@/store/settings';
    import { group } from 'd3';
    import { useTimes } from '@/store/times';
    import GlobalTooltip from '@/components/GlobalTooltip.vue';
    import MiniNavBar from '@/components/MiniNavBar.vue';
    import { sortObjByString } from '@/use/sorting';
    import ItemBarCodes from '@/components/items/ItemBarCodes.vue';
    import EmbeddingExplorer from '@/components/EmbeddingExplorer.vue';
    import { useElementSize } from '@vueuse/core';
    import ExploreExtView from '@/components/views/ExploreExtView.vue';
    import Cookies from 'js-cookie';
    import ActionContextMenu from '@/components/dialogs/ActionContextMenu.vue';
    import AgreementView from '@/components/views/AgreementView.vue';
    import ExploreEvidenceView from '@/components/views/ExploreEvidenceView.vue';

    const toast = useToast();
    const loader = useLoader()
    const settings = useSettings();
    const app = useApp()
    const times = useTimes()

    const isLoading = ref(false);
    const askUserIdentity = ref(false);

    const {
        allowEdit,
        ds,
        activeUserId,
        currentCode,
        activeTransition,
        initialized,
        fetchUpdateTime
    } = storeToRefs(app);

    const {
        expandNavDrawer,
        activeTab,
        showBarCodes,
        showScatter,
        showTable,
        showEvidenceTiles,
        showExtTiles
    } = storeToRefs(settings)

    const el = ref(null)
    const { width } = useElementSize(el)
    const showOverlay = ref(true)

    function checkReload() {
        window.scrollTo(0, 0)
        switch (activeTab.value) {
            case "coding":
                app.cancelCodeTransition();
                showBarCodes.value = false;
                showScatter.value = false;
                showEvidenceTiles.value = false;
                showTable.value = true;
                showExtTiles.value = false;
                break;
            case "transition":
                app.startCodeTransition();
                showBarCodes.value = false;
                showScatter.value = false;
                showEvidenceTiles.value = false;
                showTable.value = true;
                showExtTiles.value = false;
                loadOldTags();
                break;
            case "explore_tags":
                app.cancelCodeTransition();
                showBarCodes.value = false;
                showScatter.value = false;
                showTable.value = false;
                showEvidenceTiles.value = false;
                showExtTiles.value = false;
                break;
            case "explore_meta":
                app.cancelCodeTransition();
                showBarCodes.value = false;
                showScatter.value = true;
                showTable.value = false;
                showEvidenceTiles.value = false;
                showExtTiles.value = true;
                break;
            default:
                app.cancelCodeTransition();
                showBarCodes.value = false;
                showScatter.value = false;
                showEvidenceTiles.value = false;
                showTable.value = false;
                showExtTiles.value = false;
                break;
        }
    }

    async function init(force) {
        if (!initialized.value) {
            await loadUsers();
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
            loadGameExpertise(false)
        ])

        // add data to games
        await loadGames();

        if (!initialized.value) {
            initialized.value = true;
        }
        isLoading.value = false;
    }

    async function loadAllDatasets() {
        const list = await loadDatasets()
        app.setDatasets(list)
        if (!askUserIdentity.value && list.length > 0 && ds.value === null) {
            const dataset = Cookies.get("dataset_id")
            if (dataset) {
                app.setDataset(+dataset)
            } else {
                app.setDataset(list[0].id)
            }
        }
        times.reloaded("datasets")
    }

    async function loadUsers() {
        try {
            const list = await loadAllUsers()
            app.setGlobalUsers(list)
        } catch {
            toast.error("error loading users")
        }

        if (!ds.value) return;
        try {
            const list = await loadUsersByDataset(ds.value)
            app.setUsers(list)
        } catch {
            toast.error("error loading users for dataset")
        }
        times.reloaded("users")
    }

    async function loadCodes() {
        if (!ds.value) return;
        try {
            const data = await loadCodesByDataset(ds.value)
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
            const result = await loadItemsByDataset(ds.value)
            updateAllGames(result);
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
            const result = await loadTagsByCode(app.oldCode)
            result.forEach(t => {
                t.parent = t.parent === null ? -1 : t.parent;
                t.path = toToTreePath(t, result);
                t.pathNames = t.path.map(dd => result.find(tmp => tmp.id === dd).name).join(" / ")
            });
            result.sort(sortObjByString("name"))
            DM.setData("tags_old", result)
            DM.setDerived("tags_old_path", "tags", d => ({ id: d.id, path: toToTreePath(d, result) }))
            DM.setData("tags_old_name", new Map(result.map(d => ([d.id, d.name]))))
        } catch {
            toast.error("error loading old tags")
        }
        times.reloaded("tags_old")
    }
    async function loadTags() {
        if (!app.currentCode) return;
        try {
            const [result, irr] = await Promise.all([loadTagsByCode(app.currentCode), loadIrrByCode(app.currentCode)])
            DM.setData("tags_irr", new Map(irr.tags.map(d => ([d.tag_id, d.alpha]))))
            DM.setData("items_irr", new Map(irr.items.map(d => ([d.item_id, d.alpha]))))

            result.forEach(t => {
                t.parent = t.parent === null ? -1 : t.parent;
                t.path = toToTreePath(t, result);
                t.pathNames = t.path.map(dd => result.find(tmp => tmp.id === dd).name).join(" / ")
                t.valid = true

                if (app.editTag === t.id) {
                    app.editTagObj = t
                }
            });
            result.sort(sortObjByString("name"))
            DM.setData("tags", result)
            DM.setDerived("tags_path", "tags", d => ({ id: d.id, path: toToTreePath(d, result) }))
            DM.setData("tags_name", new Map(result.map(d => ([d.id, d.name]))))
        } catch {
            toast.error("error loading tags")
        }
        times.reloaded("tags")
    }
    async function loadDataTags(update=true) {
        if (!app.currentCode) return;
        try {
            const result = await loadDataTagsByCode(app.currentCode)
            const irr = await loadIrrByCode(app.currentCode)
            DM.setData("tags_irr", new Map(irr.tags.map(d => ([d.tag_id, d.alpha]))))
            DM.setData("items_irr", new Map(irr.items.map(d => ([d.item_id, d.alpha]))))

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

                            // count tags (overall)
                            tagCounts.set(t.id, tagCounts.get(t.id)+1)
                            // count tags (per user)
                            const pu = userTagCounts.get(t.id)
                            pu.set(dt.created_by, (pu.get(dt.created_by) || 0) + 1)
                            // save user/coder
                            coders.add(dt.created_by)

                            if (!m.has(t.id)) {
                                g.allTags.push({
                                    id: t.id,
                                    name: t.name,
                                    created_by: t.created_by,
                                    path: t.path ? t.path : toToTreePath(t, tags),
                                    pathNames: t.pathNames
                                });
                            }
                            m.add(t.id)
                            dt.name = t.name
                            dt.path = t.path ? t.path : toToTreePath(t, tags)
                            dt.pathNames = t.pathNames
                        })

                        g.tags = array.filter(d => d.pathNames !== undefined)
                        g.tags.sort(sortFunc)
                        g.allTags.sort(sortFunc)
                        g.numTags = g.allTags.length
                        g.numCoders = coders.size;
                        g.coders = Array.from(coders.values())
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
            const result = await loadEvidenceByCode(app.currentCode)
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
            const result = await loadTagAssignmentsByCodes(app.oldCode, app.newCode);
            DM.setData("tag_assignments", result);
        } catch {
            toast.error("error loading tag assignments")
        }
        times.reloaded("tag_assignments")
    }
    async function loadCodeTransitions() {
        if (!ds.value) return;
        try {
            const result = await loadCodeTransitionsByDataset(ds.value);
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
            const result = await loadExtGroupsByCode(app.currentCode);
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
                loadExternalizationsByCode(app.currentCode),
                loadExtConnectionsByCode(app.currentCode)
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
            const result = await loadExtCategoriesByCode(app.currentCode)
            result.forEach(d => {
                d.parent = d.parent ? d.parent : -1;
                d.is_leaf = result.find(dd => dd.parent === d.id) === undefined
            });
            DM.setData("meta_categories", result);
            DM.setDerived("meta_cats_path", "meta_categories", d => ({ id: d.id, path: toToTreePath(d, result) }))
        } catch {
            toast.error("error loading externalization categories")
        }
        times.reloaded("meta_categories")
    }
    async function loadExtAgreements(update=true) {
        if (!app.currentCode) return;
        try {
            const result = await loadExtAgreementsByCode(app.currentCode)
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
            const result = await loadItemExpertiseByDataset(ds.value)
            if (update && DM.hasData("items")) {
                const items = DM.getData("items", false)
                items.forEach(d => d.expertise = result.filter(e => e.item_id === d.id));
                DM.setData("items", items)
            }
            DM.setData("item_expertise", result);
        } catch {
            toast.error("error loading game expertise")
        }
        times.reloaded("item_expertise")
    }


    function updateAllGames(passed=null) {
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

            if (groupDT.has(g.id)) {
                const array = groupDT.get(g.id)
                const m = new Set()
                const coders = new Set()
                array.forEach(dt => {
                    const t = tags.find(d => d.id === dt.tag_id)
                    if (!t) return;
                    // count tags (overall)
                    tagCounts.set(t.id, tagCounts.get(t.id)+1)
                    // count tags (per user)
                    const pu = userTagCounts.get(t.id)
                    pu.set(dt.created_by, (pu.get(dt.created_by) || 0) + 1)
                    // save user/coder
                    coders.add(dt.created_by)

                    if (!m.has(t.id)) {
                        g.allTags.push({
                            id: t.id,
                            name: t.name,
                            created_by: t.created_by,
                            path: t.path ? t.path : toToTreePath(t, tags),
                            pathNames: t.pathNames
                        });
                    }
                    m.add(t.id)
                    dt.name = t.name
                    dt.path = t.path ? t.path : toToTreePath(t, tags)
                    dt.pathNames = t.pathNames
                })

                g.tags = array.filter(d => d.name !== undefined)
                g.tags.sort(sortFunc)
                g.allTags.sort(sortFunc)
                g.numTags = g.allTags.length
                g.numCoders = coders.size
                g.coders = Array.from(coders.values())
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
            DM.setData("items", data)
        }
    }

    async function fetchServerUpdate(giveToast=false) {
        if (app.static) return

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
        return setInterval(fetchServerUpdate.bind(false), 30000)
    }
    function stopPolling(handler) {
        clearInterval(handler)
    }

    app.static = APP_BUILD_TYPE == "static";

    onMounted(async () => {
        const startPage = Cookies.get("start-page")
        if (startPage) {
            settings.activeTab = startPage;
        }

        checkReload()
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
            app.activeUserId = -1;
            app.showAllUsers = true;
            init()
        }
    });

    watch(() => times.n_all, async function() {
        const showToast = initialized.value
        if (showToast) toast.info("reloading all data..")
        showOverlay.value = true
        await loadData();
        showOverlay.value = false
        if (showToast) toast.success("reloaded data")
        times.reloaded("all")
    });

    watch(ds, async function() {
        DM.clear()
        const prevDs = +Cookies.get("dataset_id")
        // load codes
        await loadCodes();
        const prevCode = +Cookies.get("code_id")
        // set code as previously stored or last one in the list
        if (prevDs && prevDs === ds.value && prevCode && app.codes.some(d => d.id === prevCode)) {
            app.setActiveCode(prevCode)
        } else {
            app.setActiveCode(app.codes.at(-1).id);
        }

        // load transitions
        await loadCodeTransitions()
        const prevTrans = +Cookies.get("trans_id")
        // set transition as previously stored or last one in the list
        if (app.transitions.length > 0) {
            if (prevDs === ds.value && prevTrans && app.transitions.some(d => d.id === prevTrans)) {
                app.setActiveTransition(prevTrans)
            } else {
                app.setActiveTransition(app.transitions.at(-1).id);
            }
        } else {
            app.setActiveTransition(null)
        }
        // overwrite cookies
        Cookies.set("dataset_id", ds.value, { expires: 365 })
        times.needsReload("all");
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

        watch(() => times.n_datasets, loadAllDatasets);
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

        watch(activeUserId, async (now, prev) => {
            askUserIdentity.value = now === null;
            if (prev === null && now !== null) {
                if (ds.value === null || app.currentCode === null) {
                    loadAllDatasets()
                } else {
                    times.needsReload("all")
                }
            } else {
                updateAllGames();
            }
        });
        watch(fetchUpdateTime, () => fetchServerUpdate(true))
    }

</script>

<style scoped>
.main-tabs {
    position: sticky;
    top: 0;
    left: 0;
    z-index: 1999;
    width: 100vw;
}
</style>