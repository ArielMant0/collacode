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
        names: {
            type: Object,
            required: false
        },
    });

    function draw() {
        const svg = d3.select(el.value);
        svg.selectAll("*").remove();

        const x = d3.scaleBand()
            .domain(props.data[0].map(d => d[props.xAttr]))
            .range([25, props.width-5])
            .padding(0.1)

        const xInner = d3.scaleBand()
            .domain(props.data.map(d => d[0][props.groupAttr]))
            .range([0, x.bandwidth()])
            .padding(0.1)

        const y = d3.scaleLinear()
            .domain([0, d3.max(props.data, d => d3.max(d, dd => dd[props.yAttr]))])
            .range([props.height-25, 5])

        svg.append("g")
            .selectAll("g")
            .data(props.data)
            .join("g")
                .attr("fill", (_, i) => d3.schemeDark2[i])
                .selectAll("rect")
                .data(d => d)
                .join("rect")
                .attr("x", d => x(d[props.xAttr]) + xInner(d[props.groupAttr]))
                .attr("y", d => y(d[props.yAttr]))
                .attr("width", xInner.bandwidth())
                .attr("height", d => y(0) - y(d[props.yAttr]))
                .append("title").text(d => getLabel(d[props.xAttr]))

        const maxLabel = x.bandwidth() / 7;
        svg.append("g")
            .attr("transform", `translate(0,${props.height-25})`)
            .call(d3.axisBottom(x).tickFormat(d => getLabel(d, maxLabel)))

        svg.append("g")
            .attr("transform", `translate(25,0)`)
            .call(d3.axisLeft(y))

        function getLabel(d, maxLength=-1) {
            if (props.names !== undefined) {
                return maxLength > 0 && props.names[d].length > maxLength ?
                    props.names[d].slice(0, maxLength) + ".." :
                    props.names[d]
            }
            return x.tickFormat(d);
        }
    }

    onMounted(draw);

    watch(props, draw, { deep: true });

</script>