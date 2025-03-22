<template>
    <div style="width: max-content;">
        <div class="d-flex justify-center align-center mb-2">
            <v-chip
                :color="action === OBJECTION_ACTIONS.DISCUSS ? getActionColor(action) : 'default'"
                @click="setAction(OBJECTION_ACTIONS.DISCUSS)">
                {{ getActionName(OBJECTION_ACTIONS.DISCUSS) }}
            </v-chip>
            <v-chip
                class="ml-1 mr-1"
                :color="action === OBJECTION_ACTIONS.ADD ? getActionColor(action) : 'default'"
                :disabled="itemId === null"
                @click="setAction(OBJECTION_ACTIONS.ADD)">
                {{ getActionName(OBJECTION_ACTIONS.ADD) }}
            </v-chip>
            <v-chip
                :color="action === OBJECTION_ACTIONS.REMOVE ? getActionColor(action) : 'default'"
                :disabled="itemId === null"
                @click="setAction(OBJECTION_ACTIONS.REMOVE)">
                {{ getActionName(OBJECTION_ACTIONS.REMOVE) }}
            </v-chip>
        </div>


        <v-select v-model="tagId"
            :readonly="!allowEdit"
            density="compact"
            label="related tag"
            class="tiny-font text-caption mb-1"
            :items="tags"
            item-title="name"
            item-value="id"
            hide-details
            hide-spin-buttons>

            <template #prepend>
                <v-tooltip v-if="tagDesc" :text="tagDesc" location="top" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-icon v-bind="props">mdi-help-circle-outline</v-icon>
                    </template>
                </v-tooltip>
            </template>

        </v-select>

        <div class="d-flex align-center mb-1">
            <ItemTeaser v-if="itemId" :id="itemId" :width="80" :height="40"/>
            <v-card v-else width="80" height="40"  color="surface-light" class="d-flex align-center justify-center prevent-select">
                <v-icon>mdi-image-area</v-icon>
            </v-card>
            <v-select v-model="itemId"
                :readonly="!allowEdit"
                density="compact"
                :label="'related '+app.itemName"
                class="tiny-font text-caption ml-1"
                :items="items"
                item-title="name"
                item-value="id"
                hide-details
                hide-spin-buttons/>
        </div>

        <v-textarea v-model="exp"
            density="compact"
            label="explanation"
            hide-details
            hide-spin-buttons
            style="min-width: 400px;"/>


        <v-btn v-if="canAct"
            rounded="sm"
            class="mt-1"
            block
            variant="tonal"
            color="primary"
            density="comfortable"
            :disabled="!canAct"
            @click="showResolve = !showResolve">
            {{ showResolve ? 'cancel' : '' }} resolve
        </v-btn>

        <div v-if="canAct && showResolve" class="mt-4">
            <div class="d-flex align-center justify-space-between mb-1">
                <b>{{ getActionName(item.action) }} tag: </b>
                <TagText v-if="tagId" :id="tagId" class="ml-1"/>
            </div>
            <v-textarea v-model="res"
                density="compact"
                label="resolution"
                hide-details
                hide-spin-buttons
                style="min-width: 400px;"/>

            <v-btn
                :color="allowEdit && res ? getActionColor(item.action) : 'default'"
                :disabled="!allowEdit || !res"
                @click="performAction"
                block
                class="mt-1"
                density="comfortable">
                confirm
            </v-btn>
        </div>

        <div v-if="allowEdit" class="d-flex justify-space-between align-center mt-4">
            <v-btn
                prepend-icon="mdi-delete"
                rounded="sm"
                variant="tonal"
                :color="hasChanges ? 'error' : 'default'"
                :disabled="!hasChanges"
                density="comfortable"
                @click="read"
                >discard</v-btn>

            <v-btn v-if="existing"
                prepend-icon="mdi-close"
                rounded="sm"
                color="error"
                variant="tonal"
                density="comfortable"
                @click="remove"
                >delete</v-btn>

            <v-btn
                :prepend-icon="existing ? 'mdi-sync' : 'mdi-plus'"
                rounded="sm"
                variant="tonal"
                :color="valid ? 'primary' : 'default'"
                :disabled="!valid"
                density="comfortable"
                @click="submit"
                >
                {{ existing ? 'sync' : 'create' }}
            </v-btn>
        </div>
    </div>
