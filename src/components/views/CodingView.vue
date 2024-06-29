<template>
    <v-sheet ref="el" class="pa-0">
    <v-layout>

        <MiniNavBar
            :user-color="app.activeUser ? app.activeUser.color : 'default'"
            :code-name="app.activeCode ? app.getCodeName(app.activeCode) : '?'"
            :num-games="stats.numGames"
            :num-tags="stats.numTags"
            :num-tags-sel="stats.numTagsSel"
            :num-d-t="stats.numDT"
            :num-d-t-user="stats.numDTUser"
            />

        <v-card v-if="expandNavDrawer"  class="pa-2" :min-width="300" position="fixed" style="z-index: 3999; height: 100vh">
            <v-btn @click="expandNavDrawer = !expandNavDrawer"
                icon="mdi-arrow-left"
                block
                class="mb-2"
                density="compact"
                rounded="sm"
                color="secondary"/>

            <div>
                <v-select v-if="datasets"
                    v-model="ds"
                    :items="datasets"
                    label="dataset"
                    class="mb-2"
                    density="compact"
                    hide-details
                    @update:model-value="app.needsReload()"
                    item-title="name"
                    item-value="id"/>

                <v-btn block prepend-icon="mdi-refresh" class="mb-2" color="primary" @click="app.needsReload()">reload data</v-btn>

                <v-switch
                    :model-value="showAllUsers"
                    class="ml-4"
                    density="compact"
                    label="show data for all users"
                    color="primary"
                    hide-details
                    hide-spin-buttons
                    @update:model-value="app.toggleUserVisibility"/>

                <MiniCollapseHeader v-model="showUsers" text="users"/>
                <v-card v-if="showUsers" class="mb-2">
                    <UserPanel/>
                </v-card>

                <MiniCollapseHeader v-model="showActiveCode" text="code"/>
                <v-card v-if="showActiveCode && codes" class="mb-2">
                    <CodeWidget :initial="activeCode" :codes="codes" @select="setActiveCode" can-edit/>
                </v-card>

            </div>
        </v-card>

        <div class="pa-2">
            <div class="d-flex flex-column pa-2" v-if="initialized">

                <div class="mb-2">
                    <TagOverview/>
                </div>

                <v-sheet class="mb-2 pa-2">
                    <h3 style="text-align: center" class="mt-4 mb-4">GAMES</h3>
                    <RawDataView
                        :data="allData"
                        :time="myTime"
                        :headers="headers"
                        selectable
                        editable
                        allow-add
                        @add-empty-row="addNewGame"
                        @add-rows="addGames"
                        @delete-rows="deleteGames"
                        @delete-tmp-row="deleteTmpGame"
                        @update-rows="updateGames"
                        @update-teaser="updateGameTeaser"
                        @add-datatags="addDataTags"
                        @delete-datatags="deleteDataTags"
                        @update-datatags="updateDataTags"
                        />
                </v-sheet>

                <v-sheet class="mb-2 pa-2">
                    <h3 style="text-align: center" class="mt-4 mb-4">TAGS</h3>
                    <TagInspector source="tags" can-edit can-delete include-intermediate/>
                </v-sheet>


                <v-sheet class="mb-2 pa-2">
                    <h3 style="text-align: center" class="mt-4 mb-2">EVIDENCE</h3>
                    <GameEvidenceTiles v-if="activeCode" :time="myTime" :code="activeCode" allow-add allow-edit/>
                </v-sheet>
            </div>
        </div>
    </v-layout>
    </v-sheet>
</template>

