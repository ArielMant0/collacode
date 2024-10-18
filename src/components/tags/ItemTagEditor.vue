<template>
    <div style="overflow-y: auto;" class="pr-2 pl-2">
        <div>
            <v-btn-toggle :model-value="addTagsView" density="comfortable">
                <v-btn icon="mdi-tree" value="tree" @click="settings.setView('tree')"/>
                <v-btn icon="mdi-view-grid" value="cards" @click="settings.setView('cards')"/>
                <v-btn icon="mdi-view-list" value="list" @click="settings.setView('list')"/>
            </v-btn-toggle>

            <v-list v-if="addTagsView === 'list'"
                density="compact"
                :height="realHeight"
                width="100%"
                class="mt-2 mb-2">
                <v-list-item v-for="tag in itemTags"
                    :key="tag.id"
                    :subtitle="getTagDescription(tag)"
                    density="compact"
                    @contextmenu="event => toggleContext(tag, event)"
                    hide-details>

                    <template v-slot:title>
                        <span v-html="tag.parent ? formatPath(tag.pathNames) : tag.name"></span>
                    </template>

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
                    :subtitle="tag.description"
                    density="compact"
                    @contextmenu="event => toggleContext(tag, event)"
                    hide-details>

                    <template v-slot:title>
                        <span v-html="tag.parent ? formatPath(tag.pathNames) : tag.name"/>
                    </template>

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

            <div v-else-if="addTagsView === 'cards'">
                <TagTiles
                    :data="leafTags"
                    :selected="itemTagObj"
                    @click="toggleTag"
                    @right-click="toggleContext"
                    :width="100"/>
            </div>

            <div v-else class="pa-2">
                <TreeMap
                    :data="allTags"
                    :time="time"
                    :selected="itemTagsIds"
                    @click="toggleTag"
                    @right-click="toggleContext"
                    :width="width-25"
                    :height="realHeight"/>
            </div>
        </div>

        <div class="mt-2 mb-2 d-flex justify-space-between" style="width: 100%;">
            <v-btn class="mr-2" @click="addNewTag" prepend-icon="mdi-plus">
                new tag
            </v-btn>
            <div class="d-flex">
                <v-btn
                    :color="tagChanges ? 'error' : 'default'"
                    :disabled="!tagChanges"
                    @click="onCancel"
                    prepend-icon="mdi-delete">
                    discard
                </v-btn>
                <v-btn
                    class="ml-2"
                    :color="tagChanges ? 'primary' : 'default'"
                    :disabled="!tagChanges"
                    @click="saveAndClose"
                    prepend-icon="mdi-sync">
                    sync
                </v-btn>
            </div>
        </div>

        <MiniDialog v-model="add" min-width="500" no-actions close-icon title="Add new tag">
            <template v-slot:text>
                <TagWidget
                    :data="newTag"
                    :parents="tags"
                    name-label="New Tag Name"
                    desc-label="New Tag Description"
                    button-label="add"
                    button-icon="mdi-plus"
                    emit-only
                    can-edit
                    @update="add = false"/>
            </template>
        </MiniDialog>
    </div>
</template>

