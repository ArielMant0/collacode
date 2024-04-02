<template>
    <v-card width="100%" height="100%" title="Edit tags for selection">
        <v-card-text>
            <v-btn-toggle :model-value="settings.addTagsView" class="mb-2">
                <v-btn icon="mdi-view-list" value="list" @click="settings.setView('list')"/>
                <v-btn icon="mdi-view-grid" value="cards" @click="settings.setView('cards')"/>
            </v-btn-toggle>
            <div v-if="settings.addTagsView === 'list'">
                <v-list density="compact"
                    :height="500"
                    class="mt-2 mb-2"
                    >
                    <v-list-item v-for="tag in tags"
                        :key="tag.id"
                        :title="tag.name"
                        :subtitle="getTagDescription(tag)"
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
                    <TagTiles :data="tags" :selected="addTagsForSelectionObj" @click="toggleAddTagForSelection" :width="100" :height="60"/>
                </div>
                <div>
                    Tags to Delete
                    <TagTiles :data="tags" :selected="delTagsForSelectionObj" @click="toggleDelTagForSelection" :width="100" :height="60"/>
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
        }
    })
    const emit = defineEmits(["add", "delete", "cancel", "save"]);

    const tags = computed(() => {
        if (props.data) {
            return props.data
        }
        return DM.getData(props.source ? props.source : "tags", false);
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

    function toggleAddTagForSelection(tag) {
        if (tag) {
            const idx = addTagsForSelection.value.indexOf(tag.id);
            if (idx >= 0) {
                addTagsForSelection.value.splice(idx, 1)
            } else {
                addTagsForSelection.value.push(tag.id)
                emit("add", tag)
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
                    code_id: app.activeCode,
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