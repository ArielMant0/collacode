<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { computed, onMounted } from 'vue';

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        dimensions: {
            type: Array,
            required: true
        },
        options: {
            type: Object,
            required: true
        },
        colorScale: {
            type: String,
            default: "schemeCategory10"
        },
        width: {
            type: Number,
            default: 300
        },
        height: {
            type: Number,
            default: 150
        },
    })

    const el = ref(null)

    const asSet = computed(() => new Set(props.data))
    // const width = computed(() => props.dimensions.length * (props.size+2))
    // const height = computed(() => maxCats.value * props.size)

    function has(name) { return asSet.value.has(name) }

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove()

        const x = d3.scaleBand()
            .domain(props.dimensions)
            .range([5, props.width-5])
            .paddingInner(0.1)

        const bands = {}
        props.dimensions.forEach(dim => {
            bands[dim] = d3.scaleBand()
                .domain(props.options[dim])
                .range([5, props.height-5])
                .paddingInner(0.1)
        })

        const color = d3.scaleOrdinal(d3[props.colorScale])
            .domain(props.dimensions)
            .unknown("#333")

        props.dimensions.forEach(dim => {
            svg.append("g")
                .attr("transform", `translate(${x(dim)},0)`)
                .selectAll("rect")
                .data(props.options[dim])
                .join("rect")
                .attr("x", d => has(d) ? 0 : 1)
                .attr("y", d => bands[dim](d) + (has(d) ? 0 : 1))
                .attr("width", d => x.bandwidth() - (has(d) ? 0 : 2))
                .attr("height", d => bands[dim].bandwidth() - (has(d) ? 0 : 2))
                .attr("fill", d => has(d) ? color(dim) : "white")
                .attr("stroke", d => has(d) ? "white" : color(dim))
                .append("title")
                .text(d => dim + " → " + d)
        })
    }

    onMounted(draw)

    watch(props, draw, { deep: true })
</script>
