<template>
    <div ref="wrapper" style="width: 100%;">
        <div style="width: 100%" class="d-flex justify-center">
            <TransitionToolbar v-if="edit"
                @add="openChildrenPrompt"
                @children="addAsChildren"
                @group="openGroupPrompt"
                @select-all="selectAll"
                @deselect-all="resetSelection"
                @delete="openDeletePrompt"
                @split="openSplitPrompt"
                @merge="openMergePrompt"
                @tree-layout="value => treeLayout = value"
                @show-links="value => showAssigned = value"
                @assign-mode="value => assigMode = value"
                />
            <ExplorationToolbar v-else/>
        </div>

        <h3 v-if="includeTitle" style="text-align: center; margin-top: 50px;" class="mb-4">
            Transition from <i>{{ app.getCodeName(oldCode) }}</i> to <i>{{ app.getCodeName(newCode) }}</i>
        </h3>

        <div v-if="data.tagTreeData" style="text-align: center;">
            <TreeMap v-if="treeLayout == 'treemap'"
                :data="data.tagTreeData"
                :time="dataTime"
                :selected="Array.from(data.selectedTags.values())"
                :width="wrapperSize.width.value-10"
                :height="1000"
                collapsible
                valid-attr="valid"
                @click="onClickTag"
                @right-click="onRightClickTag"/>
            <RadialTree v-else-if="treeLayout == 'radial'"
                :data="data.tagTreeData"
                :size="1200"
                :time="dataTime"
                @click="onClickTag"
                @right-click="onRightClickTag"/>
            <InteractiveTree v-else
                :data="data.tagTreeData"
                :assignment="tagAssignObj"
                assign-attr="assigned"
                :show-assigned="showAssigned"
                :width="wrapperSize.width.value"
                :time="dataTime"
                :layout="treeLayout"
                :radius="5"
                @click="onClickTag"
                @click-assign="onClickOriginalTag"
                @right-click="onRightClickTag"/>
        </div>

        <MiniDialog v-model="addChildrenPrompt" @cancel="closeChildrenPrompt" @submit="addChildren">
            <template v-slot:text>
                <p class="text-center">
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

        <MiniDialog v-model="deletePrompt" @cancel="closeDeletePrompt" @submit="deleteTags" submit-text="delete" submit-color="error">
            <template v-slot:text>
                <div class="d-flex flex-column align-center">
                    <p class="mb-2">
                        Delete tags <b v-if="selectedTagsData.length > 0">{{ selectedTagsData.map(d => d.name).join(", ") }}</b>?
                    </p>
                    <v-checkbox-btn v-model="deleteChildren" density="compact" hide-details hide-spin-buttons label="delete children"/>
                </div>
            </template>
        </MiniDialog>

        <MiniDialog v-model="splitPrompt" @cancel="closeSplitPrompt" @submit="splitTag">
            <template v-slot:text>
                <p class="text-center">
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

        <MiniDialog v-model="mergePrompt" @cancel="closeMergePrompt" @submit="mergeTag">
            <template v-slot:text>
                <p class="text-center">
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
                    <v-select v-model="tagNames.parent"
                        key="merge_parent"
                        hide-details
                        hide-spin-buttons
                        class="mt-1"
                        label="Tag Parent"
                        :items="data.tags"
                        item-title="name"
                        item-value="id"
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

        <MiniDialog v-model="groupPrompt" @cancel="closeGroupPrompt" @submit="groupTags">
            <template v-slot:text>
                <p class="text-center">
                    Group tags <b v-if="selectedTagsData.length > 0">{{ selectedTagsData.map(d => d.name).join(", ") }}</b>?
                </p>
                <div class="mt-2">
                    <v-text-field
                        key="group_name"
                        hide-details
                        hide-spin-buttons
                        class="mt-1"
                        label="Group Tag Name"
                        @update:model-value="val => tagNames.name = val"
                        density="compact"/>
                    <v-select v-model="tagNames.parent"
                        key="group_parent"
                        hide-details
                        hide-spin-buttons
                        class="mt-1"
                        label="Group Tag Parent"
                        :items="data.tags"
                        item-title="name"
                        item-value="id"
                        density="compact"/>
                    <v-textarea
                        key="group_desc"
                        hide-details
                        hide-spin-buttons
                        class="mt-1"
                        label="Group Tag Description"
                        @update:model-value="val => tagNames.desc = val"
                        density="compact"/>
                </div>
            </template>
        </MiniDialog>
    </div>
