<template>
    <v-sheet ref="el" class="pa-0">
    <v-layout>

        <MiniNavBar
            :user-color="app.activeUser ? app.activeUser.color : 'default'"
            :code-name="app.activeCode ? app.getCodeName(oldCode) : '?'"
            :other-code-name="transitionData ? app.getCodeName(newCode) : '?'"/>

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
                        allow-create/>
                </v-card>
            </div>
        </v-card>

        <div v-if="!loading" class="pa-2" style="width: 100%; margin-left: 80px;">
            <div v-if="activeTransition" class="d-flex flex-column">
                <CodingTransition :old-code="oldCode" :new-code="newCode"/>
            </div>
        </div>
    </v-layout>
    </v-sheet>
</template>

<script setup>
    import UserPanel from '@/components/UserPanel.vue';
    import CodingTransition from '@/components/CodingTransition.vue';
    import TransitionWidget from '../TransitionWidget.vue';
    import MiniNavBar from '../MiniNavBar.vue';

    import { useApp } from '@/store/app'
    import { useSettings } from '@/store/settings'
    import { storeToRefs } from 'pinia'
    import { ref } from 'vue'
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
        loading: {
            type: Boolean,
            default: false
        }
    })

    const el = ref(null);

</script>
