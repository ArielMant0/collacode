
<template>
    <div ref="parent">
        <v-card v-if="app.showAllUsers" class="d-flex pa-4">
            <GroupedBarChart v-if="data.bars.length > 0"
                :data="data.bars"
                :x-domain="data.tags"
                :groups="data.users"
                :width="550"
                x-attr="x"
                y-attr="y"
                group-attr="group"/>
            <GroupedBarChart v-if="data.selectionBars.length > 0"
                :data="data.selectionBars"
                :x-domain="data.selectionTags"
                :groups="data.users"
                :width="550"
                x-attr="x"
                y-attr="y"
                group-attr="group"/>
        </v-card>

        <v-card v-else class="d-flex pa-4">
            <BarChart v-if="data.bars.length > 0"
                :data="data.bars"
                :x-domain="data.tags"
                :width="550"
                x-attr="x"
                y-attr="y"/>
            <BarChart v-if="data.selectionBars.length > 0"
                :data="data.selectionBars"
                :x-domain="data.selectionTags"
                :width="550"
                x-attr="x"
                y-attr="y"/>
            </v-card>
        </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import GroupedBarChart from './vis/GroupedBarChart.vue';
    import BarChart from './vis/BarChart.vue';

    import { reactive, onMounted } from 'vue';
    import { useApp } from '@/store/app';
    import DM from '@/use/data-manager';

    const app = useApp();
    const data = reactive({
        users: {},
        tags: {},
        bars: [],
        selectionTags: {},
        selectionBars: [],
    });

    function updateUsers() {
        const obj = {};
        app.users.forEach(u => obj[u.id] = u.name);
        data.users = obj;
    }

    function updateBars() {
        const result = [];
        const dts = DM.getData("datatags")

        const obj = {};
        const tags = DM.getData("tags")

        if (app.showAllUsers) {
            app.users.forEach(u => {
                const tmp = [];
                const freqs = d3.group(dts.filter(d => d.created_by === u.id), d => d.tag_id);
                freqs.forEach((val, tag) => tmp.push({ x: tag, y: val.length, group: u.id }));
                result.push(tmp)
            });
            tags.forEach(t => obj[t.id] = t.name)
        } else {
            const id = app.activeUserId;
            const freqs = d3.group(dts.filter(d => d.created_by === id), d => d.tag_id);
            freqs.forEach((val, tag) => {
                result.push({ x: tag, y: val.length })
                obj[tag] = tags.find(t => t.id === tag).name;
            });
        }
        data.tags = obj;
        data.bars = result;
    }

    function updateSelected() {
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
                result.push({ x: tag, y: val.length })
                obj[tag] = tags.find(t => t.id === tag).name;
            });
        }
        data.selectionTags = obj;
        data.selectionBars = result;
    }

    function updateAll() {
        updateUsers();
        updateBars();
    }

    onMounted(updateAll);

    watch(() => app.dataReloaded, updateAll);
    watch(() => app.showAllUsers, updateBars);
    watch(() => app.activeUserId, updateAll);
    watch(() => app.selectionTime, updateSelected)
</script>