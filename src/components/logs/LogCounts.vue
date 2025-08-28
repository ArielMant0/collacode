<template>
    <div>
        <div class="text-caption">
            <div class="d-flex align-center justify-center">
                mean <v-icon :color="getWarningColorByType(OBJECTION_ACTIONS.ADD)" class="ml-1 mr-1" size="small" icon="mdi-circle"/>
                warnings: {{ stats.meanAdd.toFixed(2) }},
                mean <v-icon :color="getWarningColorByType(OBJECTION_ACTIONS.REMOVE)" class="ml-1 mr-1" size="small" icon="mdi-circle"/>
                warnings: {{ stats.meanDel.toFixed(2) }}
            </div>
            <div class="d-flex align-center justify-center">
                mean <v-icon class="ml-1 mr-1" icon="mdi-tag" size="small"/> fixes: {{ stats.meanFixedDt.toFixed(2) }},
                mean <v-icon class="ml-1 mr-1" icon="mdi-image" size="small"/> fixes: {{ stats.meanFixedEv.toFixed(2) }}
            </div>
        </div>

        <div style="text-align: center;" class="text-caption mt-4">
            Select a User:
            <v-chip v-for="uid in users"
                :variant="selected === uid ? 'flat' : 'outlined'"
                class="cursor-point text-caption ml-1"
                @click="selectUser(uid)"
                density="compact"
                :color="app.getUserColor(uid)">
                {{ app.getUserName(uid) }}
            </v-chip>
        </div>

        <div v-if="selected && selected > 0" class="mt-4 d-flex align-start justify-center">
            <div class="mr-8">
                <div><b>addition warnings</b> ({{ details.add.length }})</div>
                <table>
                    <tbody>
                        <tr v-for="d in details.add" class="text-caption">
                            <td>
                                <v-icon
                                    :icon="d.fixed ? 'mdi-check' : 'mdi-close'"
                                    :color="d.fixed ? 'primary' : 'error'"
                                    />
                            </td>
                             <td>
                                <v-icon v-if="d.fixed"
                                    size="small"
                                    :icon="d.how === ACTION_TYPE.DATATAG ? 'mdi-tag' : 'mdi-image'"/>
                            </td>
                            <td>{{ d.tagName }} </td>
                            <td>{{ d.itemName }} </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div class="ml-8">
                <div><b>removal warnings</b> ({{ details.remove.length }})</div>
                <table>
                    <tbody>
                        <tr v-for="d in details.remove" class="text-caption">
                            <td>
                                <v-icon
                                    :icon="d.fixed ? 'mdi-check' : 'mdi-close'"
                                    :color="d.fixed ? 'primary' : 'error'"
                                    />
                            </td>
                             <td>
                                <v-icon v-if="d.fixed"
                                    size="small"
                                    :icon="d.how === ACTION_TYPE.DATATAG ? 'mdi-tag' : 'mdi-image'"/>
                            </td>
                            <td>{{ d.tagName }} </td>
                            <td>{{ d.itemName }} </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { EVIDENCE_TYPE, OBJECTION_ACTIONS, useApp } from '@/store/app';
    import DM from '@/use/data-manager';
    import { ACTION_TYPE, getItemsFromDatatags, getItemsFromEvidence, getTagsFromDatatags, getTagsFromEvidence } from '@/use/log-utils';
    import { onMounted, reactive, watch } from 'vue';
    import { useTimes } from '@/store/times';
    import { getWarningColorByType } from '@/use/similarities';

    const app = useApp()
    const times = useTimes()

    let data
    let perUserStats = {}, perUserData = {}

    const users = ref([])
    const selected = ref(null)

    const details = reactive({
        add: [],
        remove: []
    })
    const stats = reactive({
        meanAdd: 0,
        meanDel: 0,
        meanFixedDt: 0,
        meanFixedEv: 0,
    })

    function selectUser(id) {
        selected.value = selected.value === id ? null : id
        if (selected.value) {
            const add = [], remove = []
            const subset = perUserData[selected.value]
            for (const gid in subset) {
                const itemName = DM.getDataItem("items_name", +gid)
                for (const tid in subset[gid]) {
                    const tagName = DM.getDataItem("tags_name", +tid)
                    if (subset[gid][tid].type === OBJECTION_ACTIONS.ADD) {
                        add.push({
                            tagId: +tid,
                            tagName: tagName,
                            itemName: itemName,
                            how: subset[gid][tid].how,
                            fixed: subset[gid][tid].fixed
                        })
                    }
                    if (subset[gid][tid].type === OBJECTION_ACTIONS.REMOVE) {
                        remove.push({
                            tagId: +tid,
                            tagName: tagName,
                            itemName: itemName,
                            how: subset[gid][tid].how,
                            fixed: subset[gid][tid].fixed,
                        })
                    }
                }
            }
            details.add = add
            details.remove = remove
        } else {
            details.add = []
            details.remove = []
        }
    }

    function getEvidenceForTags(time, user, item, tag, type) {
        return data.find(d => {
            if (d.timestamp < time || d.user_id !== user ||
                d.actionType !== ACTION_TYPE.EVIDENCE
            ) {
                return false
            }

            if (!getItemsFromEvidence(d.data).includes(item)) {
                return false
            }

            const filtered = Array.isArray(d.data) ?
                d.data.filter(dd => dd.type === type) :
                d.data.type === type ? [d.data] : []

            return getTagsFromEvidence(filtered).includes(tag)
        })
    }
    function getDatatagsForTags(time, user, item, tag, action) {
        return data.find(d => {
            if (d.timestamp < time || d.user_id !== user ||
                d.actionType !== ACTION_TYPE.DATATAG ||
                d.action !== action
            ) {
                return false
            }

            if (!getItemsFromDatatags(d.data).includes(item)) {
                return false
            }

            return getTagsFromDatatags(d.data).includes(tag)
        })
    }

    function read() {
        // get log data
        data = DM.getLogs()

        // track which tag was fixed for which user
        const tmp = {}, userStats = {}

        if (data) {
            // for each log entry
            data.forEach(d => {
                // if the users saw warnings
                if (d.action === "visible warnings") {

                    const user = d.user_id
                    if (!userStats[user]) {
                        userStats[user] = {
                            numToAdd: 0,
                            numToDel: 0,
                            fixedDt: 0,
                            fixedEv: 0
                        }
                    }

                    if (tmp[user] === undefined) {
                        tmp[user] = {}
                    }

                    const active = d.data.warnings.filter(w => w.active)
                    if (active.length === 0) return

                    const item = d.data.item.id
                    if (!tmp[user][item]) {
                        tmp[user][item] = {}
                    }

                    const subset = tmp[user][item]

                    active.forEach(w => {
                        const tag = w.tag_id
                        if (subset[tag] !== undefined) return

                        subset[tag] = { type: w.type, fixed: false, how: "" }
                        if (w.type === OBJECTION_ACTIONS.ADD) {
                            userStats[user].numToAdd++
                        } else {
                            userStats[user].numToDel++
                        }

                        const dtType = w.type === OBJECTION_ACTIONS.ADD ?
                            "add datatags" :
                            "delete datatags"

                        const dt = getDatatagsForTags(d.timestamp, d.user_id, item, tag, dtType)
                        if (dt) {
                            subset[tag].fixed = true
                            subset[tag].how = ACTION_TYPE.DATATAG
                            userStats[user].fixedDt++
                        } else {
                            const evType = w.type === OBJECTION_ACTIONS.ADD ?
                                EVIDENCE_TYPE.NEGATIVE :
                                EVIDENCE_TYPE.POSITIVE

                            const ev = getEvidenceForTags(d.timestamp, d.user_id, item, tag, evType)
                            if (ev) {
                                subset[tag].fixed = true
                                subset[tag].how = ACTION_TYPE.EVIDENCE
                                userStats[user].fixedEv++
                            }
                        }

                    })
                }
            })
        }

        users.value = Object.keys(tmp).map(uid => +uid)

        if (users.value.length > 0) {
            let sumAdd = 0, sumDel = 0, sumFixedDt = 0, sumFixedEv = 0
            for (const uid in userStats) {
                sumAdd += userStats[uid].numToAdd
                sumDel += userStats[uid].numToDel
                sumFixedDt += userStats[uid].fixedDt
                sumFixedEv += userStats[uid].fixedEv
            }

            stats.meanAdd = sumAdd / users.value.length
            stats.meanDel = sumDel / users.value.length
            stats.meanFixedDt = sumFixedDt / users.value.length
            stats.meanFixedEv = sumFixedEv / users.value.length
        } else {
            stats.meanAdd = 0
            stats.meanDel = 0
            stats.meanFixedDt = 0
            stats.meanFixedEv = 0
        }

        perUserStats = userStats
        perUserData = tmp

        if ((selected.value === null || selected.value <= 0) && users.value.length > 0) {
            selectUser(users.value[0])
        }
    }

    function refresh() {
        const before = selected.value
        read()
        if (users.value.includes(before)) {
            selected.value = null
            selectUser(before)
        } else if (users.value.length > 0) {
            selectUser(users.value[0])
        } else {
            selectUser(null)
        }
    }

    onMounted(read)

    watch(() => times.logs, refresh)
</script>

<style scoped>
table {
    border-spacing: .5em 2px;
}
</style>