<template>
    <div>
        <div>
            Filter by User:
            <template v-for="u in app.usersCanEdit">
                <UserChip v-model="filter.users[u.id]" class="mr-1" selectable :id="u.id"/>
            </template>
        </div>

        <div class="mt-8" style="min-width: 90vw;">
            <div>
                <b>Start</b>: {{ startDate.toFormat("dd. LLL yyyy, HH:MM") }},
                <b>End</b>: {{ endDate.toFormat("dd. LLL yyyy, HH:MM") }}
            </div>

            <v-data-table
                :items="LOG"
                :headers="headers"
                :key="'log_'+data.time+'_'+data.size"
                multi-sort
                density="compact"
                >

                <template v-slot:item.user_id="{ value }">
                    <td><UserChip :id="value" short small/></td>
                </template>

                <template v-slot:item.timestamp="{ value }">
                    <td>{{ formatDateTime(value) }}</td>
                </template>

                <template v-slot:item.data="{ value, item }">
                    <td style="flex-grow: 1;"><LogActionData :action="item.action" :data="value" class="mt-1 mb-1"/></td>
                </template>
            </v-data-table>
        </div>
    </div>
</template>

<script setup>
    import LogActionData from '@/components/LogActionData.vue';
    import UserChip from '@/components/UserChip.vue';
    import { useApp } from '@/store/app';
    import { getLogData } from '@/use/data-api';
    import { DateTime } from 'luxon';
    import { onMounted, reactive } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const toast = useToast()

    let LOG = []

    const headers = [
        { title: "Action", key: "action", minWidth: 150 },
        { title: "User", key: "user_id" },
        { title: "Time", key: "timestamp", minWidth: 180 },
        { title: "Data", key: "data" },
    ]

    const data = reactive({
        time: 0,
        size: 0,
    })

    const dates = reactive({
        diff: { hours: 24 },
        end: null
    })
    const endDate = ref(DateTime.now())
    const startDate = ref(DateTime.now().minus(dates.diff))

    const filter = reactive({
        users: {}
    })

    function formatDateTime(millis) {
        return DateTime.fromMillis(millis).toFormat("dd. LLL yyyy, HH:MM")
    }

    async function read() {
        // load log data
        try {
            endDate.value = dates.end === null ? DateTime.now() : dates.end
            startDate.value = endDate.value.minus(dates.diff)
            LOG = await getLogData(startDate.value.valueOf(), endDate.value.valueOf())
            data.size = LOG.length
            data.time = Date.now()
            toast.success("loaded log data")
        } catch(e) {
            console.error(e.toString())
        }
    }

    function init() {
        const obj = {}
        app.users.forEach(u => obj[u.id] = true)
        filter.users = obj
        read()
    }

    onMounted(init)
</script>