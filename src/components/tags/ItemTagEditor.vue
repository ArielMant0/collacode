<template>
    <div style="overflow-y: auto;">
        <div class="d-flex align-start" :class="{ 'flex-column': vertical }">
            <div class="d-flex justify-space-between align-start"
                :style="{ width: vertical ? '100%' : 'auto', height: vertical ? 'auto' : realHeight+'px' }"
                :class="{ 'flex-column': !vertical, 'mb-2': vertical, 'mr-2': !vertical }">

                <div style="text-align: center;">

                    <v-btn-toggle :model-value="addTagsView" density="compact" style="height: fit-content;" :class="{ 'flex-column': !vertical, 'd-flex': vertical, 'mb-2': !vertical }">
                        <v-btn density="compact" icon="mdi-tree" value="tree" @click="settings.setView('tree')"/>
                        <v-btn density="compact" icon="mdi-view-grid" value="cards" @click="settings.setView('cards')"/>
                        <v-btn density="compact" icon="mdi-view-list" value="list" @click="settings.setView('list')"/>
                    </v-btn-toggle>


                    <v-btn v-if="vertical"
                        rounded="sm"
                        prepend-icon="mdi-family-tree"
                        density="comfortable"
                        @click="simGraph = !simGraph"
                        variant="tonal">
                        similarities
                    </v-btn>
                    <v-btn v-else
                        style="display: block;"
                        rounded="sm"
                        :color="simGraph ? 'primary' : 'default'"
                        icon="mdi-family-tree"
                        density="comfortable"
                        @click="simGraph = !simGraph"
                        variant="tonal">
                    </v-btn>
                </div>

                <div v-if="allowEdit" class="d-flex flex-end" :class="{ 'flex-column': !vertical }">
                    <v-btn class="mr-2" @click="app.setAddTag(-1)"
                        prepend-icon="mdi-plus"
                        rounded="sm"
                        :style="{ maxWidth: vertical ? null : '20px' }"
                        :block="!vertical"
                        density="comfortable"
                        variant="tonal">
                        <span v-if="vertical">new tag</span>
                    </v-btn>
                    <div class="d-flex" :class="{ 'flex-column': !vertical }">
                        <v-btn
                            :class="{ 'mt-1': !vertical }"
                            :color="tagChanges ? 'error' : 'default'"
                            :style="{ maxWidth: vertical ? null : '20px' }"
                            :disabled="!tagChanges"
                            :block="!vertical"
                            density="comfortable"
                            @click="onCancel"
                            variant="tonal"
                            prepend-icon="mdi-delete">
                            <span v-if="vertical">discard</span>
                        </v-btn>
                        <v-btn
                            :class="{ 'ml-2': vertical, 'mt-1': !vertical }"
                            variant="tonal"
                            density="comfortable"
                            :style="{ maxWidth: vertical ? null : '20px' }"
                            :block="!vertical"
                            :color="tagChanges ? 'primary' : 'default'"
                            :disabled="!tagChanges || !allowEdit"
                            @click="saveChanges"
                            prepend-icon="mdi-sync">
                            <span v-if="vertical">sync</span>
                        </v-btn>
                    </div>
                </div>
            </div>

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

            <div v-else>
                <TreeMap
                    :data="allTags"
                    :time="time"
                    dot-attr="evidence"
                    valid-attr="valid"
                    collapsible
                    :selected="itemTagsIds"
                    :frozen="itemTagsFrozenIds"
                    @click="toggleTag"
                    @right-click="toggleContext"
                    @hover-dot="onHoverEvidence"
                    @click-dot="(e, _event, list, idx) => app.setShowEvidence(e.id, list, idx)"
                    @right-click-dot="contextEvidence"
                    :width="realWidth"
                    :height="realHeight"/>
            </div>
        </div>

        <CrowdSimilarities v-model="simGraph" :target="item"/>
    </div>
</template>

