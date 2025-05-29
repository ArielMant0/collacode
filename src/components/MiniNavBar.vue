<template>
    <v-sheet v-if="!expandNavDrawer" :min-width="minWidth" position="fixed" border :style="{ maxWidth: minWidth+'px' }">
        <div class="pa-2" style="position: relative; height: 100vh;">

        <v-btn @click="expandNavDrawer = !expandNavDrawer"
            icon="mdi-arrow-right"
            block
            density="compact"
            rounded="sm"
            color="secondary"/>

        <v-divider class="mb-3 mt-3"></v-divider>

        <div class="d-flex flex-column align-center text-caption">

            <v-tooltip :text="'logged in as: '+(app.activeUser ? app.activeUser.name : '?')" location="right" open-delay="300">
                <template v-slot:activator="{ props }">
                    <v-avatar v-bind="props"
                        icon="mdi-account"
                        density="compact"
                        :color="userColor"/>
                </template>
            </v-tooltip>

            <v-divider class="mb-3 mt-3" style="width: 100%"></v-divider>

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

        <div v-if="inMainView" class="d-flex flex-column align-center text-caption">

            <v-divider class="mb-3 mt-3" style="width: 100%"></v-divider>

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

            <v-divider class="mb-3 mt-3" style="width: 100%"></v-divider>

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

            <v-divider class="mb-3 mt-3" style="width: 100%"></v-divider>

            <v-tooltip text="show tags for all coders" location="right" open-delay="300">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props"
                        :model-value="showAllUsers"
                        color="primary"
                        density="compact"
                        class="mt-1"
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

            <v-divider class="mb-3 mt-3" style="width: 100%"></v-divider>

            <span class="mb-1" style="text-align: center;">Code:</span>
            <span class="d-flex flex-column align-center">
                <b v-for="s in codeName.split(' ')">{{ s }}</b>
                <span v-if="otherCodeName" class="d-flex flex-column align-center">
                    to
                    <b v-for="s in otherCodeName.split(' ')">{{ s }}</b>
                </span>
            </span>
        </div>

        <v-tooltip location="right" open-delay="300">
            <template v-slot:activator="{ props }">
                <v-icon v-bind="props"
                    icon="mdi-information"
                    density="compact"
                    style="position: absolute; left: 16px; bottom: 20px;"/>
            </template>
            <template #default>
                <p>
                    CollaCode was developed for a scientific project by Franziska Becker.
                </p>
            </template>
        </v-tooltip>

        <v-tooltip text="visit collacode on Github" location="right" open-delay="300">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props"
                    @click="openInNewTab('https://github.com/ArielMant0/collacode')"
                    icon="mdi-github"
                    density="compact"
                    style="position: absolute; left: 14px; bottom: 45px;"
                    variant="flat"/>
            </template>
        </v-tooltip>

        </div>

    </v-sheet>

    <v-card v-else  class="pa-2" :min-width="320" :max-width="320" position="fixed" style="z-index: 5; height: 100vh; overflow-y: auto;">
        <v-btn @click="expandNavDrawer = !expandNavDrawer"
            icon="mdi-arrow-left"
            block
            class="mb-2"
            density="compact"
            rounded="sm"
            color="secondary"/>

        <div class="mt-2">

            <NavPanel v-model="expandNav.project" v-if="inMainView && datasets" title="Project" class="mb-3">
                <template #main>
                    <div class="d-flex align-center mb-4">
                        <v-select
                           :model-value="ds"
                           :items="datasets"
                           @update:model-value="id => app.setDataset(id)"
                           label="project"
                           class="mr-1"
                           density="compact"
                           hide-details
                           item-title="name"
                           item-value="id"/>
                       <v-btn
                           icon="mdi-plus"
                           color="primary"
                           density="comfortable"
                           class="ml-1"
                           rounded="sm"
                           @click="dsDialog = true"/>
                    </div>
                </template>

                <template #details>
                    <div class="d-flex align-center mb-2">
                        <div class="text-caption mr-1" style="width: 49%; text-align: center;">
                            <v-btn
                                icon="mdi-tray-arrow-down"
                                density="comfortable"
                                disabled
                                @click="goExport"
                                variant="outlined">
                            </v-btn>
                            <div>export data</div>
                        </div>
                        <div class="text-caption ml-1" style="width: 49%; text-align: center;">
                            <v-btn
                                icon="mdi-tray-arrow-up"
                                density="comfortable"
                                @click="goImport"
                                variant="outlined">
                            </v-btn>
                            <div>import data</div>
                        </div>
                    </div>
                </template>
            </NavPanel>


            <NavPanel v-if="inMainView" v-model="expandNav.filters" title="Filters" class="mb-3">
                <template #main>
                    <div class="d-flex justify-space-between mb-2">
                        <div class="text-caption mr-1" style="width: 49%; text-align: center;">
                            <v-btn
                                icon="mdi-sync"
                                density="comfortable"
                                variant="outlined"
                                color="primary"
                                @click="times.needsReload('all')">
                            </v-btn>
                            <div>reload data</div>
                        </div>

                        <div class="text-caption ml-1" style="width: 49%; text-align: center;">
                            <v-btn
                                icon="mdi-delete"
                                density="comfortable"
                                variant="outlined"
                                color="error"
                                :disabled="numFilters === 0"
                                @click="app.resetSelections()">
                            </v-btn>
                            <div>clear selection</div>
                        </div>
                    </div>
                </template>

                <template #details>
                    <MiniCollapseHeader v-model="showFilters" :text="'active filters ('+numFilters+')'" class="text-caption"/>
                    <div v-if="showFilters && numFilters > 0" class="ml-2 text-caption">
                        <FilterPanel :max-width="300"/>
                    </div>
                </template>
            </NavPanel>


            <NavPanel v-if="!app.static" v-model="expandNav.account" title="Account" class="mb-3">
                <template #main>
                    <div v-if="activeUserId && activeUserId > 0">
                        <div class="ml-1 mb-2" style="font-size: smaller;">
                            <v-avatar class="mr-1" icon="mdi-account" density="compact" :color="userColor"/>
                            {{ app.activeUser.name }} ({{ app.activeUser.short }})
                        </div>
                    </div>
                    <div v-else>
                        <v-btn
                            color="secondary"
                            density="compact"
                            class="text-caption mb-1"
                            block
                            @click="tryLogin">
                            login
                        </v-btn>
                    </div>
                </template>

                <template #details>
                    <div v-if="activeUserId && activeUserId > 0">
                        <div class="d-flex justify-space-between mb-1">
                            <v-btn
                                density="compact"
                                class="text-caption"
                                style="width: 49%;"
                                variant="tonal"
                                color="primary"
                                @click="changePW">
                                change password
                            </v-btn>
                            <v-btn
                                color="error"
                                density="compact"
                                class="text-caption"
                                variant="tonal"
                                style="width: 49%;"
                                @click="logout">
                                logout
                            </v-btn>
                        </div>


                        <div v-if="app.isAdmin" style="text-align: center;" class="text-caption mt-3">
                            <v-btn
                                density="comfortable"
                                variant="outlined"
                                :color="inAdminView ? 'error' : 'primary'"
                                :icon="inAdminView ? 'mdi-close' : 'mdi-open-in-app'"
                                class="mb-1"
                                @click="inAdminView ? goHome() : goAdmin()">
                            </v-btn>
                            <div>{{ inAdminView ? 'close' : 'open' }} admin area</div>
                        </div>
                    </div>
                </template>
            </NavPanel>

            <NavPanel v-model="expandNav.settings" title="Settings" class="mb-3">
                <template #main>
                    <div>
                        <div class="text-caption">sound volume: {{ volume }}</div>
                        <v-slider :model-value="volume"
                            :append-icon="sounds.getVolumeIcon()"
                            :min="0"
                            :max="1"
                            :step="0.05"
                            :thumb-size="20"
                            density="compact"
                            hide-details
                            hide-spin-buttons
                            @click:append="sounds.toggleMuted()"
                            @update:model-value="setVolume"/>
                    </div>
                    <div class="d-flex align-center ml-2 mb-2">
                        <v-checkbox-btn
                            v-model="lightMode"
                            density="compact"
                            inline
                            true-icon="mdi-white-balance-sunny"
                            false-icon="mdi-weather-night"/>

                            <span class="ml-1 text-caption">{{ lightMode ? 'light' : 'dark' }} mode active</span>
                    </div>

                    <div v-if="inMainView" class="d-flex align-center mt-2 ml-2">
                        <v-checkbox-btn
                            :model-value="showAllUsers"
                            color="primary"
                            density="compact"
                            inline
                            true-icon="mdi-tag"
                            false-icon="mdi-tag-off"
                            :disabled="app.static"
                            @click="app.toggleUserVisibility"/>

                        <span class="ml-1 text-caption">showing {{ showAllUsers ? 'data for all coders' : 'only your data' }}</span>
                    </div>
                </template>

                <template #details>
                    <div v-if="inMainView" class="mb-2">
                        <div class="text-caption mt-1">
                            start page: {{ settings.tabNames[startPage] }}
                        </div>
                        <div class="d-flex justify-space-between mb-1">
                            <v-btn
                                density="compact"
                                class="text-caption"
                                variant="tonal"
                                color="primary"
                                style="width: 49%;"
                                :disabled="startPage === activeTab"
                                @click="setAsStartPage">
                                save start page
                            </v-btn>
                            <v-btn
                                color="error"
                                density="compact"
                                class="text-caption"
                                variant="tonal"
                                style="width: 49%;"
                                @click="deleteStartPage">
                                delete start page
                            </v-btn>
                        </div>
                    </div>
                </template>
            </NavPanel>

            <div v-if="inMainView">

                <v-divider class="mt-3 mb-3"></v-divider>

                <NavPanel v-model="expandNav.codes" title="Code" class="mb-3">
                    <template #main>
                        <p style="text-align: center; font-size: smaller;"><b>{{ codeName }}</b></p>
                    </template>

                    <template #details>
                        <CodeWidget :initial="activeCode" :can-edit="allowEdit"/>
                    </template>
                </NavPanel>

                <NavPanel v-if="otherCodeName" v-model="expandNav.transitions" title="Transition" class="mb-3">
                    <template #main>
                        <p style="text-align: center; font-size: smaller;"><b>{{ codeName }}</b> to <b>{{ otherCodeName }}</b></p>
                    </template>

                    <template #details>
                        <TransitionWidget :initial="activeTransition" :allow-create="allowEdit"/>
                    </template>
                </NavPanel>

                <NavPanel v-model="expandNav.components" title="Components" class="mb-3">
                    <template #main>
                        <div class="d-flex justify-space-between">
                            <v-checkbox-btn v-model="showBarCodes"
                                density="compact"
                                style="max-width: 30px;"
                                :color="showBarCodes ? 'primary' : 'default'"
                                true-icon="mdi-barcode" false-icon="mdi-barcode-off"/>

                            <v-checkbox-btn v-model="showScatter"
                                density="compact"
                                style="max-width: 30px;"
                                :color="showScatter ? 'primary' : 'default'"
                                true-icon="mdi-blur" false-icon="mdi-blur-off"/>

                            <v-checkbox-btn v-model="showTable"
                                density="compact"
                                style="max-width: 30px;"
                                :color="showTable ? 'primary' : 'default'"
                                true-icon="mdi-cube-outline" false-icon="mdi-cube-off-outline"/>

                            <v-checkbox-btn v-model="showEvidenceTiles"
                                density="compact"
                                style="max-width: 30px;"
                                :color="showEvidenceTiles ? 'primary' : 'default'"
                                true-icon="mdi-image" false-icon="mdi-image-off"/>

                            <v-checkbox-btn v-if="hasMetaItems"
                                v-model="showExtTiles"
                                density="compact"
                                style="max-width: 30px;"
                                :color="showExtTiles ? 'primary' : 'default'"
                                true-icon="mdi-lightbulb" false-icon="mdi-lightbulb-off"/>
                        </div>

                    </template>
                    <template #details>
                        <v-checkbox-btn v-model="showBarCodes"
                            density="compact" :label="'bar codes ('+(showBarCodes?'on)':'off)')"
                            :color="showBarCodes ? 'primary' : 'default'"
                            class="mt-2"
                            true-icon="mdi-barcode" false-icon="mdi-barcode-off"/>

                        <v-checkbox-btn v-model="showScatter"
                            :label="'scatter plots ('+(showScatter?'on)':'off)')"  density="compact"
                            :color="showScatter ? 'primary' : 'default'"
                            true-icon="mdi-blur" false-icon="mdi-blur-off"/>

                        <v-checkbox-btn v-model="showTable"
                            :label="'item table ('+(showTable?'on)':'off)')" density="compact"
                            :color="showTable ? 'primary' : 'default'"
                            true-icon="mdi-cube-outline" false-icon="mdi-cube-off-outline"/>

                        <v-checkbox-btn v-model="showEvidenceTiles"
                            :label="'evidence list ('+(showEvidenceTiles?'on)':'off)')" density="compact"
                            :color="showEvidenceTiles ? 'primary' : 'default'"
                            true-icon="mdi-image" false-icon="mdi-image-off"/>

                        <v-checkbox-btn v-if="hasMetaItems"
                            v-model="showExtTiles"
                            :label="app.metaItemName+'s list ('+(showExtTiles?'on)':'off)')" density="compact"
                            :color="showExtTiles ? 'primary' : 'default'"
                            true-icon="mdi-lightbulb" false-icon="mdi-lightbulb-off"/>
                    </template>
                </NavPanel>

                <NavPanel v-model="expandNav.stats" title="Stats" class="mb-3">
                    <template #main>
                        <div class="d-flex align-center justify-space-between text-caption">
                            <div class="d-flex align-center"><v-icon color="primary">mdi-cube-outline</v-icon> <b>{{ formatNumber(stats.numItems, 8)  }}</b></div>
                            <div class="d-flex align-center"><v-icon color="primary">mdi-tag-outline</v-icon> <b>{{ formatNumber(stats.numTags, 8)  }}</b></div>
                            <div class="d-flex align-center"><v-icon color="primary">mdi-account-multiple-outline</v-icon><b>{{ formatNumber(stats.numDT, 8)  }}</b></div>
                            <div class="d-flex align-center"><v-icon color="primary">mdi-image-outline</v-icon><b>{{ formatNumber(stats.numEv, 8)  }}</b></div>
                            <div class="d-flex align-center" v-if="hasMetaItems"><v-icon color="primary">mdi-lightbulb-outline</v-icon><b>{{ formatNumber(stats.numMeta, 8)  }}</b></div>
                        </div>
                    </template>
                    <template #details>
                        <div class="text-caption mt-2">
                            <div>
                                <b class="stat-num">{{ formatNumber(stats.numItems, 8) }}</b>
                                <span class="text-capitalize">{{ capitalItem }}</span>
                            </div>
                            <div>
                                <b class="stat-num">{{ formatNumber(stats.numItemTags, 8) }}</b>
                                <span class="text-capitalize">{{ capitalItem }}</span> w/ Tags
                            </div>
                            <div>
                                <b class="stat-num">{{ formatNumber(stats.numItemEv, 8) }}</b>
                                <span class="text-capitalize">{{ capitalItem }}</span> w/ Evidence
                            </div>
                            <div v-if="hasMetaItems">
                                <b class="stat-num">{{ formatNumber(stats.numItemMeta, 8) }}</b>
                                <span class="text-capitalize">{{ capitalItem }}</span> w/ <span class="text-capitalize">{{ capitalMetaItem }}</span>
                            </div>

                            <v-divider class="mb-1 mt-1"></v-divider>

                            <div><b class="stat-num">{{ formatNumber(stats.numTags, 8) }}</b> Tags</div>
                            <div v-if="allowEdit"><b class="stat-num">{{ formatNumber(stats.numTagsUser, 8) }}</b> Tags by You</div>

                            <v-divider class="mb-1 mt-1"></v-divider>

                            <div><b class="stat-num">{{ formatNumber(stats.numDT, 8) }}</b> User Tags</div>
                            <div><b class="stat-num">{{ formatNumber(stats.numDTUnique, 8) }}</b> Unique User Tags</div>
                            <div v-if="allowEdit"><b class="stat-num">{{ formatNumber(stats.numDTUser, 8) }}</b> User Tags by You</div>

                            <v-divider class="mb-1 mt-1"></v-divider>

                            <div><b class="stat-num">{{ formatNumber(stats.numEv, 8) }}</b> Evidence</div>
                            <div v-if="allowEdit"><b class="stat-num">{{ formatNumber(stats.numEvUser, 8) }}</b> Evidence by You</div>

                            <v-divider class="mb-1 mt-1"></v-divider>

                            <div v-if="hasMetaItems"><b class="stat-num">{{ formatNumber(stats.numMeta, 8) }}</b> Meta Items</div>
                            <div v-if="hasMetaItems && allowEdit">
                                <b class="stat-num">{{ formatNumber(stats.numMetaUser, 8) }}</b> <span class="text-capitalize">{{ capitalMetaItem }}</span> by You
                            </div>
                        </div>
                    </template>
                </NavPanel>
            </div>

            <v-dialog v-model="askPw" width="auto" min-width="400">
                <v-card title="Change password">
                    <v-card-text>
                        <v-text-field v-model="pwOld"
                            label="old password"
                            type="password"
                            hide-spin-buttons
                            density="compact"/>
                        <v-text-field v-model="pwNew"
                            label="new password"
                            type="password"
                            hide-spin-buttons
                            density="compact"/>

                        <div class="d-flex justify-space-between">
                            <v-btn color="warning" @click="cancelChangePW">cancel</v-btn>
                            <v-btn color="primary" @click="tryChangePW">submit</v-btn>
                        </div>
                    </v-card-text>
                </v-card>
            </v-dialog>

            <v-dialog v-model="askLogin" width="auto" min-width="400">
                <v-card title="Login">
                    <v-card-text>
                        <v-form>
                            <v-text-field v-model="name"
                                label="user name"
                                autocomplete="username"
                                density="compact"/>
                            <v-text-field v-model="pw"
                                label="password"
                                type="password"
                                autocomplete="password"
                                @keydown="pwKeyDown"
                                density="compact"/>
                        </v-form>
                        <div class="d-flex justify-space-between">
                            <v-btn color="warning" @click="cancelLogin">cancel</v-btn>
                            <v-btn color="primary" @click="login">login</v-btn>
                        </div>
                    </v-card-text>
                </v-card>
            </v-dialog>

            <NewDatasetDialog v-model="dsDialog"/>
        </div>
    </v-card>
