<template>
    <main>
        <v-overlay v-if="!initialized" v-model="isLoading" class="d-flex justify-center align-center" persistent>
            <v-progress-circular indeterminate size="64" color="white"></v-progress-circular>
        </v-overlay>
        <GlobalShortcuts/>
        <GlobalTooltip/>

        <IdentitySelector v-model="askUserIdentity" @select="app.setActiveUser"/>

        <v-tabs v-model="activeTab" class="main-tabs" color="secondary" bg-color="grey-darken-3" align-tabs="center" density="compact" @update:model-value="checkReload">
            <v-tab value="explore_exts">Explore Externalizations</v-tab>
            <v-tab value="explore_tags">Explore Tags</v-tab>
            <v-tab value="coding">Coding</v-tab>
            <v-tab value="transition">Transition</v-tab>
        </v-tabs>

        <div>

            <MiniNavBar v-if="activeTab === 'transition'"
                :user-color="app.activeUser ? app.activeUser.color : 'default'"
                :code-name="app.activeCode ? app.getCodeName(app.oldCode) : '?'"
                :other-code-name="app.transitionData ? app.getCodeName(app.newCode) : '?'"/>
            <MiniNavBar v-else
                :user-color="app.activeUser ? app.activeUser.color : 'default'"
                :code-name="app.activeCode ? app.getCodeName(app.activeCode) : '?'"/>


            <v-tabs-window v-model="activeTab">
                <v-tabs-window-item value="coding">
                    <CodingView v-if="activeUserId !== null" :loading="isLoading"/>
                </v-tabs-window-item>

                <v-tabs-window-item value="transition">
                    <TransitionView v-if="activeUserId !== null" :loading="isLoading"/>
                </v-tabs-window-item>

                <v-tabs-window-item value="explore_exts">
                    <ExploreExtView v-if="activeUserId !== null" :loading="isLoading"/>
                </v-tabs-window-item>

                <v-tabs-window-item value="explore_tags">
                    <ExploreTagsView v-if="activeUserId !== null" :loading="isLoading"/>
                </v-tabs-window-item>
            </v-tabs-window>


            <div v-if="initialized && !isLoading" class="mb-2 pa-4" style="margin-left: 80px;">

                <div style="text-align: center;">
                    <GameBarCodes :hidden="!showBarCodes"/>
                </div>

                <v-sheet class="mb-2 pa-2">
                    <h3 v-if="showTable" style="text-align: center" class="mt-4 mb-4">{{ stats.numGamesSel }} / {{ stats.numGames }} GAMES</h3>
                    <RawDataView
                        :hidden="!showTable"
                        selectable
                        editable
                        allow-add
                        check-assigned/>
                </v-sheet>

                <div style="text-align: center;">
                    <GameEvidenceTiles :hidden="!showEvidenceTiles" :code="currentCode"/>
                </div>

                <div style="text-align: center;">
                    <ExternalizationsList :hidden="!showExtTiles" show-bar-codes/>
                </div>
            </div>
        </div>
    </main>
</template>