<script setup>
    import { pointer } from 'd3';
    import TagTiles from '@/components/tags/TagTiles.vue';
    import { onMounted, ref, computed, watch } from 'vue';
    import { useToast } from "vue-toastification";
    import { OBJECTION_ACTIONS, useApp } from '@/store/app';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings'
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import TreeMap from '../vis/TreeMap.vue';
    import { useTimes } from '@/store/times';
    import { updateItemTags } from '@/use/data-api';
    import { useTooltip } from '@/store/tooltip';
    import { useWindowSize } from '@vueuse/core';
    import CrowdSimilarities from './CrowdSimilarities.vue';

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
    const tt = useTooltip()

    const { allowEdit } = storeToRefs(app)
    const { addTagsView } = storeToRefs(settings)
    const vertical = computed(() => wSize.width.value < wSize.height.value)

    const wSize = useWindowSize()
    const realWidth = computed(() => props.width + (vertical.value ? 10 : -35))
    const realHeight = computed(() => props.height + (vertical.value ? -100 : -50))

    const simGraph = ref(false)
    const time = ref(Date.now())
    const delTags = ref([]);
    const addTags = ref([])
    const tagChanges = computed(() => delTags.value.length > 0 || addTags.value.length > 0)

    const itemTagObj = computed(() => {
        const obj = {};
        if (props.item && props.item.tags) {
            props.item.tags.forEach(t => obj[t.tag_id] = true);
            addTags.value.forEach(t => obj[t.tag_id] = true)
        }
        return obj;
    })

    const itemTags = ref([])
    const itemTagsFrozen = ref([])
    const itemTagsIds = computed(() => itemTags.value.map(d => d.tag_id))
    const itemTagsFrozenIds = computed(() => itemTagsFrozen.value.map(d => d.tag_id))
    const leafTags = computed(() => allTags.value.filter(d => d.is_leaf === 1))
    const allTags = ref([])

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
        if (!props.item) return false;
        const tagName = tag.name.toLowerCase();
        return props.item.tags.find(d => {
            return d.created_by === app.activeUserId &&
                (tag.id ? d.tag_id == tag.id : d.name.toLowerCase() === tagName)
        }) !== undefined
    }
    function itemHadTag(tag) {
        if (!props.item) return false;
        const tagName = tag.name.toLowerCase();
        return delTags.value.find(d => tag.id ? d.tag_id == tag.id : d.name.toLowerCase() === tagName) !== undefined
    }

    function onHoverEvidence(d, event) {
        if (d) {
            const [mx, my] = pointer(event, document.body)
            tt.hide()
            tt.showEvidence(d.id, mx, my)
        } else {
            tt.hideEvidence()
        }
    }
    function contextEvidence(d, event) {
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "evidence", d.id,
            mx, my,
            null, null,
            CTXT_OPTIONS.evidence
        )
    }

    function toggleTag(tag) {
        if (!allowEdit.value) return;
        if (props.item && tag) {
            if (tag.is_leaf === 0) {
                // remove this tag if it exists on the item
                if (itemHasTag(tag, true)) {
                    deleteTag(tag.id);
                    toast.info("removed invalid non-leaf tag " + tag.name)
                    return;
                }

                const children = allTags.value.filter(d => d.id !== tag.id && d.path.includes(tag.id));
                const addAll = children.some(d => d.is_leaf === 1 && !itemHasTag(d))
                children.forEach(d => {
                    const exists = itemHasTag(d);
                    if (addAll && d.is_leaf === 1 && (!exists || itemHadTag(d))) {
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
        if (!props.item) return;

        const id = tag.tag_id ? tag.tag_id : tag.id;
        const [mx, my] = pointer(event, document.body)

        if (itemTagsIds.value.includes(id)) {
            settings.setRightClick(
                "tag", id,
                mx, my,
                tag.name,
                { item: props.item.id, action: OBJECTION_ACTIONS.REMOVE },
                CTXT_OPTIONS.items_tagged
            );
        } else {
            settings.setRightClick(
                "tag", id,
                mx, my,
                tag.name,
                { item: props.item.id, action: OBJECTION_ACTIONS.ADD },
                CTXT_OPTIONS.items_untagged
            );
        }
    }
    function addTag(tag) {
        if (!allowEdit.value) return;
        if (props.item && tag) {

            if (itemHasTag(tag)) {
                toast.error(`${tag.name} already tagged`)
                return;
            }
            if (tag.is_leaf === 0) {
                toast.error(`${tag.name} is not a leaf node`)
                return;
            }

            const inDel = delTags.value.findIndex(d => d.tag_id === tag.id && d.created_by === app.activeUserId);
            props.item.tags.push({
                name: tag.name,
                description: tag.description,
                created_by: app.activeUserId,
                tag_id: tag.id ? tag.id : null,
                unsaved: inDel < 0
            });

            if (inDel >= 0) {
                delTags.value.splice(inDel, 1)
            } else {
                addTags.value.push(Object.assign({}, props.item.tags.at(-1)))
            }
            readSelectedTags()

            emit("add", props.item.tags.at(-1))
        }
    }
    function deleteTag(tagId) {
        if (!allowEdit.value) return;
        if (props.item && tagId) {
            const idx = props.item.tags.findIndex(t => t.tag_id === tagId && t.created_by === app.activeUserId);
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
                toast.warning("tag does not exist for current user")
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
        }
    }
    async function saveChanges() {
        if (!allowEdit.value) return;
        if (tagChanges.value) {
            emit("save", props.item);
            try {
                await updateItemTags(props.item, app.activeUserId, app.currentCode)
                toast.success("updated tags for " + props.item.name)
                times.needsReload("datatags")
                delTags.value = [];
                addTags.value = [];
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
            itemTags.value = app.showAllUsers ?
                props.item.tags :
                props.item.tags.filter(d => d.created_by === app.activeUserId)

            const s = new Set(props.item.tags.filter(d => d.created_by === app.activeUserId).map(d => d.tag_id))
            itemTagsFrozen.value = app.showAllUsers ?
                props.item.tags.filter(d => d.created_by !== app.activeUserId && !s.has(d.tag_id)) :
                []
            }
    }
    function readTags() {
        if (props.item) {
            const ev = DM.getData("evidence", false)
            allTags.value = DM.getData(props.allDataSource ? props.allDataSource : "tags", false)
                .map(t => {
                    const obj = Object.assign({}, t)
                    obj.evidence = ev.filter(d => d.item_id === props.item.id && d.tag_id === t.id)
                    return obj
                })
        } else {
            allTags.value = []
        }
    }
    function readAllTags() {
        readTags();
        readSelectedTags();
        time.value = Date.now()
    }

    defineExpose({ discardChanges })

    onMounted(readAllTags)

    watch(() => ([times.all, props.item?.id]), () => tt.hideEvidence(), { deep: true })
    watch(() => Math.max(times.tags, times.tagging, times.evidence), readAllTags)
    watch(() => app.userTime, readSelectedTags);
    watch(() => Math.max(times.all, times.datatags, times.tagging), () => {
        if (props.item) {
            if (tagChanges.value) {
                delTags.value.forEach(d => {
                    const idx = props.item.tags.findIndex(dd => dd.tag_id === d.tag_id)
                    if (idx >= 0) props.item.tags.splice(idx, 1)
                })
                addTags.value.forEach(d => {
                    const idx = props.item.tags.findIndex(dd => dd.tag_id === d.tag_id)
                    if (idx < 0) props.item.tags.push(d)
                })
            }
            readSelectedTags()
        }
    })

</script>