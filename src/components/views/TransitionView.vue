<template>
    <div class="d-flex pa-1">
        <v-sheet width="300" class="pa-1 mr-2">
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

            <v-card v-if="codes" class="mb-2">
                <CodeWidget  :initial="activeCode" :codes="codes" @select="setActiveCode" can-edit/>
            </v-card>

            <v-card v-if="codes" class="pa-2 mb-2">
                <CodingTransitionSettings/>
            </v-card>

            <v-card class="mb-2 pa-2">
                <UserPanel/>
            </v-card>

            <v-card class="mb-2 pa-2">
                <SelectedTagsViewer v-if="!props.loading" :time="time"/>
            </v-card>
        </v-sheet>

        <div style="width: 100%;">

            <div v-if="!props.loading && activeCode && transitionCode" class="d-flex flex-column pa-2">

                <div class="mb-2">
                    <TagOverview/>
                </div>

                <CodingTransition :time="time" :old-code="activeCode" :new-code="transitionCode"/>

                <v-sheet class="mb-2 pa-2">
                    <h3 style="text-align: center" class="mt-4 mb-4">GAMES</h3>
                    <RawDataView
                        :data="allData"
                        :time="time"
                        :headers="headers"
                        selectable
                        editable
                        allow-add
                        check-assigned
                        @add-empty-row="addNewGame"
                        @add-rows="addGames"
                        @delete-rows="deleteGames"
                        @update-rows="updateGames"
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
    </div>
</template>

<script setup>
    import TagOverview from '@/components/tags/TagOverview.vue';
    import RawDataView from '@/components/RawDataView.vue';
    import UserPanel from '@/components/UserPanel.vue';
    import EvidenceInspector from '@/components/EvidenceInspector.vue';
    import TagInspector from '@/components/tags/TagInspector.vue';
    import SelectedTagsViewer from '@/components/tags/SelectedTagsViewer.vue';
    import CodingTransitionSettings from '../CodingTransitionSettings.vue';

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { ref } from 'vue'
    import { useToast } from "vue-toastification";
    import DM from '@/use/data-manager'

    const app = useApp()
    const toast = useToast();
    const loader = useLoader()

    const {
        ds, datasets,
        activeUserId,
        activeCode, codes, transitionCode
    } = storeToRefs(app);


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
    const emit = defineEmits("update")

    const allData = ref([]);

    const headers = [
        { title: "Name", key: "name", type: "string" },
        { title: "Year", key: "year", type: "integer", width: "100px" },
        { title: "Played", key: "played", type: "integer", width: "50px" },
        { title: "Tags", key: "tags", type: "array", width: "35%" },
        { title: "URL", key: "url", type: "url", width: "200px" },
    ];

    function addNewGame() {
        allData = DM.push("games", {
            dataset_id: ds.value,
            id: null,
            name: "ADD TITLE",
            year: new Date().getFullYear(),
            played: 0,
            url: "https://store.steampowered.com/",
            tags: [],
            edit: true
        });
        emit("update")
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
                app.needsReload("transition")
            })
    }
    function deleteDataTags(datatags) {
        loader.post("delete/datatags", { ids: datatags })
            .then(() => {
                toast.success("delete " + datatags.length + " datatag(s)")
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

    watch(() => props.time, function() { allData.value =  DM.getData("games") })

</script>
