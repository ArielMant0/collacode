
<template>
    <v-card ref="parent" class="pa-4">
        <GroupedBarChart v-if="app.showAllUsers && data.bars.length > 0"
            :data="data.bars"
            :x-domain="data.tags"
            :groups="data.users"
            :width="800"
            x-attr="x"
            y-attr="y"
            group-attr="group"/>
        <BarChart v-else-if="!app.showAllUsers && data.bars.length > 0"
            :data="data.bars"
            :x-domain="data.tags"
            :width="800"
            x-attr="x"
            y-attr="y"/>
    </v-card>
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
        bars: []
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

    function updateAll() {
        updateUsers();
        updateBars();
    }

    onMounted(updateAll);

    watch(() => app.dataReloaded, updateAll);
    watch(() => app.showAllUsers, updateBars);
    watch(() => app.activeUserId, updateAll);
</script>