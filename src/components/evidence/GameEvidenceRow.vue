<template>
    <div class="mr-2 d-flex">
        <div v-if="selected" class="d-flex flex-column align-center justify-center mr-1">
            <v-btn
                :disabled="!allowMoveUp"
                density="compact"
                rounded="sm"
                variant="text"
                icon="mdi-chevron-up"
                @click.stop="emit('move-up', item.id)"/>
            <v-btn
                :disabled="!allowMoveDown"
                density="compact"
                rounded="sm"
                variant="text"
                icon="mdi-chevron-down"
                @click.stop="emit('move-down', item.id)"/>
        </div>
        <div>
            <v-hover>
                <template v-slot:default="{ props, isHovering }">
                    <v-img v-bind="props"
                        :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
                        cover
                        @click.stop="emit('select', item.id)"
                        class="cursor-pointer"
                        :width="width"
                        :height="height">

                        <v-overlay v-if="item.teaser"
                            :model-value="isHovering"
                            :key="item.id+'_overlay'"
                            scroll-strategy="reposition"
                            contained class="d-flex align-center justify-center"
                            opacity="0.8"
                            >
                            <p style="color: white; white-space: break-spaces; text-align: center;" class="pa-1 font-weight-bold">{{ item.name }}</p>
                        </v-overlay>
                        <v-overlay v-else
                            :model-value="true"
                            persistent
                            scroll-strategy="reposition"
                            :key="item.id+'_overlay_p'"
                            contained class="d-flex align-center justify-center"
                            :opacity="isHovering ? 0.8 : 0.5"
                            >
                            <p style="color: white; white-space: break-spaces; text-align: center;" class="pa-1 font-weight-bold">{{ item.name }}</p>
                        </v-overlay>
                    </v-img>
                </template>
            </v-hover>
        </div>
    </div>

    <div class="d-flex flex-wrap">
        <v-sheet v-for="e in evidence"
            class="pa-1 mr-2"
            :key="'ev_t_'+e.id"
            :width="openEvidence.has(e.id) ? width*scaleFactor : height">

            <v-hover v-if="e.filepath">
                <template v-slot:default="{ isHovering, props }">
                    <v-img v-bind="props"
                        class="cursor-pointer"
                        :src="imagePreview ? imagePreview : 'evidence/'+e.filepath"
                        :cover="!openEvidence.has(e.id)"
                        @click.stop="emit('enlarge', e)"
                        v-ripple.center
                        :width="openEvidence.has(e.id) ? width*scaleFactor : height-10"
                        :height="openEvidence.has(e.id) ? height*scaleFactor : height-10">
                        <v-overlay :model-value="isHovering" contained class="d-flex align-center justify-center" opacity="0.75">
                            <v-icon size="64" color="grey-lighten-2">mdi-magnify-plus-outline</v-icon>
                        </v-overlay>
                    </v-img>
                </template>
            </v-hover>
            <div v-else>
                <v-img class="pa-1" :src="imgUrlS" :width="height-10" :height="height-10"/>
            </div>

            <div>
                <div class="d-flex" @click.stop="emit('evidence', e.id)">
                    <v-btn
                        :icon="openEvidence.has(e.id) ? 'mdi-menu-up' : 'mdi-menu-down'"
                        density="compact"
                        class="pa-0"
                        rounded="sm"
                        size="sm"
                        variant="flat"/>
                    <div v-if="e.tag" class="text-caption text-dots" style="max-width: 100%;">{{ e.tag.name }}</div>
                </div>
                <v-card v-if="openEvidence.has(e.id)" density="compact" :width="width*scaleFactor">
                    <v-card-text class="pa-0">
                        <v-textarea
                            :readonly="!allowEdit"
                            :rows="e.rows + 1"
                            class="tiny-font text-caption"
                            :model-value="e.description"
                            hide-details
                            hide-spin-buttons/>
                    </v-card-text>
                    <div v-if="allowEdit" class="d-flex justify-space-between align-center ma-1">
                        <v-btn prepend-icon="mdi-delete" color="error"
                            rounded="sm"
                            @click="discardChanges"
                            >discard</v-btn>

                        <v-file-input v-model="file"
                            :key="'ev_t_'+e.id+'_img'"
                            accept="image/*"
                            label="Upload a new image"
                            density="compact"
                            style="max-width: 350px"
                            hide-details
                            hide-spin-buttons
                            @update:model-value="readFile"/>

                        <v-btn prepend-icon="mdi-sync" color="primary"
                            rounded="sm"
                            @click="saveChanges"
                            >sync</v-btn>
                    </div>
                </v-card>
            </div>
        </v-sheet>
    </div>

</template>

<script setup>

    import { computed, ref } from 'vue';
    import { useLoader } from '@/use/loader';
    import { v4 as uuidv4 } from 'uuid';
    import { useToast } from "vue-toastification";

    import imgUrlS from '@/assets/__placeholder__s.png'

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        evidence: {
            type: Array,
            default: () => ([])
        },
        selected: {
            type: Boolean,
            default: false
        },
        openEvidence: {
            type: Set,
            required: true
        },
        allowMoveUp: {
            type: Boolean,
            default: false
        },
        allowMoveDown: {
            type: Boolean,
            default: false
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
    const emit = defineEmits(["move-down", "move-up", "evidence", "select", "enlarge", "update"])

    const desc = ref(props.item.description);
    const tagId = ref(props.item.tag_id);
    const imagePath = ref(props.item.filepath)

    const file = ref([])
    const imagePreview = ref("")

    const loader = useLoader();
    const toast = useToast();

    const hasChanges = computed(() => {
        return props.item.description !== desc.value ||
            props.item.tag_id !== tagId.value ||
            imagePreview.value
    })

    function discardChanges() {
        desc.value = props.item.description
        tagId.value = props.item.tag_id
        imagePath.value = props.item.filepath
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
                filepath: d.filepath,
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