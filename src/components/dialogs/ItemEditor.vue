<template>
    <v-dialog v-model="model" width="90vw" style="overflow-y: auto;">
        <v-card v-if="item" height="85vh">
            <v-card-text ref="wrapper" class="d-flex pa-0">
                <div>
                    <v-btn prepend-icon="mdi-close" color="error"
                        width="100%"
                        rounded="0" variant="flat"
                        @click="model = false">close</v-btn>
                    <v-tabs v-model="tab" direction="vertical" color="primary">
                        <v-tab text="Tags" value="tags"></v-tab>
                        <v-tab text="Evidence" value="evidence"></v-tab>
                    </v-tabs>
                </div>

                <v-divider vertical></v-divider>

                <v-window v-model="tab" direction="vertical" style="width: 100%;">
                    <v-window-item class="pa-4" value="tags">
                        <ItemTagEditor
                            :item="item"
                            :data="tags"
                            :width="width-150"
                            :height="height"
                            all-data-source="tags"
                            user-only
                            @add="emit('add-tag')"
                            @delete="emit('delete-tag')"
                            @save="onSave"/>
                    </v-window-item>
                    <v-window-item class="pa-4" value="evidence">
                        <ItemEvidenceEditor
                            :name="item.name"
                            :game="item.id"
                            :tags="item.allTags"/>
                    </v-window-item>
                </v-window>
            </v-card-text>
        </v-card>
    </v-dialog>
</template>

<script setup>
    import { useElementSize } from '@vueuse/core';
    import ItemEvidenceEditor from '../evidence/ItemEvidenceEditor.vue';
    import ItemTagEditor from '../tags/ItemTagEditor.vue';

    const model = defineModel()
    const props = defineProps({
        item: {
            type: Object,
        },
        tags: {
            type: Array,
        },
    })

    const emit = defineEmits(["add-tag", "delete-tag", "cancel", "save-tags"])
    const tab = ref("tags")

    const wrapper = ref(null)
    const { width, height } = useElementSize(wrapper)

    function onSave() { emit("save-tags", props.item); }
</script>