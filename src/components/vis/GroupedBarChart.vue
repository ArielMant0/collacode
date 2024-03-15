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
        groups: {
            type: Object,
            required: true
        },
        colors: {
            type: Object,
            required: false
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
        groupAttr: {
            type: String,
            default: "group"
        },
    });

    function draw() {
        const svg = d3.select(el.value);
        svg.selectAll("*").remove();

        const x = d3.scaleBand()
            .domain(Object.keys(props.xDomain))
            .range([25, props.width-5])
            .padding(0.1)

        const xInner = d3.scaleBand()
            .domain(Object.keys(props.groups))
            .range([0, x.bandwidth()])
            .padding(0.1)

        const y = d3.scaleLinear()
            .domain([0, d3.max(props.data, d => d3.max(d, dd => dd[props.yAttr]))])
            .range([props.height-25, 5])

        svg.append("g")
            .selectAll("g")
            .data(props.data.filter(d => d.length > 0))
            .join("g")
                .attr("fill", (d, i) => {
                    return props.colors ? props.colors[d[0][props.groupAttr]] : d3.schemeTableau10[i]
                })
                .selectAll("rect")
                .data(d => d)
                .join("rect")
                .attr("x", d => x(""+d[props.xAttr]) + xInner(""+d[props.groupAttr]))
                .attr("y", d => y(d[props.yAttr]))
                .attr("width", xInner.bandwidth())
                .attr("height", d => y(0) - y(d[props.yAttr]))
                .append("title").text(d => getLabel(d[props.xAttr]) + ": " + d[props.yAttr] + " (" + props.groups[d[props.groupAttr]] + ")")

        const maxLabel = x.bandwidth() / 7;
        svg.append("g")
            .attr("transform", `translate(0,${props.height-25})`)
            .call(d3.axisBottom(x).tickFormat(d => getLabel(d, maxLabel)))
            .selectAll(".tick")
            .append("title").text(d => getLabel(d))

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