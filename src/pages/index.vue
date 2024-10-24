<template>
    <main>
        <v-overlay v-if="!initialized" v-model="isLoading" class="d-flex justify-center align-center">
            <v-progress-circular indeterminate size="64" color="white"></v-progress-circular>
        </v-overlay>

        <div density="compact" rounded="0">
            <v-tabs v-model="activeTab" color="secondary" bg-color="grey-darken-3" align-tabs="center" density="compact" @update:model-value="checkReload">
                <v-tab value="exploration">Exploration</v-tab>
                <v-tab value="coding">Coding</v-tab>
                <v-tab value="transition">Transition</v-tab>
            </v-tabs>

            <v-window v-model="activeTab">
                <v-window-item value="coding">
                    <IdentitySelector v-model="askUserIdentity" @select="app.setActiveUser"/>
                    <CodingView :time="dataTime" :loading="isLoading" @update="dataTime = Date.now()"/>
                </v-window-item>

                <v-window-item value="transition">
                    <IdentitySelector v-model="askUserIdentity" @select="app.setActiveUser"/>
                    <TransitionView :time="dataTime" :loading="isLoading" @update="dataTime = Date.now()"/>
                </v-window-item>

                <v-window-item value="exploration">
                    <ExplorationView :time="dataTime"/>
                </v-window-item>
            </v-window>
        </div>

        <GlobalShortcuts/>
    </main>
</template>

