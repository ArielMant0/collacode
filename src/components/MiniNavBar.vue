<template>
    <v-sheet class="pa-2" :min-width="minWidth">
        <v-btn @click="expandNavDrawer = !expandNavDrawer"
            icon="mdi-arrow-right"
            block
            density="compact"
            rounded="sm"
            color="secondary"/>

        <v-divider class="mb-2 mt-2"></v-divider>

        <div  class="d-flex flex-column align-center text-caption">

            <v-avatar v-if="userColor" icon="mdi-account" density="compact" class="mb-2" :color="userColor"/>
            <v-switch v-if="userColor"
                :model-value="showAllUsers"
                color="primary"
                density="compact"
                direction="vertical"
                hide-details
                hide-spin-buttons
                @click="app.toggleUserVisibility"/>

            <span class="mt-2 mb-1" style="text-align: center;">Code:</span>
            <span class="d-flex flex-column align-center">
                <b v-for="s in codeName.split(' ')">{{ s }}</b>
                <span v-if="otherCodeName">
                    to
                    <b v-for="s in otherCodeName.split(' ')">{{ s }}</b>
                </span>
            </span>

            <span class="mt-3 mb-1" style="text-align: center;">Games:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(numGames) }}</v-chip>

            <span class="mt-3 mb-1" style="text-align: center;">Tags:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(numTags) }}</v-chip>
            <v-chip v-if="numTagsUser > 0" density="compact" class="mt-1 text-caption" color="primary">{{ formatNumber(numTagsUser) }}</v-chip>

            <span class="mt-3 mb-1" style="text-align: center;">User Tags:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(numDT) }}</v-chip>
            <v-chip v-if="numDTUser > 0" density="compact" class="mt-1 text-caption" color="primary">{{ formatNumber(numDTUser) }}</v-chip>
        </div>
    </v-sheet>
</template>

<script setup>
    import { storeToRefs } from 'pinia'
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { formatNumber } from '@/use/utility';

    const settings = useSettings();
    const app = useApp();

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
        numGames: {
            type: Number,
            default: 0
        },
        numTags: {
            type: Number,
            default: 0
        },
        numTagsUser: {
            type: Number,
            default: 0
        },
        numDT: {
            type: Number,
            default: 0
        },
        numDTUser: {
            type: Number,
            default: 0
        },
        minWidth: {
            type: Number,
            default: 60
        },
    })

    const { expandNavDrawer } = storeToRefs(settings);
    const { showAllUsers } = storeToRefs(app);
</script>