<template>
    <div class="mt-8">
        <div style="text-align: center;" class="text-caption mb-8">
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

        <div class="d-flex align-start justify-center">

            <div class="mr-4" v-if="selected">
                <div v-for="(vals, item) in byUserItem[selected]" class="mb-2">
                    <div class="d-flex align-start text-caption mt-1">
                        <ItemTeaser :id="+item" :width="100" :height="50"/>
                        <table class="ml-2" style="border-spacing: 12px 0px;">
                            <tbody>
                                <tr>
                                    <td><v-icon size="small">mdi-tag</v-icon></td>
                                    <td>{{ vals.tags.length }}</td>
                                </tr>
                                <tr>
                                    <td><v-icon size="small">mdi-image</v-icon></td>
                                    <td>{{ vals.evidence.length }}</td>
                                </tr>
                                <tr>
                                    <td><v-icon size="small">mdi-bell</v-icon></td>
                                    <td>{{ vals.warnings.length }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <LogCounts :user="selected"/>
        </div>
    </div>
</template>

<script setup>
    import ItemTeaser from '@/components/items/ItemTeaser.vue';
    import LogCounts from '@/components/logs/LogCounts.vue';
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { ACTION_TYPE, getItemsFromAction, getTagsFromAction } from '@/use/log-utils';
    import { onMounted } from 'vue';

    const app = useApp()
    const times = useTimes()

    const selected = ref(null)
    const users = ref([])

    let byUserItem = {}

    function selectUser(id) {
        selected.value = selected.value === id ? null : id
    }

    function read() {
        const logs = DM.getLogs()
        const uids = new Set()

        let data = {}

        const process = (d, subset, actionType, add) => {
            const item = getItemsFromAction(d)[0]
            if (!item) return
            if (!subset[item]) {
                subset[item] = {
                    tags: new Set(),
                    evidence: new Set(),
                    warnings: new Set()
                }
            }

            const tags = getTagsFromAction(d, actionType)

            switch(actionType) {
                case ACTION_TYPE.DATATAG:
                    tags.forEach(t => {
                        if (add) {
                            subset[item].tags.add(t)
                        } else {
                            subset[item].tags.delete(t)
                        }
                    })
                    break
                case ACTION_TYPE.EVIDENCE:
                    tags.forEach(t => {
                        if (add) {
                            subset[item].evidence.add(t)
                        } else {
                            subset[item].evidence.delete(t)
                        }
                    })
                    break
                case ACTION_TYPE.WARNINGS:
                    tags.forEach(t => subset[item].warnings.add(t))
                    break
            }
        }

        logs.forEach(d => {
            const uid = d.user_id
            if (!uids.has(uid)) {
                uids.add(uid)
                data[uid] = {}
            }
            const add = d.action.includes("add")
            if (Array.isArray(d.data)) {
                d.data.forEach(dd => process(dd, data[uid], d.actionType, add))
            } else {
                process(d.data, data[uid], d.actionType, add)
            }
        })

        // convert sets to array, makes other things easier later on
        for (const uid in data) {
            for (const iid in data[uid]) {
                data[uid][iid].tags = Array.from(data[uid][iid].tags.values())
                data[uid][iid].evidence = Array.from(data[uid][iid].evidence.values())
                data[uid][iid].warnings = Array.from(data[uid][iid].warnings.values())
            }
        }

        byUserItem = data
        users.value = Array.from(uids.values())

        if (!selected.value && users.value.length > 0) {
            selectUser(users.value.at(0))
        }
    }

    onMounted(read)

    watch(() => times.logs, read)
</script>