
<template>
    <GroupedBarChart :data="bars" :names="tagNames"/>
</template>

<script setup>
    import * as d3 from 'd3';
    import DM from '@/use/data-manager';
    import GroupedBarChart from './vis/GroupedBarChart.vue';
    import { computed } from 'vue';

    const tagNames = computed(() => {
        const obj = {};
        const tags = DM.getData("tags")
        tags.forEach(t => obj[t.id] = t.name)
        return obj;
    });

    const bars = computed(() => {
        const result = [];
        const data = DM.getData("data_tags")
        const tags = DM.getData("tags")
        const freq = d3.group(data.filter(d => d.tag_id), d => d.tag_id);
        freq.forEach((val, key) => result.push({
            x: key,
            y: val.length,
            group: "c0",
        }));
        return [result];
    });
</script>