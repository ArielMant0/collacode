<template>
    <div class="d-flex pa-2">
        <aside style="min-width: 250px; max-width: 300px;">
            <v-select v-if="datasets"
                v-model="ds"
                :items="datasets"
                class="mb-2"
                density="compact"
                hide-details
                @update:model-value="app.needsReload()"
                item-title="name"
                item-value="id"/>

            <v-btn block prepend-icon="mdi-refresh" class="mb-2" color="primary" @click="app.needsReload()">reload data</v-btn>

            <v-card v-if="code" class="pa-3 mt-2 mb-2 text-caption">

                <v-select :model-value="activeCode"
                    class="mb-2"
                    density="compact"
                    hide-details
                    :items="codes"
                    :disabled="view !== 'coding'"
                    item-title="name"
                    item-value="id"
                    @update:model-value="setActiveCode"/>

                <v-textarea v-model="codeDesc"
                    hide-details
                    hide-spin-buttons
                    density="compact"
                    class="mb-2"/>

                <v-btn :disabled="!codeDescChanges"
                    :color="codeDescChanges ? 'tertiary' : ''"
                    block density="comfortable"
                    prepend-icon="mdi-sync"
                    @click="updateCode">
                    sync
                </v-btn>
            </v-card>

            <div class="mb-2">
                <v-btn v-if="view === 'transition'" block prepend-icon="mdi-transfer-left" color="secondary" @click="app.cancelCodeTransition">Coding View</v-btn>
                <v-btn v-else block prepend-icon="mdi-transfer-right" color="primary" @click="app.startCodeTransition">Transition View</v-btn>
            </div>

            <v-card v-if="view === 'transition'" class="mb-2">
                <CodingTransitionSettings/>
            </v-card>

            <v-card class="mb-2">
                <v-switch v-if="view === 'coding'"
                    :model-value="showAllUsers"
                    class="ml-4"
                    density="compact"
                    label="show data for all users"
                    color="primary"
                    hide-details
                    hide-spin-buttons
                    @update:model-value="toggleUserVisibility"/>

                <UserPanel/>
            </v-card>

            <SelectedTagsViewer v-if="view === 'coding' || transitionCode"/>
        </aside>

        <IdentitySelector v-model="askUserIdentity" @select="app.setActiveUser"/>

        <div style="width: 100%;">

            <v-overlay :model-value="isLoading" class="align-center justify-center" contained opacity="0.6">
                <v-progress-circular indeterminate size="64" color="white"></v-progress-circular>
            </v-overlay>

            <div v-if="initialized" class="d-flex flex-column pa-2">

                <TagOverview v-if="view === 'coding' || transitionCode"/>

                <CodingTransition v-if="view === 'transition' && transitionCode && activeCode"
                    :old-code="activeCode" :new-code="transitionCode"/>

                <div v-if="view === 'coding' || transitionCode">
                    <h3 style="text-align: center" class="mt-4 mb-4">GAMES</h3>
                    <RawDataView
                        :data="allData.games"
                        :time="allData.time"
                        :headers="headers"
                        selectable
                        editable
                        :allow-add="view === 'coding'"
                        @add-empty-row="addNewGame"
                        @add-rows="addGames"
                        @delete-rows="deleteGames"
                        @update-rows="updateGames"
                        @add-datatags="addDataTags"
                        @delete-datatags="deleteDataTags"
                        @update-datatags="updateDataTags"
                        />
                </div>

                <div v-if="view === 'coding' || transitionCode">
                    <h3 style="text-align: center" class="mt-4 mb-4">TAGS</h3>
                    <TagInspector source="tags" can-edit can-delete></TagInspector>
                </div>


                <div v-if="view === 'coding' || transitionCode">
                    <h3 style="text-align: center" class="mt-4 mb-2">EVIDENCE</h3>
                    <EvidenceInspector/>
                </div>
            </div>

        </div>
    </div>
</template>

