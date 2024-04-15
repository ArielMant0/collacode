<template>
    <v-sheet ref="el" class="pa-0">
    <v-layout>
        <v-sheet class="pa-2" :min-width="expandNavDrawer ? 300 : 60">

            <v-btn @click="expandNavDrawer = !expandNavDrawer"
                :icon="expandNavDrawer ? 'mdi-arrow-left' : 'mdi-arrow-right'"
                block
                density="compact"
                rounded="sm"
                color="secondary"/>

            <v-divider class="mb-2 mt-2"></v-divider>

            <div v-if="!expandNavDrawer" class="d-flex flex-column align-center text-caption">
                <v-avatar icon="mdi-account"
                    density="compact"
                    class="mb-2"
                    :color="app.activeUser ? app.activeUser.color : 'default'"/>

                <span class="mt-2 mb-1">Code:</span>
                <b>{{ app.activeCode ? app.getCodeName(app.activeCode) : '?' }}</b>

                <span class="mt-3 mb-1">Games:</span>
                <v-chip density="compact">{{ stats.numGames }}</v-chip>

                <span class="mt-3 mb-1">Tags:</span>
                <v-chip density="compact">{{ stats.numTags }}</v-chip>
                <v-chip v-if="stats.numTagsSel > 0" density="compact" class="mt-1" color="primary">{{ stats.numTagsSel }}</v-chip>
            </div>
            <div v-else>
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

                <MiniCollapseHeader v-model="showTagChips" text="tag chips"/>
                <v-card v-if="!props.loading && showTagChips" class="mb-2">
                    <SelectedTagsViewer v-if="!props.loading" :time="myTime"/>
                </v-card>
            </div>
        </v-sheet>

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
                    <EvidenceInspector/>
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
    import EvidenceInspector from '@/components/evidence/EvidenceInspector.vue';
    import TagInspector from '@/components/tags/TagInspector.vue';
    import SelectedTagsViewer from '@/components/tags/SelectedTagsViewer.vue';

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { ref } from 'vue'
    import { useToast } from "vue-toastification";
    import { useSettings } from '@/store/settings';
    import DM from '@/use/data-manager'

    const app = useApp()
    const toast = useToast();
    const loader = useLoader()
    const settings = useSettings();

    const {
        initialized,
        ds, datasets,
        showAllUsers,
        activeUserId,
        activeCode, codes,
    } = storeToRefs(app);

    const { expandNavDrawer, showUsers, showTagChips, showActiveCode } = storeToRefs(settings);

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
    const stats = reactive({ numGames: 0, numTagsSel: 0, numTags: 0 })

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
            id: null,
            name: "ADD TITLE",
            year: new Date().getFullYear(),
            played: 0,
            url: "https://store.steampowered.com/",
            teaser: null,
            tags: [],
            edit: true
        });
        allData.value = DM.getData("games");
        myTime.value = Date.now();
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
    }
    function deleteDataTags(datatags) {
        loader.post("delete/datatags", { ids: datatags })
            .then(() => {
                toast.success("delete " + datatags.length + " datatag(s)")
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

    watch(() => app.activeUserId, function() {
        allData.value = app.activeUserId ? DM.getData("games") : []
        stats.numGames = DM.getSize("games", false);
        stats.numTags = DM.getSize("tags", false);
        stats.numTagsSel = DM.hasFilter("tags", "id") ? DM.getSize("tags", true) : 0;
        myTime.value = Date.now()
    })
    watch(() => props.time, function() {
        allData.value = app.activeUserId ? DM.getData("games") : []
        stats.numGames = DM.getSize("games", false);
        stats.numTags = DM.getSize("tags", false);
        stats.numTagsSel = DM.hasFilter("tags", "id") ? DM.getSize("tags", true) : 0;
        myTime.value = Date.now()
    })

</script>
