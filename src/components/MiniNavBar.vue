<template>
    <v-sheet v-if="!expandNavDrawer" class="pa-2" :min-width="minWidth" position="fixed" style="height: 100vh" border>
        <v-btn @click="expandNavDrawer = !expandNavDrawer"
            icon="mdi-arrow-right"
            block
            density="compact"
            rounded="sm"
            color="secondary"/>

        <v-divider class="mb-3 mt-3"></v-divider>

        <div class="d-flex flex-column align-center text-caption">

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

            <v-tooltip text="clear all filters" location="right" open-delay="300">
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
            <v-tooltip :text="'show '+app.schemeItemName+'s'" location="right" open-delay="300">
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
            <v-tooltip :text="'show '+app.schemeMetaItemName+'s'" location="right" open-delay="300">
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
    </v-sheet>
    <v-card v-else  class="pa-2" :min-width="300" position="fixed" style="z-index: 5; height: 100vh">
        <v-btn @click="expandNavDrawer = !expandNavDrawer"
            icon="mdi-arrow-left"
            block
            class="mb-2"
            density="compact"
            rounded="sm"
            color="secondary"/>

        <div class="mt-2">
            <div v-if="datasets" class="d-flex align-center mb-2">
                <v-select
                    v-model="ds"
                    :items="datasets"
                    label="dataset"
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

            <div class="d-flex align-center mb-2">
                <v-btn
                    prepend-icon="mdi-tray-arrow-down"
                    density="comfortable"
                    class="mr-1 text-caption"
                    rounded="sm"
                    disabled
                    @click="goExport"
                    variant="tonal">
                    export dataset
                </v-btn>
                <v-btn
                    prepend-icon="mdi-tray-arrow-up"
                    density="comfortable"
                    class="ml-1 text-caption"
                    rounded="sm"
                    @click="goImport"
                    variant="tonal">
                    import dataset
                </v-btn>
            </div>

            <v-divider class="mt-3 mb-3"></v-divider>

            <div class="d-flex justify-space-between mb-1">

                <v-btn
                    prepend-icon="mdi-sync"
                    density="compact"
                    class="text-caption"
                    style="width: 49%;"
                    variant="tonal"
                    color="primary"
                    @click="times.needsReload('all')">
                    reload data
                </v-btn>

                <v-btn
                    prepend-icon="mdi-delete"
                    density="compact"
                    class="text-caption"
                    variant="tonal"
                    style="width: 49%;"
                    color="error"
                    @click="app.resetSelections()">
                    clear selection
                </v-btn>
            </div>

            <v-divider class="mt-3 mb-3"></v-divider>

            <div v-if="!app.static">
                <div v-if="activeUserId && activeUserId > 0">
                    <div class="ml-1 mb-2" style="font-size: smaller;">
                        <v-avatar class="mr-1" icon="mdi-account" density="compact" :color="userColor"/>
                        {{ app.activeUser.name }} ({{ app.activeUser.short }})
                    </div>

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
                <v-divider class="mt-3 mb-3"></v-divider>
            </div>


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

            <v-divider class="mt-3 mb-3"></v-divider>

            <div class="d-flex align-center ml-2">
                <v-checkbox-btn
                    v-model="lightMode"
                    density="compact"
                    inline
                    size="small"
                    true-icon="mdi-white-balance-sunny"
                    false-icon="mdi-weather-night"/>

                    <span class="ml-1 text-caption">{{ lightMode ? 'light' : 'dark' }} mdoe active</span>
            </div>

            <div class="d-flex align-center mt-2 ml-2">
                <v-checkbox-btn
                    :model-value="showAllUsers"
                    color="primary"
                    density="compact"
                    inline
                    true-icon="mdi-tag"
                    false-icon="mdi-tag-off"
                    :disabled="app.static"
                    @click="app.toggleUserVisibility"/>

                <span class="ml-1 text-caption">showing {{ showAllUsers ? 'tags for all coders' : 'only your tags' }}</span>
            </div>

            <v-divider class="mt-3 mb-3"></v-divider>


            <MiniCollapseHeader v-model="expandCode" text="code"/>
            <v-card v-if="expandCode && codes" class="mb-2">
                <CodeWidget :initial="activeCode" :can-edit="allowEdit"/>
            </v-card>

            <MiniCollapseHeader v-model="expandTransition" text="transition"/>
            <v-card v-if="transitions && expandTransition" class="mb-2">
                <TransitionWidget :initial="activeTransition" :allow-create="allowEdit"/>
            </v-card>

            <MiniCollapseHeader v-model="expandComponents" text="components"/>
            <v-card v-if="expandComponents" class="mb-2 pa-1">
                <v-checkbox-btn v-model="showBarCodes"
                    density="compact" :label="'bar coes ('+(showBarCodes?'on)':'off)')"
                    :color="showBarCodes ? 'primary' : 'default'"
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

                <v-checkbox-btn v-model="showExtTiles"
                    :label="'meta items list ('+(showExtTiles?'on)':'off)')" density="compact"
                    :color="showExtTiles ? 'primary' : 'default'"
                    true-icon="mdi-lightbulb" false-icon="mdi-lightbulb-off"/>
            </v-card>

            <MiniCollapseHeader v-model="expandStats" text="stats"/>
            <v-card v-if="expandStats" class="mb-2 pa-2 text-caption">
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
                <div>
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

                <div><b class="stat-num">{{ formatNumber(stats.numMeta, 8) }}</b> Meta Items</div>
                <div v-if="allowEdit">
                    <b class="stat-num">{{ formatNumber(stats.numMetaUser, 8) }}</b> <span class="text-capitalize">{{ capitalMetaItem }}</span> by You
                </div>

            </v-card>

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
    import { useRouter } from 'vue-router';

    const settings = useSettings();
    const app = useApp();
    const times = useTimes()
    const loader = useLoader();
    const toast = useToast()
    const theme = useTheme()
    const router = useRouter()

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

    const numFilters = ref(0)

    const startPage = ref(APP_START_PAGE)

    const {
        lightMode,
        activeTab, expandNavDrawer,
        expandCode, expandTransition,
        expandStats, expandComponents,
        showTable, showScatter,
        showBarCodes, showEvidenceTiles,
        showExtTiles
    } = storeToRefs(settings);

    const {
        allowEdit,
        ds, datasets,
        codes, activeCode,
        activeTransition, transitions, transitionData,
        showAllUsers, activeUserId
    } = storeToRefs(app);

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

    const capitalItem = computed(() => capitalize(app.schemeItemName+'s'))
    const capitalMetaItem = computed(() => capitalize(app.schemeMetaItemName+'s'))

    const userColor = computed(() => {
        if (activeUserId.value) {
            return app.getUserColor(activeUserId.value)
        }
        return "default"
    })

    function setAsStartPage() {
        Cookies.set("start-page", settings.activeTab, { expires: 365 })
        startPage.value = settings.activeTab;

    }
    function deleteStartPage() {
        Cookies.set("start-page", APP_START_PAGE)
        startPage.value = APP_START_PAGE;
    }

    async function logout() {
        if (!activeUserId.value || activeUserId.value < 0) {
            return toast.error("you are not logged in")
        }

        try {
            await loader.post("/logout")
            toast.success("logged out")
            app.setActiveUser(-1)
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
        router.replace("/import")
    }
    function goExport() {
        router.replace("/export")
    }

    onMounted(function() {
        const t = Cookies.get("theme")
        if (t) {
            lightMode.value = t === "light"
        } else {
            lightMode.value = !theme.global.current.value.dark
        }
        const sp = Cookies.get("start-page")
        startPage.value = sp !== undefined ? sp : APP_START_PAGE;
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
    })

</script>

<style scoped>
.stat-num {
    font-size: larger;
    display: inline-block;
    width: 60px;
    max-width: 60px;
    min-width: 60px;
    margin-right: 2px;
}
</style>