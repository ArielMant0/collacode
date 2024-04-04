<template>
    <v-card v-if="props.item" width="100%" height="100%" :title="'Edit tags for '+item.name" ref="wrapper">
        <v-card-text>

            <v-btn-toggle :model-value="settings.addTagsView">
                <v-btn icon="mdi-view-list" value="list" @click="settings.setView('list')"/>
                <v-btn icon="mdi-view-grid" value="cards" @click="settings.setView('cards')"/>
            </v-btn-toggle>
            <v-list v-if="settings.addTagsView === 'list'" density="compact" :height="wSize.height.value-(add ? 450 : 250)" class="mt-2 mb-2">
                <v-list-item v-for="tag in item.tags"
                    :key="tag.id"
                    :title="tag.name"
                    :subtitle="getTagDescription(tag)"
                    density="compact"
                    hide-details>

                    <template v-slot:append>
                        <v-tooltip v-if="tag.id && app.activeUserId === tag.created_by" text="delete this tag" location="right">
                            <template v-slot:activator="{ props }">
                                <v-icon color="error" class="mr-1" v-bind="props" @click="deleteTag(tag.tag_id)">mdi-delete</v-icon>
                            </template>
                        </v-tooltip>
                        <v-tooltip v-else-if="!tag.id && app.activeUserId === tag.created_by" text="delete this tag" location="right">
                            <template v-slot:activator="{ props }">
                                <v-icon color="error" class="mr-1" v-bind="props" @click="deleteTempTag(tag.name)">mdi-delete</v-icon>
                            </template>
                        </v-tooltip>
                    </template>
                </v-list-item>

                <v-list-item v-for="tag in tagsFiltered"
                    :key="tag.id"
                    :title="tag.name"
                    :subtitle="tag.description"
                    density="compact"
                    hide-details>

                    <template v-slot:append>
                        <v-tooltip text="add this tag" location="right">
                            <template v-slot:activator="{ props }">
                                <v-icon color="primary" class="mr-1" v-bind="props" @click="addTag(tag)">mdi-plus</v-icon>
                            </template>
                        </v-tooltip>
                        <v-tooltip :text="app.getUserName(tag.created_by)" location="right">
                            <template v-slot:activator="{ props }">
                                <v-icon v-bind="props">mdi-information-outline</v-icon>
                            </template>
                        </v-tooltip>
                    </template>
                </v-list-item>

            </v-list>

            <div v-else>
                <TagTiles :data="tags" :selected="itemTagObj" @click="toggleTag" :width="125" :height="75"/>
            </div>

            <v-checkbox v-model="add"
                density="compact"
                hide-details
                hide-spin-buttons
                label="create new tag"
                @update:model-value="onToggleAdd"
                />

            <TagWidget v-if="add"
                :data="newTag"
                name-label="New Tag Name"
                desc-label="New Tag Description"
                button-label="add"
                button-icon="mdi-plus"
                emit-only
                :can-edit="true"
                @update="addNewTag"/>
        </v-card-text>

        <v-card-actions>
            <v-btn class="ms-auto" color="warning" @click="onCancel">cancel</v-btn>
            <v-btn class="ms-2" color="success" :disabled="!tagChanges" @click="saveAndClose">save</v-btn>
        </v-card-actions>
    </v-card>
</template>

