<template>
    <div ref="wrapper" v-if="oldCode && newCode">
        <h3 style="text-align: center;" class="mt-4 mb-4">TRANSITION FROM {{ app.getCodeName(oldCode) }} TO {{ app.getCodeName(newCode) }}</h3>

        <TransitionToolbar
            @add="openChildrenPrompt"
            @children="addAsChildren"
            @group="groupTags"
            @select-all="selectAll"
            @deselect-all="resetSelection"
            @delete="openDeletePromp"
            @split="openSplitPrompt"
            @merge="openMergePrompt"
            @tree-layout="value => treeLayout = value"
            @show-links="value => showAssigned = value"
            @assign-mode="value => assigMode = value"
            />

        <InteractiveTree v-if="data.tagTreeData"
            :data="data.tagTreeData"
            :assignment="tagAssignObj"
            assign-attr="assigned"
            :show-assigned="showAssigned"
            :width="wrapperSize.width.value"
            :time="dataTime"
            :layout="treeLayout"
            @click="onClickTag"
            @click-assign="onClickOriginalTag"/>

        <MiniDialog v-model="addChildrenPrompt" @cancel="closeChildrenPrompt" @submit="addChildren">
            <template v-slot:text>
                <p class="text-center text-caption">
                    Add
                    <input v-model="numChildren"
                        style="max-width: 40px; background-color: #eee; text-align: right;"
                        type="number"
                        min="1"
                        step="1"
                        density="compact"
                        class="ml-1 mr-1"/>
                    child(ren) to tag
                    <b v-if="selectedTagsData.length > 0">{{ selectedTagsData[0].name }}</b>?
                </p>
                <div class="mt-2">
                    <v-text-field v-for="i in numChildren"
                        :key="'child_'+i"
                        hide-details
                        hide-spin-buttons
                        class="mt-1"
                        :label="'Name for child '+i"
                        :placeholder="'child' + i"
                        @update:model-value="val => tagNames[i] = val"
                        density="compact"/>
                </div>
            </template>
        </MiniDialog>

        <MiniDialog v-model="deletePrompt" @cancel="closeDeletePromp" @submit="deleteTags" submit-text="delete" submit-color="error">
            <template v-slot:text>
                <p class="text-center text-caption">
                    Delete tags <b v-if="selectedTagsData.length > 0">{{ selectedTagsData.map(d => d.name).join(", ") }}</b>?
                </p>
            </template>
        </MiniDialog>

        <MiniDialog v-model="splitPrompt" @cancel="closeSplitPrompt" @submit="splitTag">
            <template v-slot:text>
                <p class="text-center text-caption">
                    Split tag <b v-if="selectedTagsData.length > 0">{{ selectedTagsData[0].name }}</b> into
                    <input v-model="numChildren"
                        style="max-width: 40px; background-color: #eee; text-align: right;"
                        type="number"
                        min="1"
                        step="1"
                        density="compact"
                        class="ml-1 mr-1"/>?
                </p>
                <div class="mt-2">
                    <v-text-field v-for="i in numChildren"
                        :key="'child_'+i"
                        hide-details
                        hide-spin-buttons
                        class="mt-1"
                        :label="'Name for child '+i"
                        :placeholder="'child' + i"
                        @update:model-value="val => tagNames[i] = val"
                        density="compact"/>
                </div>
            </template>
        </MiniDialog>

        <MiniDialog v-model="mergePrompt" @cancel="closeMergePrompt" @submit="mergeTags">
            <template v-slot:text>
                <p class="text-center text-caption">
                    Merge tags <b v-if="selectedTagsData.length > 0">{{ selectedTagsData.map(d => d.name).join(", ") }}</b>?
                </p>
                <div class="mt-2">
                    <v-text-field
                        key="merge_name"
                        hide-details
                        hide-spin-buttons
                        class="mt-1"
                        label="Tag Name"
                        @update:model-value="val => tagNames.name = val"
                        density="compact"/>
                    <v-textarea
                        key="merge_desc"
                        hide-details
                        hide-spin-buttons
                        class="mt-1"
                        label="Tag Description"
                        @update:model-value="val => tagNames.desc = val"
                        density="compact"/>
                </div>
            </template>
        </MiniDialog>
    </div>
</template>

