<template>
    <v-card width="100%" height="100%" title="Edit tags for selection" ref="wrapper">
        <v-card-text>
            <p v-if="selection" class="text-caption mb-2">
                Your selection includes
                <span v-for="(g, i) in selection.slice(0, 15)">
                    <a :href="g.url" target="_blank">{{ g.name }}</a>
                    <span>{{ (i < selection.length-1 ? (i == selection.length-2 ? ' and ' : ', ') : '') }}</span>
                </span>
                <span v-if="selection.length > 15"> and {{ selection.length-15 }} more ({{ selection.length }} total) ...</span>
            </p>
            <v-btn-toggle :model-value="settings.addTagsView" class="mb-2">
                <v-btn icon="mdi-view-list" value="list" @click="settings.setView('list')"/>
                <v-btn icon="mdi-view-grid" value="cards" @click="settings.setView('cards')"/>
            </v-btn-toggle>
            <span class="text-caption ml-2 float-right">
                items with a colored background are those already present for at least 1 item in the selection
            </span>
            <div v-if="settings.addTagsView === 'list'">
                <v-list density="compact" class="mt-2 mb-2" :height="wSize.height.value-250">
                    <v-list-item v-for="tag in tags"
                        :key="tag.id"
                        :title="tag.name"
                        :subtitle="getTagDescription(tag)"
                        :variant="existingTags.has(tag.id) ? 'tonal' : 'text'"
                        density="compact"
                        hide-details>

                        <template v-slot:append>
                            <v-btn-toggle density="compact">
                                <v-btn icon="mdi-plus" color="primary" @click="toggleAddTagForSelection(tag)"></v-btn>
                                <v-btn icon="mdi-delete" color="error" @click="toggleDelTagForSelection(tag)"></v-btn>
                            </v-btn-toggle>
                        </template>
                    </v-list-item>
                </v-list>
            </div>
            <div v-else class="d-flex">
                <div>
                    Tags to Add
                    <TagTiles :data="tags" item-color="color" :selected="addTagsForSelectionObj" @click="toggleAddTagForSelection" :width="100" :height="60"/>
                </div>
                <div>
                    Tags to Delete
                    <TagTiles :data="tags" item-color="color" :selected="delTagsForSelectionObj" @click="toggleDelTagForSelection" :width="100" :height="60"/>
                </div>
            </div>

        </v-card-text>

        <v-card-actions>
            <v-btn class="ms-auto" color="warning" @click="cancel">cancel</v-btn>
            <v-btn class="ms-2" :color="tagChangesForSel ? 'primary' : 'default'" :disabled="!tagChangesForSel" @click="save">update tags</v-btn>
        </v-card-actions>
    </v-card>
</template>

<script setup>
    import TagTiles from '@/components/tags/TagTiles.vue';
    import { ref, computed } from 'vue';
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings'
    import DM from '@/use/data-manager';
    import { useElementSize } from '@vueuse/core';

    const app = useApp();
    const settings = useSettings();

    const props = defineProps({
        selection: {
            type: Object,
        },
        data: {
            type: Array,
        },
        source: {
            type: String,
        },
        editable: {
            type: Boolean,
            default: false
        },
        userOnly: {
            type: Boolean,
            default: false
        }
    })
    const emit = defineEmits(["add", "delete", "cancel", "save"]);
    const wrapper = ref(null);
    const wSize = useElementSize(wrapper);

    const tags = computed(() => {
        let data;
        if (props.data) {
            data = props.data
        } else {
            data  = DM.getData(props.source ? props.source : "tags", false).filter(d => d.is_leaf === 1);
        }
        data.forEach(d => d.color = existingTags.value.has(d.id) ? '#e4e4e4' : 'default');
        data.sort((a, b) => existingTags.value.has(b.id) - existingTags.value.has(a.id))
        return data;
    })

    const addTagsForSelection = ref([]);
    const addTagsForSelectionObj = computed(() => {
        const obj = {};
        addTagsForSelection.value.forEach(d => obj[d] = true);
        return obj;
    })

    const delTagsForSelection = ref([]);
    const delTagsForSelectionObj = computed(() => {
        const obj = {};
        delTagsForSelection.value.forEach(d => obj[d] = true);
        return obj;
    })
    const tagChangesForSel = computed(() => addTagsForSelection.value.length > 0 || delTagsForSelection.value.length > 0);

    const existingTags = computed(() => {
        if (props.selection) {
            const set = new Set();
            props.selection.forEach(g => g.tags.forEach(t => {
                if (!props.userOnly || t.created_by === app.activeUserId) {
                    set.add(t.tag_id)
                }
            }));
            return set;
        }
        return new Set()
    })

    function toggleAddTagForSelection(tag) {
        if (tag) {
            const idx = addTagsForSelection.value.indexOf(tag.id);
            if (idx >= 0) {
                addTagsForSelection.value.splice(idx, 1)
            } else {
                addTagsForSelection.value.push(tag.id)
                emit("add", tag)
                if (delTagsForSelectionObj.value[tag.id]) {
                    toggleDelTagForSelection(tag);
                }
            }
        }
    }
    function toggleDelTagForSelection(tag) {
        if (tag) {
            const idx = delTagsForSelection.value.indexOf(tag.id);
            if (idx >= 0) {
                delTagsForSelection.value.splice(idx, 1)
            } else {
                delTagsForSelection.value.push(tag.id)
                emit("delete", tag)
                if (addTagsForSelectionObj.value[tag.id]) {
                    toggleAddTagForSelection(tag);
                }
            }
        }
    }
    function cancel() {
        emit("cancel");
        addTagsForSelection.value = [];
        delTagsForSelection.value = [];
    }
    function save() {
        const now = Date.now();
        const dtsAdd = [], dtsDel = [];

        props.selection.forEach(g => {
            addTagsForSelection.value.forEach(t => {
                dtsAdd.push({
                    game_id: g.id,
                    tag_id: t,
                    code_id: app.currentCode,
                    created_by: app.activeUserId,
                    created: now
                });
            });
            delTagsForSelection.value.forEach(t => {
                const dt = g.tags.find(d => d.tag_id === t && d.created_by === app.activeUserId);
                if (dt) dtsDel.push(dt.id);
            });
        });

        emit("save", dtsAdd, dtsDel)
    }

    function getTagDescription(datum) {
        if (datum.description) {
            return datum.description
        }
        const tag = tags.value.find(d => d.id === datum.tag_id);
        return tag ? tag.description : "";
    }

</script>