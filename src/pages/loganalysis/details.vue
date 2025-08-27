<template>
    <div>
        <div class="mt-12 text-caption" style="text-align: center;">
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

        <InteractionTimeline :time="data.time" class="mt-2"/>

        <div class="mt-2" style="min-width: 94vw;">

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
    import DM from '@/use/data-manager';
    import InteractionTimeline from '@/components/logs/InteractionTimeline.vue';
    import LogActionData from '@/components/logs/LogActionData.vue';
    import UserChip from '@/components/UserChip.vue';
    import { useTimes } from '@/store/times';
    import { ACTION_TYPE, ACTION_NAME } from '@/use/log-utils';
    import { DateTime } from 'luxon';
    import { onMounted, reactive, watch } from 'vue';

    const times = useTimes()

    let LOG_F = []

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

    const filter = reactive({
        actions: {},
    })

    function formatDateTime(millis) {
        return DateTime.fromMillis(millis).toFormat("dd. LLL yyyy, HH:mm")
    }

    function toggleFilter(name, key) {
        filter[name][key] = !filter[name][key]
        filterLogs()
    }

    function filterLogs() {
        const logs = DM.getLogs()
        if (logs) {
            LOG_F = DM.getLogs().filter(d => filter.actions[d.actionType])
        } else {
            LOG_F = []
        }
        data.size = LOG_F.length
        data.time = Date.now()
    }

    function init() {
        const objA = {}
        Object.values(ACTION_TYPE).forEach(v => objA[v] = true)
        filter.actions = objA
        filterLogs()
    }

    onMounted(init)

    watch(() => times.logs, filterLogs)
</script>
