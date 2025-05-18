<template>
    <div style="width: 100%;">
        <div v-if="data.tagTreeData" style="text-align: center;">
            <TransitionHistory v-if="treeLayout == 'history'"/>
            <TreeMap v-else-if="treeLayout == 'treemap'"
                flash
                :data="data.tagTreeData"
                :time="dataTime"
                :selected="Array.from(data.selectedTags.values())"
                :width="treeWidth"
                :height="treeHeight"
                collapsible
                valid-attr="valid"
                @click="onClickTag"
                @right-click="onRightClickTag"/>
            <RadialTree v-else-if="treeLayout == 'radial'"
                flash
                :data="data.tagTreeData"
                :size="Math.min(treeWidth, treeHeight)"
                :time="dataTime"
                @click="onClickTag"
                @right-click="onRightClickTag"/>
            <InteractiveTree v-else
                :data="data.tagTreeData"
                :assignment="tagAssignObj"
                assign-attr="assigned"
                :show-assigned="tagAssign"
                :width="treeWidth"
                :time="dataTime"
                :layout="treeLayout"
                show-valid
                :radius="5"
                @click="onClickTag"
                @click-assign="onClickOldTag"
                @right-click="onRightClickTag"/>
        </div>
    </div>
</template>

<script setup>
    import { pointer } from 'd3';
    import { onMounted, reactive, computed, ref, watch } from 'vue';
    import InteractiveTree from './vis/InteractiveTree.vue';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { useWindowSize } from '@vueuse/core';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import TreeMap from './vis/TreeMap.vue';
    import RadialTree from './vis/RadialTree.vue';
    import TransitionHistory from './TransitionHistory.vue';
    import { FILTER_TYPES } from '@/use/filters';

    const app = useApp();
    const settings = useSettings();
    const times = useTimes()

    const wSize = useWindowSize()

    const treeWidth = computed(() => Math.max(500, wSize.width.value*0.8))
    const treeHeight = computed(() => Math.max(500, wSize.height.value*0.8))

    const dataTime = ref(Date.now())

    const { tagAssign, tagAssignMode, treeLayout } = storeToRefs(settings)

    const data = reactive({
        tags: [],
        tagsOld: [],

        tagTreeData: null,
        tagAssign: [],

        selectedTags: new Set(),
    });

    const tagAssignObj = computed(() => {
        const obj = {};
        data.tagsOld.forEach(d => {
            const a = data.tagAssign.find(dd => dd.old_tag === d.id)
            obj[d.id] = {
                id: d.id,
                name: d.name,
                description: a ? a.description : "tag deleted",
                new_tag: a ? a.new_tag : null,
            };
        })
        return obj;
    })

    async function readData() {
        if (!app.activeCode || !DM.hasData("tags")) {
            return console.warn("missing data for transition view")
        }

        data.tags = DM.getData("tags", false)
        data.tagsOld = DM.getData("tags_old", false);
        data.tagAssign = DM.getData("tag_assignments");

        data.tags.forEach(d => {
            if (d.parent === null) {
                d.parent = -1;
            }
            d.assigned = data.tagAssign.filter(dd => dd.new_tag === d.id).map(dd => dd.old_tag)
        })

        data.tagTreeData = [{ id: -1, name: "root", parent: null, valid: true }].concat(data.tags)
        data.selectedTags = DM.getSelectedIds("tags")

        dataTime.value = Date.now()
    }
    function updateDataTags() {
        if (!data.tagTreeData) return;
        const tags = DM.getData("tags", false)
        data.tagTreeData.forEach(d => {
            const updated = tags.find(t => t.id === d.id)
            d.valid = updated ? updated.valid : false
        })
        dataTime.value = Date.now()
    }

    function onClickTag(tag) {
        if (!tag) return;
        app.toggleSelectByTag([tag.id])
        data.selectedTags = DM.getSelectedIds("tags")
    }

    function onClickOldTag(tag) {
        if (!tag) return;
        if (!tagAssignMode.value) tagAssignMode.value = true;
        DM.toggleFilter("tags_old", "id", [tag.id], FILTER_TYPES.SET_OR)
    }

    function onRightClickTag(tag, event) {
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "tag", tag.id,
            mx, my,
            tag.name, null,
            CTXT_OPTIONS.tag,
        )
    }

    onMounted(readData.bind(null, true))

    watch(() => times.f_tags, function() { data.selectedTags = DM.getSelectedIds("tags") })
    watch(() => Math.max(times.tags, times.tags_old, times.tag_assignments, times.tagging), readData, { deep: true });
    watch(() => times.datatags, updateDataTags)

</script>