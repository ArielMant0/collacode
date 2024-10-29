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
                    class="mb-2"
                    density="compact"
                    hide-details
                    @update:model-value="times.needsReload()"
                    item-title="name"
                    item-value="id"/>

                <v-btn block prepend-icon="mdi-refresh" class="mb-2" color="primary" @click="times.needsReload()">reload data</v-btn>

                <MiniCollapseHeader v-model="showUsers" text="users"/>
                <v-card v-if="showUsers" class="mb-2">
                    <UserPanel/>
                </v-card>

                <MiniCollapseHeader v-model="showTransition" text="transition"/>
                <v-card v-if="transitions && showTransition" class="mb-2">
                    <TransitionWidget :initial="activeTransition"
                        :codes="codes"
                        :transitions="transitions"
                        @create="onCreate"
                        allow-create/>
                </v-card>
            </div>
        </v-card>

        <div class="pa-2" style="width: 100%;">

            <div v-if="activeTransition" class="d-flex flex-column">

                <CodingTransition :time="myTime" :old-code="oldCode" :new-code="newCode"/>

                <v-sheet class="mb-2 pa-2">
                    <div style="text-align: center;">
                        <v-btn color="primary" @click="showGames = !showGames">{{ showGames ? 'hide' : 'show' }} games</v-btn>
                    </div>
                    <div v-if="showGames">
                        <h3 style="text-align: center" class="mt-4 mb-4">{{ stats.numGamesSel }} / {{ stats.numGames }} GAMES</h3>
                        <RawDataView
                            :time="myTime"
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
    import CodingTransition from '@/components/CodingTransition.vue';
    import TransitionWidget from '../TransitionWidget.vue';

    import { useApp } from '@/store/app'
    import { useSettings } from '@/store/settings'
    import { storeToRefs } from 'pinia'
    import { watch, ref } from 'vue'
    import DM from '@/use/data-manager'
    import { useTimes } from '@/store/times';

    const app = useApp()
    const settings = useSettings();
    const times = useTimes()

    const {
        ds, datasets,
        codes, transitions,
        transitionData,
        activeTransition, oldCode, newCode
    } = storeToRefs(app);

    const {
        expandNavDrawer,
        showUsers,
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
    const myTime = ref(props.time)

    const stats = reactive({
        numGames: 0, numGamesSel: 0,
        numTags: 0, numTagsUser: 0,
        numDT: 0, numDTUser: 0
    })

    const el = ref(null);

    function setActiveTransition(id) {
        app.setActiveTransition(id);
        times.needsReload()
    }
    function onCreate(oldC, newC) {
        app.addAction("trans view", "set transition", { oldCode: oldC, newCode: newC });
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
            stats.numGames = DM.getSize("games", false);
            stats.numGamesSel = DM.getSize("games", true);
            stats.numTags = DM.getSize("tags", false);
            stats.numTagsUser = DM.getSizeBy("tags", d => d.created_by === app.activeUserId)
            stats.numDT = DM.getSize("datatags", false);
            stats.numDTUser = DM.getSizeBy("datatags", d => d.created_by === app.activeUserId)
            if (actions) { processActions(); }
            myTime.value = Date.now();
        }
    }

    watch(() => props.time, read)
    watch(showGames, function() {
        if (showGames.value) {
            stats.numGames = DM.getSize("games", false);
            stats.numGamesSel = DM.getSize("games", true);
        }
    })

</script>
