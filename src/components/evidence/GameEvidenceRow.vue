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
            :width="e.open ? width*scaleFactor : height">

            <EvidenceCell
                :key="'ev_t_'+e.id"
                :item="e"
                :allowed-tags="item.allTags"
                :width="width"
                :height="height"
                :scale-factor="scaleFactor"
                :allow-edit="allowEdit"
                @enlarge="emit('enlarge', e)"
                />
        </v-sheet>

        <v-btn v-if="allowAdd"
            class="pa-2 ma-1"
            color="secondary"
            :width="height"
            :height="height"
            rounded="sm"
            icon="mdi-plus"
            @click="openAddDialog"
        </v-btn>
    </div>

    <v-dialog v-model="addDialog" width="auto" min-width="1000">
            <v-card title="Add new evidence">
                <v-card-text class="d-flex">
                    <v-sheet min-width="400" class="mr-1 ml-1">
                        <v-text-field :model-value="item.name"
                            readonly
                            disabled
                            density="compact"
                            label="Game title"
                            hide-details
                            hide-spin-buttons/>
                        <v-select v-model="tagId"
                            class="mt-2"
                            density="compact"
                            label="Associated tag"
                            :items="tagSelectData"
                            item-title="nameNum"
                            item-value="id"
                            hide-details
                            hide-spin-buttons/>
                        <v-textarea v-model="desc"
                            class="mt-2"
                            density="compact"
                            label="Evidence description"
                            hide-details
                            hide-spin-buttons/>
                        <v-file-input v-model="file"
                            accept="image/*"
                            label="Upload a matching image"
                            density="compact"
                            class="mt-2"
                            hide-details
                            hide-spin-buttons
                            @update:model-value="readFile"/>
                    </v-sheet>
                    <v-img class="pa-1 ml-2"
                        :src="imagePreview"
                        :lazy-src="imgUrl"
                        alt="Image Preview"
                        height="300"/>
                </v-card-text>
                <v-card-actions>
                    <v-btn class="ms-auto" @click="closeAddDialog">cancel</v-btn>
                    <v-btn class="ms-2" @click="saveChangesAndClose">submit</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

</template>

<script setup>

    import { computed, ref } from 'vue';
    import { useLoader } from '@/use/loader';
    import { v4 as uuidv4 } from 'uuid';
    import { useToast } from "vue-toastification";
    import { useApp } from '@/store/app';
    import EvidenceCell from '@/components/evidence/EvidenceCell.vue'

    import imgUrlS from '@/assets/__placeholder__s.png'
    import imgUrl from '@/assets/__placeholder__.png'

    const app = useApp();

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
        allowAdd: {
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

    const desc = ref("");
    const tagId = ref(null);

    const addDialog = ref(false);

    const file = ref(null)
    const imagePreview = ref("")

    const loader = useLoader();
    const toast = useToast();

    const tagSelectData = computed(() => {
        return props.item.allTags.map(d => {
            const obj = Object.assign({}, d)
            obj.num = 0;
            props.evidence.forEach(e => {
                if (e.tag_id && e.tag_id === d.id) {
                    obj.num++;
                }
            })
            obj.nameNum = `${obj.name} (${obj.num})`
            return obj;
        })
    })

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


    function openAddDialog() {
        if (!props.allowAdd) return;
        addDialog.value = true;
    }
    function closeAddDialog() {
        if (!props.allowAdd) return;
        addDialog.value = false;
    }
    async function saveChangesAndClose() {
        if (!props.allowAdd) return;

        const obj = {
            game_id: props.item.id,
            code_id: app.currentCode,
            description: desc.value,
            tag_id: tagId.value,
            created: Date.now(),
            created_by: app.activeUserId
        }

        if (file.value) {
            const name = uuidv4();
            await loader.postImage(`image/evidence/${name}`, file.value);
            obj.filename = name;
        }

        await loader.post("add/evidence", { rows: [obj] })
        app.needsReload("evidence")
        toast.success("updated evidence");
        file.value = [];
        imagePreview.value = "";
        closeAddDialog();
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