<script setup>

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { useToast } from "vue-toastification";
    import CodingView from '@/components/views/CodingView.vue'
    import TransitionView from '@/components/views/TransitionView.vue'
    import ExploreExtView from '@/components/views/ExploreExtView.vue'
    import ExploreTagsView from '@/components/views/ExploreTagsView.vue';
    import { storeToRefs } from 'pinia'
    import { ref, onMounted, watch } from 'vue'
    import DM from '@/use/data-manager'
    import { loadCodesByDataset, loadCodeTransitionsByDataset, loadDataTagsByCode, loadEvidenceByCode, loadExtAgreementsByCode, loadExtCategoriesByCode, loadExtConnectionsByCode, loadExternalizationsByCode, loadExtGroupsByCode, loadGameExpertiseByDataset, loadGamesByDataset, loadTagAssignmentsByCodes, loadTagsByCode, loadUsersByDataset, toToTreePath } from '@/use/utility';
    import GlobalShortcuts from '@/components/GlobalShortcuts.vue';
    import IdentitySelector from '@/components/IdentitySelector.vue';
    import GameEvidenceTiles from '@/components/evidence/GameEvidenceTiles.vue';
    import RawDataView from '@/components/RawDataView.vue';
    import ExternalizationsList from '@/components/externalization/ExternalizationsList.vue';

    import { useSettings } from '@/store/settings';
    import { group } from 'd3';
    import { useTimes } from '@/store/times';
    import GlobalTooltip from '@/components/GlobalTooltip.vue';
    import MiniNavBar from '@/components/MiniNavBar.vue';
    import { sortObjByString } from '@/use/sorting';
    import GameBarCodes from '@/components/games/GameBarCodes.vue';

    const toast = useToast();
    const loader = useLoader()
    const settings = useSettings();
    const app = useApp()
    const times = useTimes()

    const isLoading = ref(false);
    const askUserIdentity = ref(false);

    const {
        ds,
        showAllUsers,
        activeUserId,
        activeCode,
        currentCode,
        activeTransition,
        initialized,
        fetchUpdateTime
    } = storeToRefs(app);

    const {
        activeTab,
        showTable,
        showBarCodes,
        showEvidenceTiles,
        showExtTiles
    } = storeToRefs(settings)

    const stats = reactive({ numGames: 0, numGamesSel: 0 })

    async function readStats() {
        if (showTable.value) {
            if (DM.hasData("games")) {
                stats.numGames = DM.getSize("games", false);
                stats.numGamesSel = DM.getSize("games", true);
            } else {
                stats.numGames = 0;
                stats.numGamesSel = 0;
            }
        }
    }

    function checkReload() {
        window.scrollTo(0, 0)
        switch (activeTab.value) {
            case "coding":
                app.cancelCodeTransition();
                showEvidenceTiles.value = false;
                showTable.value = true;
                showExtTiles.value = false;
                break;
            case "transition":
                app.startCodeTransition();
                showEvidenceTiles.value = false;
                showTable.value = false;
                showExtTiles.value = false;
                loadOldTags();
                break;
            case "explore_tags":
                app.cancelCodeTransition();
                showTable.value = false;
                showEvidenceTiles.value = true;
                showExtTiles.value = false;
                break;
            case "explore_exts":
                app.cancelCodeTransition();
                showTable.value = false;
                showEvidenceTiles.value = false;
                showExtTiles.value = true;
                break;
            default:
                app.cancelCodeTransition();
                showEvidenceTiles.value = false;
                showTable.value = false;
                showExtTiles.value = false;
                break;
        }
    }

    async function init(force) {
        if (!initialized.value) {
            await loader.get("datasets").then(list => {
                app.setDatasets(list)
                times.reloaded("datasets")
            })
            await loadUsers();
            askUserIdentity.value = activeUserId.value === null;
        } else if (force) {
            await loadData();
        }
    }

    async function loadData() {
        if (!app.activeUserId) { return }

        isLoading.value = true;
        await loadUsers();
        await loadCodes();
        await loadCodeTransitions()
        await Promise.all([
            loadAllTags(false),
            loadDataTags(false),
            loadEvidence(false),
            loadExtCategories(),
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

    async function loadUsers() {
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
            if (!activeCode.value && data.length > 0) {
                app.setActiveCode(data.at(-1).id);
            }
        } catch {
            toast.error("error loading codes for dataset")
        }
        times.reloaded("codes")
    }
    async function loadGames() {
        if (!ds.value) return;
        try {
            const result = await loadGamesByDataset(ds.value)
            updateAllGames(result);
        } catch {
            toast.error("error loading games for dataset")
        }
        times.reloaded("games")
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
        } catch {
            toast.error("error loading old tags")
        }
        times.reloaded("tags_old")
    }
    async function loadTags() {
        if (!app.currentCode) return;
        try {
            const result = await loadTagsByCode(app.currentCode)
            result.forEach(t => {
                t.parent = t.parent === null ? -1 : t.parent;
                t.path = toToTreePath(t, result);
                t.pathNames = t.path.map(dd => result.find(tmp => tmp.id === dd).name).join(" / ")
            });
            result.sort(sortObjByString("name"))
            DM.setData("tags", result)
        } catch {
            toast.error("error loading tags")
        }
        times.reloaded("tags")
    }
    async function loadDataTags(update=true) {
        if (!app.currentCode) return;
        try {
            const result = await loadDataTagsByCode(app.currentCode)
            if (update && DM.hasData("games") && DM.hasData("tags")) {
                const data = DM.getData("games", false)
                const tags = DM.getData("tags", false)

                const sortFunc = sortObjByString("name")
                const groupDT = group(result, d => d.game_id)

                data.forEach(g => {
                    g.tags = [];
                    g.allTags = [];

                    if (groupDT.has(g.id)) {
                        const array = groupDT.get(g.id)
                        const m = new Set()
                        array.forEach(dt => {
                            const t = tags.find(d => d.id === dt.tag_id)
                            if (!t) return;
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
                    }
                });
            }
            DM.setData("datatags", result)
        } catch {
            toast.error("error loading datatags")
        }
        times.reloaded("datatags")
    }
    async function loadEvidence(update=true) {
        if (!app.currentCode) return;
        try {
            const result = await loadEvidenceByCode(app.currentCode)
            if (update && DM.hasData("games")) {
                const data = DM.getData("games", false)
                const g = group(result, d => d.game_id)
                data.forEach(d => {
                    d.evidence = g.has(d.id) ? g.get(d.id) : []
                    d.numEvidence = d.evidence.length
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
            DM.setData("code_transitions", result);
            if (!app.activeTransition && result.length > 0) {
                app.setActiveTransition(result.at(-1).id)
            } else {
                app.transitions = result;
            }
        } catch {
            toast.error("error loading code transitions")
        }
        times.reloaded("code_transitions")
    }
    async function loadExternalizations(update=true) {
        if (!app.currentCode) return;
        try {
            const [groups, result, [catc, tagc, evc]] = await Promise.all([
                loadExtGroupsByCode(app.currentCode),
                loadExternalizationsByCode(app.currentCode),
                loadExtConnectionsByCode(app.currentCode)
            ]);
            DM.setData("ext_groups", groups);
            DM.setData("ext_cat_connections", catc);
            DM.setData("ext_tag_connections", tagc);
            DM.setData("ext_ev_connections", evc);

            const agree = DM.getData("ext_agreements", false)
            result.forEach(d => {
                d.game_id = groups.find(g => g.id === d.group_id).game_id
                d.code_id = app.currentCode;
                d.categories = catc.filter(c => c.ext_id === d.id);
                d.tags = tagc.filter(t => t.ext_id === d.id);
                d.evidence = evc.filter(t => t.ext_id === d.id);
                const ld = agree.filter(dd => dd.ext_id === d.id)
                d.likes = ld ? ld.filter(dd => dd.value > 0) : []
                d.dislikes = ld ? ld.filter(dd => dd.value < 0) : []
            });
            if (update && DM.hasData("games")) {
                const data = DM.getData("games", false)
                const g = group(result, d => d.game_id)
                data.forEach(d => {
                    d.exts = g.has(d.id) ? g.get(d.id) : []
                    d.numExt = d.exts.length
                });
            }
            DM.setData("externalizations", result);
        } catch {
            toast.error("error loading externalizations")
        }
        times.reloaded("externalizations")
    }
    async function loadExtCategories() {
        if (!app.currentCode) return;
        try {
            const result = await loadExtCategoriesByCode(app.currentCode)
            result.forEach(d => {
                d.parent = d.parent ? d.parent : -1;
                d.is_leaf = result.find(dd => dd.parent === d.id) === undefined
            });
            DM.setData("ext_categories", result);
        } catch {
            toast.error("error loading externalization categories")
        }
        times.reloaded("ext_categories")
    }
    async function loadExtAgreements(update=true) {
        if (!app.currentCode) return;
        try {
            const result = await loadExtAgreementsByCode(app.currentCode)
            if (update && DM.hasData("externalizations")) {
                const exts = DM.getData("externalizations", false)
                exts.forEach(d => {
                    const ld = result.filter(dd => dd.ext_id === d.id)
                    d.likes = ld ? ld.filter(dd => dd.value > 0) : []
                    d.dislikes = ld ? ld.filter(dd => dd.value < 0) : []
                });
            }
            DM.setData("ext_agreements", result);
        } catch {
            toast.error("error loading externalization agreements")
        }
        times.reloaded("ext_agreements")
    }

    async function loadGameExpertise(update=true) {
        if (!ds.value) return;
        try {
            const result = await loadGameExpertiseByDataset(ds.value)
            if (update && DM.hasData("games")) {
                const games = DM.getData("games", false)
                games.forEach(d => d.expertise = result.filter(e => e.game_id === d.id));
                DM.setData("games", games)
            }
            DM.setData("game_expertise", result);
        } catch {
            toast.error("error loading game expertise")
        }
        times.reloaded("game_expertise")
    }


    function updateAllGames(passed=null) {
        if (!Array.isArray(passed) && !DM.hasData("games")) return console.warn("missing data")

        const data = Array.isArray(passed) ? passed : DM.getData("games", false)

        const tags = DM.getData("tags", false);

        const groupDT = group(DM.getData("datatags", false), d => d.game_id)
        const groupExp = group(DM.getData("game_expertise", false), d => d.game_id)
        const groupEv = group(DM.getData("evidence", false), d => d.game_id)
        const groupExt = group(DM.getData("externalizations", false), d => d.game_id)

        const sortFunc = sortObjByString("name")

        data.forEach(g => {
            g.expertise = groupExp.has(g.id) ? groupExp.get(g.id) : [];
            g.tags = [];
            g.allTags = [];
            g.evidence = groupEv.has(g.id) ? groupEv.get(g.id) : []
            g.exts = groupExt.has(g.id) ? groupExt.get(g.id) : []
            g.numEvidence = g.evidence.length
            g.numExt = g.exts.length

            if (groupDT.has(g.id)) {
                const array = groupDT.get(g.id)
                const m = new Set()
                array.forEach(dt => {
                    const t = tags.find(d => d.id === dt.tag_id)
                    if (!t) return;
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
            }
        });

        if (passed !== null) {
            DM.setData("games", data)
        }

        readStats();
    }

    function filterByVisibility() {
        if (showAllUsers.value) {
            DM.removeFilter("datatags", "created_by")
        } else {
            DM.setFilter("datatags", "created_by", activeUserId.value)
        }
        updateAllGames();
    }

    async function fetchServerUpdate(giveToast=false) {
        try {
            const resp = await loader.get("/lastupdate")
            if (resp.length === 0 || !initialized.value) {
                loadData()
            } else {
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

    onMounted(() => {
        let handler = startPolling()
        document.addEventListener("visibilitychange", () => {
            if (document.hidden) {
                stopPolling(handler)
            } else {
                handler = startPolling(true);
            }
        });
        init(true)
    });

   watch(() => times.n_all, async function() {
        await loadData();
        times.reloaded("all")
        toast.info("reloaded data", { timeout: 2000 })
    });
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

    watch(() => times.n_games, loadGames);
    watch(() => times.n_game_expertise, loadGameExpertise);
    watch(() => times.n_codes, loadCodes);
    watch(() => times.n_tags, loadTags);
    watch(() => times.n_tags_old, loadOldTags);
    watch(() => times.n_datatags, loadDataTags);
    watch(() => times.n_evidence, loadEvidence);
    watch(() => times.n_tag_assignments, loadTagAssignments);
    watch(() => times.n_code_transitions, loadCodeTransitions);
    watch(() => times.n_externalizations, loadExternalizations);
    watch(() => times.n_ext_categories, loadExtCategories);
    watch(() => times.n_ext_agreements, loadExtAgreements);

    watch(activeUserId, async (now, prev) => {
        askUserIdentity.value = now === null;
        if (prev === null && now !== null) {
            await fetchServerUpdate();
        } else {
            filterByVisibility();
        }
    });
    watch(showAllUsers, filterByVisibility)
    watch(fetchUpdateTime, () => fetchServerUpdate(true))

    watch(() => times.f_games, readStats)
    watch(showTable, readStats)

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