<template>
    <v-sheet
        position="fixed"
        border
        :style="{
            left: 0,
            top: 0,
            zIndex: zIndex,
            minWidth: showNavTop ? '100vw' : size+'px',
            maxWidth: showNavTop ? '100vw' : size+'px'
        }">
        <div class="pa-2" style="position: relative;"
            :style="{ height: showNavTop ? 'auto' : '100vh' }"
            :class="{ 'd-flex': showNavTop, 'align-center': showNavTop }">

            <v-btn @click="expandNavDrawer = !expandNavDrawer"
                :icon="showNavTop ? 'mdi-arrow-down' : 'mdi-arrow-right'"
                :block="!showNavTop"
                density="compact"
                rounded="sm"
                :class="{ 'mr-2': showNavTop }"
                color="secondary"/>

            <v-divider :vertical="showNavTop" :class="{ mobile: showNavTop, 'nav-divider': true }"></v-divider>

            <div class="d-flex align-center text-caption" :class="{ 'flex-column': !showNavTop }">

                <v-tooltip :text="'logged in as: '+(app.activeUser ? app.activeUser.name : '?')" location="right" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-avatar v-bind="props"
                            icon="mdi-account"
                            density="compact"
                            size="small"
                            :color="userColor"/>
                    </template>
                </v-tooltip>

                <v-divider :vertical="showNavTop" :class="{ mobile: showNavTop, 'nav-divider': true }"></v-divider>

                <v-tooltip text="toggle light/dark mode" location="right" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-checkbox-btn v-bind="props"
                            v-model="lightMode"
                            density="compact"
                            inline
                            true-icon="mdi-white-balance-sunny"
                            false-icon="mdi-weather-night"/>
                    </template>
                </v-tooltip>
            </div>

            <div v-if="inMainView" class="d-flex align-center text-caption" :class="{ 'flex-column': !showNavTop }">

                <v-divider :vertical="showNavTop" :class="{ mobile: showNavTop, 'nav-divider': true }"></v-divider>

                <v-tooltip text="reload all data" location="right" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props"
                            icon="mdi-sync"
                            color="primary"
                            variant="tonal"
                            @click="times.needsReload('all')"
                            density="compact"/>
                    </template>
                </v-tooltip>

                <v-divider :vertical="showNavTop" :class="{ mobile: showNavTop, 'nav-divider': true }"></v-divider>

                <v-tooltip text="clear selection" location="right" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props"
                            icon="mdi-delete"
                            color="error"
                            variant="tonal"
                            :disabled="numFilters === 0"
                            @click="app.resetSelections()"
                            density="compact"/>
                    </template>
                </v-tooltip>

                <v-divider :vertical="showNavTop" :class="{ mobile: showNavTop, 'nav-divider': true }"></v-divider>

                <v-tooltip text="show tags for all coders" location="right" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-checkbox-btn v-bind="props"
                            :model-value="showAllUsers"
                            color="primary"
                            density="compact"
                            inline
                            true-icon="mdi-tag"
                            false-icon="mdi-tag-off"
                            :disabled="app.static"
                            @click="app.toggleUserVisibility"/>
                    </template>
                </v-tooltip>

                <v-tooltip text="show bar codes" location="right" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-checkbox-btn v-bind="props" v-model="showBarCodes" density="compact"
                            :color="showBarCodes ? 'primary' : 'default'"
                            inline true-icon="mdi-barcode" false-icon="mdi-barcode-off"/>
                    </template>
                </v-tooltip>
                <v-tooltip text="show scatter plots" location="right" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-checkbox-btn v-bind="props" v-model="showScatter" density="compact"
                            :color="showScatter ? 'primary' : 'default'"
                            inline true-icon="mdi-blur" false-icon="mdi-blur-off"/>
                    </template>
                </v-tooltip>
                <v-tooltip :text="'show '+app.itemName+'s'" location="right" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-checkbox-btn v-bind="props" v-model="showTable" density="compact"
                            :color="showTable ? 'primary' : 'default'"
                            inline true-icon="mdi-cube-outline" false-icon="mdi-cube-off-outline"/>
                    </template>
                </v-tooltip>
                <v-tooltip text="show evidences" location="right" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-checkbox-btn v-bind="props" v-model="showEvidenceTiles" density="compact"
                            :color="showEvidenceTiles ? 'primary' : 'default'"
                            inline true-icon="mdi-image" false-icon="mdi-image-off"/>
                    </template>
                </v-tooltip>
                <v-tooltip v-if="hasMetaItems" :text="'show '+app.metaItemName+'s'" location="right" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-checkbox-btn v-bind="props" v-model="showExtTiles" density="compact"
                            :color="showExtTiles ? 'primary' : 'default'"
                            inline true-icon="mdi-lightbulb" false-icon="mdi-lightbulb-off"/>
                    </template>
                </v-tooltip>

                <v-divider v-if="smAndUp" class="nav-divider"></v-divider>

                <div v-if="smAndUp" style="text-align: center;" :class="{ 'mb-1': !showNavTop, 'mr-1': showNavTop, 'ml-2': showNavTop }">Code:</div>
                <span v-if="smAndUp" class="d-flex align-center" :class="{ 'flex-column': !showNavTop }">
                    <b v-for="s in codeName.split(' ')">{{ s }}</b>
                    <span v-if="otherCodeName" class="d-flex align-center" :class="{ 'flex-column': !showNavTop }">
                        to
                        <b v-for="s in otherCodeName.split(' ')">{{ s }}</b>
                    </span>
                </span>
            </div>

            <div v-if="smAndUp && height > 500">
                <v-tooltip :location="showNavTop ? 'bottom' : 'right'" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-icon v-bind="props"
                            icon="mdi-information"
                            density="compact"
                            variant="flat"
                            :style="{
                                position: 'absolute',
                                left: showNavTop ? null : '16px',
                                right: showNavTop ? '48px' : null,
                                bottom: showNavTop ? '10px' : '20px'
                            }"/>
                    </template>
                    <template #default>
                        <p>
                            CollaCode was developed for a scientific project by Franziska Becker.
                        </p>
                    </template>
                </v-tooltip>

                <v-tooltip text="visit collacode on Github" :location="showNavTop ? 'bottom' : 'right'" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props"
                            @click="openInNewTab('https://github.com/ArielMant0/collacode')"
                            icon="mdi-github"
                            density="compact"
                            variant="flat"
                            :style="{
                                position: 'absolute',
                                left: showNavTop ? null : '14px',
                                right: showNavTop ? '16px' : null,
                                bottom: showNavTop ? '8px' : '45px'
                            }"/>
                    </template>
                </v-tooltip>
            </div>
        </div>
    </v-sheet>
