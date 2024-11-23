<template>
    <v-sheet class="pa-2" :min-width="minWidth" position="fixed" style="height: 100vh" border>
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

            <v-avatar v-if="userColor" icon="mdi-account" density="compact" class="mt-3 mb-1" :color="userColor"/>
            <v-divider class="mb-2 mt-2" style="width: 100%"></v-divider>

            <v-tooltip  v-if="userColor" text="show tags for all users" location="right">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props"
                        :model-value="showAllUsers"
                        color="primary"
                        density="compact"
                        class="mt-1"
                        inlines true-icon="mdi-tag"
                        false-icon="mdi-tag-off"
                        @click="app.toggleUserVisibility"/>
                </template>
            </v-tooltip>

            <v-tooltip text="show bar codes" location="right">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props" v-model="showBarCodes" density="compact"
                        inline true-icon="mdi-barcode" false-icon="mdi-barcode-off"/>
                </template>
            </v-tooltip>
            <v-tooltip text="show games" location="right">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props" v-model="showTable" density="compact"
                        inline true-icon="mdi-controller" false-icon="mdi-controller-off"/>
                </template>
            </v-tooltip>
            <v-tooltip text="show evidences" location="right">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props" v-model="showEvidenceTiles" density="compact"
                         inline true-icon="mdi-image" false-icon="mdi-image-off"/>
                </template>
            </v-tooltip>
            <v-tooltip text="show externalizations" location="right">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props" v-model="showExtTiles" density="compact"
                        inline true-icon="mdi-lightbulb" false-icon="mdi-lightbulb-off"/>
                </template>
            </v-tooltip>

            <v-divider class="mb-2 mt-2" style="width: 100%"></v-divider>

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

            <span class="mt-3 mb-1" style="text-align: center;">User Tags:</span>
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
    import { useTimes } from '@/store/times';

    const settings = useSettings();
    const app = useApp();
    const times = useTimes()

    const props = defineProps({
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

    const { expandNavDrawer, showTable, showBarCodes, showEvidenceTiles, showExtTiles } = storeToRefs(settings);
    const { showAllUsers, activeUserId } = storeToRefs(app);

    const stats = reactive({
        numGames: 0, numGamesTags: 0, numGamesEv: 0, numGamesExt: 0,
        numTags: 0, numTagsUser: 0,
        numDT: 0, numDTUnique: 0, numDTUser: 0,
        numEv: 0, numEvUser: 0,
        numExt: 0, numExtUser: 0
    })

    function readStats() {
        readGameStats()
        readTagStats()
        readDatatagsStats();
        readEvidenceStats();
        readExtStats()
        readExtStats();
    }
    function readGameStats() {
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
        stats.numDTUnique = dtU
    }
    function readTagStats() {
        stats.numTags = DM.getSize("tags", false);
        stats.numTagsUser = showAllUsers.value ? 0 :
            DM.getSizeBy("tags", d => d.created_by === activeUserId.value);
    }
    function readDatatagsStats() {
        stats.numDT = DM.getSize("datatags", false);
        stats.numDTUser = showAllUsers.value ? 0 :
            DM.getSizeBy("datatags", d => d.created_by === activeUserId.value)
    }
    function readEvidenceStats() {
        stats.numEv = DM.getSize("evidence", false);
        stats.numEvUser = showAllUsers.value ? 0 :
            DM.getSizeBy("evidence", d => d.created_by === activeUserId.value)
    }
    function readExtStats() {
        stats.numExt = DM.getSize("externalizations", false);
        stats.numExtUser = showAllUsers.value ? 0 :
            DM.getSizeBy("externalizations", d => d.created_by === activeUserId.value)
    }


    onMounted(readStats)

    watch(() => times.games, readGameStats)
    watch(() => times.tags, readTagStats)
    watch(() => times.datatags, readDatatagsStats)
    watch(() => times.evidence, readEvidenceStats)
    watch(() => times.externalizations, readExtStats)
    watch(activeUserId, readStats)
</script>