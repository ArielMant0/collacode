<template>
    <v-sheet class="pa-2" :min-width="minWidth" position="fixed" style="z-index: 3999; height: 100vh" border>
        <v-btn @click="expandNavDrawer = !expandNavDrawer"
            icon="mdi-arrow-right"
            block
            density="compact"
            rounded="sm"
            color="secondary"/>

        <v-divider class="mb-2 mt-2"></v-divider>

        <div class="d-flex flex-column align-center text-caption">

            <v-btn icon="mdi-sync" color="primary" @click="app.fetchUpdate()" density="comfortable"/>
            <v-divider class="mb-2 mt-2" style="width: 100%"></v-divider>

            <v-switch v-if="userColor"
                :model-value="showAllUsers"
                color="primary"
                density="compact"
                direction="vertical"
                hide-details
                hide-spin-buttons
                @click="app.toggleUserVisibility"/>

            <v-avatar v-if="userColor" icon="mdi-account" density="compact" class="mt-3 mb-1" :color="userColor"/>

            <span class="mt-2 mb-1" style="text-align: center;">Code:</span>
            <span class="d-flex flex-column align-center">
                <b v-for="s in codeName.split(' ')">{{ s }}</b>
                <span v-if="otherCodeName" class="d-flex flex-column align-center">
                    to
                    <b v-for="s in otherCodeName.split(' ')">{{ s }}</b>
                </span>
            </span>

            <span class="mt-3 mb-1" style="text-align: center;">Games:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numGames) }}</v-chip>
            <v-tooltip text="games with tags" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props" density="compact" class="mt-1 text-caption" color="primary">{{ formatNumber(stats.numGamesTags) }}</v-chip>
                </template>
            </v-tooltip>

            <v-tooltip text="games with evidence" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props" density="compact" class="mt-1 text-caption" color="primary">{{ formatNumber(stats.numGamesEv) }}</v-chip>
                </template>
            </v-tooltip>

            <v-tooltip text="games with externalizations" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props" density="compact" class="mt-1 text-caption" color="primary">{{ formatNumber(stats.numGamesExt) }}</v-chip>
                </template>
            </v-tooltip>

            <span class="mt-3 mb-1" style="text-align: center;">Tags:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numTags) }}</v-chip>
            <v-tooltip v-if="stats.numTagsUser > 0" :text="'tags created by '+app.activeUser.name" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props" density="compact" class="mt-1 text-caption" :color="userColor">{{ formatNumber(stats.numTagsUser) }}</v-chip>
                </template>
            </v-tooltip>

            <span class="mt-3 mb-1" style="text-align: center;">Game Tags:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numDT) }}</v-chip>
            <v-tooltip v-if="stats.numDTUser > 0" text="number of unique tags" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props"density="compact" class="mt-1 text-caption" color="primary">{{ formatNumber(stats.numDTUnique) }}</v-chip>
                </template>
            </v-tooltip>
            <v-tooltip v-if="stats.numDTUser > 0" :text="'game tags added by '+app.activeUser.name" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props" density="compact" class="mt-1 text-caption" :color="userColor">{{ formatNumber(stats.numDTUser) }}</v-chip>
                </template>
            </v-tooltip>

            <span class="mt-3 mb-1" style="text-align: center;">Evidence:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numEv) }}</v-chip>
            <v-tooltip v-if="stats.numEvUser > 0" :text="'evidence created by '+app.activeUser.name" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props" density="compact" class="mt-1 text-caption" :color="userColor">{{ formatNumber(stats.numEvUser) }}</v-chip>
                </template>
            </v-tooltip>

            <span class="mt-3 mb-1" style="text-align: center;">Exts:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numExt) }}</v-chip>
            <v-tooltip v-if="stats.numExtUser > 0" :text="'evidence created by '+app.activeUser.name" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props" density="compact" class="mt-1 text-caption" :color="userColor">{{ formatNumber(stats.numExtUser) }}</v-chip>
                </template>
            </v-tooltip>
        </div>
    </v-sheet>
</template>

<script setup>
    import { storeToRefs } from 'pinia'
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { formatNumber } from '@/use/utility';
    import { onMounted, reactive, watch } from 'vue';
    import DM from '@/use/data-manager';

    const settings = useSettings();
    const app = useApp();

    const props = defineProps({
        time: {
            type: Number,
            default: 0
        },
        codeName: {
            type: String,
            required: true
        },
        otherCodeName: {
            type: String,
        },
        userColor: {
            type: String,
            default: ""
        },
        minWidth: {
            type: Number,
            default: 60
        },
    })

    const { expandNavDrawer } = storeToRefs(settings);
    const { showAllUsers, activeUserId } = storeToRefs(app);

    const stats = reactive({
        numGames: 0, numGamesTags: 0, numGamesEv: 0, numGamesExt: 0,
        numTags: 0, numTagsUser: 0,
        numDT: 0, numDTUnique: 0, numDTUser: 0,
        numEv: 0, numEvUser: 0,
        numExt: 0, numExtUser: 0
    })

    function readStats() {
        stats.numGames = DM.getSize("games", false);
        let wT = 0, wEv = 0, wEx = 0, dtU = 0;
        DM.getData("games", false).forEach(d => {
            if (d.allTags.length > 0) wT++
            if (d.numEvidence > 0) wEv++
            if (d.numExt > 0) wEx++
            dtU += d.allTags.length
        })
        stats.numGamesTags = wT
        stats.numGamesEv = wEv
        stats.numGamesExt = wEx
        stats.numTags = DM.getSize("tags", false);
        stats.numDT = DM.getSize("datatags", false);
        stats.numDTUnique = dtU
        stats.numEv = DM.getSize("evidence", false);
        stats.numExt = DM.getSize("externalizations", false);
        readUserStats()
    }

    function readUserStats() {
        if (!showAllUsers.value) {
            stats.numTagsUser = DM.getSizeBy("tags", d => d.created_by === activeUserId.value);
            stats.numDTUser = DM.getSizeBy("datatags", d => d.created_by === activeUserId.value)
            stats.numEvUser = DM.getSizeBy("evidence", d => d.created_by === activeUserId.value)
            stats.numExtUser = DM.getSizeBy("externalizations", d => d.created_by === activeUserId.value)
        } else {
            stats.numTagsUser = 0
            stats.numDTUser = 0
            stats.numEvUser = 0
            stats.numExtUser = 0
        }
    }

    onMounted(readStats)

    watch(() => props.time, readStats)
    watch(activeUserId, readUserStats)
</script>