<template>
    <div class="d-flex align-center flex-wrap justify-start">
        <v-data-table :headers="visibleHeaders" :items="filtered" density="compact" class="text-body-2">
            <template v-slot:item="{ item }">
                <tr>
                    <td v-if="allowEdit">
                        <v-btn
                            icon="mdi-pencil"
                            density="compact"
                            class="mr-1"
                            @click="app.setShowObjection(item.id)"
                            variant="text"/>
                        <v-btn
                            icon="mdi-delete"
                            density="compact"
                            color="error"
                            @click="remove(item.id)"
                            variant="text"/>
                    </td>
                    <td><v-icon :color="getActionColor(item.action)" :icon="getActionIcon(item.action)"/></td>
                    <td><v-chip variant="flat" density="compact" :color="app.getUserColor(item.user_id)">{{ app.getUserShort(item.user_id) }}</v-chip></td>
                    <td>{{ item.tag_name }}</td>
                    <td>{{ item.explanation }}</td>
                    <td>{{ DateTime.fromMillis(item.created).toLocaleString(DateTime.DATETIME_MED_WITH_WEEKDAY) }}</td>
                </tr>
            </template>
        </v-data-table>
    </div>
</template>

<script setup>
    import { getActionColor, getActionIcon, useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { deleteObjections } from '@/use/utility';
    import { DateTime } from 'luxon';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted, watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    const { showAllUsers, allowEdit } = storeToRefs(app)

    const props = defineProps({
        item: {
            type: Object,
            required: true
        }
    })

    const objections = ref([])
    const filtered = computed(() => {
        if (showAllUsers.value) {
            return objections.value
        }
        return objections.value.filter(d => d.user_id === app.activeUserId)
    })

    const headers = [
        { key: "action", title: "Action", width: 50 },
        { key: "user_id", title: "Owner", maxWidth: 100 },
        { key: "tag_name", title: "Tag" },
        { key: "explanation", title: "Explanation", sortable: false },
        { key: "created", title: "Time Created", minWidth: 250 }
    ]
    const visibleHeaders = computed(() => {
        const list = allowEdit.value ? [{ key: "id", title: "Edit Actions", width: 150 }] : []
        return list.concat(headers)
    })

    async function remove(id) {
        try {
            await deleteObjections([id])
            toast.success("delete objection")
            times.needsReload("objections")
        } catch(e) {
            console.error(e.toString())
            toast.error("error deleting objection")
        }
    }

    function read() {
        const list = DM.getDataItem("objections_items", props.item.id)
        objections.value = list ? list : []
    }

    onMounted(read)

    watch(() => props.item.id, read)
    watch(() => Math.max(times.all, times.objections), read)
</script>