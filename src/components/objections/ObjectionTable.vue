<template>
    <div style="width: 100%;" class="text-caption">

        <div class="d-flex align-center mb-1">
            <span class="mr-2">filter by status:</span>
            <v-chip v-for="val, key in showStatus"
                density="comfortable"
                class="text-caption mr-1 mb-1"
                @click="showStatus[key] = !showStatus[key]"
                :color="getObjectionStatusColor(+key)"
                :variant="val ? 'flat' : 'outlined'">
                {{ getObjectionStatusName(+key) }}
            </v-chip>
        </div>

        <div class="d-flex align-center mb-1">
            <span class="mr-2">filter by action:</span>
            <v-chip v-for="val, key in showAction"
                density="compact"
                class="text-caption mr-1 mb-1"
                @click="showAction[key] = !showAction[key]"
                :color="getActionColor(+key)"
                :variant="val ? 'flat' : 'outlined'">
                {{ getActionName(+key) }}
            </v-chip>
        </div>

        <v-text-field v-model="search"
            label="Search"
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="compact"
            class="mb-1"
            clearable
            hide-details
            single-line/>

        <v-data-table
            :headers="headers"
            :items="filtered"
            :search="search"
            v-model:page="page"
            density="compact"
            :key="'obj_'+time"
            style=" width: 100%;">
            <template v-slot:item="{ item }">
                <tr :class="item.edit ? 'edit data-row' : 'data-row'" @click="openIfNotEdit(item.id, item.edit)">
                    <td v-if="hasHeader('edit')">
                        <v-btn
                            icon="mdi-open-in-app"
                            density="compact"
                            class="mr-1"
                            size="sm"
                            @click.stop="openWidget(item.id)"
                            variant="text"/>
                        <v-btn v-if="allowEdit"
                            :icon="item.edit ? 'mdi-check' : 'mdi-pencil'"
                            density="compact"
                            size="sm"
                            class="mr-1"
                            @click.stop="toggleEdit(item)"
                            variant="text"/>
                        <v-btn v-if="allowEdit"
                            icon="mdi-delete"
                            density="compact"
                            size="sm"
                            color="error"
                            @click.stop="remove(item.id)"
                            variant="text"/>
                    </td>

                    <td v-if="hasHeader('id')">{{ item.id }}</td>

                    <td v-if="hasHeader('action')">
                        <span v-if="item.edit">
                            <div @click.stop="setItemAction(item, OBJECTION_ACTIONS.DISCUSS)" class="cursor-pointer">
                                <v-icon
                                    :color="item.action === OBJECTION_ACTIONS.DISCUSS ? getActionColor(OBJECTION_ACTIONS.DISCUSS) : 'default'"
                                    :icon="getActionIcon(OBJECTION_ACTIONS.DISCUSS)"/>
                                <span class="ml-1">{{ getActionName(OBJECTION_ACTIONS.DISCUSS) }}</span>
                            </div>
                            <div @click.stop="setItemAction(item, OBJECTION_ACTIONS.ADD)" class="cursor-pointer">
                                <v-icon
                                    :color="item.action === OBJECTION_ACTIONS.ADD ? getActionColor(OBJECTION_ACTIONS.ADD) : 'default'"
                                    :icon="getActionIcon(OBJECTION_ACTIONS.ADD)"/>
                                <span class="ml-1">{{ getActionName(OBJECTION_ACTIONS.ADD) }}</span>
                            </div>
                            <div @click.stop="setItemAction(item, OBJECTION_ACTIONS.REMOVE)" class="cursor-pointer">
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

                    <td v-if="itemId <= 0 && hasHeader('item_name')">
                        <ItemTeaser v-if="item.item_id" :id="item.item_id" :width="100" :height="50" prevent-open/>
                    </td>

                    <td v-if="tagId <= 0 && hasHeader('tag_name')">
                        <TagText :id="item.tag_id"/>
                    </td>

                    <td v-if="hasHeader('user_id')">
                        <v-chip variant="flat" density="compact" :color="app.getUserColor(item.user_id)">{{ app.getUserShort(item.user_id) }}</v-chip>
                    </td>

                    <td v-if="hasHeader('explanation')">
                        <textarea v-if="item.edit"
                            v-model="item.explanation"
                            type="text"
                            class="pa-1"
                            style="width: 100%;"
                            @change="setItemChanges(item, true)"/>

                        <span v-else>{{ item.explanation }}</span>
                    </td>

                    <td v-if="hasHeader('created')">
                        {{ DateTime.fromMillis(item.created).toLocaleString(DateTime.DATETIME_SHORT_WITH_SECONDS) }}
                    </td>

                    <td v-if="hasHeader('status')">
                        <v-icon
                            :color="getObjectionStatusColor(item.status)"
                            :icon="getObjectionStatusIcon(item.status)"/>
                    </td>

                    <td v-if="hasHeader('resolution')">
                        <textarea v-if="item.edit"
                            v-model="item.resolution"
                            type="text"
                            class="pa-1"
                            style="width: 100%;"
                            @change="setItemChanges(item, true)"/>

                        <span v-else>{{ item.resolution ? item.resolution : "-" }}</span>
                    </td>

                    <td v-if="hasHeader('resolved_by')">
                        <v-chip v-if="item.resolved_by" variant="flat" density="compact" :color="app.getUserColor(item.resolved_by)">{{ app.getUserShort(item.resolved_by) }}</v-chip>
                        <span v-else>-</span>
                    </td>

                    <td v-if="hasHeader('resolved')">
                        {{ item.resolved ?
                            DateTime.fromMillis(item.resolved).toLocaleString(DateTime.DATETIME_SHORT_WITH_SECONDS) :
                            "-"
                        }}
                    </td>
                </tr>
            </template>
        </v-data-table>
    </div>
