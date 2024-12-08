<template>
    <v-sheet v-if="!expandNavDrawer" class="pa-2" :min-width="minWidth" position="fixed" style="height: 100vh" border>
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

            <v-checkbox-btn v-model="lightMode" density="compact"
                inline true-icon="mdi-white-balance-sunny" false-icon="mdi-weather-night"/>

            <v-divider class="mb-2 mt-2" style="width: 100%"></v-divider>

            <v-avatar icon="mdi-account" density="compact" class="mt-3 mb-1" :color="userColor"/>
            <v-divider class="mb-2 mt-2" style="width: 100%"></v-divider>

            <v-tooltip text="show tags for all users" location="right">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props"
                        :model-value="showAllUsers"
                        color="primary"
                        density="compact"
                        class="mt-1"
                        inlines true-icon="mdi-tag"
                        false-icon="mdi-tag-off"
                        :disabled="app.static"
                        @click="app.toggleUserVisibility"/>
                </template>
            </v-tooltip>

            <v-tooltip text="show bar codes" location="right">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props" v-model="showBarCodes" density="compact"
                        :color="showBarCodes ? 'primary' : 'default'"
                        inline true-icon="mdi-barcode" false-icon="mdi-barcode-off"/>
                </template>
            </v-tooltip>
            <v-tooltip text="show scatter plots" location="right">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props" v-model="showScatter" density="compact"
                        :color="showScatter ? 'primary' : 'default'"
                        inline true-icon="mdi-blur" false-icon="mdi-blur-off"/>
                </template>
            </v-tooltip>
            <v-tooltip text="show games" location="right">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props" v-model="showTable" density="compact"
                        :color="showTable ? 'primary' : 'default'"
                        inline true-icon="mdi-controller" false-icon="mdi-controller-off"/>
                </template>
            </v-tooltip>
            <v-tooltip text="show evidences" location="right">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props" v-model="showEvidenceTiles" density="compact"
                        :color="showEvidenceTiles ? 'primary' : 'default'"
                        inline true-icon="mdi-image" false-icon="mdi-image-off"/>
                </template>
            </v-tooltip>
            <v-tooltip text="show externalizations" location="right">
                <template v-slot:activator="{ props }">
                    <v-checkbox-btn v-bind="props" v-model="showExtTiles" density="compact"
                        :color="showExtTiles ? 'primary' : 'default'"
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

            <span class="mt-3 mb-1" style="text-align: center;">Tags:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numTags) }}</v-chip>
            <v-tooltip v-if="stats.numTagsUser > 0" :text="'tags created by '+userName" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props" density="compact" class="mt-1 text-caption" :color="userColor">{{ formatNumber(stats.numTagsUser) }}</v-chip>
                </template>
            </v-tooltip>

            <span class="mt-3 mb-1" style="text-align: center;">User Tags:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numDT) }}</v-chip>
            <v-tooltip v-if="stats.numDTUser > 0" :text="'game tags added by '+userName" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props" density="compact" class="mt-1 text-caption" :color="userColor">{{ formatNumber(stats.numDTUser) }}</v-chip>
                </template>
            </v-tooltip>

            <span class="mt-3 mb-1" style="text-align: center;">Evidence:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numEv) }}</v-chip>
            <v-tooltip v-if="stats.numEvUser > 0" :text="'evidence created by '+userName" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props" density="compact" class="mt-1 text-caption" :color="userColor">{{ formatNumber(stats.numEvUser) }}</v-chip>
                </template>
            </v-tooltip>

            <span class="mt-3 mb-1" style="text-align: center;">Exts:</span>
            <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numExt) }}</v-chip>
            <v-tooltip v-if="stats.numExtUser > 0" :text="'evidence created by '+userName" location="right">
                <template v-slot:activator="{ props }">
                    <v-chip v-bind="props" density="compact" class="mt-1 text-caption" :color="userColor">{{ formatNumber(stats.numExtUser) }}</v-chip>
                </template>
            </v-tooltip>
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
                :disabled="app.static"
                @update:model-value="app.toggleUserVisibility"/>

            <div v-if="!app.static">
                <div v-if="activeUserId && activeUserId > 0">
                    <v-btn
                        color="error"
                        density="compact"
                        class="text-caption mb-1"
                        block
                        @click="logout">
                        logout
                    </v-btn>
                    <v-btn
                        color="secondary"
                        density="compact"
                        class="text-caption mb-1"
                        block
                        @click="changePW">
                        change password
                    </v-btn>
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
            </div>

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
                    :label="'game table ('+(showTable?'on)':'off)')" density="compact"
                    :color="showTable ? 'primary' : 'default'"
                    true-icon="mdi-controller" false-icon="mdi-controller-off"/>

                <v-checkbox-btn v-model="showEvidenceTiles"
                    :label="'evidence tiles ('+(showEvidenceTiles?'on)':'off)')" density="compact"
                    :color="showEvidenceTiles ? 'primary' : 'default'"
                    true-icon="mdi-image" false-icon="mdi-image-off"/>

                <v-checkbox-btn v-model="showExtTiles"
                    :label="'externalization tiles ('+(showExtTiles?'on)':'off)')" density="compact"
                    :color="showExtTiles ? 'primary' : 'default'"
                    true-icon="mdi-lightbulb" false-icon="mdi-lightbulb-off"/>
            </v-card>

            <MiniCollapseHeader v-model="expandStats" text="stats"/>
            <v-card v-if="expandStats" class="mb-2 pa-2 text-caption">
                <div><b class="stat-num">{{ formatNumber(stats.numGames, 8) }}</b> Games</div>
                <div><b class="stat-num">{{ formatNumber(stats.numGamesTags, 8) }}</b> Games w/ Tags</div>
                <div><b class="stat-num">{{ formatNumber(stats.numGamesEv, 8) }}</b> Games w/ Evidence</div>
                <div><b class="stat-num">{{ formatNumber(stats.numGamesExt, 8) }}</b> Games w/ Externalizations</div>

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

                <div><b class="stat-num">{{ formatNumber(stats.numExt, 8) }}</b> Externalizations</div>
                <div v-if="allowEdit"><b class="stat-num">{{ formatNumber(stats.numExtUser, 8) }}</b> Externalizations by You</div>

            </v-card>

            <div v-if="activeTab === 'transition'">
                <MiniCollapseHeader v-model="expandTransition" text="transition"/>
                <v-card v-if="transitions && expandTransition" class="mb-2">
                    <TransitionWidget :initial="activeTransition"
                        :codes="codes"
                        :transitions="transitions"
                        :allow-create="allowEdit"/>
                </v-card>
            </div>
            <div v-else>
                <MiniCollapseHeader v-model="expandCode" text="code"/>
                <v-card v-if="expandCode && codes" class="mb-2">
                    <CodeWidget :initial="activeCode" :can-edit="allowEdit"/>
                </v-card>
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
                        <v-text-field v-model="name"
                            label="user name"
                            hide-spin-buttons
                            density="compact"/>
                        <v-text-field v-model="pw"
                            label="password"
                            type="password"
                            hide-spin-buttons
                            density="compact"/>

                        <div class="d-flex justify-space-between">
                            <v-btn color="warning" @click="cancelLogin">cancel</v-btn>
                            <v-btn color="primary" @click="login">login</v-btn>
                        </div>
                    </v-card-text>
                </v-card>
            </v-dialog>
        </div>
    </v-card>