<script setup>
    import TagOverview from '@/components/tags/TagOverview.vue';
    import IdentitySelector from '@/components/IdentitySelector.vue';
    import RawDataView from '@/components/RawDataView.vue';
    import UserPanel from '@/components/UserPanel.vue';
    import EvidenceInspector from '@/components/EvidenceInspector.vue';
    import CodingTransition from '@/components/CodingTransition.vue';
    import CodingTransitionSettings from '@/components/CodingTransitionSettings.vue';
    import TagInspector from '@/components/tags/TagInspector.vue';
    import SelectedTagsViewer from '@/components/tags/SelectedTagsViewer.vue';

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { reactive, onMounted, watch, computed } from 'vue'
    import { useToast } from "vue-toastification";
    import DM from '@/use/data-manager'
    import { toToTreePath } from '@/use/utility';

    const toast = useToast();

    const loader = useLoader()
    const app = useApp()
    const {
        ds, datasets,
        showAllUsers,
        activeUserId,
        view, transitionCode,
        activeCode, code, codes,
        initialized, dataNeedsReload
    } = storeToRefs(app);

    const isLoading = ref(false);
    const codeDesc = ref("");
    const codeDescChanges = computed(() => code.value && codeDesc.value !== code.value.description)
    const askUserIdentity = ref(false);
    const allData = reactive({ games: [], time: null });

    const headers = [
        // { title: "ID", key: "id", type: "id" },
        { title: "Name", key: "name", type: "string" },
        { title: "Year", key: "year", type: "integer", width: "100px" },
        { title: "Played", key: "played", type: "integer", width: "50px" },
        { title: "Tags", key: "tags", type: "array", width: "35%" },
        { title: "URL", key: "url", type: "url", width: "200px" },
    ];

    async function loadData() {
        isLoading.value = true;
        await loadCodes();
        return Promise.all([
            loadTags(),
            loadDataTags(),
            loadEvidence(),
            loadTagAssignments(),
            loadCodeTransitions()
        ]).then(async () => {
            await loadGames();
            if (!initialized.value) {
                initialized.value = true;
            }
            app.setReloaded()
            isLoading.value = false;
            if (!activeUserId.value || app.users.find(d => d.id === activeUserId.value) === null) {
                askUserIdentity.value = true;
            }
        });
    }

    async function loadCodes() {
        if (!ds.value) return;
        return loader.get(`codes/dataset/${ds.value}`).then(data => {
            DM.setData("codes", data);
            app.codes = data;
            if (activeCode.value === null && data.length > 0) {
                app.setActiveCode(data[0].id);
            }
            if (activeCode.value) {
                codeDesc.value = code.value.description
            }
            app.setReloaded("codes")
        })
    }
    async function loadGames() {
        if (ds.value === null) return;
        const result = await loader.get(`games/dataset/${ds.value}`)
        DM.setData("games", result)
        updateAllGames();
        return app.setReloaded("games")
    }
    async function loadTags() {
        if (activeCode.value === null) return;
        const c = app.view === 'transition' && app.transitionCode ? app.transitionCode : activeCode.value
        const result = await loader.get(`tags/code/${c}`)
        result.forEach(t => {
            t.path = toToTreePath(t, result),
            t.pathNames = t.path.map(dd => result.find(tmp => tmp.id === dd).name).join("/")
        });
        DM.setData("tags", result)
        return app.setReloaded("tags")
    }
    async function loadDataTags() {
        if (activeCode.value === null) return;
        const c = app.view === 'transition' && app.transitionCode ? app.transitionCode : activeCode.value
        const result = await loader.get(`datatags/code/${c}`)
        DM.setData("datatags", result)
        return app.setReloaded("datatags")
    }
    async function loadEvidence() {
        if (activeCode.value === null) return;
        const c = app.view === 'transition' && app.transitionCode ? app.transitionCode : activeCode.value
        const result = await loader.get(`evidence/code/${c}`)
        DM.setData("evidence", result)
        return app.setReloaded("evidence")
    }
    async function loadTagAssignments() {
        if (activeCode.value === null || app.transitionCode === null) return;
        const result = await loader.get(`tag_assignments/old/${activeCode.value}/new/${app.transitionCode}`);
        DM.setData("tag_assignments", result);
        return app.setReloaded("tag_assignments")
    }
    async function loadCodeTransitions() {
        if (!ds.value) return;
        if (activeCode.value === null) {
            const result = await loader.get(`code_transitions/dataset/${ds.value}`);
            DM.setData("code_transitions", result);
            return app.setReloaded("code_transitions")
        } else if (app.transitionCode === null) {
            const result = await loader.get(`code_transitions/code/${activeCode.value}`);
            DM.setData("code_transitions", result);
            return app.setReloaded("code_transitions")
        } else {
            const result = await loader.get(`code_transitions/old/${activeCode.value}/new/${app.transitionCode}`);
            DM.setData("code_transitions", result);
            return app.setReloaded("code_transitions")
        }
    }

    function updateAllGames() {
        const data = DM.getData("games")
        if (!data) return;
        const games = DM.getData("games", false);
        const dts = DM.getData("datatags", app.view === "coding");
        const tags = DM.getData("tags", false);
        const ev = DM.getData("evidence", false);
        data.forEach(d => {
            d.tags = [];
            d.numEvidence = ev.reduce((acc, e) => acc + (e.game_id === d.id ? 1 : 0), 0);
        });

        dts.forEach(d => {

            const g = games.find(dd => dd.id === d.game_id);
            if (!g) return;

            const t = tags.find(dd => dd.id === d.tag_id)
            if (!t) return;

            g.tags.push({
                id: d.id,
                tag_id: t.id,
                name: t.name,
                created_by: d.created_by,
                path: t.path ? t.path : toToTreePath(t)
            });
        });

        data.forEach(d => d.tags.sort((a, b) => {
            const nameA = a.name.toLowerCase(); // ignore upper and lowercase
            const nameB = b.name.toLowerCase(); // ignore upper and lowercase
            if (nameA < nameB) { return -1; }
            if (nameA > nameB) { return 1; }
            // names must be equal
            return 0;
        }));

        allData.games = data;
        allData.time = Date.now();
        console.debug("updated games")
    }


    async function init(force) {
        if (!initialized.value) {
            isLoading.value = true;
            await loader.get("datasets").then(list => {
                app.setDatasets(list)
                app.setReloaded("datasets")
            })
            await loader.get(`users/dataset/${ds.value}`).then(list => {
                app.setUsers(list)
                app.setReloaded("users")
            });
            DM.setFilter("tags", "is_leaf", 1)
            DM.setFilter("tags_old", "is_leaf", 1)
            return loadData();
        } else if (force) {
            return loadData();
        } else {
            allData.time = Date.now()
        }
    }

    function addNewGame() {
        allData.games = DM.push("games", {
            dataset_id: ds.value,
            id: null,
            name: "ADD TITLE",
            year: new Date().getFullYear(),
            played: 0,
            url: "https://store.steampowered.com/",
            tags: [],
            edit: true
        });
        allData.time = Date.now();
    }
    function addGames(games) {
        loader.post("add/games", { rows: games, dataset: ds.value })
            .then(() => {
                toast.success("added " + games.length + " game(s)")
                app.needsReload("games")
            })
    }
    function deleteGames(ids) {
        loader.post(`delete/games`, { ids: ids })
            .then(() => {
                toast.success("deleted " + ids.length + " game(s)")
                app.needsReload("games")
            })
    }
    function updateGames(games) {
        loader.post("update/games", { rows: games })
            .then(() => {
                toast.success("updated " + games.length + " game(s)")
                app.needsReload("games")
            })
    }

    function addDataTags(datatags) {
        loader.post("add/datatags", { rows: datatags })
            .then(() => {
                toast.success("added " + datatags.length + " datatag(s)")
                app.needsReload(app.view)
            })
    }
    function deleteDataTags(datatags) {
        loader.post("delete/datatags", { ids: datatags })
            .then(() => {
                toast.success("delete " + datatags.length + " datatag(s)")
                app.needsReload(app.view)
            })
    }
    function updateDataTags(game) {

        const body = {
            game_id: game.id,
            user_id: activeUserId.value,
            code_id: app.currentCode,
            created: Date.now(),
        };
        body.tags = game.tags
            .filter(t => (app.view === 'transition' && app.transitionCode) || t.created_by === activeUserId.value)
            .map(t => {
                if (t.tag_id !== null) {
                    return  { tag_id: t.tag_id };
                }
                return { tag_name: t.name, description: t.description }
            })

        loader.post("update/game/datatags", body)
            .then(() => {
                toast.success("updated tags for " + game.name)
                app.needsReload("coding")
            })
    }

    function toggleUserVisibility() {
        app.toggleUserVisibility();
        filterByVisibility();
    }

    function filterByVisibility() {
        if (showAllUsers.value) {
            DM.removeFilter("datatags", "created_by")
        } else {
            DM.setFilter("datatags", "created_by", activeUserId.value)
        }
        updateAllGames();
    }

    function setActiveCode(id) {
        app.setActiveCode(id);
        app.needsReload();
    }
    function updateCode() {
        if (activeCode.value && codeDescChanges.value) {
            loader.post("update/codes", { rows: [{ id: activeCode.value, name: code.value.name, description: codeDesc.value }] })
                .then(() => {
                    code.value.description = codeDesc.value
                    toast.success("updated code description for code" + code.value.name)
                })
        }
    }

    onMounted(() => init(true));

    watch(() => dataNeedsReload.value._all, async function() {
        await loadData();
        toast.info("reloaded data", { timeout: 2000 })
    });
    watch(() => dataNeedsReload.value.coding, async function() {
        await loadTags();
        await loadDataTags();
        app.setReloaded("coding")
    });

    watch(() => app.dataLoading.transition, function(val) {
        if (val === false) {
            updateAllGames();
        }
    });
    watch(() => app.dataLoading.coding, function(val) {
        if (val === false) {
            updateAllGames();
        }
    });
    watch(() => ([app.dataLoading.datatags, app.dataLoading.evidence]), function(val) {
        if (val.some(d => d === false)) {
            updateAllGames();
        }
    });

    watch(() => dataNeedsReload.value.games, loadGames);
    watch(() => dataNeedsReload.value.codes, loadCodes);
    watch(() => dataNeedsReload.value.tags, loadTags);
    watch(() => dataNeedsReload.value.datatags, loadDataTags);
    watch(() => dataNeedsReload.value.evidence, loadEvidence);

    watch(activeUserId, () => {
        askUserIdentity.value = activeUserId.value === null;
        filterByVisibility();
    });
    watch(showAllUsers, filterByVisibility)
    watch(() => app.selectionTime, updateAllGames)
    watch(() => app.view, function() {
        if (app.view === "coding") {
            app.needsReload();
        }
    })
</script>