</template>

<script setup>
    import { storeToRefs } from 'pinia'
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { openInNewTab } from '@/use/utility';
    import { computed } from 'vue';
    import { useTimes } from '@/store/times';
    import { useDisplay } from 'vuetify';
    import { useWindowSize } from '@vueuse/core';

    const settings = useSettings();
    const app = useApp();
    const times = useTimes()

    const { smAndUp } = useDisplay()

    const props = defineProps({
        stats: {
            type: Object,
            required: true
        },
        numFilters: {
            type: Number,
            default: 0
        },
        size: {
            type: Number,
            default: 60
        },
        zIndex: {
            type: Number,
            default: 1999
        },
    })

    const {
        lightMode,
        inMainView,
        activeTab,
        showNavTop,
        expandNavDrawer,
        showTable, showScatter,
        showBarCodes, showEvidenceTiles,
        showExtTiles
    } = storeToRefs(settings);

    const {
        hasMetaItems,
        transitionData,
        showAllUsers,
        activeUserId
    } = storeToRefs(app);

    const { height } = useWindowSize()

    const codeName = computed(() => {
        return app.activeCode ?
            app.getCodeName(activeTab.value === "transition" && transitionData.value ? app.oldCode : app.activeCode) :
            "?"
    })
    const otherCodeName = computed(() => {
        return activeTab.value === "transition" && transitionData.value ?
            (app.newCode ? app.getCodeName(app.newCode) : "?") :
            null
    })

    const userColor = computed(() => {
        if (activeUserId.value) {
            return app.getUserColor(activeUserId.value)
        }
        return "default"
    })

</script>

<style scoped>
.nav-divider {
   margin: 8px 0px
}

.nav-divider.mobile {
   margin: 0px 6px
}
</style>
