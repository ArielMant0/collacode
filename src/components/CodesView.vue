
<template>
    <BarChart v-if="bars.length > 0 && bars[0].length > 0" :data="bars" :names="tagNames"/>
</template>

<script setup>
    import * as d3 from 'd3';
    import DM from '@/use/data-manager';
    import BarChart from './vis/BarChart.vue';
    import { computed } from 'vue';
    import { useApp } from '@/store/app';

    const app = useApp();
    const tagNames = computed(() => {
        const obj = {};
        const tags = DM.getData("tags")
        tags.forEach(t => obj[t.id] = t.name)
        return obj;
    });

    const bars = computed(() => {
        const result = [];
        const data = DM.getData("datatags")
        const freq = d3.group(data.filter(d => d.tag_id), d => d.tag_id);
        freq.forEach((val, key) => result.push({
            x: key,
            y: val.length,
            code: app.activeCode,
        }));
        return result;
    });
</script>