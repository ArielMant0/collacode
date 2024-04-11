<template>
    <v-overlay :model-value="isLoading" class="align-center justify-center" opacity="0.6">
        <v-progress-circular indeterminate size="64" color="white"></v-progress-circular>
    </v-overlay>

    <v-card density="compact" rounded="0">
        <v-tabs v-model="tab" color="secondary" bg-color="grey-darken-3" align-tabs="center" density="compact" @update:model-value="checkReload">
            <v-tab value="coding">Coding</v-tab>
            <v-tab value="transition">Transition</v-tab>
            <v-tab value="exploration">Exploration</v-tab>
        </v-tabs>

        <v-card-text>
            <v-window v-model="tab">
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
        </v-card-text>
    </v-card>
</template>

<script setup>

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { useToast } from "vue-toastification";
    import CodingView from '@/components/views/CodingView.vue'
    import { storeToRefs } from 'pinia'
    import { ref, onMounted } from 'vue'
    import DM from '@/use/data-manager'
    import { toToTreePath } from '@/use/utility';

    const toast = useToast();
    const loader = useLoader()
    const app = useApp()

   const tab = ref("coding");
   const isLoading = ref(false);
   const dataTime = ref(Date.now())
   const askUserIdentity = ref(false);

   const {
        ds,
        showAllUsers,
        activeUserId,
        activeCode,
        initialized
    } = storeToRefs(app);

    function checkReload() {
        switch (tab.value) {
            case "coding":
                app.cancelCodeTransition();
                app.needsReload("coding")
                break;
            case "transition":
                app.startCodeTransition();
                app.needsReload("transition")
                break;
            default:
                app.cancelCodeTransition();
                app.needsReload()
        }
    }

    async function init(force) {
        if (!initialized.value) {
            isLoading.value = true;
            await loader.get("datasets").then(list => {
                app.setDatasets(list)
                app.setReloaded("datasets")
            })
            await loadUsers();
            DM.setFilter("tags", "is_leaf", 1)
            DM.setFilter("tags_old", "is_leaf", 1)
            return loadData();
        } else if (force) {
            DM.setFilter("tags", "is_leaf", 1)
            DM.setFilter("tags_old", "is_leaf", 1)
            return loadData();
        } else {
            dataTime.value = Date.now()
        }
    }

    async function loadData() {
        isLoading.value = true;
        await loadUsers();
        await loadCodes();
        return Promise.all([
            loadAllTags(),
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
        });
    }

    async function loadUsers() {
        const list = await loader.get(`users/dataset/${ds.value}`)
        app.setUsers(list)
        if (!app.activeUserId) {
            askUserIdentity.value = true;
        }
        return app.setReloaded("users")
    }

    async function loadCodes() {
        if (!ds.value) return;
        return loader.get(`codes/dataset/${ds.value}`).then(data => {
            DM.setData("codes", data);
            app.codes = data;
            if (activeCode.value === null && data.length > 0) {
                app.setActiveCode(data[0].id);
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
    async function loadAllTags() {
        return Promise.all([loadTags(), loadOldTags()])
    }
    async function loadOldTags() {
        if (app.transitionCode === null) return;
        const result = await loader.get(`tags/code/${app.activeCode}`)
        result.forEach(t => {
            t.path = toToTreePath(t, result),
            t.pathNames = t.path.map(dd => result.find(tmp => tmp.id === dd).name).join(" / ")
        });
        DM.setData("tags_old", result)
        return app.setReloaded("tags_old")
    }
    async function loadTags() {
        if (activeCode.value === null) return;
        const result = await loader.get(`tags/code/${app.currentCode}`)
        result.forEach(t => {
            t.path = toToTreePath(t, result),
            t.pathNames = t.path.map(dd => result.find(tmp => tmp.id === dd).name).join(" / ")
        });
        DM.setData("tags", result)
        return app.setReloaded("tags")
    }
    async function loadDataTags() {
        if (activeCode.value === null) return;
        const result = await loader.get(`datatags/code/${app.currentCode}`)
        DM.setData("datatags", result)
        return app.setReloaded("datatags")
    }
    async function loadEvidence() {
        if (activeCode.value === null) return;
        const result = await loader.get(`evidence/code/${app.currentCode}`)
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
        const data = DM.getData("games", false)
        if (!data) {
            console.warn("missing data")
            return;
        }

        const dts = DM.getData("datatags", tab.value === "coding");
        const tags = DM.getData("tags", false);
        const ev = DM.getData("evidence", false);

        data.forEach(d => {
            d.tags = [];
            d.numEvidence = ev.reduce((acc, e) => acc + (e.game_id === d.id ? 1 : 0), 0);
        });

        dts.forEach(d => {

            const g = data.find(dd => dd.id === d.game_id);
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

   watch(() => app.dataNeedsReload._all, async function() {
        await loadData();
        toast.info("reloaded data", { timeout: 2000 })
    });
    watch(() => app.dataNeedsReload.coding, async function() {
        isLoading.value = true;
        await loadTags();
        await loadDataTags();
        await loadEvidence()
        isLoading.value = false;
        app.setReloaded("coding")
    });
    watch(() => app.dataNeedsReload.transition, async function() {
        isLoading.value = true;
        await loadAllTags();
        await loadDataTags();
        await Promise.all([loadEvidence(), loadTagAssignments(), loadCodeTransitions()])
        isLoading.value = false;
        app.setReloaded("transition")
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

    watch(() => app.dataNeedsReload.games, loadGames);
    watch(() => app.dataNeedsReload.codes, loadCodes);
    watch(() => app.dataNeedsReload.tags, loadTags);
    watch(() => app.dataLoading.datatags, updateAllGames);
    watch(() => app.dataNeedsReload.evidence, loadEvidence);

    watch(() => [app.dataLoading.tags, app.dataLoading.datatags, app.dataLoading.evidence], function(val) {
        if (val.some(v => v === false)) { updateAllGames() }
    });

    watch(() => app.activeUserId, () => {
        askUserIdentity.value = activeUserId.value === null;
        filterByVisibility();
    });
    watch(showAllUsers, filterByVisibility)
    watch(() => app.selectionTime, updateAllGames)

</script>