<script setup>
    import TagOverview from '@/components/tags/TagOverview.vue';
    import RawDataView from '@/components/RawDataView.vue';
    import UserPanel from '@/components/UserPanel.vue';
    import GameEvidenceTiles from '@/components/evidence/GameEvidenceTiles.vue';
    import TagInspector from '@/components/tags/TagInspector.vue';

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { ref } from 'vue'
    import { useToast } from "vue-toastification";
    import { useSettings } from '@/store/settings';
    import DM from '@/use/data-manager'
    import { formatNumber } from '@/use/utility';

    const app = useApp()
    const toast = useToast();
    const loader = useLoader()
    const settings = useSettings();

    let TMP_ID = -1;

    const {
        initialized,
        ds, datasets,
        showAllUsers,
        activeUserId,
        activeCode, codes,
    } = storeToRefs(app);

    const { expandNavDrawer, showUsers, showActiveCode } = storeToRefs(settings);

    const props = defineProps({
        time: {
            type: Number,
            required: true
        },
        loading: {
            type: Boolean,
            default: false
        }
    })

    const allData = ref([]);
    const myTime = ref(props.time)
    const stats = reactive({
        numGames: 0,
        numTags: 0, numTagsSel: 0,
        numDT: 0, numDTUser: 0
    })

    const el = ref(null);

    const headers = [
        { title: "Name", key: "name", type: "string" },
        { title: "Teaser", key: "teaser", type: "string" },
        { title: "Year", key: "year", type: "integer", width: "100px" },
        { title: "Played", key: "played", type: "integer", width: "50px" },
        { title: "Tags", key: "tags", type: "array", width: "35%" },
        { title: "URL", key: "url", type: "url", width: "200px" },
    ];

    function addNewGame() {
        DM.push("games", {
            dataset_id: ds.value,
            id: TMP_ID--,
            name: "ADD TITLE",
            year: new Date().getFullYear(),
            played: 0,
            url: "https://store.steampowered.com/",
            teaser: null,
            tags: [],
            edit: true
        });
        read();
    }
    function addGames(games) {
        loader.post("add/games", { rows: games, dataset: ds.value })
            .then(() => {
                toast.success("added " + games.length + " game(s)")
                app.needsReload("games")
            })
            .catch(() => {
                toast.error("could not add " + games.length + " game(s)")
                app.needsReload("games")
            })
    }
    function deleteGames(ids) {
        loader.post(`delete/games`, { ids: ids })
            .then(() => {
                toast.success("deleted " + ids.length + " game(s)")
                app.needsReload("games")
            })
            .catch(() => {
                toast.error("could not delete " + ids.length + " game(s)")
                app.needsReload("games")
            })
    }
    function deleteTmpGame(id) {
        if (DM.remove('games', id)) {
            read();
        }
    }
    function updateGames(games) {
        loader.post("update/games", { rows: games })
            .then(() => {
                toast.success("updated " + games.length + " game(s)")
                app.needsReload("games")
            })
            .catch(() => {
                toast.error("could not update " + games.length + " game(s)")
                app.needsReload("games")
            })
    }
    async function updateGameTeaser(item, name, file) {
        await loader.postImage(`image/teaser/${name}`, file);
        item.teaserName = name;
        return updateGames([item]);
    }

    function addDataTags(datatags) {
        loader.post("add/datatags", { rows: datatags })
            .then(() => {
                toast.success("added " + datatags.length + " datatag(s)")
                app.needsReload("coding")
            })
            .catch(() => {
                toast.error("could not add " + datatagsdatatags.length + " datatag(s)")
                app.needsReload("coding")
            })
    }
    function deleteDataTags(datatags) {
        loader.post("delete/datatags", { ids: datatags })
            .then(() => {
                toast.success("delete " + datatags.length + " datatag(s)")
                app.needsReload("coding")
            })
            .catch(() => {
                toast.error("could not delete " + datatagsdatatags.length + " datatag(s)")
                app.needsReload("coding")
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
            .filter(t => t.created_by === activeUserId.value)
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

    function setActiveCode(id) {
        if (id !== app.activeCode) {
            app.setActiveCode(id);
            app.needsReload();
        }
    }

    function read() {
        allData.value = app.activeUserId ? DM.getData("games") : []
        stats.numGames = DM.getSize("games", false);
        stats.numTags = DM.getSize("tags", false);
        stats.numTagsSel = DM.hasFilter("tags", "id") ? DM.getSize("tags", true) : 0;
        stats.numDT = DM.getSize("datatags", false);
        stats.numDTUser = DM.getSizeBy("datatags", d => d.created_by === app.activeUserId)
        myTime.value = Date.now()
    }

    watch(() => app.activeUserId, read)
    watch(() => props.time, read)

</script>
