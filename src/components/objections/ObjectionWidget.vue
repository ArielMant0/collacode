<template>

    <div :style="{ maxWidth: mdAndUp ? '900px' : '85vw' }">
        <div class="d-flex" style="max-width: 100%;" :class="{
            'align-stretch': !smAndDown,
            'justify-space-between': !smAndDown,
            'flex-column': smAndDown,
            'align-center': smAndDown,
        }">

            <div style="width: max-content; max-height: 80vh; overflow-y: auto;">

                <div class="text-caption mb-2"><b>owner:</b> {{ app.getUserName(item.user_id) }}</div>

                <div class="d-flex justify-center align-center mb-3">
                    <v-chip
                        :variant="action === OBJECTION_ACTIONS.DISCUSS ? 'flat' : 'outlined'"
                        :color="action === OBJECTION_ACTIONS.DISCUSS ? getActionColor(action) : 'default'"
                        @click="setAction(OBJECTION_ACTIONS.DISCUSS)">
                        {{ getActionName(OBJECTION_ACTIONS.DISCUSS) }}
                    </v-chip>
                    <v-chip
                        class="ml-1 mr-1"
                        :variant="action === OBJECTION_ACTIONS.ADD ? 'flat' : 'outlined'"
                        :color="action === OBJECTION_ACTIONS.ADD ? getActionColor(action) : 'default'"
                        :disabled="!canAdd"
                        @click="setAction(OBJECTION_ACTIONS.ADD)">
                        {{ getActionName(OBJECTION_ACTIONS.ADD) }}
                    </v-chip>
                    <v-chip
                        :variant="action === OBJECTION_ACTIONS.REMOVE ? 'flat' : 'outlined'"
                        :color="action === OBJECTION_ACTIONS.REMOVE ? getActionColor(action) : 'default'"
                        :disabled="!canRemove"
                        @click="setAction(OBJECTION_ACTIONS.REMOVE)">
                        {{ getActionName(OBJECTION_ACTIONS.REMOVE) }}
                    </v-chip>
                </div>


                <v-select v-model="tagId"
                    :readonly="!canEdit"
                    density="compact"
                    label="related tag"
                    class="tiny-font text-caption mb-1"
                    :items="tags"
                    item-title="name"
                    item-value="id"
                    :clearable="canEdit"
                    hide-details
                    hide-spin-buttons>

                    <template #prepend>
                        <v-tooltip :text="tagDesc" location="top" open-delay="100">
                            <template v-slot:activator="{ props }">
                                <v-icon v-bind="props" @contextmenu="onTagRightClick">mdi-help-circle-outline</v-icon>
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
                        :readonly="!canEdit"
                        density="compact"
                        :label="'related '+app.itemName"
                        class="tiny-font text-caption ml-1"
                        :items="items"
                        item-title="name"
                        item-value="id"
                        :clearable="canEdit"
                        hide-details
                        hide-spin-buttons/>
                </div>

                <v-textarea v-model="exp"
                    density="compact"
                    label="explanation"
                    hide-details
                    hide-spin-buttons
                    :readonly="!canEdit"
                    :style="{ minWidth: smAndUp ? '400px' : '275px' }"/>


                <v-btn v-if="!item.resolved"
                    rounded="sm"
                    class="mt-1"
                    block
                    variant="tonal"
                    :color="canAct ? (showResolve ? 'warning' : 'primary') : 'default'"
                    density="comfortable"
                    :disabled="!canAct"
                    @click="showResolve = !showResolve">
                    {{ showResolve ? 'cancel' : '' }} resolve
                </v-btn>

                <div v-if="item.resolved" class="mt-2">
                    <div class="d-flex align-center justify-space-between">
                        <b>resolved by: </b>
                        <span class="ml-1">{{ app.getUserName(item.resolved_by) }}</span>
                    </div>
                    <div class="d-flex align-center justify-space-between mb-1">
                        <b>status: </b>
                        <span class="ml-1 d-flex align-center">
                            <v-icon :color="getObjectionStatusColor(item.status)" class="mr-1">{{ getObjectionStatusIcon(item.status) }}</v-icon>
                            <span>{{ getObjectionStatusName(item.status) }}</span>
                        </span>
                    </div>
                    <v-textarea
                        :model-value="item.resolution"
                        density="compact"
                        label="resolution"
                        readonly
                        hide-details
                        hide-spin-buttons
                        :style="{ minWidth: smAndUp ? '400px' : '275px' }"/>
                </div>
                <div v-else-if="canAct && showResolve" class="mt-4">
                    <div class="d-flex align-center justify-space-between mb-1" style="width: 100%;">
                        <b>{{ getActionName(item.action) }} tag: </b>
                        <TagText v-if="tagId" :id="tagId" class="ml-1"/>
                    </div>
                    <v-textarea v-model="res"
                        density="compact"
                        label="resolution"
                        hide-details
                        hide-spin-buttons
                        :style="{ minWidth: smAndUp ? '400px' : '275px' }"/>

                    <div class="mt-1 d-flex align-center justify-space-between">
                        <v-btn
                            :color="canEdit && res ? 'error' : 'default'"
                            :disabled="!canEdit || !res"
                            @click="performAction(false)"
                            style="width: 49%;"
                            density="comfortable">
                            deny
                        </v-btn>
                        <v-btn
                            :color="canEdit && res ? 'primary' : 'default'"
                            :disabled="!canEdit || !res"
                            @click="performAction(true)"
                            style="width: 49%;"
                            density="comfortable">
                            approve
                        </v-btn>
                    </div>
                </div>
            </div>

            <div v-if="showResolve || hasCodersOrEvidence"
                class="d-flex flex-column justify-space-between"
                :class="{ 'ml-4': !smAndDown, 'mt-4': smAndDown }"
                :style="{ maxWidth: mdAndUp ? '50%' : '100%' }"
                style="text-align: center; min-width: 200px; max-height: 80vh; overflow-y: auto;">

                <div v-if="hasCodersOrEvidence">
                    <div class="text-decoration-underline mb-1">coders</div>
                    <div class="d-flex flex-wrap justify-center">
                        <UserChip v-for="uid in coders" :id="uid" class="mr-1 mb-1" small short/>
                    </div>
                    <div class="mt-3 text-decoration-underline">evidence</div>
                    <div v-if="canSelectEvidence" class="text-caption text-error text-wrap">
                        {{ evToRemove.size }} / {{ evidence.length }} evidence will be removed
                    </div>
                    <div class="mt-1 d-flex flex-wrap justify-center" style="min-width: 180px;">
                        <EvidenceCell v-for="e in evidence"
                            :item="e"
                            :height="80"
                            :prevent-click="canSelectEvidence"
                            :highlight="evToRemove.has(e.id)"
                            @click="toggleEvidence(e.id)"
                            zoom-on-hover/>
                    </div>
                </div>

                <div v-if="!item.resolved && showResolve && itemObj && action === OBJECTION_ACTIONS.ADD">
                    <div><b>attach new evidence</b></div>
                    <EvidenceWidget v-if="newEv"
                        ref="evw"
                        emit-only
                        tag-fixed
                        :item="newEv"
                        vertical
                        :max-image-height="200"/>
                </div>
            </div>

        </div>

        <div class="d-flex justify-space-between align-center mt-4">
            <v-btn
                prepend-icon="mdi-delete"
                rounded="sm"
                variant="tonal"
                :color="hasChanges ? 'error' : 'default'"
                :disabled="!canEdit || !hasChanges"
                density="comfortable"
                @click="read"
                >discard</v-btn>

            <v-btn
                :prepend-icon="existing ? 'mdi-sync' : 'mdi-plus'"
                rounded="sm"
                variant="tonal"
                :color="valid ? 'primary' : 'default'"
                :disabled="!canEdit || !valid"
                density="comfortable"
                @click="submit"
                >
                {{ existing ? 'sync' : 'create' }}
            </v-btn>
        </div>
    </div>
