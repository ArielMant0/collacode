<template>

    <div v-if="item.filepath" style="position: relative;">
        <v-btn icon="mdi-close" density="comfortable" size="x-small" color="error"
            @click="deleteEvidence" style="position: absolute; right: -5px; top: -5px; z-index: 3999;"/>
        <v-hover>
            <template v-slot:default="{ isHovering, props }">
                <v-img v-bind="props"
                    class="cursor-pointer"
                    :src="imagePreview ? imagePreview : 'evidence/'+item.filepath"
                    :cover="!item.open"
                    @click.stop="emit('enlarge', item)"
                    v-ripple.center
                    :width="item.open ? width*scaleFactor : height-10"
                    :height="item.open ? height*scaleFactor : height-10">
                    <v-overlay :model-value="isHovering" contained class="d-flex align-center justify-center" opacity="0.75">
                        <v-icon size="64" color="grey-lighten-2">mdi-magnify-plus-outline</v-icon>
                    </v-overlay>
                </v-img>
            </template>
        </v-hover>
    </div>

    <div v-else  style="position: relative;">
        <v-btn icon="mdi-close" density="comfortable" size="x-small" color="error"
            @click="deleteEvidence" style="position: absolute; right: -5px; top: -5px; z-index: 3999;"/>
        <v-img class="pa-1" :src="imgUrlS" :width="height-10" :height="height-10"/>
    </div>

    <div>
        <div class="d-flex" @click.stop="item.open = !item.open">
            <v-btn
                :icon="item.open ? 'mdi-menu-up' : 'mdi-menu-down'"
                density="compact"
                class="pa-0"
                rounded="sm"
                size="sm"
                variant="flat"/>
            <div v-if="tagName" class="text-caption text-dots" style="max-width: 100%;">{{ tagName }}</div>
        </div>
        <v-card v-if="item.open" density="compact" :width="width*scaleFactor">
            <v-card-text class="pa-0">
                <v-textarea v-model="desc"
                    :readonly="!allowEdit"
                    :rows="item.rows + 1"
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
            </v-card-text>
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
        </v-card>
    </div>
</template>

<script setup>

    import { ref, computed } from 'vue';
    import { useLoader } from '@/use/loader';
    import { v4 as uuidv4 } from 'uuid';
    import { useToast } from "vue-toastification";
    import { useApp } from '@/store/app';

    import imgUrlS from '@/assets/__placeholder__s.png'

    const app = useApp();

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
        },
        width: {
            type: Number,
            default: 150
        },
        height: {
            type: Number,
            default: 80
        },
        scaleFactor: {
            type: Number,
            default: 4
        },
    })
    const emit = defineEmits(["enlarge", "evidence"])

    const desc = ref(props.item.description);
    const tagId = ref(props.item.tag_id);

    const file = ref([])
    const imagePreview = ref("")

    const loader = useLoader();
    const toast = useToast();

    const tagName = computed(() => {
        if (props.item.tag_id && props.allowedTags) {
            const tag = props.allowedTags.find(d => d.id === props.item.tag_id);
            return tag ? tag.name : null
        }
        return null
    })

    const hasChanges = computed(() => {
        return props.item.description !== desc.value ||
            props.item.tag_id !== tagId.value ||
            imagePreview.value
    })

    function discardChanges() {
        desc.value = props.item.description
        tagId.value = props.item.tag_id
        file.value = [];
        imagePreview.value = ""
    }

    function readFile() {
        if (!props.allowEdit) return;

        if (file.value.length === 0) {
            imagePreview.value = "";
            return;
        }

        const reader = new FileReader();
        reader.addEventListener('load', () => imagePreview.value = reader.result);
        reader.readAsDataURL(file.value[0]);
    }

    async function saveChanges() {
        if (!props.allowEdit) return;

        if (hasChanges.value) {

            const obj = {
                id: props.item.id,
                description: desc.value,
                filepath: props.item.filepath,
                tag_id: tagId.value
            }

            if (file.value && file.value[0]) {
                const name = uuidv4();
                await loader.postImage(`image/evidence/${name}`, file.value[0]);
                obj.filename = name;
            }

            await loader.post("update/evidence", { rows: [obj] })
            app.needsReload("evidence")
            toast.success("updated evidence");
            file.value = [];
            imagePreview.value = "";

        } else {
            toast.error("need description to add new evidence")
        }
    }

    async function deleteEvidence() {
        if (!props.allowEdit) return;
        await loader.post("delete/evidence", { ids: [props.item.id] })
        toast.success("deleted 1 evidence");
        app.needsReload("evidence")
    }

</script>

<style scoped>
.text-dots {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis
}
.tiny-font {
    font-size: 10px;
    max-height: 200px;
}
</style>