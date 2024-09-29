<template>
    <div class="d-flex flex-column align-center">
        <img :src="item.filepath ? 'evidence/'+item.filepath : imgUrl" style="max-width: 100%; height: auto;"/>
        <div class="pa-0 mt-2" style="width: 100%;">
            <v-text-field :model-value="app.getUserName(item.created_by)"
                readonly
                disabled
                density="compact"
                label="Created By"
                hide-details
                hide-spin-buttons/>
            <v-textarea v-model="desc"
                :readonly="!allowEdit"
                :rows="item.rows ? item.rows + 1 : 2"
                label="description"
                class="tiny-font text-caption"
                density="compact"
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
            <div v-if="allowEdit" class="d-flex justify-space-between align-center ma-1">
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
                    style="max-width: 350px"
                    hide-details
                    hide-spin-buttons
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

    import imgUrl from '@/assets/__placeholder__.png'

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
            default: true
        }
    })

    const app = useApp();
    const desc = ref(props.item.description);
    const tagId = ref(props.item.tag_id);

    const file = ref(null)
    const imagePreview = ref("")

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
        if (hasChanges.value) {
            const obj = {
                id: props.item.id,
                description: desc.value,
                filepath: props.item.filepath,
                tag_id: tagId.value
            }

            if (file.value) {
                const name = uuidv4();
                await loader.postImage(`image/evidence/${name}`, file.value);
                obj.filename = name;
            }

            await loader.post("update/evidence", { rows: [obj] })
            app.needsReload("evidence")
            toast.success("updated evidence");
            file.value = null;
            imagePreview.value = "";
        } else {
            toast.error("need description to add new evidence")
        }
    }

    watch(() => props.item.id, function() {
        desc.value = props.item.description;
        tagId.value = props.item.tag_id;
    })
</script>