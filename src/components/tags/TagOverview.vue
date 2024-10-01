
<template>
    <div>
        <v-switch v-model="showAll"
            label="grouped by user"
            density="compact"
            hide-details
            hide-spin-buttons
            color="primary"
            @update:model-value="updateAll"/>
        <div ref="parent" style="width: 100%">
            <v-sheet v-if="showAll" class="d-flex pa-4">
                <GroupedBarChart v-if="data.bars.length > 0"
                    :data="data.bars"
                    :x-domain="data.tags"
                    :groups="data.users"
                    :colors="data.userColors"
                    :width="Math.max(pSize.width.value-50, 100)"
                    :height="250"
                    clickable
                    sort
                    x-attr="x"
                    y-attr="y"
                    @click-bar="toggleSelectedTag"
                    @click-label="toggleSelectedTag"
                    group-attr="group"/>
            </v-sheet>

            <v-sheet v-else class="d-flex pa-4">
                <GroupedBarChart v-if="data.bars.length > 0 && data.selectionBars.length > 0"
                    :data="[data.bars, data.selectionBars]"
                    :x-domain="data.tags"
                    :groups="{ 'all': 'all', 'selected': 'selected' }"
                    :colors="{ 'all': '#078766', 'selected': '#0ad39f' }"
                    :width="Math.max(pSize.width.value-50, 100)"
                    :height="250"
                    x-attr="x"
                    y-attr="y"
                    clickable
                    sort
                    @click-bar="toggleSelectedTag"
                    @click-label="toggleSelectedTag"
                    group-attr="group"/>
                <BarChart v-else-if="data.bars.length > 0"
                    :data="data.bars"
                    :x-domain="data.tags"
                    @click-bar="toggleSelectedTag"
                    @click-label="toggleSelectedTag"
                    clickable
                    sort
                    :width="Math.max(pSize.width.value-50, 100)"
                    :height="250"
                    x-attr="x"
                    y-attr="y"/>
            </v-sheet>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import GroupedBarChart from '@/components/vis/GroupedBarChart.vue';
    import BarChart from '@/components/vis/BarChart.vue';

    import { reactive, onMounted, watch, ref, computed } from 'vue';
    import { useApp } from '@/store/app';
    import DM from '@/use/data-manager';
    import { useElementSize } from '@vueuse/core';

    const app = useApp();
    const parent = ref(null)
    const pSize = useElementSize(parent);

    const props = defineProps({
        alwaysFullData: {
            type: Boolean,
            default: false
        }
    })

    const data = reactive({
        users: {},
        tags: {},
        bars: [],
        userColors: {},
        selectionTags: {},
        selectionBars: [],
    });
    const showAll = ref(app.showAllUsers);

    function updateBars() {
        if (!DM.hasData("games") || !DM.hasData("tags") || !DM.hasData("datatags")) {
            return;
        }

        const result = [];
        const dts = DM.getData("datatags", !showAll.value && !props.alwaysFullData)

        const obj = {};
        const userObj = {};
        const tags = DM.getData("tags", false)

        if (showAll.value) {
            app.users.forEach(u => {
                const freqs = d3.group(dts.filter(d => d.created_by === u.id), d => d.tag_id);
                if (freqs.size > 0) {
                    userObj[u.id] = u.name
                    data.userColors[u.id] = u.color;
                    const tmp = [];
                    freqs.forEach((val, tag) => {
                        const item = tags.find(t => t.id === val[0].tag_id);
                        if (item) {
                            tmp.push({ x: tag, y: val.length, group: u.id })
                            obj[tag] = item.name
                        }
                    });
                    result.push(tmp)
                }
            });
        } else {
            const freqs = d3.group(dts, d => d.tag_id);
            freqs.forEach((val, tag) => {
                const item = tags.find(t => t.id === val[0].tag_id);
                if (item) {
                    result.push({ x: tag, y: val.length, group: 'all' })
                    obj[tag] = item.name
                }
            });
        }

        data.users = userObj;
        data.tags = obj;
        data.bars = result;
    }

    function updateSelected() {

        if (!DM.hasFilter("games")) {
            data.selectionTags = {};
            data.selectionBars = [];
        } else {
            if (!DM.hasData("games") || !DM.hasData("tags") || !DM.hasData("datatags")) {
                return;
            }

            const games = DM.getData("games", true);
            const gameIds = {};
            games.forEach(d => gameIds[d.id] = true);

            const dtags = DM.getDataBy("datatags", d => {
                return gameIds[d.game_id] !== undefined &&
                    (showAll.value || props.alwaysFullData || d.created_by === app.activeUserId)
            });
            const tagIds = {};
            dtags.forEach(d => tagIds[d.tag_id] = true);

            const tags = DM.getDataBy("tags", d => tagIds[d.id] !== undefined);

            const obj = {};
            const userObj = {};
            const result = [];

            if (showAll.value) {
                app.users.forEach(u => {
                    const freqs = d3.group(dtags.filter(d => d.created_by === u.id), d => d.tag_id);
                    if (freqs.size > 0) {
                        userObj[u.id] = u.name
                        data.userColors[u.id] = u.color;
                        const tmp = [];
                        freqs.forEach((val, tag) => {
                            const item = tags.find(t => t.id === tag);
                            if (item) {
                                tmp.push({ x: tag, y: val.length, group: u.id })
                                obj[tags] = item.name
                            }
                        });
                        result.push(tmp)
                    }
                });
            } else {
                const freqs = d3.group(dtags, d => d.tag_id);
                freqs.forEach((val, tag) => {
                    const item = tags.find(t => t.id === tag);
                    if (item) {
                        result.push({ x: tag, y: val.length, group: 'selected' })
                        obj[tag] = item.name;
                    }
                });
            }
            data.users = userObj;
            data.selectionTags = obj;
            data.selectionBars = result;
        }
    }

    function updateAll() {
        updateBars();
        updateSelected();
    }

    function toggleSelectedTag(tagId) {
        app.toggleSelectByTag([+tagId])
    }

    onMounted(updateAll);

    watch(() => ([
        times.all,
        times.coding,
        times.transition,
        times.tags,
        times.datatags
    ]), updateAll, { deep: true });

    watch(() => app.showAllUsers, function(value) { showAll.value = value });
    watch(() => app.userTime, updateAll);
    watch(() => app.selectionTime, updateSelected)

</script>