</template>

<script setup>
    import { storeToRefs } from 'pinia'
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { formatNumber, formatStats } from '@/use/utility';
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

    const settings = useSettings();
    const app = useApp();
    const times = useTimes()
    const loader = useLoader();
    const toast = useToast()
    const theme = useTheme()

    const props = defineProps({
        minWidth: {
            type: Number,
            default: 60
        },
    })

    const pwNew = ref("")
    const pwOld = ref("")
    const askPw = ref(false)

    const pw = ref("")
    const name = ref("")
    const askLogin = ref(false)

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
        activeTransition, transitions,
        showAllUsers, activeUserId
    } = storeToRefs(app);

    const codeName = computed(() => {
        return app.activeCode ?
            app.getCodeName(activeTab.value === "transition" ? app.oldCode : app.activeCode) :
            "?"
    })
    const otherCodeName = computed(() => {
        return activeTab.value === "transition" ?
            (app.newCode ? app.getCodeName(app.newCode) : "?") :
            null
    })

    const userName = computed(() => {
        if (activeUserId.value) {
            return app.getUserName(activeUserId.value)
        }
        return "?"
    })
    const userColor = computed(() => {
        if (activeUserId.value) {
            return app.getUserColor(activeUserId.value)
        }
        return "default"
    })

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


    onMounted(function() {
        const t = Cookies.get("theme")
        if (t) {
            lightMode.value = t === "light"
        } else {
            lightMode.value = !theme.global.current.value.dark
        }
        readStats()
    })

    watch(() => times.games, readGameStats)
    watch(() => times.tags, readTagStats)
    watch(() => times.datatags, readDatatagsStats)
    watch(() => times.evidence, readEvidenceStats)
    watch(() => times.externalizations, readExtStats)
    watch(activeUserId, readStats)

    watch(lightMode, function(light) {
        theme.global.name.value = light ? 'customLight' : 'customDark'
        Cookies.set("theme", light ? "light" : "dark")
    })

</script>

<style scoped>
.stat-num {
    font-size: larger;
    display: inline-block;
    width: 60px;
    margin-right: 2px;
}
</style>