<script setup>

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { useToast } from "vue-toastification";
    import CodingView from '@/components/views/CodingView.vue'
    import { storeToRefs } from 'pinia'
    import { ref, onMounted, watch } from 'vue'
    import DM from '@/use/data-manager'
    import { loadCodesByDataset, loadCodeTransitionsByDataset, loadDataTagsByCode, loadEvidenceByCode, loadExtAgreementsByCode, loadExtCategoriesByCode, loadExtConnectionsByCode, loadExternalizationsByCode, loadGamesByDataset, loadTagAssignmentsByCodes, loadTagsByCode, loadUsersByDataset, toToTreePath } from '@/use/utility';
    import { useSettings } from '@/store/settings';
    import { group } from 'd3';
    import { useTimes } from '@/store/times';
    import GlobalShortcuts from '@/components/GlobalShortcuts.vue';

    const toast = useToast();
    const loader = useLoader()
    const settings = useSettings();
    const app = useApp()
    const times = useTimes()

    const isLoading = ref(false);
    const dataTime = ref(Date.now())
    const askUserIdentity = ref(false);

    const {
        ds,
        showAllUsers,
        activeUserId,
        activeCode,
        activeTransition,
        initialized,
        selectionTime
    } = storeToRefs(app);

    const { activeTab } = storeToRefs(settings)

    function checkReload() {
        switch (activeTab.value) {
            case "coding":
                app.cancelCodeTransition();
                break;
            default:
                app.startCodeTransition();
                loadOldTags();
        }
    }

    async function init(force) {
        if (!initialized.value) {
            isLoading.value = true;
            await loader.get("datasets").then(list => {
                app.setDatasets(list)
                times.reloaded("datasets")
            })
            await loadData();
            DM.setFilter("tags", "is_leaf", 1)
            DM.setFilter("tags_old", "is_leaf", 1)
        } else if (force) {
            await loadData();
            DM.setFilter("tags", "is_leaf", 1)
            DM.setFilter("tags_old", "is_leaf", 1)
        } else {
            dataTime.value = Date.now()
        }
    }

    async function loadData() {
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
        ])
        // add data to games
        await loadGames();
        if (!initialized.value) {
            initialized.value = true;
        }
        if (!app.activeUserId) {
            askUserIdentity.value = true;
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
            DM.setData("games", result)
            updateAllGames();
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
            result.sort((a, b) => {
                const nameA = a.name.toLowerCase(); // ignore upper and lowercase
                const nameB = b.name.toLowerCase(); // ignore upper and lowercase
                if (nameA < nameB) { return -1; }
                if (nameA > nameB) { return 1; }
                // names must be equal
                return 0;
            })
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
            result.sort((a, b) => {
                const nameA = a.name.toLowerCase(); // ignore upper and lowercase
                const nameB = b.name.toLowerCase(); // ignore upper and lowercase
                if (nameA < nameB) { return -1; }
                if (nameA > nameB) { return 1; }
                // names must be equal
                return 0;
            })
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
                const userOnly = !showAllUsers.value;

                data.forEach(d => {
                    d.tags = [];
                    d.allTags = [];
                });

                result.forEach(d => {

                    const g = data.find(dd => dd.id === d.game_id);
                    if (!g) return;

                    const t = tags.find(dd => dd.id === d.tag_id)
                    if (!t) return;

                    if (!userOnly || d.created_by === app.activeUserId) {
                        g.tags.push({
                            id: d.id,
                            tag_id: t.id,
                            name: t.name,
                            created_by: d.created_by,
                            path: t.path ? t.path.slice() : toToTreePath(t, tags)
                        });
                    }

                    if (!g.allTags.find(dd => dd.id === t.id)) {
                        g.allTags.push({
                            id: t.id,
                            name: t.name,
                            created_by: t.created_by,
                            path: t.path ? t.path.slice()  : toToTreePath(t, tags)
                        });
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
                data.forEach(d => d.numEvidence = g.has(d.id) ? g.get(d.id).length : 0);
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
            const [result, [catc, tagc]] = await Promise.all([
                loadExternalizationsByCode(app.currentCode),
                loadExtConnectionsByCode(app.currentCode)
            ]);
            DM.setData("ext_cat_connections", catc);
            DM.setData("ext_tag_connections", tagc);
            const agree = DM.getData("ext_agreements")
            result.forEach(d => {
                d.categories = catc.filter(c => c.ext_id === d.id);
                d.tags = tagc.filter(t => t.ext_id === d.id);
                const ld = agree.filter(dd => dd.ext_id === d.id)
                d.likes = ld ? ld.filter(dd => dd.value > 0) : []
                d.dislikes = ld ? ld.filter(dd => dd.value < 0) : []
            });
            if (update && DM.hasData("games")) {
                const data = DM.getData("games", false)
                const g = group(result, d => d.game_id)
                data.forEach(d => d.numExt = g.has(d.id) ? g.get(d.id).length : 0);
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
                const exts = DM.getData("externalizations")
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

    function updateAllGames() {
        const data = DM.getData("games", false)
        if (!data) {
            return console.warn("missing data")
        }

        const userOnly = !showAllUsers.value;
        const dts = DM.getData("datatags", false);
        const tags = DM.getData("tags", false);
        const ev = DM.getData("evidence", false);
        const ext = DM.getData("externalizations", false);

        data.forEach(d => {
            d.tags = [];
            d.allTags = [];
            d.numEvidence = ev.reduce((acc, e) => acc + (e.game_id === d.id ? 1 : 0), 0);
            d.numExt = ext.reduce((acc, e) => acc + (e.game_id === d.id ? 1 : 0), 0);
        });

        dts.forEach(d => {

            const g = data.find(dd => dd.id === d.game_id);
            if (!g) return;

            const t = tags.find(dd => dd.id === d.tag_id)
            if (!t) return;

            if (!userOnly || d.created_by === app.activeUserId) {
                g.tags.push({
                    id: d.id,
                    tag_id: t.id,
                    name: t.name,
                    created_by: d.created_by,
                    path: t.path ? t.path.slice() : toToTreePath(t, tags)
                });
            }

            if (!g.allTags.find(dd => dd.id === t.id)) {
                g.allTags.push({
                    id: t.id,
                    name: t.name,
                    created_by: t.created_by,
                    path: t.path ? t.path.slice()  : toToTreePath(t, tags)
                });
            }
        });

        data.forEach(d => {
            d.tags.sort((a, b) => {
                const nameA = a.name.toLowerCase(); // ignore upper and lowercase
                const nameB = b.name.toLowerCase(); // ignore upper and lowercase
                if (nameA < nameB) { return -1; }
                if (nameA > nameB) { return 1; }
                // names must be equal
                return 0;
            })

            d.allTags.sort((a, b) => {
                const nameA = a.name.toLowerCase(); // ignore upper and lowercase
                const nameB = b.name.toLowerCase(); // ignore upper and lowercase
                if (nameA < nameB) { return -1; }
                if (nameA > nameB) { return 1; }
                // names must be equal
                return 0;
            })
        });

        dataTime.value = Date.now();
    }

    function filterByVisibility() {
        if (showAllUsers.value) {
            DM.removeFilter("datatags", "created_by")
        } else {
            DM.setFilter("datatags", "created_by", activeUserId.value)
        }
        updateAllGames();
    }

   onMounted(() => init(true));

   watch(() => times.n_all, async function() {
        await loadData();
        times.reloaded("all")
        toast.info("reloaded data", { timeout: 2000 })
    });
    watch(() => times.n_coding, async function() {
        isLoading.value = true;
        await loadTags();
        await loadDataTags(false);
        await Promise.all([
            loadEvidence(false),
            loadCodeTransitions(),
            loadExtCategories(),
            loadExtAgreements(false),
            loadExternalizations(false)
        ])
        updateAllGames();
        isLoading.value = false;
        times.reloaded("coding")
    });
    watch(() => times.n_transition, async function() {
        isLoading.value = true;
        await loadAllTags();
        await loadDataTags();
        await Promise.all([
            loadEvidence(false),
            loadTagAssignments(),
            loadCodeTransitions(),
            loadExtCategories(),
            loadExtAgreements(false),
            loadExternalizations(false),
        ])
        updateAllGames();
        isLoading.value = false;
        times.reloaded("transition")
    });
    watch(() => times.n_tagging, async function() {
        isLoading.value = true;
        await loadAllTags();
        await loadDataTags();
        isLoading.value = false;
        times.reloaded("tagging")
    });

    watch(() => times.n_games, loadGames);
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

    watch(activeUserId, () => {
        askUserIdentity.value = activeUserId.value === null;
        filterByVisibility();
    });
    watch(showAllUsers, filterByVisibility)
    watch(selectionTime, updateAllGames)

</script>