</template>

<script setup>
    import { getActionColor, getActionIcon, getActionName, getObjectionStatusColor, getObjectionStatusIcon, getObjectionStatusName, OBJECTION_ACTIONS, OBJECTION_STATUS, useApp } from '@/store/app'
    import { useTimes } from '@/store/times'
    import DM from '@/use/data-manager'
    import { capitalize } from '@/use/utility'
    import { deleteObjections, updateObjections } from '@/use/data-api'
    import { DateTime } from 'luxon'
    import { storeToRefs } from 'pinia'
    import { ref, computed, watch, onMounted, reactive } from 'vue'
    import { useToast } from 'vue-toastification'
    import ItemTeaser from '../items/ItemTeaser.vue'
    import TagText from '../tags/TagText.vue'

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
        showAll: {
            type: Boolean,
            default: true
        },
        excludeHeaders: {
            type: Array,
            default: () => ([])
        }
    })

    const time = ref(0)
    const search = ref("")
    const objections = ref([])

    const page = ref(1)

    const showStatus = reactive({})
    showStatus[OBJECTION_STATUS.OPEN] = true
    showStatus[OBJECTION_STATUS.CLOSED_APPROVE] = false
    showStatus[OBJECTION_STATUS.CLOSED_DENY] = false

    const showAction = reactive({})
    showAction[OBJECTION_ACTIONS.DISCUSS] = true
    showAction[OBJECTION_ACTIONS.ADD] = true
    showAction[OBJECTION_ACTIONS.REMOVE] = true

    const allVisible = computed(() => props.showAll === true || showAllUsers.value)
    const filtered = computed(() => {
        const base = objections.value.filter(d => showStatus[d.status] && showAction[d.action])
        if (allVisible.value) {
            return base
        }
        return base.filter(d => d.user_id === app.activeUserId || d.resolved_by === app.activeUserId)
    })

    const selectedTags = ref(new Set())

    const headers = computed(() => {
        let list = [
            { key: "edit", title: "Editing", width: 110 },
            { key: "id", title: "ID" },
            { key: "action", title: "Action", value: d => getActionName(d.action), width: 120 },
            { key: "item_name", title: capitalize(app.itemName), width: 120 },
            { key: "tag_name", title: "Tag", width: 100 },
            { key: "user_id", title: "Owner", width: 100 },
            { key: "explanation", title: "Explanation", sortable: false },
            { key: "created", title: "Created On", width: 150 },
            { key: "status", title: "Status" },
            { key: "resolution", title: "Resolution", sortable: false },
            { key: "resolved_by", title: "Resolver" },
            { key: "resolved", title: "Resolved On", width: 150 }
        ]

        if (props.itemId > 0) {
            list = list.filter(d => d.key !== "item_name")
        } else if (props.tagId > 0) {
            list = list.filter(d => d.key !== "tag_name")
        }

        if (props.excludeHeaders.length > 0) {
            list = list.filter(d => !props.excludeHeaders.includes(d.key))
        }

        return list
    })

    function hasHeader(key) {
        return headers.value.find(d => d.key === key)
    }

    function setItemAction(item, action) {
        setItemChanges(item, item.action !== action)
        item.action = action
    }
    function setItemChanges(item, changed) {
        item.hasChanges = changed
    }
    function openWidget(id) {
        app.setShowObjection(id)
    }
    function openIfNotEdit(id, edit) {
        if (!edit) {
            openWidget(id)
        }
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
        time.value = Date.now()
    }

    onMounted(read)

    watch(props, read, { deep: true })
    watch(() => Math.max(times.all, times.objections, times.f_objections), read)

</script>

<style scoped>
.v-theme--customDark .data-row:hover {
    background-color: #3d3d3d;
    cursor: pointer;
}
.v-theme--customDark .data-row.edit {
    background-color: #42504c;
    color: white;
}

.v-theme--customLight .data-row:hover {
    background-color: #efefef;
    cursor: pointer;
}
.v-theme--customLight .data-row.edit {
    background-color: #b8e0d6;
    color: black;
}
</style>