</template>

<script setup>
    import { pointer } from 'd3';
    import TransitionToolbar from './TransitionToolbar.vue';
    import { onMounted, reactive, computed, ref, watch } from 'vue';
    import InteractiveTree from './vis/InteractiveTree.vue';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';
    import { storeToRefs } from 'pinia';
    import { useElementSize } from '@vueuse/core';
    import { getSubtree, deleteTags as deleteTagsFunc, addTags, splitTags, mergeTags, deleteTagAssignments, updateTags, addTagAssignments } from '@/use/utility';
    import ExplorationToolbar from './ExplorationToolbar.vue';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import TreeMap from './vis/TreeMap.vue';
    import RadialTree from './vis/RadialTree.vue';

    const app = useApp();
    const settings = useSettings();
    const loader = useLoader();
    const toast = useToast();
    const times = useTimes()

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
        edit: {
            type: Boolean,
            default: true
        },
        includeTitle: {
            type: Boolean,
            default: true
        }
    })

    const deletePrompt = ref(false);
    const splitPrompt = ref(false);
    const mergePrompt = ref(false);
    const addChildrenPrompt = ref(false);
    const groupPrompt = ref(false);

    const numChildren = ref(2);
    const deleteChildren = ref(false);

    const assigMode = ref(undefined);
    const showAssigned = ref(false);
    const dataTime = ref(Date.now())

    const { treeLayout } = storeToRefs(settings)

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

    async function readData(processActions=false) {
        if (!props.oldCode || !props.newCode ||
            !DM.hasData("tags") || !DM.hasData("datatags") ||
            !DM.hasData("tags_old") || !DM.hasData("tag_assignments")
        ) {
            console.warn("missing data for transition view")
            return;
        }

        data.tags = DM.getData("tags", false)
        data.tagsOld = DM.getData("tags_old", false);
        data.tagAssign = DM.getData("tag_assignments");
        const dts = DM.getData("datatags", false)

        data.tags.forEach(d => {
            if (d.parent === null) {
                d.parent = -1;
            }
            d.assigned = data.tagAssign.filter(dd => dd.new_tag === d.id).map(dd => dd.old_tag)
        })

        data.tagTreeData = [{ id: -1, name: "root", parent: null, valid: true }].concat(data.tags)
        data.selectedTags = DM.getSelectedIds("tags")

        if (processActions) {

            const toAdd = [];
            let action = app.popAction("trans")

            while (action) {
                switch(action.action) {
                    case "group tags":
                        const result = await addTagsToGroup(action.values.name, action.values.tags);
                        if (!result) {
                            toAdd.push(action);
                        }
                        break;
                }
                action = app.popAction("trans")
            }
            toAdd.forEach(d => app.addAction("trans", d.action, d.values));
        }
        dataTime.value = Date.now()
    }
    function updateDataTags() {
        if (!data.tagTreeData) return;
        const tags = DM.getData("tags", false)
        data.tagTreeData.forEach(d => d.valid = tags.find(t => t.id === d.id).valid || false)
        dataTime.value = Date.now()
    }

    function onClickTag(tag) {

        if (!tag) return;

        if (props.edit && assigMode.value) {
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

        if (!tag) return;

        if (props.edit && assigMode.value) {
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
    }

    function onRightClickTag(tag, event) {
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "tag", tag.id,
            mx + 10,
            my + 10,
            null,
            CTXT_OPTIONS.tag,
        )
    }

    function selectAll() {
        data.selectedTags = new Set(data.tags.map(d => d.id));
        const sels = Array.from(data.selectedTags.values());
        app.selectByTag(sels);
    }

    async function splitTag() {
        if (!props.edit) return;

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

            try {
                await splitTags({ id: tag.id, names: names, created_by: app.activeUserId, created: now })
                toast.success("split tag into " + names.length + " children")
                resetSelection();
                times.needsReload("tagging")
            } catch {
                toast.error("error splitting tag")
            }
        }
        splitPrompt.value = false;
    }

    async function mergeTag() {
        if (!props.edit) return;
        const now = Date.now();

        if (selectedTagsData.value.length > 0) {

            if (!tagNames.name) {
                toast.error("missing new tag name")
                return;
            }

            if (!selectedTagsData.value.some(d => d.name === tagNames.name) &&
                data.tags.some(d => d.name === tagNames.name)
            ) {
                toast.error("name must be unique")
                return;
            }

            const p = selectedTagsData.value.find(d => d.id === tagNames.parent);
            if (p) {
                if (p.parent && !selectedTagsData.value.find(d => d.id === p.parent)) {
                    tagNames.parent = p.parent === -1 ? null : p.parent;
                } else {
                    tagNames.parent = null;
                }
            }

            const obj = {
                name: tagNames.name,
                description: tagNames.desc,
                created: now,
                created_by: app.activeUserId,
                code_id: props.newCode,
                parent:  tagNames.parent,
                ids: []
            }
            selectedTagsData.value.forEach(tag => obj.ids.push(tag.id))

            try {
                await mergeTags(obj)
                toast.success("merged tags into tag " + tagNames.name)
                resetSelection();
                tagNames.name = "";
                tagNames.desc = "";
                tagNames.parent = null;
                times.needsReload("tagging")
            } catch {
                toast.error("error merging tags into tag " + tagNames.name)
            }
        }
        mergePrompt.value = false;
    }

    async function addChildren() {
        if (!props.edit) return;
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

                try {
                    await addTags(rows)
                    toast.success("created " + rows.length + " children")
                    resetSelection();
                    times.needsReload("tags")
                } catch {
                    toast.error("error creating " + rows.length + " children")
                }
            }
        }
        addChildrenPrompt.value = false;
    }

    async function deleteTags() {
        if (!props.edit) return;
        if (data.selectedTags.size > 0) {

            let ids = [];
            if (deleteChildren.value) {
                data.selectedTags.forEach(d => {
                    const tag = data.tags.find(dd => dd.id === d);
                    ids = ids.concat(getSubtree(tag, data.tags))
                });
                ids = Array.from(new Set(ids));
            } else {
                ids = Array.from(data.selectedTags.values())
            }

            try {
                await deleteTagsFunc(ids)
                toast.success("deleted " + ids.length + " tag(s)")
                times.needsReload("tagging")
                resetSelection();
            } catch {
                toast.error("error deleting " + ids.length + " tag(s)")
            }

        }
        deletePrompt.value = false;
        deleteChildren.value = false;
    }
    async function deleteTagAssignment(oldTag, newTag) {
        if (!props.edit) return;
        const old = data.tagAssign.find(d => d.old_tag == oldTag && d.new_tag == newTag);
        if (!old) {
            toast.error("tag assignment does not exist")
            return;
        }

        try {
            await deleteTagAssignments(old.id)
            toast.success("deleted tag assignment")
            data.selectedOldTag = null;
            data.selectedNewTag = null;
            DM.removeFilter("tags_old", "id")
            times.needsReload("tag_assignments");
        } catch {
            toast.error("error deleting tag assignment")
        }
    }
    async function groupTags() {
        if (!props.edit) return;
        if (data.selectedTags.size > 0) {

            if (!tagNames.name) {
                toast.error("missing new tag name")
                return;
            }
            if (!tagNames.desc) {
                toast.error("missing new tag description")
                return;
            }
            if (data.tags.some(d => d.name === tagNames.name)) {
                toast.error("name must be unique")
                return;
            }

            const p = selectedTagsData.value.find(d => d.id === tagNames.parent);
            if (p) {
                if (p.parent && !selectedTagsData.value.find(d => d.id === p.parent)) {
                    tagNames.parent = p.parent === -1 ? null : p.parent;
                } else {
                    tagNames.parent = null;
                }
            }

            const parent = {
                name: tagNames.name,
                description: tagNames.desc,
                code_id: props.newCode,
                created: Date.now(),
                created_by: app.activeUserId,
                is_leaf: false,
                parent: tagNames.parent,
            }

            try {
                await addTags(parent)
                app.addAction("trans", "group tags", {
                    tags: Array.from(data.selectedTags.values()),
                    name: tagNames.name.slice(),
                });
                toast.success("added new parent tag")
                tagNames.name = "";
                tagNames.desc = "";
                tagNames.parent = null;
                times.needsReload("tagging")
            } catch {
                toast.error("error grouping tags")
            }
        }
        groupPrompt.value = false;
        resetSelection();
    }
    async function addAsChildren() {
        if (!props.edit) return;
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

            try {
                await updateTags(tags)
                toast.success("updated " + tags.length + "tag(s)")
                resetSelection();
                times.needsReload("tagging")
            } catch {
                toast.error("error updating " + tags.length + "tag(s)")
            }
        }
    }

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    async function addTagsToGroup(name, tags) {
        if (tags.length === 0 || !name) return false;

        const parent = data.tags.find(d => d.name === name);
        if (!parent) {
            return false;
        }

        try {
            await updateTags(tags.map(d => {
                const tag = data.tags.find(t => t.id === d);
                return {
                    id: d,
                    name: tag.name,
                    description: tag.description,
                    parent: parent.id,
                    is_leaf: tag.is_leaf
                }
            }));
            toast.success(`updated ${tags.length} tags`);
            times.needsReload("tagging");
        } catch {
            toast.error(`error updating ${tags.length} tags`);
            return false;
        }
        return true
    }

    async function assignTag(oldTag, newTag) {
        if (!props.edit) return;
        if (!oldTag || !newTag) {
            toast.error("one of the tags is missing")
            return;
        }

        try {
            await addTagAssignments({
                old_tag: oldTag,
                new_tag: newTag,
                old_code: props.oldCode,
                new_code: props.newCode,
                description: "",
                created: Date.now()
            });
            toast.success(`updated tag assignment`);
            data.selectedOldTag = null;
            data.selectedNewTag  = null;
            DM.removeFilter("tags_old", "id")
            times.needsReload("tag_assignments");
        } catch {
            toast.success(`error updating tag assignment`);
        }
    }

    function openDeletePrompt() { deletePrompt.value = true; }
    function closeDeletePrompt() { deletePrompt.value = false; }

    function openChildrenPrompt() { addChildrenPrompt.value = true; }
    function closeChildrenPrompt() { addChildrenPrompt.value = false; }

    function openSplitPrompt() { splitPrompt.value = true; }
    function closeSplitPrompt() { splitPrompt.value = false; }

    function openMergePrompt() {
        let p = null;
        let minDepth = Number.MAX_SAFE_INTEGER;
        selectedTagsData.value.forEach(d => {
            if (d.parent && d.path.length - 1 < minDepth) {
                minDepth = d.path.length - 1;
                p = d.parent;
            }
        })

        tagNames.parent = p;
        mergePrompt.value = true;
    }
    function closeMergePrompt() { mergePrompt.value = false; }

    function openGroupPrompt() {
        let p = null;
        let minDepth = Number.MAX_SAFE_INTEGER;
        selectedTagsData.value.forEach(d => {
            if (d.parent && d.path.length - 1 < minDepth) {
                minDepth = d.path.length - 1;
                p = d.parent;
            }
        })

        tagNames.parent = p;
        groupPrompt.value = true;
    }
    function closeGroupPrompt() { groupPrompt.value = false; }

    onMounted(readData.bind(null, true))

    watch(() => times.f_tags, function() { data.selectedTags = DM.getSelectedIds("tags") })
    watch(() => Math.max(times.tags, times.tags_old, times.tag_assignments, times.tagging), readData, { deep: true });
    watch(() => times.datatags, updateDataTags)

</script>