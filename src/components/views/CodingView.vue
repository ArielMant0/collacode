<template>
    <v-sheet ref="el" class="pa-0">
    <v-layout>

        <MiniNavBar
            :user-color="app.activeUser ? app.activeUser.color : 'default'"
            :code-name="app.activeCode ? app.getCodeName(app.activeCode) : '?'"
            :time="myTime"/>

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
                    @update:model-value="app.fetchUpdate()"
                    item-title="name"
                    item-value="id"/>

                <v-btn block prepend-icon="mdi-refresh" class="mb-2" color="primary" @click="app.fetchUpdate()">reload data</v-btn>

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


        <div v-if="initialized" class="mb-2 pa-2" style="width: 100%; margin-left: 80px;">
            <h3 style="text-align: center" class="mt-4 mb-4">{{ stats.numGamesSel }} / {{ stats.numGames }} GAMES</h3>
            <RawDataView
                :time="myTime"
                selectable
                editable
                allow-add
                check-assigned/>
        </div>
    </v-layout>
    </v-sheet>
</template>

<script setup>
    import RawDataView from '@/components/RawDataView.vue';
    import UserPanel from '@/components/UserPanel.vue';

    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { ref } from 'vue'
    import { useSettings } from '@/store/settings';
    import DM from '@/use/data-manager'
    import MiniNavBar from '../MiniNavBar.vue';
    import { useTimes } from '@/store/times';

    const app = useApp()
    const settings = useSettings();
    const times = useTimes()

    const {
        initialized,
        ds, datasets,
        showAllUsers,
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

    const myTime = ref(props.time)
    const stats = reactive({ numGames: 0, numGamesSel: 0 })

    const el = ref(null);

    function setActiveCode(id) {
        if (id !== app.activeCode) {
            app.setActiveCode(id);
            times.needsReload();
        }
    }

    function read() {
        stats.numGames = DM.getSize("games", false);
        stats.numGamesSel = DM.getSize("games", true);
        myTime.value = Date.now()
    }

    watch(() => app.activeUserId, read)
    watch(() => ([
        props.time,
        times.datatags,
        times.evidence,
        times.externalizations
    ]), read, { deep: true })

</script>
