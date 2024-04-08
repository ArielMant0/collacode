
<template>
    <div class="d-flex">
        <div ref="parent" style="width: 100%">
            <v-card v-if="app.showAllUsers" class="d-flex pa-4">
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
            </v-card>

            <v-card v-else class="d-flex pa-4">
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
            </v-card>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import GroupedBarChart from '@/components/vis/GroupedBarChart.vue';
    import BarChart from '@/components/vis/BarChart.vue';

    import { reactive, onMounted, watch } from 'vue';
    import { useApp } from '@/store/app';
    import DM from '@/use/data-manager';
    import { useElementSize } from '@vueuse/core';

    const app = useApp();
    const parent = ref(null)
    const pSize = useElementSize(parent);

    const data = reactive({
        users: {},
        tags: {},
        bars: [],
        userColors: {},
        selectionTags: {},
        selectionBars: [],
    });

    function updateUsers() {
        const obj = {};
        app.users.forEach(u => {
            obj[u.id] = u.name;
            data.userColors[u.id] = u.color;
        });
        data.users = obj;
    }

    function updateBars() {
        const result = [];
        const dts = DM.getData("datatags")

        const obj = {};
        const tags = DM.getData("tags", false)

        if (app.showAllUsers) {
            app.users.forEach(u => {
                const tmp = [];
                const freqs = d3.group(dts.filter(d => d.created_by === u.id), d => d.tag_id);
                freqs.forEach((val, tag) => {
                    const item = tags.find(t => t.id === val[0].tag_id);
                    if (item) {
                        tmp.push({ x: tag, y: val.length, group: u.id })
                        obj[tag] = item.name
                    }
                });
                result.push(tmp)
            });
        } else {
            const id = app.activeUserId;
            const freqs = d3.group(dts.filter(d => d.created_by === id), d => d.tag_id);
            freqs.forEach((val, tag) => {
                const item = tags.find(t => t.id === val[0].tag_id);
                if (item) {
                    result.push({ x: tag, y: val.length, group: 'all' })
                    obj[tag] = item.name
                }
            });
        }

        data.tags = obj;
        data.bars = result;
    }

    function updateSelected() {

        if (!DM.hasFilter("games")) {
            data.selectionTags = {};
            data.selectionBars = [];
        } else {
            const games = DM.getData("games", true);
            const gameIds = {};
            games.forEach(d => gameIds[d.id] = true);

            const dtags = DM.getDataBy("datatags", d => {
                return gameIds[d.game_id] !== undefined &&
                    (app.showAllUsers || d.created_by === app.activeUserId)
            });
            const tagIds = {};
            dtags.forEach(d => tagIds[d.tag_id] = true);

            const tags = DM.getDataBy("tags", d => tagIds[d.id] !== undefined);

            const obj = {};
            const result = [];

            if (app.showAllUsers) {
                app.users.forEach(u => {
                    const tmp = [];
                    const freqs = d3.group(dtags.filter(d => d.created_by === u.id), d => d.tag_id);
                    freqs.forEach((val, tag) => {
                        const item = tags.find(t => t.id === tag);
                        if (item) {
                            tmp.push({ x: tag, y: val.length, group: u.id })
                            obj[tags] = item.name
                        }
                    });
                    result.push(tmp)
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
            data.selectionTags = obj;
            data.selectionBars = result;
        }
    }

    function updateAll() {
        updateUsers();
        updateBars();
        updateSelected();
    }

    function toggleSelectedTag(tagId) {
        app.toggleSelectByTag([+tagId])
    }

    onMounted(updateAll);

    watch(() => app.dataLoading._all, function(val) { if (val === false) { updateAll(); }});
    watch(() => app.dataLoading.coding, function(val) { if (val === false) { updateAll(); }});
    watch(() => app.dataLoading.transition, function(val) { if (val === false) { updateAll(); }});
    watch(() => app.dataLoading.tags, function(val) { if (val === false) { updateAll(); }});

    watch(() => app.userTime, updateAll);
    watch(() => app.selectionTime, updateSelected)

</script>