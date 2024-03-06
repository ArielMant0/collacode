
<template>
    <GroupedBarChart v-if="data.bars.length > 0"
        :data="data.bars"
        :x-domain="data.tags"
        :groups="data.users"
        x-attr="x"
        y-attr="y"
        group-attr="group"/>
</template>

<script setup>
    import * as d3 from 'd3';
    import DM from '@/use/data-manager';
    import GroupedBarChart from './vis/GroupedBarChart.vue';
    import { reactive, onMounted } from 'vue';
    import { useApp } from '@/store/app';

    const app = useApp();
    const data = reactive({ users: {}, tags: {}, bars: [] })

    function updateUsers() {
        const obj = {};
        app.users.forEach(u => obj[u.id] = u.name);
        data.users = obj;
    }
    function updateTags() {
        const tags = DM.getData("tags")
        const obj = {};
        tags.forEach(t => obj[t.id] = t.name)
        data.tags = obj;
    }
    function updateBars() {
        const result = [];
        const dts = DM.getData("datatags")
        app.users.forEach(u => {
            const tmp = [];
            const freqs = d3.group(dts.filter(d => d.created_by === u.id), d => d.tag_id);
            freqs.forEach((val, tag) => tmp.push({ x: tag, y: val.length, group: u.id }));
            result.push(tmp)
        })
        data.bars = result;
    }

    function updateAll() {
        updateUsers();
        updateTags();
        updateBars();
    }

    onMounted(updateAll);

    watch(() => app.dataReloaded, updateAll);
</script>