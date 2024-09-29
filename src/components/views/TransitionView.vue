<template>
    <v-sheet ref="el" class="pa-0">
    <v-layout>

        <MiniNavBar
            :user-color="app.activeUser ? app.activeUser.color : 'default'"
            :code-name="transitionData ? app.getCodeName(oldCode) : '?'"
            :other-code-name="transitionData ? app.getCodeName(newCode) : '?'"
            :num-games="stats.numGames"
            :num-tags="stats.numTags"
            :num-tags-uer="stats.numTagsUser"
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

        <div class="pa-2" style="width: 100%;">

            <div v-if="activeTransition" class="d-flex flex-column">

                <CodingTransition :time="myTime" :old-code="oldCode" :new-code="newCode"/>

                <v-sheet class="mb-2 pa-2" style="text-align: center;">
                    <v-btn color="primary" @click="showGames = !showGames">{{ showGames ? 'hide' : 'show' }} games</v-btn>
                    <div v-if="showGames">
                        <h3 style="text-align: center" class="mt-4 mb-4">{{ allData.length }} GAMES</h3>
                        <RawDataView
                        :data="allData"
                        :time="myTime"
                        :headers="headers"
                        selectable
                        editable
                        allow-add
                        check-assigned/>
                    </div>
                </v-sheet>
            </div>
        </div>
    </v-layout>
    </v-sheet>
</template>

<script setup>
    import RawDataView from '@/components/RawDataView.vue';
    import UserPanel from '@/components/UserPanel.vue';
    import SelectedTagsViewer from '@/components/tags/SelectedTagsViewer.vue';
    import CodingTransition from '@/components/CodingTransition.vue';

    import { useApp } from '@/store/app'
    import { useSettings } from '@/store/settings'
    import { storeToRefs } from 'pinia'
    import { watch, ref } from 'vue'
    import DM from '@/use/data-manager'

    const app = useApp()
    const settings = useSettings();

    const {
        ds, datasets,
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

    const showGames = ref(false)
    const allData = ref([]);
    const myTime = ref(props.time)

    const stats = reactive({
        numGames: 0,
        numTags: 0, numTagsUser: 0,
        numDT: 0, numDTUser: 0
    })

    const el = ref(null);

    const headers = [
        { title: "Name", key: "name", type: "string", width: "600px" },
        { title: "Teaser", key: "teaser", type: "string" },
        { title: "Year", key: "year", type: "integer", width: "100px" },
        { title: "Tags", key: "tags", type: "array" },
        { title: "Evidence", key: "numEvidence", type: "integer" },
        { title: "URL", key: "url", type: "url", width: "100px" },
    ];


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
            stats.numTagsUser = DM.getSizeBy("tags", d => d.created_by === app.activeUserId)
            stats.numDT = DM.getSize("datatags", false);
            stats.numDTUser = DM.getSizeBy("datatags", d => d.created_by === app.activeUserId)
            if (actions) {
                processActions();
            }
            myTime.value = Date.now();
        }
    }

    watch(() => props.time, read)

</script>
