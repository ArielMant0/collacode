<template>
    <v-dialog v-model="model" width="95vw" style="overflow-y: auto;">
        <v-card v-if="item" min-height="95vh" height="95vh">
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
                        <v-img v-if="item.teaser"
                            :src="'teaser/'+item.teaser"
                            style="max-width: 80px; max-height: 40px;"
                            class="ml-2"
                            cover
                            width="80"
                            height="40"/>

                        <span style="max-width: 200px;" :title="item?.name" class="font-weight-bold ml-2 mr-4 text-dots">{{ item?.name }}</span>

                        <ExpertiseRating :item="item" :user="activeUserId" :key="'rate_'+item.id"/>

                        <v-divider vertical></v-divider>
                        <v-btn
                            density="compact"
                            variant="plain"
                            size="small"
                            class="ml-2 mr-2"
                            :icon="showInfo ? 'mdi-information' : 'mdi-information-off'"
                            @click="showInfo = !showInfo"/>

                        <v-divider vertical></v-divider>
                        <v-tabs v-model="tab" color="primary">
                            <v-tab text="Tags" value="tags"></v-tab>
                            <v-tab text="Evidence" value="evidence"></v-tab>
                            <v-tab text="Objections" value="objections"></v-tab>
                            <v-tab v-if="app.hasMetaItems" :text="capitalize(app.metaItemName+'s')" value="meta_items"></v-tab>
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

                <div class="d-flex justify-space-between align-start">
                    <div v-if="showInfo"
                        :style="{ minWidth: '200px', width: infoWidth+'px', maxHeight: '90vh', overflowY: 'auto' }"
                        class="pa-2 text-caption"
                        >
                        <div><b>Name</b>: {{ item?.name }}</div>
                        <div v-if="item?.url"><b>URL</b>: <a :href="item?.url" target="_blank">{{ item?.url }}</a></div>
                        <div v-for="c in app.schema.columns" :key="'col_'+c.name" class="mt-1">
                            <b>{{ capitalize(c.name) }}</b>: {{ item ? item[c.name] : '?' }}
                        </div>
                        <div v-if="item?.description" class="mt-1 mb-1">
                            <b>Description</b>
                            <p>{{ item?.description }}</p>
                        </div>
                    </div>
                    <v-tabs-window v-model="tab" style="width: 100%; max-height: 90vh;">

                        <v-tabs-window-item class="pa-4" value="tags" key="tags">
                            <ItemTagEditor ref="tedit"
                                :key="'tags_'+item.id"
                                :item="item"
                                :data="tags"
                                :width="width - (showInfo ? infoWidth + 30 : 50)"
                                :height="height-50"
                                all-data-source="tags"
                                @add="emit('add-tag')"
                                @delete="emit('delete-tag')"/>
                        </v-tabs-window-item>

                        <v-tabs-window-item class="pa-4" value="evidence" key="evidence">
                            <ItemEvidenceEditor
                                :key="'ev_'+item.id"
                                :name="item.name"
                                :game="item.id"
                                :tags="item.allTags"/>
                        </v-tabs-window-item>

                        <v-tabs-window-item class="pa-4" value="objections" key="objections">
                            <ObjectionTable :itemId="item.id" :key="'ob_'+item.id"/>
                        </v-tabs-window-item>

                        <v-tabs-window-item class="pa-4" value="meta_items" key="meta_items">
                            <ItemMetaItemEditor :item="item" :key="'mt_'+item.id"/>
                        </v-tabs-window-item>
                    </v-tabs-window>
                </div>

            </v-card-text>
        </v-card>
    </v-dialog>
</template>

<script setup>
    import { useElementSize } from '@vueuse/core';
    import ItemEvidenceEditor from '../evidence/ItemEvidenceEditor.vue';
    import ItemTagEditor from '../tags/ItemTagEditor.vue';
    import ItemMetaItemEditor from '../meta_items/ItemMetaItemEditor.vue';
    import { watch, ref } from 'vue';
    import ExpertiseRating from '../ExpertiseRating.vue';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { capitalize } from '@/use/utility';
    import ObjectionTable from '../objections/ObjectionTable.vue';

    const app = useApp()
    const { activeUserId } = storeToRefs(app)

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

    const emit = defineEmits(["prev-item", "next-item", "add-tag", "delete-tag", "cancel"])

    const tedit = ref(null)
    const wrapper = ref(null)
    const tab = ref("tags")

    const showInfo = ref(false)
    const infoWidth = ref(220)

    const { width, height } = useElementSize(wrapper)

    function cancel() {
        let hasChanges = false;
        if (tedit.value) {
            hasChanges = tedit.value.discardChanges()
        }
        emit("cancel", hasChanges)
        model.value = false;
    }

    watch(model, function(now, prev) {
        if (now === false && prev == true) {
            cancel();
        }
    });

</script>