</template>

<script setup>
    import { getActionColor, getActionName, OBJECTION_ACTIONS, OBJECTION_STATUS, useApp } from '@/store/app'
    import { useTimes } from '@/store/times'
    import DM from '@/use/data-manager'
    import { addDataTags, addObjections, deleteDataTags, deleteObjections, updateObjections } from '@/use/utility'
    import { storeToRefs } from 'pinia'
    import { watch, ref, onMounted, computed } from 'vue'
    import { useToast } from 'vue-toastification'
    import TagText from '../tags/TagText.vue'
    import ItemTeaser from '../items/ItemTeaser.vue'

    const times = useTimes()
    const app = useApp()
    const toast = useToast()

    const { allowEdit } = storeToRefs(app)

    const props = defineProps({
        item: {
            type: Object,
            required: true
        }
    })

    const emit = defineEmits(["update", "action"])

    const action = ref(null)
    const exp = ref("")
    const res = ref("")
    const tagId = ref(null)
    const itemId = ref(null)
    const tagName = ref("")
    const tagDesc = ref("")

    const showResolve = ref(false)

    const tags = ref([])
    const items = ref([])

    const existing = computed(() => props.item.id !== null && props.item.id !== undefined && props.item.id > 0)
    const isOpen = computed(() => props.item.status === OBJECTION_STATUS.OPEN)
    const canAct = computed(() => {
        return existing.value && !hasChanges.value && isOpen.value &&
            (props.item.item_id !== null || props.item.tag_id !== null)
    })

    const hasChanges = computed(() => {
        return props.item.tag_id !== tagId.value ||
            props.item.item_id !== itemId.value ||
            props.item.action !== action.value ||
            props.item.explanation !== exp.value
    })
    const valid = computed(() => hasChanges.value && exp.value && exp.value.length > 0)

    function setAction(value) {
        action.value = value
    }

    function readTags() {
        const it = itemId.value !== null ? DM.getDataItem("items", itemId.value) : null
        if (it !== null && action.value === OBJECTION_ACTIONS.REMOVE) {
            tags.value = DM.getDataBy("tags", t => t.is_leaf === 1 && it.allTags.find(d => d.id === t.id))
        } else {
            tags.value = DM.getData("tags", false)
        }

    }
    function readItems() {
        if (action.value === OBJECTION_ACTIONS.REMOVE && tagId.value !== null) {
            items.value = DM.getDataBy("items", d => d.allTags.find(t => t.id === tagId.value))
                .map(d => ({ id: d.id, name: d.name }))
        } else {
            items.value = DM.getData("items", false).map(d => ({ id: d.id, name: d.name }))
        }
    }

    async function performAction() {
        if (!allowEdit.value || !canAct.value) {
            return toast.error("you are not allowed to perform this action")
        }

        if (!res.value || res.value.length === 0) {
            return toast.error("missing resolution text")
        }

        const n = getActionName(props.item.action)
        try {
            const it = DM.getDataItem("items", props.item.item_id)
            if (!it) {
                return toast.error("missing item for objection")
            }

            const tid = props.item.tag_id

            let updateObj = false, updateDts = false;
            switch(props.item.action) {
                case OBJECTION_ACTIONS.DISCUSS:
                    updateObj = true
                    break;
                case OBJECTION_ACTIONS.ADD: {
                    const cids = new Set(it.tags.filter(d => d.tag_id === tid).map(d => d.created_by))
                    const dts = []
                    const now = Date.now()
                    it.coders.forEach(uid => {
                        if (!cids.has(uid)) {
                            dts.push({
                                item_id: it.id,
                                tag_id: tid,
                                code_id: app.currentCode,
                                created_by: uid,
                                created: now
                            })
                        }
                    })
                    if (dts.length > 0) {
                        await addDataTags(dts)
                        toast.success(`added ${dts.length} user tag(s)`)
                        updateObj = true
                        updateDts = true
                    } else {
                        toast.warning("user tag(s) already exists")
                    }
                }
                break;
                case OBJECTION_ACTIONS.REMOVE: {
                    const dts = it.tags.filter(d => d.tag_id === tid).map(d => d.id)
                    if (dts.length > 0) {
                        await deleteDataTags(dts)
                        toast.success(`deleted ${dts.length} user tag(s)`)
                        updateObj = true
                        updateDts = true
                    }else {
                        toast.warning("tag does not exist")
                    }
                }
                break;
            }

            if (updateDts) {
                times.needsReload("datatags")
            }
            if (updateObj) {
                await updateObjections([{
                    id: props.item.id,
                    code_id: props.item.code_id,
                    user_id: props.item.user_id,
                    tag_id: tagId.value,
                    item_id: itemId.value,
                    explanation: exp.value,
                    resolution: res.value,
                    action: action.value,
                    created: props.item.created,
                    status: OBJECTION_STATUS.CLOSED
                }])
                times.needsReload("objections")
                emit("action")
            }

        } catch(e) {
            console.error(e.toString())
            toast.error(`error performing action: ${n}`)
        }
    }

    async function submit() {
        if (!allowEdit.value || !isOpen.value) {
            return toast.error("you are not allowed to perform this action")
        }

        if (tagId.value === null && itemId.value === null) {
            return toast.error("missing related tag or " + app.itemName)
        }

        if (exp.value === null || exp.value.length === 0) {
            return toast.error("missing explanation")
        }

        try {
             if (existing.value) {
                await updateObjections([{
                    id: props.item.id,
                    code_id: props.item.code_id,
                    user_id: props.item.user_id,
                    tag_id: tagId.value,
                    item_id: itemId.value,
                    explanation: exp.value,
                    resolution: res.value,
                    action: action.value,
                    created: props.item.created,
                    status: props.item.status
                }])
                toast.success("updated objection")
            } else {
                await addObjections([{
                    code_id: app.currentCode,
                    user_id: app.activeUserId,
                    tag_id: tagId.value,
                    item_id: itemId.value,
                    explanation: exp.value,
                    resolution: res.value,
                    action: action.value,
                    status: OBJECTION_STATUS.OPEN,
                    created: Date.now()
                }])
                toast.success("added objection")
            }
            times.needsReload("objections")
            emit("update")
        } catch(e) {
            console.error(e.toString())
            toast.error(`error ${existing ? 'updating' : 'adding'} objection`)
        }
    }
    async function remove() {
        if (!allowEdit.value || !existing.value) return

        try {
            await deleteObjections([props.item.id])
            toast.success("deleted objection")
            times.needsReload("objections")
        } catch(e) {
            console.error(e.toString())
            toast.error("error deleted objection")
        }
    }

    function read() {
        action.value = props.item.action;
        exp.value = props.item.explanation;
        res.value = props.item.resolution;
        tagId.value = props.item.tag_id;
        itemId.value = props.item.item_id;
        tagName.value = tagId.value ? DM.getDataItem("tags_name", tagId.value) : ""
        tagDesc.value = tagId.value ? DM.getDataItem("tags_desc", tagId.value) : ""
        readTags()
        readItems()
    }

    onMounted(read)

    watch(() => props.item.id, read)
    watch(() => times.objections, read)
    watch(itemId, readTags)
    watch(tagId, readItems)
    watch(action, function() {
        readTags()
        readItems()
    })
</script>