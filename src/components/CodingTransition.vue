<template>
    <div ref="wrapper" style="width: 100%;">
        <div v-if="data.tagTreeData" style="text-align: center;">
            <TransitionHistory v-if="treeLayout == 'history'"/>
            <TreeMap v-else-if="treeLayout == 'treemap'"
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
                :show-assigned="tagAssign"
                :width="wrapperSize.width.value"
                :time="dataTime"
                :layout="treeLayout"
                :radius="5"
                @click="onClickTag"
                @click-assign="onClickOriginalTag"
                @right-click="onRightClickTag"/>
        </div>

        <MiniDialog v-model="addChildrenPrompt">
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

        <MiniDialog v-model="deletePrompt" submit-text="delete" submit-color="error">
            <template v-slot:text>
                <div class="d-flex flex-column align-center">
                    <p class="mb-2">
                        Delete tags <b v-if="selectedTagsData.length > 0">{{ selectedTagsData.map(d => d.name).join(", ") }}</b>?
                    </p>
                    <v-checkbox-btn v-model="deleteChildren" density="compact" hide-details hide-spin-buttons label="delete children"/>
                </div>
            </template>
        </MiniDialog>

        <MiniDialog v-model="splitPrompt">
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

        <MiniDialog v-model="mergePrompt">
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

        <MiniDialog v-model="groupPrompt">
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
    import { onMounted, reactive, computed, ref, watch } from 'vue';
    import InteractiveTree from './vis/InteractiveTree.vue';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { useElementSize } from '@vueuse/core';
    import ExplorationToolbar from './ExplorationToolbar.vue';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import TreeMap from './vis/TreeMap.vue';
    import RadialTree from './vis/RadialTree.vue';
    import TransitionHistory from './TransitionHistory.vue';

    const app = useApp();
    const settings = useSettings();
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
    const dataTime = ref(Date.now())

    const { tagAssign, treeLayout } = storeToRefs(settings)

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

    onMounted(readData.bind(null, true))

    watch(() => times.f_tags, function() { data.selectedTags = DM.getSelectedIds("tags") })
    watch(() => Math.max(times.tags, times.tags_old, times.tag_assignments, times.tagging), readData, { deep: true });
    watch(() => times.datatags, updateDataTags)

</script>