</template>

<script setup>
    import { storeToRefs } from 'pinia'
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { capitalize, formatNumber, openInNewTab } from '@/use/utility';
    import { computed, onMounted, reactive, watch } from 'vue';
    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import CodeWidget from './CodeWidget.vue';
    import TransitionWidget from './TransitionWidget.vue';
    import MiniCollapseHeader from './MiniCollapseHeader.vue';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';
    import { useTheme } from 'vuetify/lib/framework.mjs';
    import Cookies from 'js-cookie'
    import NewDatasetDialog from './dialogs/NewDatasetDialog.vue';
    import { useRoute, useRouter } from 'vue-router';
    import FilterPanel from './FilterPanel.vue';
    import { useSounds } from '@/store/sounds';
    import NavPanel from './NavPanel.vue';
    import { useGames } from '@/store/games';

    const settings = useSettings();
    const app = useApp();
    const times = useTimes()
    const loader = useLoader();
    const sounds = useSounds()
    const games = useGames()

    const { volume } = storeToRefs(sounds)

    const toast = useToast()
    const theme = useTheme()
    const router = useRouter()
    const route = useRoute()

    const props = defineProps({
        minWidth: {
            type: Number,
            default: 60
        },
    })

    const dsDialog = ref(false)

    const pwNew = ref("")
    const pwOld = ref("")
    const askPw = ref(false)

    const pw = ref("")
    const name = ref("")
    const askLogin = ref(false)

    const showFilters = ref(false)
    const numFilters = ref(0)

    const startPage = ref(__APP_START_PAGE__)

    const {
        lightMode,
        inMainView,
        activeTab,
        expandNav, expandNavDrawer,
        showTable, showScatter,
        showBarCodes, showEvidenceTiles,
        showExtTiles
    } = storeToRefs(settings);

    const {
        allowEdit, hasMetaItems,
        ds, datasets,
        codes, activeCode,
        activeTransition, transitions, transitionData,
        showAllUsers, activeUserId
    } = storeToRefs(app);

    const inAdminView = computed(() => route.path.startsWith("/admin"))

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

    const capitalItem = computed(() => capitalize(app.itemName+'s'))
    const capitalMetaItem = computed(() => capitalize(app.metaItemName+'s'))

    const userColor = computed(() => {
        if (activeUserId.value) {
            return app.getUserColor(activeUserId.value)
        }
        return "default"
    })

    function setVolume(value) {
        sounds.setVolume(value)
        Cookies.set("volume", volume.value, { expires: 365 })
    }

    function setAsStartPage() {
        Cookies.set("start-page", settings.activeTab, { expires: 365 })
        startPage.value = settings.activeTab;

    }
    function deleteStartPage() {
        Cookies.set("start-page", __APP_START_PAGE__, { expires: 365 })
        startPage.value = __APP_START_PAGE__;
    }

    async function logout() {
        if (!activeUserId.value || activeUserId.value < 0) {
            return toast.error("you are not logged in")
        }

        try {
            await loader.post("/logout")
            toast.success("logged out")
            app.setActiveUser(-1)
            Cookies.set("isGuest", true, { expires: 365 })
        } catch {
            console.debug("logout error")
        }
    }

    function cancelLogin() {
        if (activeUserId.value && activeUserId.value >= 0) {
            return toast.error("you are already logged in")
        }
        name.value = ""
        pw.value = ""
        askLogin.value = true;
    }
    function tryLogin() {
        if (activeUserId.value && activeUserId.value >= 0) {
            return toast.error("you are already logged in")
        }
        name.value = ""
        pw.value = ""
        askLogin.value = true;
    }
    function pwKeyDown(event) {
        if (event.code === "Enter") {
            login()
        }
    }
    function makeBasicAuth(name, pw) { return btoa(name+":"+pw) }
    async function login() {
        if (!name.value) return toast.error("missing name")
        if (!pw.value) return toast.error("missing password")

        try {
            const uid = await loader.post("/login", null, null, { "Authorization": "Basic "+makeBasicAuth(name.value, pw.value)})
            toast.success("logged in succesfully")
            askLogin.value = false;
            app.setActiveUser(uid.id)
            Cookies.remove("isGuest")
            name.value = ""
            pw.value = ""
        } catch {
            toast.error("error during login")
        }
    }

    function changePW() {
        pwOld.value = ""
        pwNew.value = ""
        askPw.value = true;
    }
    function cancelChangePW() {
        askPw.value = false;
        pwOld.value = ""
        pwNew.value = ""
    }
    async function tryChangePW() {
        if (!pwOld.value) return toast.error("missing old password")
        if (!pwNew.value) return toast.error("missing new password")
        if (pwOld.value === pwNew.value) return toast.error("passwords must be different")

        try {
            await loader.post("/user_pwd", null, { old: btoa(pwOld.value), new: btoa(pwNew.value) })
            askPw.value = false;
            pwOld.value = ""
            pwNew.value = ""
        } catch {
            toast.error("error changing password")
        }
    }

    const stats = reactive({
        numItems: 0, numItemTags: 0, numItemEv: 0, numItemMeta: 0,
        numTags: 0, numTagsUser: 0,
        numDT: 0, numDTUnique: 0, numDTUser: 0,
        numEv: 0, numEvUser: 0,
        numMeta: 0, numMetaUser: 0
    })

    function readStats() {
        readItemStats()
        readTagStats()
        readDatatagsStats();
        readEvidenceStats();
        readMetaItemsStats()
        readMetaItemsStats();
    }
    function readItemStats() {
        stats.numItems = DM.getSize("items", false);
        let wT = 0, wEv = 0, wEx = 0, dtU = 0;
        DM.getData("items", false).forEach(d => {
            if (d.allTags.length > 0) wT++
            if (d.numEvidence > 0) wEv++
            if (d.numMeta > 0) wEx++
            dtU += d.allTags.length
        })
        stats.numItemTags = wT
        stats.numItemEv = wEv
        stats.numItemMeta = wEx
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
    function readMetaItemsStats() {
        stats.numMeta = DM.getSize("meta_items", false);
        stats.numMetaUser = showAllUsers.value ? 0 :
            DM.getSizeBy("meta_items", d => d.created_by === activeUserId.value)
    }

    function goImport() {
        router.push("/import")
        expandNavDrawer.value = false
    }
    function goExport() {
        router.push("/export")
        expandNavDrawer.value = false
    }
    function goAdmin() {
        router.push('/admin')
        expandNavDrawer.value = false
    }
    function goHome() {
        router.push('/')
        expandNavDrawer.value = false
    }

    onMounted(function() {
        const t = Cookies.get("theme")
        if (t) {
            lightMode.value = t === "light"
        } else {
            let preferDark;
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                preferDark = true
            }

            lightMode.value = preferDark !== undefined?
                !preferDark :
                !theme.global.current.value.dark
        }
        const sp = Cookies.get("start-page")
        startPage.value = sp !== undefined ? sp : __APP_START_PAGE__;
        Cookies.set("start-page", startPage.value, { expires: 365 })
        const initialVolume = Cookies.get("volume")
        if (initialVolume) {
            sounds.setVolume(Number.parseFloat(initialVolume), false)
        }
        readStats()
        numFilters.value = DM.filters.size
    })

    watch(() => times.f_any, function() {
        numFilters.value = DM.filters.size
    });

    watch(() => times.items, readItemStats)
    watch(() => times.tags, readTagStats)
    watch(() => times.datatags, readDatatagsStats)
    watch(() => times.evidence, readEvidenceStats)
    watch(() => times.meta_items, readMetaItemsStats)
    watch(activeUserId, readStats)

    watch(lightMode, function(light) {
        theme.global.name.value = light ? 'customLight' : 'customDark'
        Cookies.set("theme", light ? "light" : "dark", { expires: 365 })
        games.setThemeColors(theme.current.value.colors)
    })

</script>

<style scoped>
.stat-num {
    display: inline-block;
    width: 60px;
    max-width: 60px;
    min-width: 60px;
    margin-right: 2px;
}
</style>