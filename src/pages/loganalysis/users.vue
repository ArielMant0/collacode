<template>
    <div>
        <div class="text-caption">
            Filter by User:
            <span v-for="u in app.usersCanEdit">
                <UserChip v-model="filter.users[u.id]"
                    class="mr-1 text-caption"
                    caption
                    selectable
                    @click="filterLogs"
                    :id="u.id"/>
            </span>
        </div>

        <div class="mt-2 text-caption">
            Filter by Action Type:
            <span v-for="(value, key) in ACTION_TYPE">
                <v-chip
                    class="mr-1 text-caption"
                    color="primary"
                    :variant="filter.actions[value] ? 'flat' : 'outlined'"
                    @click="toggleFilter('actions', value)"
                    density="compact">
                    {{ ACTION_NAME[key] }}
                </v-chip>
            </span>
        </div>

        <div class="mt-8" style="min-width: 94vw;">

            <div class="d-flex align-center justify-center">
                <DateTimePicker v-model="startDate" max-width="250px"></DateTimePicker>
                <DateTimePicker v-model="endDate" max-width="250px" class="ml-2 mr-2"></DateTimePicker>
                <v-btn color="primary" @click="read">load</v-btn>
            </div>

            <v-data-table
                :items="LOG_F"
                :headers="headers"
                :key="'log_'+data.time"
                multi-sort
                density="compact"
                >

                <template v-slot:item.user_id="{ value }">
                    <UserChip :id="value" short small/>
                </template>

                <template v-slot:item.timestamp="{ value }">
                    <td>{{ formatDateTime(value) }}</td>
                </template>

                <template v-slot:item.data="{ value, item }">
                    <td style="flex-grow: 5;"><LogActionData :action-type="item.actionType" :data="value" class="mt-1 mb-1"/></td>
                </template>
            </v-data-table>
        </div>
    </div>
</template>

<script setup>
    import DateTimePicker from '@/components/dialogs/DateTimePicker.vue';
    import LogActionData from '@/components/logs/LogActionData.vue';
    import UserChip from '@/components/UserChip.vue';
    import { useApp } from '@/store/app';
    import { getLogData } from '@/use/data-api';
    import { ACTION_TYPE, ACTION_NAME, parseAction } from '@/use/log-utils';
    import { DateTime } from 'luxon';
    import { onMounted, reactive } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const toast = useToast()

    let LOG = [], LOG_F = []

    const headers = [
        { title: "Action", key: "action", width: 200 },
        { title: "User", key: "user_id" },
        { title: "Time", key: "timestamp", width: 200 },
        { title: "Data", key: "data" },
    ]

    const data = reactive({
        time: 0,
        size: 0,
    })

    const endDate = ref(DateTime.now().toJSDate())
    const startDate = ref(DateTime.now().minus({ days: 3 }).toJSDate())

    const filter = reactive({
        users: {},
        actions: {}
    })

    function formatDateTime(millis) {
        return DateTime.fromMillis(millis).toFormat("dd. LLL yyyy, HH:mm")
    }

    function toggleFilter(name, key) {
        filter[name][key] = !filter[name][key]
        filterLogs()
    }

    function filterLogs() {
        LOG_F = LOG.filter(d => filter.actions[d.actionType] && filter.users[d.user_id])
        data.size = LOG_F.length
        data.time = Date.now()
    }

    async function read() {
        // load log data
        try {
            LOG = await getLogData(startDate.value.valueOf(), endDate.value.valueOf())
            LOG.forEach(d => d.actionType = parseAction(d.action))
            filterLogs()
            toast.success("loaded log data")
        } catch(e) {
            console.error(e.toString())
        }
    }

    function init() {
        const objU = {}, objA = {}
        app.users.forEach(u => objU[u.id] = true)
        filter.users = objU

        Object.values(ACTION_TYPE).forEach(v => objA[v] = true)
        filter.actions = objA

        read()
    }

    onMounted(init)
</script>