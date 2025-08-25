<template>
    <v-dialog v-model="model" width="97vw" style="overflow-y: auto;" persistent>
        <v-card v-if="item" min-height="95vh" height="95vh" density="compact" ref="wrapper" class="pa-0">
            <div style="max-height: 40px;">
                <div class="d-flex align-center justify-start">
                    <div v-if="mdAndUp">
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
                    <v-divider vertical v-if="mdAndUp"></v-divider>
                    <v-img v-if="smAndUp && item.teaser"
                        :src="mediaPath('teaser', item.teaser)"
                        style="max-width: 80px; max-height: 40px;"
                        class="ml-2"
                        cover
                        width="80"
                        height="40"/>

                    <span v-if="smAndUp" style="max-width: 200px;" :title="item?.name" class="font-weight-bold ml-2 mr-4 text-dots">{{ item?.name }}</span>

                    <ExpertiseRating v-if="mdAndUp" :item="item" :user="activeUserId" :key="'rate_'+item.id"/>

                    <v-divider vertical v-if="smAndUp"></v-divider>
                    <v-btn
                        density="compact"
                        variant="plain"
                        size="small"
                        class="ml-2 mr-2"
                        :icon="showInfo ? 'mdi-information' : 'mdi-information-off'"
                        @click="showInfo = !showInfo"/>

                    <v-divider vertical></v-divider>
                    <v-tabs v-model="tab" color="primary" density="compact" class="mt-1">
                        <v-tab text="Tags" value="tags"></v-tab>
                        <v-tab text="Evidence" value="evidence"></v-tab>
                        <v-tab text="Objections" value="objections"></v-tab>
                        <v-tab v-if="app.hasMetaItems" :text="capitalize(app.metaItemName+'s')" value="meta_items"></v-tab>
                    </v-tabs>
                </div>

                <div style="position: absolute; top: 5px; right: 5px;">
                    <v-btn
                        :style="{ backgroundColor: lightMode ? 'white' : 'black' }"
                        class="bordered-grey-light-thin"
                        icon="mdi-close"
                        color="error"
                        rounded
                        variant="text"
                        density="compact"
                        @click="cancel"/>
                </div>
            </div>

            <v-divider></v-divider>

            <div class="d-flex justify-space-between align-start">

                <ItemInfo v-if="showInfo"
                    :item="item"
                    min-width="200px"
                    :width="infoWidth"
                    class="pa-2 text-caption"/>

                <v-tabs-window v-model="tab" style="width: 100%; max-height: 94vh; overflow-y: auto;">

                    <v-tabs-window-item class="pa-4" value="tags" key="tags">
                        <ItemTagEditor ref="tedit"
                            :key="'tags_'+item.id"
                            :item="item"
                            :data="tags"
                            :width="Math.max(300, width-(showInfo ? infoWidth + 40 : 60))"
                            :height="Math.max(200, height-60)"
                            all-data-source="tags"
                            @add="emit('add-tag')"
                            @delete="emit('delete-tag')"/>
                    </v-tabs-window-item>

                    <v-tabs-window-item class="pa-4" value="evidence" key="evidence">
                        <ItemEvidenceEditor
                            :key="'ev_'+item.id"
                            :name="item.name"
                            :game="item.id"/>
                    </v-tabs-window-item>

                    <v-tabs-window-item class="pa-4" value="objections" key="objections">
                        <ObjectionTable :itemId="item.id" :key="'ob_'+item.id"/>
                    </v-tabs-window-item>

                    <v-tabs-window-item class="pa-4" value="meta_items" key="meta_items">
                        <ItemMetaItemEditor :item="item" :key="'mt_'+item.id"/>
                    </v-tabs-window-item>
                </v-tabs-window>
            </div>

            <MiniDialog v-model="askDiscard" persistent min-width="50%" max-width="75%">
                <template #text>
                    <div style="text-align: center;">
                        You have <b>{{ numTagChanges }} unsaved tag changes</b>.
                        Do you want to save or discard them?
                        <div v-if="tagChanges" class="mt-2 d-flex align-start" style="max-height: 50vh; overflow-y: auto;">
                            <div style="width: 49%; max-width: 50%;" class="mr-2">
                                <div><b>added tags</b></div>
                                <div class="text-caption">
                                    <span v-for="(t, i) in tagChanges.add">
                                        {{ i > 0 ? " - " : "" }}{{ t }}
                                    </span>
                                </div>
                            </div>
                            <div style="width: 49%; max-width: 50%;" class="ml-2">
                                <div><b>removed tags</b></div>
                                <div class="text-caption">
                                    <span v-for="(t, i) in tagChanges.remove">
                                        {{ i > 0 ? " - " : "" }}{{ t }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </template>

                <template #actions>
                    <v-btn color="warning" @click="cancelClose">
                        cancel
                    </v-btn>
                    <v-btn color="error" @click="discardChanges">
                        discard changes
                    </v-btn>
                    <v-btn color="primary" @click="saveChanges">
                        save changes
                    </v-btn>
                </template>
            </MiniDialog>
        </v-card>
    </v-dialog>
</template>

<script setup>
    import { useElementSize } from '@vueuse/core';
    import ItemEvidenceEditor from '../evidence/ItemEvidenceEditor.vue';
    import ItemTagEditor from '../tags/ItemTagEditor.vue';
    import ItemMetaItemEditor from '../meta_items/ItemMetaItemEditor.vue';
    import { ref, useTemplateRef } from 'vue';
    import ExpertiseRating from '../ExpertiseRating.vue';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { capitalize, mediaPath } from '@/use/utility';
    import ObjectionTable from '../objections/ObjectionTable.vue';
    import { useDisplay } from 'vuetify';
    import { useSettings } from '@/store/settings';
    import ItemInfo from '../items/ItemInfo.vue';
    import MiniDialog from './MiniDialog.vue';

    const app = useApp()
    const settings = useSettings()
    const { activeUserId } = storeToRefs(app)
    const { lightMode } = storeToRefs(settings)

    const { smAndUp, mdAndUp } = useDisplay()

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

    const tedit = useTemplateRef("tedit")
    const wrapper = useTemplateRef("wrapper")

    const tab = ref("tags")

    const askDiscard = ref(false)
    const showInfo = ref(false)
    const infoWidth = ref(220)

    let tagChanges = null
    const numTagChanges = ref(0)

    const { width, height } = useElementSize(wrapper)

    function close() {
        emit("cancel", numTagChanges.value)
        numTagChanges.value = 0
        tagChanges = null
        model.value = false
    }
    function cancel() {
        if (tedit.value) {
            const changes = tedit.value.getChanges()
            tagChanges = changes
            if (tagChanges) {
                tagChanges.add.sort()
                tagChanges.remove.sort()
                numTagChanges.value = tagChanges.add.length + tagChanges.remove.length
            } else {
                numTagChanges.value = 0
            }
        } else {
            numTagChanges.value = 0
            tagChanges = null
        }

        if (numTagChanges.value === 0) {
            close()
        } else {
            askDiscard.value = true
        }
    }

    function cancelClose() {
        askDiscard.value = false
    }
    function discardChanges() {
        askDiscard.value = false
        if (tedit.value) {
            tedit.value.discardChanges()
        }
        close()
    }
    async function saveChanges() {
        askDiscard.value = false
        if (tedit.value) {
            await tedit.value.saveChanges()
            numTagChanges.value = 0
            tagChanges = null
        }
        close()
    }

</script>