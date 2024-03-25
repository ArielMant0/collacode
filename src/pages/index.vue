<template>
    <div class="d-flex pa-2">
        <aside style="min-width: 250px; max-width: 300px;">
            <v-select v-model="ds"
                class="mb-2"
                density="compact"
                hide-details
                :items="datasets"
                @update:model-value="app.needsReload('_all')"
                item-title="name"
                item-value="id"/>

            <v-btn v-if="view === 'transition'" block prepend-icon="mdi-transfer-left" color="secondary" @click="app.cancelCodeTransition">Coding View</v-btn>
            <v-btn v-else block prepend-icon="mdi-transfer-right" color="primary" @click="app.startCodeTransition">Transition View</v-btn>

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

        </aside>

        <IdentitySelector v-model="askUserIdentity" @select="app.setActiveUser"/>

        <div style="width: 100%;">

            <v-overlay v-model="isLoading" class="align-center justify-center" contained opacity="0.6">
                <v-progress-circular indeterminate size="64" color="white"></v-progress-circular>
            </v-overlay>

            <div v-if="initialized" class="d-flex flex-column pa-2">

                <div v-if="view === 'transition'">
                    <CodingTransition v-if="transitionCode && activeCode"
                        :old-code="activeCode" :new-code="transitionCode"/>
                    <TagInspector source="tagsNew" can-edit can-delete/>
                </div>
                <TagOverview v-if="view === 'coding'"/>

                <div class="mt-2">
                    <RawDataView
                        :data="allData.games"
                        :time="allData.time"
                        :headers="headers"
                        selectable
                        :editable="view === 'coding'"
                        :allow-add="view === 'coding'"
                        @add-empty-row="addNewGame"
                        @add-rows="addGames"
                        @delete-rows="deleteGames"
                        @update-rows="updateGames"
                        @update-datatags="updateDataTags"
                        />
                </div>
                <TagInspector v-if="view === 'coding'" source="tags" can-edit can-delete></TagInspector>
                <EvidenceInspector/>
            </div>

        </div>
    </div>
</template>

<script setup>
    import TagOverview from '@/components/TagOverview.vue';
    import IdentitySelector from '@/components/IdentitySelector.vue';
    import RawDataView from '@/components/RawDataView.vue';
    import UserPanel from '@/components/UserPanel.vue';
    import EvidenceInspector from '@/components/EvidenceInspector.vue';
    import CodingTransition from '@/components/CodingTransition.vue';
    import CodingTransitionSettings from '@/components/CodingTransitionSettings.vue';
    import TagInspector from '@/components/TagInspector.vue';

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { reactive, onMounted, watch, computed } from 'vue'
    import { useToast } from "vue-toastification";
    import DM from '@/use/data-manager'

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
        { title: "Name", key: "name", type: "string", width: "35%" },
        { title: "Year", key: "year", type: "integer", width: "100px" },
        { title: "Played", key: "played", type: "integer", width: "50px" },
        { title: "Tags", key: "tags", type: "array" },
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
        return updateAllGames(result);
    }
    async function loadTags() {
        if (activeCode.value === null) return;
        const result = await loader.get(`tags/code/${activeCode.value}`)
        DM.setData("tags", result)
        return app.setReloaded("tags")
    }
    async function loadDataTags() {
        if (activeCode.value === null) return;
        const result = await loader.get(`datatags/code/${activeCode.value}`)
        DM.setData("datatags", result)
        return app.setReloaded("datatags")
    }
    async function loadEvidence() {
        if (activeCode.value === null) return;
        const result = await loader.get(`image_evidence/code/${activeCode.value}`)
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

    function updateAllGames(data) {
        app.setReloaded("games")
        const dts = DM.getData("datatags");
        const tags = DM.getData("tags");
        const ev = DM.getData("evidence");
        data.forEach(d => {
            d.tags = [];
            d.numEvidence = ev.reduce((acc, e) => acc + (e.game_id === d.id ? 1 : 0), 0);
        });

        dts.forEach(d => {
            const g = data.find(dd => dd.id === d.game_id);
            if (g) {
                const t = tags.find(dd => dd.id === d.tag_id)
                g.tags.push({
                    id: d.id,
                    tag_id: t.id,
                    name: t.name,
                    created_by: d.created_by,
                });
            }
        });

        data.forEach(d => d.tags.sort((a, b) => {
            const nameA = a.name.toLowerCase(); // ignore upper and lowercase
            const nameB = b.name.toLowerCase(); // ignore upper and lowercase
            if (nameA < nameB) { return -1; }
            if (nameA > nameB) { return 1; }
            // names must be equal
            return 0;
        }));

        DM.setData("games", data)
        allData.games = data;
        allData.time = Date.now();
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
            loadData();
        } else if (force) {
            loadData();
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
    function updateDataTags(game) {

        const body = {
            game_id: game.id,
            user_id: activeUserId.value,
            code_id: activeCode.value,
            created: Date.now(),
        };
        body.tags = game.tags
            .filter(t => t.created_by === activeUserId.value)
            .map(t => {
                if (t.tag_id !== null) {
                    return  { tag_id: t.tag_id };
                }
                return { tag_name: t.name, description: t.description }
            })

        loader.post("update/game/datatags", body)
            .then(() => {
                toast.success("added new tags to " + game.name)
                app.needsReload("tags")
                app.needsReload("datatags")
            })
    }

    function toggleUserVisibility() {
        app.toggleUserVisibility();
        filterByVisibility();
    }

    function filterByVisibility() {
        if(showAllUsers.value) {
            DM.removeFilter("datatags", "created_by")
        } else {
            DM.setFilter("datatags", "created_by", activeUserId.value)
        }
        updateAllGames(DM.getData("games", false));
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
    watch(() => dataNeedsReload.value.games, loadGames);
    watch(() => dataNeedsReload.value.codes, loadCodes);
    watch(() => dataNeedsReload.value.tags, loadTags);
    watch(() => dataNeedsReload.value.datatags, loadDataTags);
    watch(() => dataNeedsReload.value.evidence, loadEvidence);
    watch(activeUserId, () => {
        askUserIdentity.value = activeUserId.value === null;
        filterByVisibility();
    });
    watch(transitionCode, async function() {
        await loadCodes();
        loadDataTags();
    })
    watch(showAllUsers, filterByVisibility)

</script>
