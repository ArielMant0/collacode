<template>
    <v-sheet ref="el" class="pa-0">
    <v-layout>

        <MiniNavBar
            :user-color="app.activeUser ? app.activeUser.color : 'default'"
            :code-name="transitionData ? app.getCodeName(oldCode) : '?'"
            :other-code-name="transitionData ? app.getCodeName(newCode) : '?'"
            :num-games="stats.numGames"
            :num-tags="stats.numTags"
            :num-tags-sel="stats.numTagsSel"
            :num-d-t="stats.numDT"
            :num-d-t-user="stats.numDTUser"
            />

        <v-card v-if="expandNavDrawer"  class="pa-2" :min-width="300" position="fixed" style="z-index: 3999; height: 100vh">

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

            <MiniCollapseHeader v-model="showUsers" text="users"/>
            <v-card v-if="showUsers" class="mb-2">
                <UserPanel/>
            </v-card>

            <MiniCollapseHeader v-model="showTransition" text="transition"/>
            <v-card v-if="transitions && showTransition" class="mb-2">
                <TransitionWidget :initial="activeTransition" :codes="codes" :transitions="transitions" @create="onCreate" @create-code="onCreateCode" allow-create/>
            </v-card>

            <MiniCollapseHeader v-model="showTagChips" text="tag chips"/>
            <v-card v-if="showTagChips && !props.loading" class="mb-2">
                <SelectedTagsViewer :time="myTime"/>
            </v-card>
        </v-card>

        <div class="pa-2">

            <div v-if="activeTransition" class="d-flex flex-column pa-2">

                <div class="mb-2">
                    <TagOverview always-full-data/>
                </div>

                <CodingTransition :time="myTime" :old-code="oldCode" :new-code="newCode"/>

                <v-sheet class="mb-2 pa-2">
                    <h3 style="text-align: center" class="mt-4 mb-4">GAMES</h3>
                    <RawDataView
                        :data="allData"
                        :time="myTime"
                        :headers="headers"
                        selectable
                        editable
                        allow-add
                        check-assigned
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
                    <GameEvidenceTiles v-if="transitionData" :time="myTime" :code="transitionData.new_code" allow-add allow-edit/>
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
    import SelectedTagsViewer from '@/components/tags/SelectedTagsViewer.vue';
    import CodingTransition from '@/components/CodingTransition.vue';

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { useSettings } from '@/store/settings'
    import { storeToRefs } from 'pinia'
    import { watch, ref } from 'vue'
    import { useToast } from "vue-toastification";
    import DM from '@/use/data-manager'
    import { formatNumber } from '@/use/utility';

    const app = useApp()
    const toast = useToast();
    const loader = useLoader()
    const settings = useSettings();

    let TMP_ID = -1;

    const {
        ds, datasets,
        activeUserId,
        codes, transitions,
        transitionData,
        activeTransition, oldCode, newCode
    } = storeToRefs(app);

    const {
        expandNavDrawer,
        showUsers, showTagChips,
        showTransition
    } = storeToRefs(settings);

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
        read(false);
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
                app.needsReload("transition")
            })
            .catch(() => {
                toast.error("could not add " + datatagsdatatags.length + " datatag(s)")
                app.needsReload("transition")
            })
    }
    function deleteDataTags(datatags) {
        loader.post("delete/datatags", { ids: datatags })
            .then(() => {
                toast.success("delete " + datatags.length + " datatag(s)")
                app.needsReload("transition")
            })
            .catch(() => {
                toast.error("could not delete " + datatagsdatatags.length + " datatag(s)")
                app.needsReload("transition")
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
            .map(t => {
                if (t.tag_id !== null) {
                    return  { tag_id: t.tag_id };
                }
                return { tag_name: t.name, description: t.description }
            })

        loader.post("update/game/datatags", body)
            .then(() => {
                toast.success("updated datatag for " + game.name)
                app.needsReload("coding")
            })
            .catch(() => {
                toast.error("could not update datatags for " + game.name)
                app.needsReload("transition")
            })
    }

    function setActiveTransition(id) {
        app.setActiveTransition(id);
        app.needsReload("transition")
    }
    function onCreate(oldC, newC) {
        app.addAction("trans view", "set transition", { oldCode: oldC, newCode: newC });
    }
    function onCreateCode(code) {
        // app.addAction("trans view", "set new code", { name: code.name });
    }
    function processActions() {
        const toAdd = [];
        let action = app.popAction("trans view");
        while (action) {
            switch (action.action) {
                case "set transition":
                    const item = transitions.value.find(d => d.old_code === action.values.oldCode && d.new_code === action.values.newCode)
                    if (item) {
                        setActiveTransition(item.id);
                    } else {
                        toAdd(action);
                    }
                    break;
                default: break;
            }
            action = app.popAction("trans view");
        }
        toAdd.forEach(d => app.addAction("trans view", d.action, d.values));
    }

    async function read(actions=true) {
        if (DM.hasData("games")) {
            allData.value =  DM.getData("games");
            stats.numGames = DM.getSize("games", false);
            stats.numTags = DM.getSize("tags", false);
            stats.numTagsSel = DM.hasFilter("tags", "id") ? DM.getSize("tags", true) : 0;
            stats.numDT = DM.getSize("datatags", false);
            stats.numDTUser = DM.getSizeBy("datatags", d => d.created_by === app.activeUserId)
            if(actions) {
                processActions();
            }
            myTime.value = Date.now();
        }
    }

    watch(() => props.time, read)

</script>