<script setup>
    import TagWidget from '@/components/tags/TagWidget.vue';
    import TagTiles from '@/components/tags/TagTiles.vue';
    import { ref, reactive, computed } from 'vue';
    import { useToast } from "vue-toastification";
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings'
    import DM from '@/use/data-manager';
    import { useElementSize } from '@vueuse/core';

    const props = defineProps({
        item: {
            type: Object,
        },
        data: {
            type: Array,
        },
        source: {
            type: String,
        }
    })
    const emit = defineEmits(["add", "delete", "cancel", "save"]);

    const wrapper = ref(null);
    const wSize = useElementSize(wrapper);

    const app = useApp();
    const settings = useSettings();
    const toast = useToast();

    const add = ref(false);
    const delTags = ref([]);
    const tagChanges = computed(() => delTags.value.length > 0 || (props.item && props.item.tags.some(d => d.unsaved)))
    const newTag = reactive({
        name: "",
        description: "",
        created_by: app.activeUserId,
    });

    const itemTagObj = computed(() => {
        const obj = {};
        if (props.item && props.item.tags) {
            props.item.tags.forEach(t => obj[t.tag_id] = true);
        }
        return obj;
    })

    const tags = computed(() => {
        if (props.data) {
            return props.data
        }
        return DM.getData(props.source ? props.source : "tags", false);
    })
    const tagsFiltered = computed(() => {
        if (!tags.value) return [];
        if (!props.item || !props.item.tags) return tags.value;
        return tags.value.filter(d => props.item.tags.find(dd => dd.tag_id === d.id) === undefined)
    })

    function toggleTag(tag) {
        if (props.item && tag) {
            const tagName = tag.name.toLowerCase();
            const t = props.item.tags.find(d => tag.id !== undefined ? d.tag_id == tag.id : d.name.toLowerCase() === tagName);
            if (t) {
                if (tag.id !== undefined) {
                    deleteTag(tag.id)
                } else {
                    deleteTempTag(tag.name);
                }
            } else {
                addTag(tag)
            }
        }
    }
    function addTag(tag) {
        if (props.item && tag) {
            props.item.tags.push({
                name: tag.name,
                description: tag.description,
                created_by: app.activeUserId,
                tag_id: tag.id ? tag.id : null,
                unsaved: true,
            });
            newTag.name = "";
            newTag.description = "";
            const tagName = tag.name.toLowerCase();
            const delIdx = delTags.value.findIndex(d => tag.id !== undefined ? d.tag_id == tag.id : d.name.toLowerCase() === tagName);
            if (delIdx >= 0) {
                delTags.value.splice(delIdx, 1)
            }
            emit("add", props.item.tags.at(-1))
        }
    }
    function addNewTag(tag) {
        if (props.item && tag) {
            const tagName = tag.name.toLowerCase();
            const t = tags.value.find(d => d.name.toLowerCase() === tagName);
            if (t) {
                toast.error("tag with name " + tag.name + " already exists");
                newTag.name = "";
                return;
            }
            props.item.tags.push({
                name: tag.name,
                description: tag.description,
                created_by: app.activeUserId,
                tag_id: null,
                unsaved: true,
            });
            add = false;
            newTag.name = "";
            newTag.description = "";
            emit("add", props.item.tags.at(-1))
        }
    }
    function deleteTag(tagId) {
        if (props.item && tagId) {
            const idx = props.item.tags.findIndex(t => t.tag_id === tagId);
            if (idx >= 0) {
                const item = props.item.tags.splice(idx, 1)[0];
                if (!item.unsaved) {
                    delTags.value.push(item);
                }
                emit("delete", delTags.value.at(-1))
            }
        }
    }
    function deleteTempTag(tagName) {
        if (props.item && tagName) {
            const idx = props.item.tags.findIndex(t => t.name === tagName);
            if (idx >= 0) {
                const todel = props.item.tags.splice(idx, 1);
                emit("delete", todel)
            }
        }
    }

    function onCancel() {
        if (props.item) {

            props.item.tags = props.item.tags.filter(d => !d.unsaved)
            add.value = false;
            delTags.value = [];
            newTag.name = "";
            newTag.description = "";
            if (tagChanges.value) {
                toast.warning("unsaved changes were discarded")
            }
            emit("cancel")
        }
    }
    function saveAndClose() {
        if (tagChanges.value) {
            emit("save", props.item);
        }
        add.value = false;
        delTags.value = [];
        newTag.name = "";
        newTag.description = "";
    }

    function getTagDescription(datum) {
        if (datum.description) {
            return datum.description
        }
        const tag = tags.value.find(d => d.id === datum.tag_id);
        return tag ? tag.description : "";
    }

    function onToggleAdd() {
        newTag.created_by = app.activeUserId;
    }
</script>