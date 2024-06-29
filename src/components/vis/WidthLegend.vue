<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3';
    import { ref, computed, onMounted, watch } from 'vue';

    const props = defineProps({
        values: {
            type: Array,
            required: true
        },
        ticks: {
            type: Array,
            required: true
        },
        size: {
            type: Number,
            default: 20
        },
        lineSize: {
            type: Number,
            default: 50
        },
        color: {
            type: String,
            default: "black"
        }
    })

    let scale = d3.scalePoint();
    const padding = 75, offset = 15;

    const el = ref(null);

    const width = computed(() => props.lineSize + padding)
    const height = computed(() => props.size * props.values.length)

    function draw() {
        const svg = d3.select(el.value);
        svg.selectAll("*").remove();

        scale
            .domain(d3.range(props.values.length))
            .range([offset, height.value-offset])

        svg.append("g")
            .selectAll("line")
            .data(props.values)
            .join("line")
            .attr("x1", (_, i) => 0)
            .attr("y1", (_, i) => scale(i))
            .attr("x2", (_, i) => props.lineSize)
            .attr("y2", (_, i) => scale(i))
            .attr("stroke", props.color)
            .attr("stroke-width", d => d)

        svg.append("g")
            .attr("font-size", 10)
            .attr("transform", `translate(${props.lineSize},0)`)
            .selectAll("text")
            .data(props.ticks)
            .join("text")
            .attr("dx", 10)
            .attr("dy", (_, i) => scale(i) + 5)
            .text(d => d)
    }

    onMounted(draw)

    watch(props, draw, { deep: true })

</script>