<template>
    <v-dialog v-model="model" width="90vw" style="overflow-y: auto;">
        <v-card v-if="item" height="85vh">
            <v-card-text ref="wrapper" class="pa-0">
                <div>
                    <div class="d-flex align-center justify-start">
                        <div>
                            <v-btn icon="mdi-arrow-left"
                                density="compact"
                                rounded="sm"
                                class="mr-1 ml-2"
                                variant="plain"
                                :disabled="!hasPrev"
                                @click="emit('prev-item')"/>
                            <v-btn icon="mdi-arrow-right"
                                rounded="sm"
                                density="compact"
                                class="mr-2"
                                variant="plain"
                                :disabled="!hasNext"
                                @click="emit('next-item')"/>
                        </div>
                        <v-divider vertical></v-divider>
                        <v-img v-if="item?.teaser"
                            :src="'teaser/'+item.teaser"
                            style="max-width: 80px; max-height: 40px;"
                            class="ml-2"
                            cover
                            width="80"
                            height="40"/>
                        <span class="font-weight-bold ml-2 mr-4">{{ item?.name }}</span>
                        <v-divider vertical></v-divider>
                        <v-tabs v-model="tab" color="primary">
                            <v-tab text="Tags" value="tags"></v-tab>
                            <v-tab text="Evidence" value="evidence"></v-tab>
                            <v-tab text="Externalizations" value="ext"></v-tab>
                        </v-tabs>
                    </div>
                    <div style="position: absolute; top: 5px; right: 5px;">
                        <v-btn
                            icon="mdi-close"
                            color="error"
                            rounded="sm"
                            size="large"
                            variant="text"
                            density="compact"
                            @click="model = false"/>
                    </div>
                </div>

                <v-divider></v-divider>

                <v-tabs-window v-model="tab" style="width: 100%;">
                    <v-tabs-window-item class="pa-4" value="tags" key="tags">
                        <ItemTagEditor ref="tedit"
                            :key="'tags_'+item.id+'_'+time"
                            :item="item"
                            :data="tags"
                            :width="width-50"
                            :height="height-50"
                            all-data-source="tags"
                            user-only
                            @add="emit('add-tag')"
                            @delete="emit('delete-tag')"
                            @save="onSave"/>
                    </v-tabs-window-item>
                    <v-tabs-window-item class="pa-4" value="evidence" key="evidence">
                        <ItemEvidenceEditor
                            :key="'ev_'+item.id+'_'+time"
                            :name="item.name"
                            :game="item.id"
                            :tags="item.allTags"/>
                    </v-tabs-window-item>
                    <v-tabs-window-item class="pa-4" value="ext" key="ext">
                        <ItemExternalizationEditor :item="item" :key="'exts_'+item.id"/>
                    </v-tabs-window-item>
                </v-tabs-window>
            </v-card-text>
        </v-card>
    </v-dialog>
</template>

<script setup>
    import { useElementSize } from '@vueuse/core';
    import ItemEvidenceEditor from '../evidence/ItemEvidenceEditor.vue';
    import ItemTagEditor from '../tags/ItemTagEditor.vue';
    import ItemExternalizationEditor from '../externalization/ItemExternalizationEditor.vue';
    import { watch, ref } from 'vue';
    import { useTimes } from '@/store/times';

    const model = defineModel()
    const props = defineProps({
        item: {
            type: Object,
        },
        tags: {
            type: Array,
        },
        hasPrev: {
            type: Boolean,
            default: false,
        },
        hasNext: {
            type: Boolean,
            default: false,
        }
    })

    const emit = defineEmits(["prev-item", "next-item", "add-tag", "delete-tag", "cancel", "save-tags"])

    const times = useTimes()

    const tedit = ref(null)
    const wrapper = ref(null)
    const tab = ref("tags")
    const time = ref(Date.now())

    const { width, height } = useElementSize(wrapper)

    function cancel() {
        const hasChanges = tedit.value.discardChanges()
        emit("cancel", hasChanges)
    }
    function onSave() { emit("save-tags", props.item); }

    watch(model, function(now, prev) {
        if (now === false && prev == true) {
            cancel();
        }
    });
    watch(() => [times.coding, times.games], () => time.value = Date.now(), { deep: true })

</script>