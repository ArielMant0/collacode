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
                        <v-tooltip v-if="app.activeUserId === tag.created_by" text="delete this tag" location="right">
                            <template v-slot:activator="{ props }">
                                <v-icon color="error" class="mr-1" v-bind="props" @click="deleteTag(tag.tag_id)">mdi-delete</v-icon>
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
                    @click="saveChanges"
                    prepend-icon="mdi-sync">
                    sync
                </v-btn>
            </div>
        </div>

        <MiniDialog v-model="add" min-width="500" no-actions close-icon title="Add new tag">
            <template v-slot:text>
                <TagWidget
                    :data="newTag"
                    :parents="allTags"
                    name-label="New Tag Name"
                    desc-label="New Tag Description"
                    button-label="add"
                    button-icon="mdi-plus"
                    can-edit
                    @update="add = false"/>
            </template>
        </MiniDialog>
    </div>
</template>

<script setup>
    import TagWidget from '@/components/tags/TagWidget.vue';
    import TagTiles from '@/components/tags/TagTiles.vue';
    import { onMounted, ref, reactive, computed, watch } from 'vue';
    import { useToast } from "vue-toastification";
    import { useApp } from '@/store/app';
    import { ALL_GAME_OPTIONS, CTXT_OPTIONS, useSettings } from '@/store/settings'
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import TreeMap from '../vis/TreeMap.vue';
    import MiniDialog from '../dialogs/MiniDialog.vue';
    import { useTimes } from '@/store/times';
    import { updateGameTags } from '@/use/utility';

    const props = defineProps({
        item: {
            type: Object,
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
    const times = useTimes();
    const settings = useSettings();
    const toast = useToast();

    const { addTagsView } = storeToRefs(settings)

    const realHeight = computed(() => props.height - 150)

    const time = ref(Date.now())
    const add = ref(false);
    const delTags = ref([]);
    const addTags = ref([])
    const tagChanges = computed(() => delTags.value.length > 0 || addTags.value.length > 0)
    const newTag = reactive({
        name: "",
        description: "",
        parent: null,
        created_by: app.activeUserId,
        is_leaf: true
    });

    const itemTagObj = computed(() => {
        const obj = {};
        if (props.item && props.item.tags) {
            props.item.tags.forEach(t => obj[t.tag_id] = true);
            addTags.value.forEach(t => obj[t.tag_id] = true)
        }
        return obj;
    })

    const itemTags = ref([])
    const itemTagsIds = computed(() => itemTags.value.map(d => d.tag_id))
    const leafTags = computed(() => allTags.value.filter(d => d.is_leaf === 1))
    const allTags = ref(DM.getData(props.allDataSource ? props.allDataSource : "tags", false))

    const tagsFiltered = computed(() => {
        if (!props.item || props.item.tags.length === 0) return leafTags.value;
        return leafTags.value.filter(d => props.item.tags.find(dd => dd.tag_id === d.id) === undefined)
    })

    function formatPath(path) {
        return path.split(" / ")
            .map((d, i, arr) => i === 0 ? d : (i === arr.length-1 ? `<b>${d}</b>` : ".."))
            .join(" / ")
    }

    function itemHasTag(tag) {
        if (!props.item) { return false; }
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

                const children = allTags.value.filter(d => d.id !== tag.id && d.path.includes(tag.id));
                const addAll = children.some(d => d.is_leaf === 1 && !itemHasTag(d))
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
                deleteTag(tag.id)
            } else {
                addTag(tag)
            }
        }
    }
    function toggleContext(tag, event) {
        event.preventDefault();
        const id = tag.tag_id ? tag.tag_id : tag.id;
        if (!itemTagsIds.value.includes(id)) {
            settings.setRightClick(
                "tag", id,
                window.scrollX + event.clientX + 10,
                window.scrollY + event.clientY + 10,
                props.item ? { game: props.item.id } : null,
                CTXT_OPTIONS.tag
            );
        } else {
            settings.setRightClick(
                "tag", id,
                window.scrollX + event.clientX + 10,
                window.scrollY + event.clientY + 10,
                props.item ? { game: props.item.id } : null,
                ALL_GAME_OPTIONS
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
            addTags.value.push(Object.assign({}, props.item.tags.at(-1)))
            readSelectedTags()

            newTag.name = "";
            newTag.parent = null;
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
        newTag.parent = null;
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
                } else {
                    const idx2 = addTags.value.findIndex(t => t.tag_id === tagId);
                    if (idx2 >= 0) {
                        addTags.value.splice(idx2, 1)
                    }
                }
                readSelectedTags()
                emit("delete", delTags.value.at(-1))
            } else {
                toast.warning("tag does not exist on this item")
            }
        }
    }

    function discardChanges() {
        if (tagChanges.value) {
            props.item.tags = props.item.tags.filter(d => !d.unsaved)
            delTags.value.forEach(d => props.item.tags.push(d))
            readSelectedTags()
            delTags.value = [];
            addTags.value = [];
            return true;
        }
        return false;
    }

    function onCancel() {
        if (props.item) {
            emit("cancel", tagChanges.value)
            discardChanges()
            add.value = false;
            newTag.name = "";
            newTag.parent = null;
            newTag.description = "";
        }
    }
    async function saveChanges() {
        if (tagChanges.value) {
            emit("save", props.item);
            try {
                await updateGameTags(props.item, app.activeUserId, app.currentCode)
                toast.success("updated tags for " + props.item.name)
                times.needsReload("datatags")
                add.value = false;
                delTags.value = [];
                addTags.value = [];
                newTag.name = "";
                newTag.parent = null;
                newTag.description = "";
            } catch {
                toast.error("error updating tags for " + props.item.name)
                times.needsReload("datatags")
            }
        }
    }

    function getTagDescription(datum) {
        if (datum.description) {
            return datum.description
        }
        const tag = allTags.value.find(d => d.id === datum.tag_id);
        return tag ? tag.description : "";
    }

    function readSelectedTags() {
        if (props.item) {
            itemTags.value = props.item.tags.filter(d => props.userOnly || d.created_by === app.activeUserId)
        }
    }

    defineExpose({ discardChanges })

    onMounted(readSelectedTags)

    watch(() => ([times.all, times.tags, times.tagging]), () => {
        allTags.value = DM.getData(props.allDataSource ? props.allDataSource : "tags", false);
        readSelectedTags();
        time.value = Date.now()
    }, { deep: true })
    watch(() => ([times.all, times.datatags, times.tagging]), () => {
        if (tagChanges.value && props.item) {
            delTags.value.forEach(d => {
                const idx = props.item.tags.findIndex(dd => dd.tag_id === d.tag_id)
                if (idx >= 0) props.item.tags.splice(idx, 1)
            })
            addTags.value.forEach(d => {
                const idx = props.item.tags.findIndex(dd => dd.tag_id === d.tag_id)
                if (idx < 0) props.item.tags.push(d)
            })
            readSelectedTags();
        }
    }, { deep: true })

</script>