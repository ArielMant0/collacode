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
            hide-spin-buttons/>

        <v-select v-model="itemId"
            :readonly="!allowEdit"
            density="compact"
            :label="'related '+app.itemName"
            class="tiny-font text-caption mb-1"
            :items="items"
            item-title="name"
            item-value="id"
            hide-details
            hide-spin-buttons/>

        <v-textarea v-model="exp"
            density="compact"
            label="explanation"
            hide-details
            hide-spin-buttons
            style="min-width: 400px;"/>

        <div v-if="allowEdit" class="d-flex justify-space-between align-center mt-4">
            <v-btn
                prepend-icon="mdi-delete"
                rounded="sm"
                variant="tonal"
                :color="hasChanges ? 'error' : 'default'"
                :disabled="!hasChanges"
                @click="read"
                >discard</v-btn>

            <v-btn v-if="existing"
                prepend-icon="mdi-close"
                rounded="sm"
                color="error"
                variant="tonal"
                @click="remove"
                >delete evidence</v-btn>

            <v-btn
                :prepend-icon="existing ? 'mdi-sync' : 'mdi-plus'"
                rounded="sm"
                variant="tonal"
                :color="valid ? 'primary' : 'default'"
                :disabled="!valid"
                @click="submit"
                >
                {{ existing ? 'sync' : 'create' }}
            </v-btn>
        </div>
    </div>
</template>

<script setup>
    import { getActionColor, getActionName, OBJECTION_ACTIONS, useApp } from '@/store/app'
    import { useTimes } from '@/store/times'
    import DM from '@/use/data-manager'
    import { addObjections, deleteObjections, updateObjections } from '@/use/utility'
    import { storeToRefs } from 'pinia'
    import { watch, ref, onMounted, computed } from 'vue'
    import { useToast } from 'vue-toastification'

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

    const emit = defineEmits(["update"])

    const action = ref(null)
    const exp = ref("")
    const tagId = ref(null)
    const itemId = ref(null)

    const tags = ref([])
    const items = ref([])

    const existing = computed(() => props.item.id !== null && props.item.id !== undefined)

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
        tags.value = DM.getDataBy("tags", t => {
            if (it !== null && t.is_leaf === 1 && action.value === OBJECTION_ACTIONS.REMOVE) {
                return it.allTags.find(d => d.id === t.id)
            }
            return t.is_leaf === 1
        })
    }
    function readItems() {
        if (action.value === OBJECTION_ACTIONS.REMOVE && tagId.value !== null) {
            items.value = DM.getDataBy("items", d => d.allTags.find(t => t.id === tagId.value))
                .map(d => ({ id: d.id, name: d.name }))
        } else {
            items.value = DM.getData("items", false).map(d => ({ id: d.id, name: d.name }))
        }
    }

    async function submit() {
        if (!allowEdit.value) return

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
                    action: action.value,
                    created: props.item.created
                }])
                toast.success("updated objection")
            } else {
                await addObjections([{
                    code_id: app.currentCode,
                    user_id: app.activeUserId,
                    tag_id: tagId.value,
                    item_id: itemId.value,
                    explanation: exp.value,
                    action: action.value,
                    created: Date.now()
                }])
                toast.success("added objection")
            }
            emit("update")
            times.needsReload("objections")
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
        tagId.value = props.item.tag_id;
        itemId.value = props.item.item_id;
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