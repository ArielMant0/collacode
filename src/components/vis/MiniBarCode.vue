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

        const ORDER = [
            "make sense", "why", "how long",
            "what", "encoding 1", "encoding 2",
            "mechanics", "level of expression", "automation",
            "mechanics coupling"
        ]
        const dims = props.dimensions.slice()
        dims.sort((a, b) => ORDER.indexOf(a)-ORDER.indexOf(b))

        const options = {}
        for (const dim in props.options) {
            options[dim] = props.options[dim].slice()
            options[dim].sort()
        }

        const x = d3.scaleBand()
            .domain(dims)
            .range([5, props.width-5])
            .paddingInner(props.width < 200 ? 0 : 0.1)

        const bands = {}
        dims.forEach(dim => {
            bands[dim] = d3.scaleBand()
                .domain(options[dim])
                .range([5, props.height-5])
                .paddingInner(props.height < 200 ? 0 : 0.1)
        })

        const color = d3.scaleOrdinal(d3[props.colorScale])
            .domain(dims)
            .unknown("#333")

        dims.forEach(dim => {
            svg.append("g")
                .attr("transform", `translate(${x(dim)},0)`)
                .selectAll("rect")
                .data(options[dim])
                .join("rect")
                .attr("x", 1)
                .attr("y", d => bands[dim](d)+1)
                .attr("width", x.bandwidth()-2)
                .attr("height", bands[dim].bandwidth()-2)
                .attr("fill", d => has(d) ? color(dim) : "white")
                .attr("stroke", color(dim))
                .append("title")
                .text(d => dim + " → " + d)
        })
    }

    onMounted(draw)

    watch(props, draw, { deep: true })
</script>
