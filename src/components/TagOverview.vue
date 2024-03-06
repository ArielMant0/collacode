
<template>
    <GroupedBarChart v-if="bars.length > 0" :data="bars" :x-domain="tagNames" :groups="userNames"/>
</template>

<script setup>
    import * as d3 from 'd3';
    import DM from '@/use/data-manager';
    import GroupedBarChart from './vis/GroupedBarChart.vue';
    import { computed } from 'vue';
    import { useApp } from '@/store/app';

    const app = useApp();
    const userNames = computed(() => {
        const obj = {};
        app.users.forEach(u => obj[u.id] = u.name);
        return obj;
    });
    const tagNames = computed(() => {
        const obj = {};
        const tags = DM.getData("tags")
        tags.forEach(t => obj[t.id] = t.name)
        return obj;
    });

    const bars = computed(() => {
        const result = [];
        const data = DM.getData("data_tags")
        app.users.forEach(u => {
            const tmp = [];
            const freqs = d3.group(data.filter(d => d.created_by === u.id), d => d.tag_id);
            freqs.forEach((val, tag) => tmp.push({ x: tag, y: val.length, group: u.id }));
            result.push(tmp)
        })
        return result;
    });
</script>