</template>

<script setup>
    import { pointer } from 'd3'
    import { EVIDENCE_TYPE, getActionColor, getActionName, getObjectionStatusColor, getObjectionStatusIcon, getObjectionStatusName, OBJECTION_ACTIONS, OBJECTION_STATUS, useApp } from '@/store/app'
    import { useTimes } from '@/store/times'
    import DM from '@/use/data-manager'
    import { addDataTags, addEvidence, addEvidenceImage, addObjections, deleteDataTags, deleteEvidence, updateObjections } from '@/use/data-api'
    import { storeToRefs } from 'pinia'
    import { watch, ref, onMounted, computed, reactive } from 'vue'
    import { useToast } from 'vue-toastification'
    import TagText from '../tags/TagText.vue'
    import ItemTeaser from '../items/ItemTeaser.vue'
    import { useDisplay } from 'vuetify'
    import UserChip from '../UserChip.vue'
    import EvidenceCell from '../evidence/EvidenceCell.vue'
    import EvidenceWidget from '../evidence/EvidenceWidget.vue'
    import { CTXT_OPTIONS, useSettings } from '@/store/settings'

    const times = useTimes()
    const app = useApp()
    const toast = useToast()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(app)
    const { smAndDown, smAndUp, mdAndUp } = useDisplay()

    const props = defineProps({
        item: {
            type: Object,
            required: true
        }
    })

    const emit = defineEmits(["update", "action"])

    const evw = ref(null)

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
    const itemObj = ref(null)

    const coders = ref([])
    const evidence = ref([])

    const hasCodersOrEvidence = computed(() => coders.value.length > 0 || evidence.value.length > 0)
    const existing = computed(() => props.item.id !== null && props.item.id !== undefined && props.item.id > 0)
    const isOpen = computed(() => props.item.status === OBJECTION_STATUS.OPEN)

    const newEv = ref(null)

    const canEdit = computed(() => allowEdit.value && isOpen.value)
    const canAct = computed(() => {
        return existing.value &&
            !hasChanges.value && isOpen.value &&
            props.item.user_id !== app.activeUserId &&
            (props.item.item_id !== null || props.item.tag_id !== null)
    })

    const evToRemove = reactive(new Set())
    const canSelectEvidence = computed(() => action.value === OBJECTION_ACTIONS.REMOVE &&
        !props.item.resolved && showResolve.value &&
        itemObj.value && evidence.value.length > 0
    )

    const hasChanges = computed(() => {
        return props.item.tag_id !== tagId.value ||
            props.item.item_id !== itemId.value ||
            props.item.action !== action.value ||
            props.item.explanation !== exp.value
    })
    const valid = computed(() => hasChanges.value && exp.value && exp.value.length > 0)

    const canAdd = computed(() => {
        if (itemObj.value !== null && tagId.value !== null) {
            return !itemObj.value.allTags.find(d => d.id === tagId.value)
        }
        return false
    })
    const canRemove = computed(() => {
        if (itemObj.value !== null && tagId.value !== null) {
            return itemObj.value.allTags.find(d => d.id === tagId.value)
        }
        return false
    })

    function toggleEvidence(id) {
        if (!canSelectEvidence.value) return

        if (evToRemove.has(id)) {
            evToRemove.delete(id)
        } else {
            evToRemove.add(id)
        }
    }

    function onTagRightClick(event) {
        event.preventDefault()
        if (!tagId.value) return
        const [mx, my] = pointer(event, document.body)
        const extra = itemId.value ?
            {
                item: itemId.value,
                type: action.value === OBJECTION_ACTIONS.ADD ?
                    EVIDENCE_TYPE.POSITIVE :
                    EVIDENCE_TYPE.NEGATIVE

            } : null

        const opt = itemId.value ?
            (action.value === OBJECTION_ACTIONS.ADD ?
                CTXT_OPTIONS.items_tagged :
                CTXT_OPTIONS.items_untagged) :
            CTXT_OPTIONS.tag

        settings.setRightClick(
            "tag", tagId.value,
            mx, my,
            DM.getDataItem("tags_name", tagId.value),
            extra,
            opt
        )
    }

    function setAction(value) {
        action.value = value
    }

    function readMisc() {
        evToRemove.clear()
        if (itemObj.value === null) {
            coders.value = []
            evidence.value = []
            newEv.value = null
        } else {
            if (tagId.value === null) {
                coders.value = itemObj.value.coders
                evidence.value = itemObj.value.evidence
                newEv.value = null
            } else {
                coders.value = itemObj.value.tags
                    .filter(d => tagId.value === null || d.tag_id === tagId.value)
                    .map(d => d.created_by)

                evidence.value = itemObj.value.evidence
                    .filter(d => tagId.value === null || d.tag_id === tagId.value)

                newEv.value = makePositiveEvidence()
            }
        }
    }

    function makePositiveEvidence() {
        return {
            code_id: app.currentCode,
            created_by: app.activeUserId,
            created: Date.now(),
            tag_id: tagId.value,
            item_id: itemId.value,
            type: EVIDENCE_TYPE.POSITIVE,
            filepath: null,
            description: ""
        }
    }

    function makeNegativeEvidence() {
        const auto = `This tag was removed as the result of objection ${props.item.id}, ` +
            `owned by ${app.getUserName(props.item.user_id)} and resolved by ${app.activeUser.name}`

        return {
            code_id: app.currentCode,
            created_by: app.activeUserId,
            created: Date.now(),
            tag_id: tagId.value,
            item_id: itemId.value,
            type: EVIDENCE_TYPE.NEGATIVE,
            filepath: null,
            description: `${exp.value}\n${auto}`
        }
    }

    function readTags(update=true) {
        itemObj.value = itemId.value !== null ? DM.getDataItem("items_id", itemId.value) : null
        if (itemObj.value !== null && action.value === OBJECTION_ACTIONS.REMOVE) {
            tags.value = DM.getDataBy("tags", t => t.is_leaf === 1 && (!isOpen.value || itemObj.value.allTags.find(d => d.id === t.id)))
        } else {
            tags.value = DM.getData("tags", false)
        }
        if (update)  readMisc()
    }

    function readItems(update=true) {
        if (!isOpen.value && itemObj.value) {
            items.value = [{ id: itemObj.value.id, name: itemObj.value.name }]
        } else {
            if (action.value === OBJECTION_ACTIONS.REMOVE && tagId.value !== null) {
                items.value = DM.getDataBy("items", d => d.allTags.find(t => t.id === tagId.value))
                    .map(d => ({ id: d.id, name: d.name }))
            } else {
                items.value = DM.getData("items", false).map(d => ({ id: d.id, name: d.name }))
            }
        }

        if (update)  readMisc()
    }

    async function performAction(apply) {
        if (!canEdit.value || !canAct.value) {
            return toast.error("you are not allowed to perform this action")
        }

        if (!res.value || res.value.length === 0) {
            return toast.error("missing resolution text")
        }

        const n = getActionName(props.item.action)
        try {
            const it = DM.getDataItem("items_id", props.item.item_id)
            if (!it) {
                return toast.error("missing item for objection")
            }

            const tid = props.item.tag_id

            const addEv = evw.value ? evw.value.getEvidenceObj() : null

            let updateObj = false, updateDts = false, updateEv = false;
            switch(props.item.action) {
                case OBJECTION_ACTIONS.DISCUSS:
                    updateObj = true
                    break;
                case OBJECTION_ACTIONS.ADD: {
                    if (!apply) {
                        updateObj = true
                        break
                    }
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
                        if (addEv) {
                            // add image first if there is one
                            if (addEv.file) {
                                const resp = await addEvidenceImage(addEv.filename, addEv.file)
                                addEv.filepath = resp.name
                                delete addEv.file
                                delete addEv.filename
                            }
                            // add the evidence itself
                            await addEvidence([addEv])
                            updateEv = true
                        }
                        updateObj = true
                        updateDts = true
                    } else {
                        toast.warning("user tag(s) already exists")
                    }
                }
                break;
                case OBJECTION_ACTIONS.REMOVE: {
                    if (!apply) {
                        updateObj = true
                        break
                    }
                    // remove evidence
                    if (evToRemove.size > 0) {
                        await deleteEvidence(Array.from(evToRemove.values()))
                        evToRemove.clear()
                        updateEv = true
                    }

                    // add new negative evidence
                    await addEvidence([makeNegativeEvidence()])
                    updateEv = true

                    // remove tags
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

            if (updateEv) {
                times.needsReload("evidence")
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
                    resolved: Date.now(),
                    status: apply ? OBJECTION_STATUS.CLOSED_APPROVE : OBJECTION_STATUS.CLOSED_DENY,
                    resolved_by: app.activeUserId
                }])
                toast.success("resolved objection")
                times.needsReload("objections")
                emit("action")
            }

        } catch(e) {
            console.error(e.toString())
            toast.error(`error performing action: ${n}`)
        }
    }

    async function submit() {
        if (!canEdit.value) {
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
                    status: props.item.status,
                    created: props.item.created,
                    resolved_by: props.item.resolved_by,
                    resolved: props.item.resolved
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
                    created: Date.now(),
                    resolved_by: null,
                    resolved: null
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

    function read() {
        action.value = props.item.action
        exp.value = props.item.explanation
        res.value = props.item.resolution
        tagId.value = props.item.tag_id
        itemId.value = props.item.item_id
        tagName.value = tagId.value ? DM.getDataItem("tags_name", tagId.value) : "no tag selected"
        tagDesc.value = tagId.value ? DM.getDataItem("tags_desc", tagId.value) : "no tag selected"
        readTags(false)
        readItems(false)
        readMisc()
    }

    onMounted(read)

    watch(() => props.item.id, read)
    watch(() => times.objections, read)
    watch(itemId, readTags)
    watch(tagId, readItems)
    watch(action, function() {
        readTags(false)
        readItems()
    })
</script>