<script setup>
    import TagWidget from '@/components/tags/TagWidget.vue';
    import TagTiles from '@/components/tags/TagTiles.vue';
    import { ref, reactive, computed, watch } from 'vue';
    import { useToast } from "vue-toastification";
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings'
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import TreeMap from '../vis/TreeMap.vue';
    import MiniDialog from '../dialogs/MiniDialog.vue';

    const props = defineProps({
        item: {
            type: Object,
        },
        data: {
            type: Array,
        },
        source: {
            type: String,
        },
        allDataSource: {
            type: String,
        },
        userOnly: {
            type: Boolean,
            default: false
        },
        width: {
            type: Number,
            default: 500,
        },
        height: {
            type: Number,
            default: 250,
        }
    })
    const emit = defineEmits(["add", "delete", "cancel", "save"]);

    const app = useApp();
    const settings = useSettings();
    const toast = useToast();

    const { addTagsView } = storeToRefs(settings)

    const realHeight = computed(() => props.height - 250)

    const time = ref(Date.now())
    const add = ref(false);
    const delTags = ref([]);
    const tagChanges = computed(() => delTags.value.length > 0 || (props.item && props.item.tags.some(d => d.unsaved)))
    const newTag = reactive({
        name: "",
        description: "",
        created_by: app.activeUserId,
        is_leaf: true
    });

    const itemTagObj = computed(() => {
        const obj = {};
        if (props.item && props.item.tags) {
            props.item.tags.forEach(t => obj[t.tag_id] = true);
        }
        return obj;
    })

    const itemTags = computed(() => {
        if (!props.item) return [];
        if (props.userOnly) {
            return props.item.tags.filter(d => d.created_by === app.activeUserId)
        }
        return props.item.tags
    });
    const itemTagsIds = computed(() => {
        return allTags.value.filter(d => props.item.tags.find(dd => {
            return (!props.userOnly || dd.created_by === app.activeUserId) && dd.tag_id === d.id
        }) !== undefined).map(d => d.id)
    });
    const tags = computed(() => {
        if (props.data) {
            return props.data
        }
        return DM.getData(props.source ? props.source : "tags", false);
    })
    const leafTags = computed(() => tags.value.filter(d => d.is_leaf === 1))
    const allTags = computed(() => DM.getData(props.allDataSource ? props.allDataSource : "tags", false))

    const tagsFiltered = computed(() => {
        if (!tags.value) return [];
        if (!props.item || !props.item.tags) return leafTags.value;
        return leafTags.value.filter(d => props.item.tags.find(dd => dd.tag_id === d.id) === undefined)
    })

    function formatPath(path) {
        return path.split(" / ")
            .map((d, i, arr) => i === 0 ? d : (i === arr.length-1 ? `<b>${d}</b>` : ".."))
            .join(" / ")
    }

    function itemHasTag(tag) {
        if (!props.item) {
            return false;
        }
        const tagName = tag.name.toLowerCase();
        return props.item.tags.find(d => tag.id ? d.tag_id == tag.id : d.name.toLowerCase() === tagName) !== undefined
    }

    function toggleTag(tag) {
        if (props.item && tag) {
            if (tag.is_leaf === 0) {
                // remove this tag if it exists on the item
                if (itemHasTag(tag)) {
                    deleteTag(tag.id);
                    toast.info("removed invalid non-leaf tag " + tag.name)
                    return;
                }

                const children = tags.value.filter(d => d.id !== tag.id && d.path.includes(tag.id));
                const addAll = children.some(d => !itemHasTag(d))
                children.forEach(d => {
                    const exists = itemHasTag(d);
                    if (addAll && d.is_leaf === 1 && !exists) {
                        addTag(d)
                    } else if (!addAll && d.is_leaf === 1 && exists) {
                        deleteTag(d.id)
                    }
                })
                return;
            }

            if (itemHasTag(tag)) {
                if (tag.id !== null) {
                    deleteTag(tag.id)
                } else {
                    deleteTempTag(tag.name);
                }
            } else {
                addTag(tag)
            }
            time.value = Date.now();
        }
    }
    function toggleContext(tag, event) {
        event.preventDefault();
        const id = tag.tag_id ? tag.tag_id : tag.id;
        if (!itemTagsIds.value.includes(id)) {
            settings.setRightClick(
                props.item?.id,
                id,
                event.pageX + 10,
                event.pageY + 10,
                ["edit tag"]
            );
        } else {
            settings.setRightClick(
                props.item?.id,
                id,
                event.pageX + 10,
                event.pageY + 10,
            );
        }
    }
    function addTag(tag) {
        if (props.item && tag) {

            if (itemHasTag(tag)) {
                toast.error(`${tag.name} already tagged`)
                return;
            }
            if (tag.is_leaf === 0) {
                toast.error(`${tag.name} is not a leaf node`)
                return;
            }

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
            const delIdx = delTags.value.findIndex(d => {
                return tag.id !== undefined ?
                    d.tag_id == tag.id && d.created_by === app.activeUserId :
                    d.name.toLowerCase() === tagName
            });
            if (delIdx >= 0) {
                delTags.value.splice(delIdx, 1)
            }
            emit("add", props.item.tags.at(-1))
        }
    }
    function addNewTag() {
        newTag.name = ""
        newTag.description = ""
        newTag.created_by = app.activeUserId;
        add.value = true
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
            } else {
                toast.warning("tag does not exist on this item")
            }
        }
    }
    function deleteTempTag(tagName) {
        if (props.item && tagName) {
            const idx = props.item.tags.findIndex(t => t.name === tagName);
            if (idx >= 0) {
                const todel = props.item.tags.splice(idx, 1);
                emit("delete", todel)
            } else {
                toast.warning("tag does not exist on this item")
            }
        }
    }

    function onCancel() {
        if (props.item) {
            emit("cancel", tagChanges.value)
            props.item.tags = props.item.tags.filter(d => !d.unsaved)
            delTags.value.forEach(d => props.item.tags.push(d))
            add.value = false;
            delTags.value = [];
            newTag.name = "";
            newTag.description = "";
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
</script>