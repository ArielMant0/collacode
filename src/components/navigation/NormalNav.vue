<template>
    <v-card class="pa-2"
        position="fixed"
        :style="{
            top: 0,
            left: 0,
            zIndex: zIndex,
            height: '100vh',
            overflowY: 'auto',
            minWidth: showNavTop ? '100vw' : size+'px',
            maxWidth: showNavTop ? '100vw' : size+'px',
        }">
        <v-btn @click="expandNavDrawer = !expandNavDrawer"
            :icon="showNavTop ? 'mdi-arrow-up' : 'mdi-arrow-left'"
            block
            class="mb-2"
            density="compact"
            rounded="sm"
            color="secondary"/>

        <div class="mt-2">

            <NavPanel v-model="expandNav.project" :expand-on-hover="expandOnHover" v-if="inMainView && datasets" title="Project" class="mb-3">
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
                                @click="goTo('/export')"
                                variant="outlined">
                            </v-btn>
                            <div>export data</div>
                        </div>
                        <div class="text-caption ml-1" style="width: 49%; text-align: center;">
                            <v-btn
                                icon="mdi-tray-arrow-up"
                                density="comfortable"
                                @click="goTo('/import')"
                                variant="outlined">
                            </v-btn>
                            <div>import data</div>
                        </div>
                    </div>
                </template>
            </NavPanel>


            <NavPanel v-if="inMainView" v-model="expandNav.filters" :expand-on-hover="expandOnHover" title="Filters" class="mb-3">
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


            <NavPanel v-if="!app.static" v-model="expandNav.account" :expand-on-hover="expandOnHover" title="Account" class="mb-3">
                <template #main>
                    <div v-if="activeUserId && activeUserId > 0">
                        <div class="ml-1 mb-2" style="font-size: smaller;">
                            <v-avatar class="mr-1" icon="mdi-account" size="small" :color="userColor"/>
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


                        <div v-if="app.isAdmin" class="text-caption mt-3 d-flex align-center justify-space-around">
                            <div style="text-align: center;">
                                <v-btn
                                    density="comfortable"
                                    variant="outlined"
                                    :color="inAdminView ? 'error' : 'primary'"
                                    :icon="inAdminView ? 'mdi-close' : 'mdi-open-in-app'"
                                    class="mb-1"
                                    @click="inAdminView ? goTo('/') : goTo('/admin')">
                                </v-btn>
                                <div>{{ inAdminView ? 'close' : 'open' }} admin area</div>
                            </div>

                            <div style="text-align: center;">
                                <v-btn
                                    density="comfortable"
                                    variant="outlined"
                                    :color="inAdminView ? 'error' : 'primary'"
                                    :icon="inAdminView ? 'mdi-close' : 'mdi-open-in-app'"
                                    class="mb-1"
                                    @click="inAdminView ? goTo('/') : goTo('/loganalysis')">
                                </v-btn>
                                <div>{{ inLogView ? 'close' : 'open' }} log analysis</div>
                            </div>
                        </div>
                    </div>
                </template>
            </NavPanel>

            <NavPanel v-model="expandNav.settings" :expand-on-hover="expandOnHover" title="Settings" class="mb-3">
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
                            readonly
                            color="primary"
                            density="compact"
                            inline
                            true-icon="mdi-tag"
                            false-icon="mdi-tag-off"
                            :disabled="app.static"
                            @click="toggleVisibiliy"/>

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

                <NavPanel v-model="expandNav.codes" :expand-on-hover="expandOnHover" title="Code" class="mb-3">
                    <template #main>
                        <p style="text-align: center; font-size: smaller;"><b>{{ codeName }}</b></p>
                    </template>

                    <template #details>
                        <CodeWidget :initial="activeCode" :can-edit="allowEdit"/>
                    </template>
                </NavPanel>

                <NavPanel v-if="otherCodeName" v-model="expandNav.transitions" :expand-on-hover="expandOnHover" title="Transition" class="mb-3">
                    <template #main>
                        <p style="text-align: center; font-size: smaller;"><b>{{ codeName }}</b> to <b>{{ otherCodeName }}</b></p>
                    </template>

                    <template #details>
                        <TransitionWidget :initial="activeTransition" :allow-create="allowEdit"/>
                    </template>
                </NavPanel>

                <NavPanel v-model="expandNav.components" :expand-on-hover="expandOnHover" title="Components" class="mb-3">
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

                <NavPanel v-model="expandNav.stats" :expand-on-hover="expandOnHover" title="Stats" class="mb-3">
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
    import { capitalize, formatNumber } from '@/use/utility';
    import { computed, onMounted } from 'vue';
    import { useTimes } from '@/store/times';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';
    import Cookies from 'js-cookie'
    import { useRoute, useRouter } from 'vue-router';
    import { useSounds } from '@/store/sounds';
    import CodeWidget from '../CodeWidget.vue';
    import NewDatasetDialog from '../dialogs/NewDatasetDialog.vue';
    import NavPanel from './NavPanel.vue';
    import TransitionWidget from '../TransitionWidget.vue';
    import FilterPanel from '../FilterPanel.vue';
    import MiniCollapseHeader from '../MiniCollapseHeader.vue';

    const settings = useSettings();
    const app = useApp();
    const times = useTimes()
    const loader = useLoader();
    const sounds = useSounds()

    const { volume } = storeToRefs(sounds)
    const { showNavTop } = storeToRefs(settings)

    const toast = useToast()
    const router = useRouter()
    const route = useRoute()

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
            default: 320
        },
        zIndex: {
            type: Number,
            default: 1999
        },
        expandOnHover: {
            type: Boolean,
            default: true
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
        allowEdit,
        hasMetaItems,
        ds, datasets,
        activeCode,
        activeTransition, transitionData,
        showAllUsers, activeUserId
    } = storeToRefs(app);

    const inAdminView = computed(() => route.name.startsWith("admin"))
    const inLogView = computed(() => route.name.startsWith("loganalysis"))

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


    function toggleVisibiliy() {
        app.toggleUserVisibility()
    }

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
    function goTo(path) {
        router.push(path)
        expandNavDrawer.value = false
    }

    onMounted(function() {
        const sp = Cookies.get("start-page")
        startPage.value = sp !== undefined ? sp : __APP_START_PAGE__;
        Cookies.set("start-page", startPage.value, { expires: 365 })
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