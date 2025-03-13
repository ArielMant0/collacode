<template>
    <div>
        <v-text-field v-model="search"
        label="Search"
        prepend-inner-icon="mdi-magnify"
        variant="outlined"
        density="compact"
        class="mb-1"
        clearable
        hide-details
        single-line/>

        <v-data-table :headers="headers" :items="filtered" :search="search" density="compact">
            <template v-slot:item="{ item }">
                <tr>
                    <td v-if="allowEdit">
                        <v-btn
                            :icon="item.edit ? 'mdi-check' : 'mdi-pencil'"
                            density="compact"
                            class="mr-1"
                            @click="toggleEdit(item)"
                            variant="text"/>
                        <v-btn
                            icon="mdi-delete"
                            density="compact"
                            color="error"
                            @click="remove(item.id)"
                            variant="text"/>
                    </td>

                    <td>
                        <span v-if="item.edit">
                            <div @click="setItemAction(item, OBJECTION_ACTIONS.DISCUSS)" class="cursor-pointer">
                                <v-icon
                                    :color="item.action === OBJECTION_ACTIONS.DISCUSS ? getActionColor(OBJECTION_ACTIONS.DISCUSS) : 'default'"
                                    :icon="getActionIcon(OBJECTION_ACTIONS.DISCUSS)"/>
                                <span class="ml-1">{{ getActionName(OBJECTION_ACTIONS.DISCUSS) }}</span>
                            </div>
                            <div @click="setItemAction(item, OBJECTION_ACTIONS.ADD)" class="cursor-pointer">
                                <v-icon
                                    :color="item.action === OBJECTION_ACTIONS.ADD ? getActionColor(OBJECTION_ACTIONS.ADD) : 'default'"
                                    :icon="getActionIcon(OBJECTION_ACTIONS.ADD)"/>
                                <span class="ml-1">{{ getActionName(OBJECTION_ACTIONS.ADD) }}</span>
                            </div>
                            <div @click="setItemAction(item, OBJECTION_ACTIONS.REMOVE)" class="cursor-pointer">
                                <v-icon
                                    :color="item.action === OBJECTION_ACTIONS.REMOVE ? getActionColor(OBJECTION_ACTIONS.REMOVE) : 'default'"
                                    :icon="getActionIcon(OBJECTION_ACTIONS.REMOVE)"/>
                                <span class="ml-1">{{ getActionName(OBJECTION_ACTIONS.REMOVE) }}</span>
                            </div>
                        </span>
                        <span v-else>
                            <v-icon :color="getActionColor(item.action)" :icon="getActionIcon(item.action)"/>
                            <span class="ml-1">{{ getActionName(item.action) }}</span>
                        </span>
                    </td>

                    <td v-if="itemId <= 0">
                        <ItemTeaser v-if="item.item_id" :id="item.item_id" :width="100" :height="50"/>
                    </td>
                    <td v-if="tagId <= 0"
                        :style="{
                            maxWidth: '250px',
                            fontWeight: selectedTags.has(item.tag_id) ? 'bold' : null,
                        }"
                        class="cursor-pointer hover-it"
                        @click="app.toggleSelectByTag(item.tag_id)">
                        {{ item.tag_name }}
                    </td>

                    <td v-if="showAllUsers">
                        <v-chip variant="flat" density="compact" :color="app.getUserColor(item.user_id)">{{ app.getUserShort(item.user_id) }}</v-chip>
                    </td>

                    <td>
                        <textarea v-if="item.edit"
                            v-model="item.explanation"
                            type="text"
                            class="pa-1"
                            style="width: 100%;"
                            @change="setItemChanges(item, true)"/>

                        <span v-else>{{ item.explanation }}</span>
                    </td>

                    <td>{{ DateTime.fromMillis(item.created).toLocaleString(DateTime.DATETIME_MED_WITH_WEEKDAY) }}</td>
                </tr>
            </template>
        </v-data-table>
    </div>
</template>

<script setup>
    import { getActionColor, getActionIcon, getActionName, OBJECTION_ACTIONS, useApp } from '@/store/app'
    import { useTimes } from '@/store/times'
    import DM from '@/use/data-manager'
    import { capitalize, deleteObjections, updateObjections } from '@/use/utility'
    import { DateTime } from 'luxon'
    import { storeToRefs } from 'pinia'
    import { ref, computed, watch, onMounted } from 'vue'
    import { useToast } from 'vue-toastification'
    import ItemTeaser from '../items/ItemTeaser.vue'

    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    const { showAllUsers, allowEdit } = storeToRefs(app)

    const props = defineProps({
        itemId: {
            type: Number,
            default: -1
        },
        tagId: {
            type: Number,
            default: -1
        },
    })

    const search = ref("")
    const objections = ref([])
    const filtered = computed(() => {
        if (showAllUsers.value) {
            return objections.value
        }
        return objections.value.filter(d => d.user_id === app.activeUserId)
    })

    const selectedTags = ref(new Set())

    const headers = computed(() => {
        let list = allowEdit.value ? [{ key: "edit", title: "Editing", width: 100 }] : []
        list = list.concat([
            { key: "action", title: "Action", value: d => getActionName(d.action), width: 120 },
            { key: "item_name", title: capitalize(app.itemName), width: 120 },
            { key: "tag_name", title: "Tag", width: 250 },
            { key: "user_id", title: "Owner", width: 100 },
            { key: "explanation", title: "Explanation", sortable: false },
            { key: "created", title: "Time Created", width: 250 }
        ])

        if (props.itemId > 0) {
            list = list.filter(d => d.key !== "item_id")
        } else if (props.tagId > 0) {
            list = list.filter(d => d.key !== "tag_id")
        }

        return showAllUsers.value ? list : list.filter(d => d.key !== "user_id")
    })

    function setItemAction(item, action) {
        setItemChanges(item, item.action !== action)
        item.action = action
    }
    function setItemChanges(item, changed) {
        item.hasChanges = changed
    }

    async function toggleEdit(item) {
        if (item.edit && item.hasChanges) {
            try {
                await updateObjections([item])
                toast.success("updated objection")
                times.needsReload("objections")
            } catch(e) {
                console.error(e.toString())
                toast.error("error updating objection")
            }
        }
        item.edit = !item.edit
    }

    async function remove(id) {
        try {
            await deleteObjections([id])
            toast.success("deleted objection")
            times.needsReload("objections")
        } catch(e) {
            console.error(e.toString())
            toast.error("error deleting objection")
        }
    }

    function read() {
        let list
        selectedTags.value = DM.getSelectedIds("tags")
        if (props.itemId > 0) {
            list = DM.getDataItem("objections_items", props.itemId)
            if (selectedTags.value.size > 0) {
                list = list.filter(d => selectedTags.value.has(d.tag_id))
            }
        } else if (props.tagId > 0) {
            list = DM.getDataItem("objections_tags", props.tagId)
        } else {
            list = DM.getData("objections", true)
        }

        if (list) {
            list.forEach(d => {
                d.edit = false
                d.hasChanges = false
            })
            objections.value = list
        } else {
            objections.value = []
        }
    }

    onMounted(read)

    watch(props, read, { deep: true })
    watch(() => Math.max(times.all, times.objections, times.f_objections), read)

</script>