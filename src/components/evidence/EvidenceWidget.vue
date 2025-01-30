<template>
    <div class="d-flex flex-column align-center">

        <video v-if="isVideo"
            :src="'evidence/'+item.filepath"
            :autoplay="true"
            :controls="true"
            style="max-width: 100%; width: auto; max-height: 75vh;"/>

        <img v-else
            :src="imagePreview ? imagePreview : (item.filepath ? 'evidence/'+item.filepath : imgUrl)"
            style="max-width: 100%; width: auto; max-height: 75vh;"/>

        <div class="pa-0 mt-2" style="width: 100%;">
            <v-text-field :model-value="app.getUserName(item.created_by)"
                readonly
                disabled
                density="compact"
                label="Created By"
                hide-details
                hide-spin-buttons/>
            <v-select v-model="tagId"
                :readonly="!allowEdit"
                density="compact"
                label="related tag"
                class="tiny-font text-caption"
                :items="allowedTags"
                item-title="name"
                item-value="id"
                hide-details
                hide-spin-buttons/>
            <v-textarea v-model="desc"
                :readonly="!allowEdit"
                :rows="item.rows ? item.rows + 1 : 3"
                label="description"
                class="tiny-font text-caption"
                density="compact"
                hide-details
                hide-spin-buttons/>
            <div v-if="allowEdit" class="d-flex justify-space-between align-center mt-2">
                <v-btn prepend-icon="mdi-delete"
                    rounded="sm"
                    :color="hasChanges ? 'error' : 'default'"
                    :disabled="!hasChanges"
                    @click="discardChanges"
                    >discard</v-btn>

                <v-file-input v-model="file"
                    :key="'ev_t_'+item.id+'_img'"
                    accept="image/*"
                    label="Upload a new image"
                    density="compact"
                    class="ml-1 mr-1"
                    style="max-width: 350px"
                    hide-details
                    hide-spin-buttons
                    single-line
                    @update:model-value="readFile"/>

                <v-btn prepend-icon="mdi-sync"
                    rounded="sm"
                    :color="hasChanges ? 'primary' : 'default'"
                    :disabled="!hasChanges"
                    @click="saveChanges"
                    >sync</v-btn>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { computed, ref, watch } from 'vue';
    import { v4 as uuidv4 } from 'uuid';
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';

    import imgUrl from '@/assets/__placeholder__.png'
    import { addEvidenceImage, updateEvidence } from '@/use/utility';

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        allowedTags: {
            type: Array,
            required: true
        },
        allowEdit: {
            type: Boolean,
            default: false
        }
    })

    const app = useApp();
    const times = useTimes()
    const toast = useToast();

    const desc = ref(props.item.description);
    const tagId = ref(props.item.tag_id);

    const file = ref(null)
    const imagePreview = ref("")

    const isVideo = computed(() => props.item.filepath && props.item.filepath.endsWith("mp4"))

    const hasChanges = computed(() => {
        return props.item.description !== desc.value ||
            props.item.tag_id !== tagId.value ||
            imagePreview.value
    })

    function discardChanges() {
        desc.value = props.item.description
        tagId.value = props.item.tag_id
        file.value = null;
        imagePreview.value = ""
    }

    function readFile() {
        if (!props.allowEdit) return;

        if (!file.value) {
            imagePreview.value = "";
            return;
        }

        const reader = new FileReader();
        reader.addEventListener('load', () => imagePreview.value = reader.result);
        reader.readAsDataURL(file.value);
    }

    async function saveChanges() {
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
    }

    watch(() => props.item.id, readItem)
    watch(() => times.evidence, readItem)
</script>