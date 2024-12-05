<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useSettings } from '@/store/settings';
    import { computed, onMounted } from 'vue';
import { sortObjByString } from '@/use/sorting';

    const settings = useSettings()

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
        binary: {
            type: Boolean,
            default: false
        }
    })

    const el = ref(null)

    function has(id) { return props.data.find(d => d.cat_id === id) }

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove()

        const dims = props.dimensions.slice()
        dims.sort((a, b) => settings.extCatOrder.indexOf(a)-settings.extCatOrder.indexOf(b))

        const options = {}
        for (const dim in props.options) {
            options[dim] = props.options[dim].slice()
            options[dim].sort((a, b) => settings.getExtCatValueOrder(dim, a.name, b.name))
        }

        const x = d3.scaleBand()
            .domain(dims)
            .range([5, props.width-5])
            .paddingInner(props.width < 200 ? 0 : 0.1)

        const bands = {}
        dims.forEach(dim => {
            bands[dim] = d3.scaleBand()
                .domain(options[dim].map(d => d.name))
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
                .attr("y", d => bands[dim](d.name)+1)
                .attr("width", x.bandwidth()-2)
                .attr("height", bands[dim].bandwidth()-2)
                .attr("fill", d => has(d.id) ? (props.binary ? "#333" : color(dim)) : "white")
                .attr("stroke", props.binary ? "#333" : color(dim))
                .append("title")
                .text(d => dim + " → " + d.name)
        })
    }

    onMounted(draw)

    watch(props, draw, { deep: true })
</script>
