<template>
    <div class="d-flex"
        style="min-width: 250px;"
        :style="{ 'max-width': lgAndUp ? '70vw' : '85vw' }"
        :class="{
            'flex-column': !horizontal,
            'align-stretch': horizontal,
            'justify-space-between': horizontal,
            }">

        <div style="max-width: 100%;">
            <v-file-input
                    v-model="file"
                    :key="'ev_t_'+item.id+'_img'"
                    accept="image/*, video/mp4"
                    label="upload a new image or video"
                    density="compact"
                    class="mb-1"
                    hide-details
                    hide-spin-buttons
                    single-line
                    style="min-width: 200px;"
                    @update:model-value="readFile">
                </v-file-input>

            <div>
                <video v-if="isVideoFile"
                    :src="imagePreview ? imagePreview : mediaPath('evidence', item.filepath)"
                    :autoplay="true"
                    :controls="true"
                    :style="{ maxHeight: maxImageHeight ? maxImageHeight+'px' : '50vh' }"
                    style="max-width: 100%; width: auto; min-width: 50px;"></video>
                <img v-else
                    :src="imagePreview ? imagePreview : (item.filepath ? mediaPath('evidence', item.filepath) : imgUrl)"
                    :style="{ maxHeight: maxImageHeight ? maxImageHeight+'px' : '50vh' }"
                    style="max-width: 100%; width: auto; min-width: 50px;"/>
            </div>
        </div>

        <div style="max-width: 100%; min-width: 350px;"
            class="d-flex flex-column justify-space-between pa-1"
            :class="{ 'ml-4': horizontal, 'mt-2': !horizontal }"
            :style="{ width: horizontal && (file || item.filepath) ? '50%' : '100%' }">

            <div>
                <div class="d-flex justify-space-between text-caption">
                    <EvidenceIcon
                        :type="type"
                        :prevent-click="!allowEdit"
                        label
                        @click="toggleType"/>
                    <UserChip :id="item.created_by" small/>
                </div>

                <v-select v-model="tagId"
                    density="compact"
                    label="related tag"
                    class="tiny-font text-caption mb-1 mt-1"
                    :items="tags"
                    item-title="name"
                    item-value="id"
                    :readonly="tagFixed"
                    hide-details
                    hide-spin-buttons>

                    <template #prepend>
                        <v-tooltip :text="tagDesc" location="top" open-delay="300">
                            <template v-slot:activator="{ props }">
                                <v-icon v-bind="props" class="mr-1">mdi-help-circle-outline</v-icon>
                            </template>
                        </v-tooltip>
                    </template>
                </v-select>
            </div>

            <v-textarea v-model="desc"
                :rows="item.rows ? item.rows + 2 : 5"
                label="description"
                class="tiny-font text-caption mt-1"
                density="compact"
                hide-details
                hide-spin-buttons/>

            <div class="d-flex align-center mt-2"
                :class="{
                    'justify-space-between': !emitOnly || existing,
                    'justify-center': emitOnly && !existing
                }">

                <v-btn
                    prepend-icon="mdi-delete"
                    rounded="sm"
                    variant="tonal"
                    density="comfortable"
                    :color="hasChanges ? 'error' : 'default'"
                    :disabled="!hasChanges"
                    @click="discardChanges">
                    discard
                </v-btn>

                <v-btn v-if="existing"
                    prepend-icon="mdi-close"
                    rounded="sm"
                    :color="allowEdit ? 'error' : 'default'"
                    density="comfortable"
                    variant="tonal"
                    :disabled="!allowEdit"
                    @click="remove"
                    >delete</v-btn>

                <v-btn v-if="!emitOnly"
                    prepend-icon="mdi-sync"
                    rounded="sm"
                    variant="tonal"
                    density="comfortable"
                    :color="allowEdit && hasChanges ? 'primary' : 'default'"
                    :disabled="!allowEdit || !hasChanges || !isValid"
                    @click="saveChanges"
                    >{{ existing ? 'sync' : 'create' }}</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { computed, onMounted, ref, watch } from 'vue';
    import { EVIDENCE_TYPE, useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import { useToast } from 'vue-toastification';

    import imgUrl from '@/assets/__placeholder__.png'
    import { addEvidence, addEvidenceImage, deleteEvidence, updateEvidence } from '@/use/data-api';
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import { isVideo, mediaPath } from '@/use/utility';
    import UserChip from '../UserChip.vue';
    import { useDisplay } from 'vuetify';
    import EvidenceIcon from './EvidenceIcon.vue';

    const app = useApp();
    const times = useTimes()
    const toast = useToast();

    const { allowEdit } = storeToRefs(app)
    const { xs, lgAndUp } = useDisplay()

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        maxImageHeight: {
            type: Number,
            required: false
        },
        tagFixed: {
            type: Boolean,
            default: false
        },
        emitOnly: {
            type: Boolean,
            default: false
        },
        vertical: {
            type: Boolean,
            default: false
        },
    })

    const emit = defineEmits(["update", "remove"])

    const horizontal = computed(() => !xs.value && !props.vertical)

    const desc = ref(props.item.description);
    const tagId = ref(props.item.tag_id);
    const tagDesc = ref("")
    const tags = ref([])
    const type = ref(0)

    const file = ref(null)
    const imagePreview = ref("")

    const isVideoFile = computed(() => {
        return file.value && (
            file.value.type === "video/mp4" ||
            file.value.type === "video/mov" ||
            file.value.type === "video/mkv"
        ) || isVideo(props.item.filepath)
    })

    const hasChanges = computed(() => {
        return props.item.description !== desc.value ||
            props.item.tag_id !== tagId.value ||
            props.item.type !== type.value ||
            imagePreview.value
    })
    const isValid = computed(() => tagId.value && ((desc.value && desc.value.length > 0) || imagePreview.value || props.item.filepath))
    const existing = computed(() => props.item.id !== null && props.item.id !== undefined)

    function toggleType() {
        type.value = type.value === EVIDENCE_TYPE.POSITIVE ?
            EVIDENCE_TYPE.NEGATIVE :
            EVIDENCE_TYPE.POSITIVE
        readTags()
    }

    async function remove() {
        if (allowEdit.value && existing.value) {
            try {
                await deleteEvidence([props.item.id])
                toast.success("deleted evidence")
                emit("remove")
                times.needsReload("evidence")
            } catch (e) {
                console.error(e.toString())
                toast.error("error deleting evidence")
            }
        }
    }
    function discardChanges() {
        desc.value = props.item.description
        tagId.value = props.item.tag_id
        file.value = null;
        type.value = EVIDENCE_TYPE.POSITIVE
        imagePreview.value = ""
    }

    function readFile() {
        if (!allowEdit.value) return;

        if (!file.value) {
            imagePreview.value = "";
            return;
        }

        const reader = new FileReader();
        reader.addEventListener('load', () => imagePreview.value = reader.result);
        reader.readAsDataURL(file.value);
    }

    async function saveChanges() {
        if (!allowEdit.value) return;

        if (!hasChanges.value) {
            return toast.warning("no changes to save")
        }

        if (!tagId.value) {
            return toast.error("missing related tag")
        }

        if (!props.item.filepath && !file.value && !desc.value) {
            return toast.error("need either a description or image")
        }

        const obj = {
            description: desc.value,
            filepath: props.item.filepath,
            item_id: props.item.item_id,
            tag_id: tagId.value,
            code_id: app.currentCode,
            type: type.value,
            created_by: app.activeUserId
        }

        if (props.emitOnly) {

            if (existing.value) {
                obj.id = props.item.id
                obj.created_by = props.item.created_by
            } else {
                obj.created = Date.now()
                obj.created_by = app.activeUserId
            }

            if (file.value) {
                const idx = file.value.name.lastIndexOf(".")
                const name = idx >= 0 ? file.value.name.slice(0, idx) : file.value.name
                obj.filename = name
                obj.file = file.value
            }
            emit("update", obj)
            return
        }

        if (file.value) {
            const idx = file.value.name.lastIndexOf(".")
            const name = idx >= 0 ? file.value.name.slice(0, idx) : file.value.name
            try {
                const resp = await addEvidenceImage(name, file.value)
                obj.filepath = resp.name;
            } catch {
                return toast.error("error uploading evidence image")
            }
        }

        try {
            if (existing.value) {
                obj.id = props.item.id
                obj.created_by = props.item.created_by
                await updateEvidence([obj]);
                toast.success("updated evidence");
            } else {
                obj.created = Date.now()
                obj.created_by = app.activeUserId
                await addEvidence(obj)
                toast.success("added evidence");
            }
            emit("update", obj)
            file.value = null;
            imagePreview.value = "";
            times.needsReload("evidence")
        } catch {
            toast.error("error updated evidence");
        }
    }

    function readItem(reset=true) {
        if (reset) {
            file.value = null
            type.value = props.item.type
            imagePreview.value = ""
            desc.value = props.item.description
            tagId.value = props.item.tag_id
            tagDesc.value = tagId.value ? DM.getDataItem("tags_desc", tagId.value) : ""
        }

        readTags()
    }

    function readTags() {
        if (props.item.item_id) {
            if (props.tagFixed) {
                tags.value = [DM.getDataItem("tags", props.item.tag_id)]
            } else {
                const it = DM.getDataItem("items_id", props.item.item_id)
                if (it && type.value === EVIDENCE_TYPE.POSITIVE) {
                    if (!it.allTags.find(d => d.id === props.item.tag_id)) {
                        tags.value = it.allTags.concat([DM.getDataItem("tags", props.item.tag_id)])
                    } else {
                        tags.value = it.allTags
                    }
                }
                if (type.value === EVIDENCE_TYPE.NEGATIVE) {
                    const allTags = DM.getDataBy("tags", t => t.is_leaf === 1)
                    const match = new Set(it ? it.allTags.map(t => t.id) : [])
                    tags.value = allTags.filter(t => !match.has(t.id) || t.id === props.item.tag_id)
                }
            }
        }
    }

    function getEvidenceObj() {
        // must have a tag
        if (!tagId.value) {
            return null
        }

        // must have a description or attached image/video
        if (!props.item.filepath && !file.value && !desc.value) {
            return null
        }

        const obj = {
            description: desc.value,
            filepath: props.item.filepath,
            item_id: props.item.item_id,
            tag_id: tagId.value,
            code_id: app.currentCode,
            type: type.value
        }

        if (existing.value) {
            obj.id = props.item.id
        } else {
            obj.created = Date.now()
            obj.created_by = app.activeUserId
        }

        if (file.value) {
            const idx = file.value.name.lastIndexOf(".")
            const name = idx >= 0 ? file.value.name.slice(0, idx) : file.value.name
            obj.filename = name
            obj.file = file.value
        }

        return obj
    }

    defineExpose({ getEvidenceObj })

    onMounted(function() {
        readItem(true)
    })

    watch(() => props.item.id, () => readItem(true))
    watch(() => times.evidence, () => readItem(false))
</script>