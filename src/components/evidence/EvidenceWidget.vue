<template>
    <div class="d-flex flex-column align-center">
        <video v-if="isVideo"
            :src="imagePreview ? imagePreview : 'evidence/'+item.filepath"
            :autoplay="true"
            :controls="true"
            style="max-width: 100%; width: auto; max-height: 75vh;"/>

        <img v-else
            :src="imagePreview ? imagePreview : (item.filepath ? 'evidence/'+item.filepath : imgUrl)"
            style="max-width: 100%; width: auto; max-height: 75vh;"/>

        <div class="pa-0 mt-2" style="width: 100%;">
            <v-text-field :model-value="app.getUserName(item.created_by)"
                disabled
                density="compact"
                label="Created By"
                hide-details
                hide-spin-buttons/>

            <v-select v-model="tagId"
                density="compact"
                label="related tag"
                class="tiny-font text-caption mb-1"
                :items="tags"
                item-title="name"
                item-value="id"
                hide-details
                hide-spin-buttons>

                <template #prepend>
                    <v-tooltip :text="tagDesc" location="top" open-delay="300">
                        <template v-slot:activator="{ props }">
                            <v-icon v-bind="props">mdi-help-circle-outline</v-icon>
                        </template>
                    </v-tooltip>
                </template>
            </v-select>

            <v-textarea v-model="desc"
                :rows="item.rows ? item.rows + 1 : 3"
                label="description"
                class="tiny-font text-caption"
                density="compact"
                hide-details
                hide-spin-buttons/>

            <v-file-input
                v-model="file"
                :key="'ev_t_'+item.id+'_img'"
                accept="image/*, video/mp4"
                label="Upload a new image or video"
                density="compact"
                class="mt-1"
                hide-details
                hide-spin-buttons
                single-line
                @update:model-value="readFile"/>

            <div class="d-flex justify-space-between align-center mt-4">
                <v-btn prepend-icon="mdi-delete"
                    rounded="sm"
                    variant="tonal"
                    density="comfortable"
                    :color="hasChanges ? 'error' : 'default'"
                    :disabled="!hasChanges"
                    @click="discardChanges"
                    >discard</v-btn>

                <v-btn v-if="existing"
                    prepend-icon="mdi-close"
                    rounded="sm"
                    :color="allowEdit ? 'error' : 'default'"
                    density="comfortable"
                    variant="tonal"
                    :disabled="!allowEdit"
                    @click="remove"
                    >delete</v-btn>

                <v-btn prepend-icon="mdi-sync"
                    rounded="sm"
                    variant="tonal"
                    density="comfortable"
                    :color="allowEdit && hasChanges ? 'primary' : 'default'"
                    :disabled="!allowEdit || !hasChanges || !isValid"
                    @click="saveChanges"
                    >sync</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { computed, onMounted, ref, watch } from 'vue';
    import { v4 as uuidv4 } from 'uuid';
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import { useToast } from 'vue-toastification';

    import imgUrl from '@/assets/__placeholder__.png'
    import { addEvidenceImage, deleteEvidence, updateEvidence } from '@/use/data-api';
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';

    const app = useApp();
    const times = useTimes()
    const toast = useToast();

    const { allowEdit } = storeToRefs(app)

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        allowedTags: {
            type: Array,
            required: false
        },
    })

    const emit = defineEmits(["update", "remove"])


    const desc = ref(props.item.description);
    const tagId = ref(props.item.tag_id);
    const tagDesc = ref("")
    const tags = ref([])

    const file = ref(null)
    const imagePreview = ref("")

    const isVideo = computed(() => file.value && file.value.type === "video/mp4" ||
        props.item.filepath && props.item.filepath.endsWith("mp4"))

    const hasChanges = computed(() => {
        return props.item.description !== desc.value ||
            props.item.tag_id !== tagId.value ||
            imagePreview.value
    })
    const isValid = computed(() => {
        return desc.value && desc.value.length > 0 || imagePreview.value
    })

    const existing = computed(() => props.item.id !== null && props.item.id !== undefined)

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
            id: props.item.id,
            description: desc.value,
            filepath: props.item.filepath,
            tag_id: tagId.value,
            code_id: app.currentCode
        }

        if (file.value) {
            const name = uuidv4();
            try {
                await addEvidenceImage(name, file.value)
                obj.filename = name;
            } catch {
                return toast.error("error uploading evidence image")
            }
        }

        try {
            await updateEvidence([obj]);
            toast.success("updated evidence");
            emit("update")
            file.value = null;
            imagePreview.value = "";
            times.needsReload("evidence")
        } catch {
            toast.error("error updated evidence");
        }
    }

    function readItem() {
        file.value = null;
        imagePreview.value = "";
        desc.value = props.item.description;
        tagId.value = props.item.tag_id;
        tagDesc.value = tagId.value ? DM.getDataItem("tags_desc", tagId.value) : ""
        if (props.allowedTags !== undefined) {
            tags.value = props.allowedTags
        } else if (props.item.item_id) {
            const it = DM.getDataItem("items", props.item.item_id)
            tags.value = it ? it.allTags : []
        }
    }

    onMounted(readItem)

    watch(() => props.item.id, readItem)
    watch(() => times.evidence, readItem)
</script>