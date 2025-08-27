<template>
    <div>
        <div style="text-align: center;">
            fixed warnings: {{ stats.numFixed }} / {{ stats.numFixed+stats.numNotFixed }}
            ({{ stats.fixedDt }} tag fixes, {{ stats.fixedEv }} evidence fixes)
        </div>

        <div style="text-align: center;" class="text-caption mt-2">
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
                <div><b>addition warnings</b></div>
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
                <div><b>removal warnings</b></div>
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

    const app = useApp()
    const times = useTimes()

    let data
    let statusPerUser = {}

    const users = ref([])
    const selected = ref(null)

    const details = reactive({
        add: [],
        remove: []
    })
    const stats = reactive({
        numFixed: 0,
        numNotFixed: 0,
        numToAdd: 0,
        numToDel: 0,
        fixedDt: 0,
        fixedEv: 0,
    })

    function selectUser(id) {
        selected.value = selected.value === id ? null : id
        if (selected.value) {
            const add = [], remove = []
            const subset = statusPerUser[selected.value]
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
        let numFixed = 0,
            numToAdd = 0,
            numToDel = 0,
            fixedDt = 0,
            fixedEv = 0

        // track which tag was fixed for which user
        const tmp = {}

        if (data) {
            // for each log entry
            data.forEach(d => {
                // if the users saw warnings
                if (d.action === "visible warnings") {

                    if (tmp[d.user_id] === undefined) {
                        tmp[d.user_id] = {}
                    }

                    const active = d.data.warnings.filter(w => w.active)
                    if (active.length === 0) return

                    const item = d.data.item.id
                    if (!tmp[d.user_id][item]) {
                        tmp[d.user_id][item] = {}
                    }

                    const subset = tmp[d.user_id][item]

                    active.forEach(w => {
                        const tag = w.tag_id
                        if (subset[tag] !== undefined) return

                        subset[tag] = { type: w.type, fixed: false, how: "" }
                        if (w.type === OBJECTION_ACTIONS.ADD) {
                            numToAdd++
                        } else {
                            numToDel++
                        }

                        const dtType = w.type === OBJECTION_ACTIONS.ADD ?
                            "add datatags" :
                            "delete datatags"

                        const dt = getDatatagsForTags(d.timestamp, d.user_id, item, tag, dtType)
                        if (dt) {
                            subset[tag].fixed = true
                            subset[tag].how = ACTION_TYPE.DATATAG
                            fixedDt++
                        } else {
                            const evType = w.type === OBJECTION_ACTIONS.ADD ?
                                EVIDENCE_TYPE.POSITIVE :
                                EVIDENCE_TYPE.NEGATIVE

                            const ev = getEvidenceForTags(d.timestamp, d.user_id, item, tag, evType)
                            if (ev) {
                                subset[tag].fixed = true
                                subset[tag].how = ACTION_TYPE.EVIDENCE
                                fixedEv++
                            }
                        }

                    })
                }
            })
        }

        for (const user in tmp) {
            for (const gid in tmp[user]) {
                for (const tid in tmp[user][gid]) {
                    numFixed += (tmp[user][gid][tid].fixed ? 1 : 0)
                }
            }
        }

        stats.numFixed = numFixed
        stats.numToAdd = numToAdd
        stats.numToDel = numToDel
        stats.numNotFixed = (numToAdd + numToDel) - numFixed
        stats.fixedDt = fixedDt
        stats.fixedEv = fixedEv

        users.value = Object.keys(tmp).map(uid => +uid)

        statusPerUser = tmp

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