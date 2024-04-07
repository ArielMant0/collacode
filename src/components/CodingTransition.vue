<template>
    <div ref="wrapper" v-if="oldCode && newCode">
        <h3 style="text-align: center;" class="mt-4 mb-4">TRANSITION FROM {{ app.getCodeName(oldCode) }} TO {{ app.getCodeName(newCode) }}</h3>

        <v-sheet class="d-flex justify-center mb-2">
            <v-tooltip text="add children to selected tags" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-plus" color="primary" @click="openPrompt"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="group selected tags" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-group" color="primary" @click="groupTags"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="add as children to first selected tag" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-graph" color="primary" @click="addAsChildren"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="select all tags" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-select-all" color="secondary" @click="selectAll"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="deselect tags" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-select" color="secondary" @click="resetSelection"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="show tag assignments" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" :icon="showAssigned ? 'mdi-eye' : 'mdi-eye-off'" color="secondary" @click="showAssigned = !showAssigned"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="delete selected tags" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-delete" color="error" @click="deleteTags"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="tag assignments mode" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn-toggle v-bind="props" v-model="assigMode" :disabled="!showAssigned" color="primary" density="compact" rounded="sm" divided @update:model-value="resetSelection">
                        <v-btn value="add" class="pl-4 pr-4" icon="mdi-link"></v-btn>
                        <v-btn value="delete" class="pl-4 pr-4" icon="mdi-link-off"></v-btn>
                    </v-btn-toggle>
                </template>
            </v-tooltip>
        </v-sheet>

        <InteractiveTree v-if="data.tagTreeData"
            :data="data.tagTreeData"
            :assignment="tagAssignObj"
            assign-attr="assigned"
            :show-assigned="showAssigned"
            :width="wrapperSize.width.value"
            @click="onClickTag"
            @click-assign="onClickOriginalTag"/>

        <v-dialog v-model="tagPrompt"
            min-width="200"
            width="auto"
            elevation="8"
            density="compact"
            >
            <v-card>
            <v-card-text>
                <div class="d-flex justify-center text-caption">
                    Add
                    <input v-model="numChildren"
                        style="max-width: 40px; background-color: #eee; text-align: right;"
                        type="number"
                        min="1"
                        step="1"
                        density="compact"
                        class="ml-1 mr-1"/>
                    child(ren) to {{ data.selectedTags.size }} tags?
                </div>
            </v-card-text>

            <v-card-actions>
                <v-btn class="ms-2" color="warning" @click="closePrompt">cancel</v-btn>
                <v-btn class="ms-auto" color="primary" @click="addChildren">okay</v-btn>
            </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup>
    import { onMounted, reactive, computed } from 'vue';
    import InteractiveTree from './vis/InteractiveTree.vue';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';
    import { storeToRefs } from 'pinia';
    import { useElementSize } from '@vueuse/core';

    const app = useApp();
    const loader = useLoader();
    const toast = useToast();

    const wrapper = ref(null);
    const wrapperSize = useElementSize(wrapper);

    const props = defineProps({
        oldCode: {
            type: Number,
            required: true
        },
        newCode: {
            type: Number,
            required: true
        },
    })

    const tagPrompt = ref(false);
    const numChildren = ref(2);

    const assigMode = ref(undefined);
    const showAssigned = ref(true);

    const { dataLoading } = storeToRefs(app);

    let actionQueue = [];
    const data = reactive({

        tags: [],
        tagsOld: [],

        tagTreeData: null,
        tagAssign: [],

        selectedTags: new Set(),
        selectedOldTag: null,
        selectedNewTag: null
    });

    const tagAssignObj = computed(() => {
        const obj = {};
        data.tagsOld.forEach(d => {
            const a = data.tagAssign.find(dd => dd.old_tag === d.id)
            if (!a) return;
            obj[d.id] = {
                name: d.name,
                description: a.description,
                new_tag: a.new_tag,
            };
        })
        return obj;
    })
    const selectedTagsData = computed(() => {
        if (data.selectedTags.size > 0) {
            return data.tags.filter(d => data.selectedTags.has(d.id))
        }
        return [];
    });

    function readData(performActions=false) {
        if (!props.oldCode || !props.newCode ||
            !DM.hasData("tags") || !DM.hasData("datatags") ||
            !DM.hasData("tag_old") || !DM.hasData("tag_assignments")
        ) {
            return;
        }

        data.tags = DM.getData("tags", false)
        data.tagsOld = DM.getData("tag_old", false);
        data.tagAssign = DM.getData("tag_assignments");
        const dts = DM.getData("datatags", false)

        data.tags.forEach(d => {
            if (d.parent === null) {
                d.parent = -1;
            }
            d.assigned = data.tagAssign.filter(dd => dd.new_tag === d.id).map(dd => dd.old_tag)
            const numDTS = dts.filter(dd => dd.tag_id === d.id).length
            d.valid = d.is_leaf === 0 && numDTS === 0 || d.is_leaf === 1 && numDTS > 0
        })

        data.tagTreeData = [{ id: -1, name: "root", parent: null }].concat(data.tags)

        if (DM.hasFilter("tags", "id")) {
            data.selectedTags = new Set(DM.getFilter("tags", "id"));
        }

        if (performActions && actionQueue.length > 0) {
            let action = actionQueue.pop();
            do {
                switch(action.action) {
                    case "group tags":
                        addTagsToGroup(action.values.name, action.values.tags);
                        break;
                }
                action = actionQueue.pop();
            } while (action)
        }
    }

    function onClickTag(tag) {

        if (!tag) return;

        if (assigMode.value) {
            data.selectedNewTag = tag.id;
            if (data.selectedOldTag) {
                switch(assigMode.value) {
                    case "add":
                        assignTag(data.selectedOldTag, data.selectedNewTag);
                        break;
                    case "delete":
                        deleteTagAssignment(data.selectedOldTag, data.selectedNewTag);
                        break;
                }
            }
        }

        if (data.selectedTags.has(tag.id)) {
            data.selectedTags.delete(tag.id);
        } else {
            data.selectedTags.add(tag.id);
        }

        if (data.selectedTags.size > 0) {
            const sels = Array.from(data.selectedTags.values());
            DM.setFilter("tags", "id", sels)
            app.selectByAttr("tags", tags => {
                return data.selectedTags.has(-1) || tags && tags.some(d => data.selectedTags.has(d.tag_id) || d.path.some(p => data.selectedTags.has(p)))
            })
        } else {
            DM.removeFilter("tags", "id")
            DM.removeFilter("games", "tags")
            app.selectionTime = Date.now();
        }
    }

    function onClickOriginalTag(tag) {

        if (assigMode.value) {
            data.selectedOldTag = tag.id;
            if (data.selectedNewTag) {
                switch(assigMode.value) {
                    case "add":
                        assignTag(data.selectedOldTag, data.selectedNewTag);
                        break;
                    case "delete":
                        deleteTagAssignment(data.selectedOldTag, data.selectedNewTag);
                        break;
                }
            }
        }
        if (data.selectedOldTag) {
            DM.setFilter("tags_old", "id", [data.selectedOldTag])
        } else {
            DM.removeFilter("tags_old", "id")
        }
        app.selectionTime = Date.now();
    }

    function selectAll() {
        data.selectedTags = new Set(data.tags.map(d => d.id));
        const sels = Array.from(data.selectedTags.values());
        DM.setFilter("tags", "id", sels)
        app.selectByAttr("tags", tags => {
            return data.selectedTags.has(-1) || tags && tags.some(d => data.selectedTags.has(d.tag_id) || d.path.some(p => data.selectedTags.has(p)))
        })
    }

    function addChildren() {
        const num = Number.parseInt(numChildren.value);
        const rows = [];
        const now = Date.now();

        if (num > 0) {

            if (data.selectedTags.size > 0) {

                // add to root
                if (selectedTagsData.value.length === 0) {
                    for (let i = 0; i < num; ++i) {
                        rows.push({
                            name: "new tag "+(i+1),
                            description: "",
                            code_id: props.newCode,
                            parent: null,
                            is_leaf: true,
                            created: now,
                            created_by: app.activeUserId
                        })
                    }
                } else {
                    selectedTagsData.value.forEach(tag => {
                        const name = tag.name;
                        for (let i = 0; i < num; ++i) {
                            rows.push({
                                name: name+" child "+(i+1),
                                description: "",
                                code_id: props.newCode,
                                parent: tag.id,
                                is_leaf: true,
                                created: now,
                                created_by: app.activeUserId
                            })
                        }
                    })
                }
                loader.post("add/tags", { rows: rows })
                    .then(() => {
                        toast.success("created " + rows.length + " children")
                        resetSelection();
                        app.needsReload("transition")
                    })
            }
        }
        tagPrompt.value = false;
    }

    function deleteTags() {
        if (data.selectedTags.size > 0) {
            const ids = Array.from(data.selectedTags.values())
            loader.post("delete/tags", { ids: ids })
                .then(() => {
                    toast.success("deleted " + ids.length + " tag(s)")
                    app.needsReload("transition")
                })
            resetSelection();
        }
    }
    async function deleteTagAssignment(oldTag, newTag) {
        const old = data.tagAssign.find(d => d.old_tag == oldTag && d.new_tag == newTag);
        if (!old) {
            toast.error("tag assignment does not exist")
            return;
        }
        await loader.post("delete/tag_assignments", { ids: [old.id]});
        data.selectedOldTag = null;
        data.selectedNewTag = null;
        DM.removeFilter("tags_old", "id")
        app.selectionTime = Date.now();

        toast.success(`deleted tag assignment`);
        app.needsReload("tag_assignments");
    }
    function getTagFromId(id) {
        return data.tags.find(d => d.id == id)
    }
    async function groupTags() {
        if (data.selectedTags.size > 0) {
            const sels = Array.from(data.selectedTags.values());
            const firstParent = getTagFromId(sels[0]).parent;
            const parent = {
                name: "new tag subtree",
                description: "",
                code_id: props.newCode,
                created: Date.now(),
                created_by: app.activeUserId,
                is_leaf: false,
                parent: sels.every(d => getTagFromId(d).parent === firstParent) ? firstParent : null
            }
            actionQueue.push({
                action: "group tags",
                values: {
                    tags: sels,
                    name: "new tag subtree",
                }
            });
            await loader.post("add/tags", { rows: [parent] });
            app.needsReload("transition")
        }
        resetSelection();
    }
    async function addAsChildren() {
        if (data.selectedTags.size > 0) {
            const vals = Array.from(data.selectedTags.values())
            const first = data.tags.find(d => d.id === vals[0]);
            if (!first) {
                toast.error("cannot find first selected tag with id" + vals[0])
                return;
            }

            const tags = [];
            vals.forEach(d => {
                if (d === first.id) return;
                const t = data.tags.find(dd => dd.id === d)
                tags.push({
                    id: t.id,
                    name: t.name,
                    description: t.description,
                    parent: first.id,
                    is_leaf: t.is_leaf
                });
            })

            await loader.post("update/tags", { rows: tags });
            resetSelection();

            app.needsReload("transition")
            toast.success("updated " + tags.length + "tag(s)")
        }
    }

    function resetSelection() {
        data.selectedTags.clear();
        DM.removeFilter("tags", "id")
        DM.removeFilter("tags_old", "id")
        DM.removeFilter("games", "tags")
        app.selectionTime = Date.now();
    }

    async function addTagsToGroup(name, tags) {
        if (tags.length === 0 || !name) return;

        const parent = data.tags.find(d => d.name === name);
        if (!parent) {
            console.error("cannot find parent for grouping")
            return;
        }
        await loader.post("update/tags", { rows: tags.map(d => {
                const tag = data.tags.find(t => t.id === d);
                return {
                    id: d,
                    name: tag.name,
                    description: tag.description,
                    parent: parent.id,
                    is_leaf: tag.is_leaf
                }
            })}
        );
        toast.success(`updated ${tags.length} tags`);
        app.needsReload("transition");
    }

    async function assignTag(oldTag, newTag) {
        if (!oldTag || !newTag) {
            toast.error("one of the tags is missing")
            return;
        }
        await loader.post("add/tag_assignments", { rows: [{
            old_tag: oldTag,
            new_tag: newTag,
            old_code: props.oldCode,
            new_code: props.newCode,
            description: "",
            created: Date.now()
        }]});
        data.selectedOldTag = null;
        data.selectedNewTag  = null;
        DM.removeFilter("tags_old", "id")
        app.selectionTime = Date.now();

        toast.success(`updated tag assignment`);
        app.needsReload("tag_assignments");
    }


    function openPrompt() { tagPrompt.value = true; }
    function closePrompt() { tagPrompt.value = false; }

    onMounted(readData)

    watch(() => ([dataLoading.value._all, dataLoading.value.transition]), function() {
        if (dataLoading.value._all === false && dataLoading.value.transition === false) {
            readData(true);
        }
    }, { deep: true });
    watch(() => ([
        dataLoading.value.codes,
        dataLoading.value.tags,
        dataLoading.value.tags_old,
        dataLoading.value.tag_assignments,
    ]), function(val) {
        if (val && (val.every(d => d === false) || val[3] === false)) {
            readData();
        }
    }, { deep: true });

</script>