<script setup>
    import TransitionToolbar from './TransitionToolbar.vue';
    import { onMounted, reactive, computed, ref } from 'vue';
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

    const deletePrompt = ref(false);
    const splitPrompt = ref(false);
    const mergePrompt = ref(false);
    const addChildrenPrompt = ref(false);
    const numChildren = ref(2);

    const treeLayout = ref("cluster")
    const assigMode = ref(undefined);
    const showAssigned = ref(true);
    const dataTime = ref(Date.now())

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
    const tagNames = reactive({})

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

        const tagTreeData =[{ id: -1, name: "root", parent: null, valid: true }].concat(data.tags)
        // tagTreeData.sort((a, b) => {
        //     const nameA = a.name.toLowerCase(); // ignore upper and lowercase
        //     const nameB = b.name.toLowerCase(); // ignore upper and lowercase
        //     if (nameA < nameB) { return 1; }
        //     if (nameA > nameB) { return -1; }
        //     // names must be equal
        //     return 0;
        //     })
        data.tagTreeData = tagTreeData

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

        dataTime.value = Date.now()
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
            app.selectByTag(sels);
        } else {
            app.selectByTag();
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
        app.selectByTag(sels);
    }

    function splitTag() {
        const num = Number.parseInt(numChildren.value);
        const now = Date.now();

        if (num > 0 && selectedTagsData.value.length > 0) {

            const names = [];
            const tag = selectedTagsData.value[0];
            for (let i = 0; i < num; ++i) {
                names.push(tagNames[(i+1)] ? tagNames[(i+1)] : tag.name+" child "+(i+1))
            }

            const nameSet = new Set(names)
            if (nameSet.size < names.length || data.tags.some(d => nameSet.has(d.name))) {
                toast.error("names must be unique")
                return;
            }

            loader.post("split/tags", { rows: [{ id: tag.id, names: names, created_by: app.activeUserId, created: now }] })
                .then(() => {
                    toast.success("split tag into " + names.length + " children")
                    resetSelection();
                    app.needsReload("transition")
                })
        }
        splitPrompt.value = false;
    }

    function mergeTags() {
        const now = Date.now();

        if (selectedTagsData.value.length > 0) {

            if (!tagNames.name) {
                toast.error("missing new tag name")
                return;
            }
            const obj = {
                name: tagNames.name,
                description: tagNames.desc,
                created: now,
                created_by: app.activeUserId,
                code_id: props.newCode,
                ids: []
            }
            selectedTagsData.value.forEach(tag => obj.ids.push(tag.id))
            if (data.tags.some(d => d.name === obj.name)) {
                toast.error("name must be unique")
                return;
            }

            loader.post("merge/tags", { rows: [obj] })
                .then(() => {
                    toast.success("merged tags into tag " + tagNames.name)
                    resetSelection();
                    tagNames.name = "";
                    tagNames.desc = "";
                    app.needsReload("transition")
                })
        }
        mergePrompt.value = false;
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
                            name: tagNames[(i+1)] ? tagNames[(i+1)] : "new tag "+(i+1),
                            description: "",
                            code_id: props.newCode,
                            parent: null,
                            is_leaf: true,
                            created: now,
                            created_by: app.activeUserId
                        })
                    }
                } else {
                    const tag = selectedTagsData.value[0]
                    const name = tag.name;
                    for (let i = 0; i < num; ++i) {
                        rows.push({
                            name: tagNames[(i+1)] ? tagNames[(i+1)] : name+" child "+(i+1),
                            description: "",
                            code_id: props.newCode,
                            parent: tag.id,
                            is_leaf: true,
                            created: now,
                            created_by: app.activeUserId
                        })
                    }
                }

                const nameSet = new Set(rows.map(d => d.name))
                if (nameSet.size < rows.length || data.tags.some(d => nameSet.has(d.name))) {
                    toast.error("names must be unique")
                    return;
                }

                loader.post("add/tags", { rows: rows })
                    .then(() => {
                        toast.success("created " + rows.length + " children")
                        resetSelection();
                        app.needsReload("transition")
                    })
            }
        }
        addChildrenPrompt.value = false;
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
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
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

    function openDeletePromp() { deletePrompt.value = true; }
    function closeDeletePromp() { deletePrompt.value = false; }

    function openChildrenPrompt() { addChildrenPrompt.value = true; }
    function closeChildrenPrompt() { addChildrenPrompt.value = false; }

    function openSplitPrompt() { splitPrompt.value = true; }
    function closeSplitPrompt() { splitPrompt.value = false; }

    function openMergePrompt() { mergePrompt.value = true; }
    function closeMergePrompt() { mergePrompt.value = false; }

    onMounted(readData)

    watch(() => ([dataLoading.value._all, dataLoading.value.transition]), function() {
        if (dataLoading.value._all === false && dataLoading.value.transition === false) {
            readData(true);
        }
    }, { deep: true });
    watch(() => app.selectionTime, function() {
        // just do it everytime, should not be a problem if we do it twice
        data.selectedTags = new Set(DM.getFilter("tags", "id"))
    })
    watch(() => ([
        dataLoading.value.codes,
        dataLoading.value.tags,
        dataLoading.value.tags_old,
        dataLoading.value.datatags,
        dataLoading.value.tag_assignments,
    ]), function(val) {
        if (val && (val.every(d => d === false) || val[3] === false || val[4] === false)) {
            readData();
        }
    }, { deep: true });

</script>