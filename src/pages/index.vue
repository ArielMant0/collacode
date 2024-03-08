<template>
    <div class="d-flex pa-2">
        <aside style="max-width: 300px;">
            <v-select v-model="ds"
                class="mb-2"
                density="compact"
                hide-details
                :items="datasets"
                item-title="name" item-value="id"/>

            <v-card v-if="code" class="pa-3 mb-2 text-caption">
                <v-select v-model="activeCode"
                    class="mb-2"
                    density="compact"
                    hide-details
                    :items="codes"
                    item-title="name" item-value="id"/>

                <v-switch v-model="showAllUsers"
                    class="ml-2 mb-2"
                    density="compact"
                    label="show all users"
                    color="#078766"
                    hide-details
                    hide-spin-buttons
                    @update:model-value="filterByVisibility"/>

                {{ code.description }}

                <UserPanel/>
            </v-card>

        </aside>
        <IdentitySelector v-model="askUserIdentity" @select="app.setActiveUser"/>
        <div v-if="initialized" class="d-flex flex-column pa-2" style="width: 100%;">
            <RawDataView
                :data="allData.games"
                :time="allData.time"
                :headers="headers"
                selectable editable allow-add
                @add-empty-row="addNewGame"
                @add-rows="addGames"
                @delete-rows="deleteGames"
                @update-rows="updateGames"
                @update-datatags="updateDateTags"
                />
            <TagOverview/>
        </div>
    </div>
</template>

<script setup>
    import TagOverview from '@/components/TagOverview.vue';
    import IdentitySelector from '@/components/IdentitySelector.vue';
    import RawDataView from '@/components/RawDataView.vue';
    import UserPanel from '@/components/UserPanel.vue';

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { reactive, onMounted } from 'vue'
    import { useToast } from "vue-toastification";
    import DM from '@/use/data-manager'

    const toast = useToast();

    const loader = useLoader()
    const app = useApp()
    const {
        ds, datasets,
        showAllUsers,
        activeUserId,
        activeCode, code, codes,
        initialized, needsDataReload
    } = storeToRefs(app);

    const askUserIdentity = ref(false);
    const allData = reactive({ games: [], time: null });

    const headers = [
        // { title: "ID", key: "id", type: "id" },
        { title: "Name", key: "name", type: "string", width: "35%" },
        { title: "Year", key: "year", type: "integer", width: "100px" },
        { title: "Played", key: "played", type: "integer", width: "50px" },
        { title: "Tags", key: "tags", type: "array" },
        { title: "URL", key: "url", type: "url", width: "300px" },
    ];

    async function loadData() {
        await loadCodes();
        return Promise.all([loadTags(), loadDataTags()]).then(async () => {
            await loadGames();
            if (!initialized.value) {
                initialized.value = true;
            }
            app.setReloaded();
        });
    }

    async function loadCodes() {
        if (!ds.value) return;
        return loader.get(`codes/dataset/${ds.value}`).then(data => {
            DM.setData("codes", data);
            if (activeCode.value === null) {
                app.setActiveCode(data[0].id);
            }
        })
    }
    async function loadGames() {
        if (ds.value === null) return;
        return loader.get(`games/dataset/${ds.value}`).then(updateAllGames);
    }
    async function loadTags() {
        if (activeCode.value === null) return;
        return loader.get(`tags/code/${activeCode.value}`).then(data => DM.setData("tags", data))
    }
    async function loadDataTags() {
        if (activeCode.value === null) return;
        return loader.get(`datatags/code/${activeCode.value}`).then(data => DM.setData("datatags", data))
    }

    function updateAllGames(data) {
        const dts = DM.getData("datatags");
        const tags = DM.getData("tags");
        data.forEach(d => d.tags = [])
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

        DM.setData("games", data)
        allData.games = data;
        allData.time = Date.now();
    }


    async function init() {
        if (!initialized.value) {
            await loader.get("datasets").then(list => app.setDatasets(list))
            await loader.get(`users/dataset/${ds.value}`).then(list => {
                app.setUsers(list);
                askUserIdentity.value = true;
            });

            loadData();
        }
    }

    function addNewGame() {
        allData.games = DM.pushFront("games", {
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
                toast.success("added " + ids.length + " game(s)")
                app.needsReload()
            })
    }
    function deleteGames(ids) {
        loader.post(`delete/games`, { ids: ids })
            .then(() => {
                toast.success("deleted " + ids.length + " game(s)")
                app.needsReload()
            })
    }
    function updateGames(games) {
        loader.post("update/games", { rows: games })
            .then(() => {
                toast.success("updated " + games.length + " game(s)")
                app.needsReload()
            })
    }
    function updateDateTags(game) {

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
                app.needsReload()
            })
    }

    function filterByVisibility() {
        if(showAllUsers.value) {
            DM.removeFilter("datatags", "created_by")
        } else {
            DM.setFilter("datatags", "created_by", activeUserId.value)
        }
        updateAllGames(DM.getData("games"));
    }

    onMounted(init);

    watch(needsDataReload, loadData);
    watch(activeUserId, () => {
        askUserIdentity.value = activeUserId.value === null;
        filterByVisibility();
    });
</script>
