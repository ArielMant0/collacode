<template>
    <v-sheet ref="el" class="pa-0">
    <v-layout>

        <MiniNavBar
            :user-color="app.activeUser ? app.activeUser.color : 'default'"
            :code-name="app.activeCode ? app.getCodeName(app.activeCode) : '?'"/>

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


        <div v-if="initialized && !loading" class="mb-2 pa-4" style="width: 100%; margin-left: 80px;">
            <h3 style="text-align: center" class="mt-4 mb-4">{{ stats.numGamesSel }} / {{ stats.numGames }} GAMES</h3>
            <RawDataView
                selectable
                editable
                allow-add
                check-assigned/>

            <div style="text-align: center;">
                <v-btn
                    color="primary"
                    density="compact"
                    class="text-caption mt-8 mb-4"
                    @click="showEvidence = !showEvidence">
                    {{ showEvidence ? 'hide' : 'show' }} evidence
                </v-btn>
                <GameEvidenceTiles v-if="showEvidence" :code="activeCode"/>
            </div>
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
    import GameEvidenceTiles from '../evidence/GameEvidenceTiles.vue';
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
        loading: {
            type: Boolean,
            default: false
        }
    })

    const showEvidence = ref(false)
    const stats = reactive({ numGames: 0, numGamesSel: 0 })

    const el = ref(null);

    function setActiveCode(id) {
        if (id !== app.activeCode) {
            app.setActiveCode(id);
            times.needsReload();
        }
    }

    function readStats() {
        stats.numGames = DM.getSize("games", false);
        stats.numGamesSel = DM.getSize("games", true);
    }

    watch(() => Math.max(times.games, times.f_games), readStats)

</script>
