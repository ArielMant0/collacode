
<template>
    <div class="d-flex">
        <div ref="parent" style="width: 75%">
            <v-card v-if="app.showAllUsers" class="d-flex pa-4">
                <GroupedBarChart v-if="data.bars.length > 0"
                    :data="data.bars"
                    :x-domain="data.tags"
                    :groups="data.users"
                    :colors="data.userColors"
                    :width="pSize.width.value * (data.selectionBars.length > 0 ? 0.5 : 1) - 50"
                    :height="200"
                    clickable
                    x-attr="x"
                    y-attr="y"
                    @click-bar="toggleSelectedTag"
                    @click-label="toggleSelectedTag"
                    group-attr="group"/>
                <GroupedBarChart v-if="data.selectionBars.length > 0"
                    :data="data.selectionBars"
                    :x-domain="data.selectionTags"
                    :groups="data.users"
                    :colors="data.userColors"
                    :width="pSize.width.value * 0.5 - 50"
                    :height="200"
                    clickable
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
                    :width="pSize.width.value-50"
                    :height="200"
                    x-attr="x"
                    y-attr="y"
                    clickable
                    @click-bar="toggleSelectedTag"
                    @click-label="toggleSelectedTag"
                    group-attr="group"/>
                <BarChart v-else-if="data.bars.length > 0"
                    :data="data.bars"
                    :x-domain="data.tags"
                    @click-bar="toggleSelectedTag"
                    @click-label="toggleSelectedTag"
                    clickable
                    :width="pSize.width.value-50"
                    :height="200"
                    x-attr="x"
                    y-attr="y"/>
            </v-card>
        </div>

        <div style="width: 25%;" class="ml-2">
            <TagWidget :data="data.selectedTagData" can-edit/>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import GroupedBarChart from '@/components/vis/GroupedBarChart.vue';
    import BarChart from '@/components/vis/BarChart.vue';
    import TagWidget from '@/components/tags/TagWidget.vue';

    import { reactive, onMounted } from 'vue';
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

        selectedTag: null,
        selectedTagData: null,
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
        const tags = DM.getData("tags")

        const tmpTags = tags.map(t => ({ id: t.id, name: t.name }));
        tmpTags.sort((a, b) => {
            const nameA = a.name.toLowerCase(); // ignore upper and lowercase
            const nameB = b.name.toLowerCase(); // ignore upper and lowercase
            if (nameA < nameB) { return -1; }
            if (nameA > nameB) { return 1; }
            // names must be equal
            return 0;
        })
        tmpTags.forEach(t => obj[t.id] = t.name)

        if (app.showAllUsers) {
            app.users.forEach(u => {
                const tmp = [];
                const freqs = d3.group(dts.filter(d => d.created_by === u.id), d => d.tag_id);
                freqs.forEach((val, tag) => tmp.push({ x: tag, y: val.length, group: u.id }));
                result.push(tmp)
            });
        } else {
            const id = app.activeUserId;
            const freqs = d3.group(dts.filter(d => d.created_by === id), d => d.tag_id);
            freqs.forEach((val, tag) => result.push({ x: tag, y: val.length, group: 'all' }));
        }
        data.tags = obj;
        data.bars = result;
    }

    function updateSelected() {

        if (!DM.hasSelection()) {
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
                    freqs.forEach((val, tag) => tmp.push({ x: tag, y: val.length, group: u.id }));
                    result.push(tmp)
                });
                tags.forEach(t => obj[t.id] = t.name)
            } else {
                const freqs = d3.group(dtags, d => d.tag_id);
                freqs.forEach((val, tag) => {
                    result.push({ x: tag, y: val.length, group: 'selected' })
                    obj[tag] = tags.find(t => t.id === tag).name;
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

        if (data.selectedTag) {
            const tags = DM.getData("tags")
            data.selectedTagData = tags.find(d => data.selectedTag == d.id)
        }
    }

    function toggleSelectedTag(tagId) {
        if (data.selectedTag && data.selectedTag.id == tagId) {
            data.selectedTag = null;
            data.selectedTagData = null;
        } else {
            const tags = DM.getData("tags")
            data.selectedTag = tagId;
            data.selectedTagData = tags.find(d => data.selectedTag == d.id)
        }
    }

    onMounted(updateAll);

    watch(() => ([
        app.dataLoading._all,
        app.dataLoading.coding,
        app.dataLoading.transition,
    ]), function(vals) { if (vals.some(d => d === false)) {
            updateAll();
        }
    }, { deep: true });

    watch(() => app.userTime, updateAll);
    watch(() => app.selectionTime, updateSelected)
</script>