<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>

    import * as d3 from 'd3'
    import { ref, watch, onMounted } from 'vue'

    const el = ref(null);

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        xDomain: {
            type: Object,
            required: true
        },
        width: {
            type: Number,
            default: 300
        },
        height: {
            type: Number,
            default: 120
        },
        xAttr: {
            type: String,
            default: "x"
        },
        yAttr: {
            type: String,
            default: "y"
        },
        color: {
            type: String,
            default: "#078766"
        },
        altColor: {
            type: String,
            default: "#0ad39f"
        },
        clickable: {
            type: Boolean,
            default: false
        },
    });
    const emit = defineEmits(["click-bar", "click-label"])

    function draw() {
        const svg = d3.select(el.value);
        svg.selectAll("*").remove();

        const x = d3.scaleBand()
            .domain(Object.keys(props.xDomain))
            .range([25, props.width-5])
            .padding(0.1)

        const y = d3.scaleLinear()
            .domain([0, d3.max(props.data, d => d[props.yAttr])])
            .range([props.height-75, 5])

        const rects = svg.append("g")
            .selectAll("rect")
            .data(props.data)
            .join("rect")
            .attr("fill", props.color)
            .attr("x", d => x(""+d[props.xAttr]))
            .attr("y", d => y(d[props.yAttr]))
            .attr("width", x.bandwidth())
            .attr("height", d => y(0) - y(d[props.yAttr]))

        rects.append("title")
            .text(d => getLabel(d[props.xAttr]) + ": " + d[props.yAttr])


        if (props.clickable) {
            rects
                .style("cursor", "pointer")
                .on("click", (_, d) => emit("click-bar", d[props.xAttr]))
                .on("pointerenter", function() { d3.select(this).attr("fill", props.altColor) })
                .on("pointerleave", function() { d3.select(this).attr("fill", props.color) })
        }

        const maxLabel = 75 / 4;
        const ticks = svg.append("g")
            .attr("transform", `translate(0,${props.height-75})`)
            .call(d3.axisBottom(x).tickFormat(d => getLabel(d, maxLabel)))
            .selectAll(".tick text")

        if (props.clickable) {
            ticks
                .style("cursor", "pointer")
                .attr("transform", "rotate(-45)")
                .attr("text-anchor", "end")
                .on("click", (_, d) => emit("click-label", d))
                .on("pointerenter", function() { d3.select(this).attr("font-weight", "bold") })
                .on("pointerleave", function() { d3.select(this).attr("font-weight", null) })
        }

        svg.append("g")
            .attr("transform", `translate(25,0)`)
            .call(d3.axisLeft(y).ticks(Math.max(3, Math.round(props.height / 30))))

        function getLabel(d, maxLength=-1) {
            if (props.xDomain !== undefined) {
                return maxLength > 0 && props.xDomain[d].length > maxLength ?
                    props.xDomain[d].slice(0, maxLength) + ".." :
                    props.xDomain[d]
            }
            return x.tickFormat(d);
        }
    }

    onMounted(draw);

    watch(props, draw, { deep: true });

</script>