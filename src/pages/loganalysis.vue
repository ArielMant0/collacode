<template>
    <div>
        <nav class="topnav d-flex align-stretch justify-center">
            <NavLink to="/coding" text="back to coding" icon="mdi-arrow-left" style="position: absolute; left: 2px;"/>
            <NavLink to="/loganalysis/details" :active="route.path" text="details" icon="mdi-table"/>
            <NavLink to="/loganalysis/stats" :active="route.path" text="stats" icon="mdi-chart-bar"/>
        </nav>
        <div class="pa-2 d-flex align-center justify-center">
            <div v-if="isAdmin" style="width: 100%;">
                <table v-if="showSettings" class="text-caption" style="border-spacing: 4px;">
                    <tbody>
                        <tr>
                            <td>Time:</td>
                            <td class="d-flex align-center">
                                <DateTimePicker v-model="startDate" max-width="250px" class="mr-1"></DateTimePicker>
                                <DateTimePicker v-model="endDate" max-width="250px" class="ml-1"></DateTimePicker>
                            </td>
                        </tr>

                        <tr>
                            <td>Users:</td>
                            <td>
                                <span v-for="u in app.usersCanEdit">
                                    <UserChip v-model="filter.users[u.id]"
                                        :id="u.id"
                                        class="mr-1 text-caption"
                                        caption
                                        selectable
                                        />
                                </span>
                            </td>
                        </tr>

                        <tr>
                            <td>{{ app.itemNameCaptial }}s:</td>
                            <td class="d-flex align-center">
                                <v-btn
                                    color="primary"
                                    class="mr-3"
                                    density="compact"
                                    variant="outlined"
                                    icon="mdi-plus"
                                    rounded="sm"
                                    @click="showItemSelect = true"
                                    ></v-btn>

                                <div class="d-flex flex-wrap">
                                    <ItemTeaser v-for="item in filter.items"
                                        :item="item"
                                        :width="100"
                                        :height="50"
                                        class="mr-1 mb-1"
                                        @click="removeFilterItem(item.id)"
                                        prevent-open/>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <div class="d-flex align-center justify-center mt-2">
                    <v-btn
                        color="primary"
                        variant="outlined"
                        class="mr-1"
                        @click="read"
                        >
                        load logs
                    </v-btn>
                    <v-btn
                        color="secondary"
                        variant="outlined"
                        class="ml-1"
                        @click="showSettings = !showSettings"
                        >
                        {{ showSettings ? 'hide' : 'show' }} settings
                    </v-btn>
                </div>
                <router-view/>

                <MiniDialog v-model="showItemSelect" min-width="50%" max-width="65%" no-actions>
                    <template #text>
                        <ItemSelect multiple @submit="setFilterItems"/>
                    </template>
                </MiniDialog>
            </div>
            <div v-else class="text-h2 mt-12">
                You are not an admin <b>:(</b>
            </div>
        </div>
    </div>
</template>

<script setup>
    import DateTimePicker from '@/components/dialogs/DateTimePicker.vue';
    import MiniDialog from '@/components/dialogs/MiniDialog.vue';
    import ItemTeaser from '@/components/items/ItemTeaser.vue';
    import NavLink from '@/components/navigation/NavLink.vue';
    import UserChip from '@/components/UserChip.vue';
    import router from '@/router';
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import { loadLogData } from '@/use/data-api';
    import DM from '@/use/data-manager';
    import { parseAction } from '@/use/log-utils';
    import { storeToRefs } from 'pinia';
    import { onMounted, ref, watch } from 'vue';
    import { useRoute } from 'vue-router';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const route = useRoute()
    const times = useTimes()
    const toast = useToast()

    const { isAdmin } = storeToRefs(app)

    const showSettings = ref(true)
    const showItemSelect = ref(false)

    const endDate = ref(null)
    const startDate = ref(null)
    const filter = reactive({
        users: {},
        items: []
    })
    const userIds = computed(() => {
        const list = []
        for (const id in filter.users) {
            if (filter.users[id]) {
                list.push(+id)
            }
        }
        return list
    })
    const itemIds = computed(() => filter.items.map(d => d.id))

    function setFilterItems(items) {
        filter.items = items
        showItemSelect.value = false
    }
    function removeFilterItem(id) {
        filter.items = filter.items.filter(d => d.id !== id)
    }

    async function read() {
        // load log data
        try {
            const logs = await loadLogData(
                startDate.value ? startDate.value.valueOf() : null,
                endDate.value ? endDate.value.valueOf() : null,
                userIds.value,
                itemIds.value
            )
            if (logs) {
                logs.forEach(d => d.actionType = parseAction(d.action))
                DM.setLogs(logs)
                toast.success("loaded log data")
                times.reloaded("logs")
            }
        } catch(e) {
            console.error(e.toString())
        }
    }

    function checkData() {
        const cols = ["users", "items", "datatags", "evidence", "objections"]
        if (cols.every(c => !DM.hasData(c))) {
            times.needsReload("all")
            toast.info("reloading all data")
            return true
        } else {
            cols.forEach(c => {
                if (!DM.hasData(c)) {
                    times.needsReload(c)
                }
            })
            return false
        }
    }

    function readUsers() {
        const objU = {}
        app.usersCanEdit.forEach(u => objU[u.id] = true)
        filter.users = objU

        read()
    }

    async function init() {
        const pages = route.path.split("/").filter(d => d.length > 0)
        if (pages.length < 2) {
            router.replace("/loganalysis/details")
        }

        if (checkData()) return
        readUsers()
    }

    onMounted(init)

    watch(
        () => Math.max(times.all, times.users),
        readUsers
    )
    watch(
        () => Math.max(times.items, times.datatags, times.evidence, times.objections),
        read
    )

    watch(() => times.n_logs, read)

</script>