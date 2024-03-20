<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>

    import * as d3 from 'd3';
    import { useApp } from '@/store/app';
    import { ref, onMounted, computed } from 'vue';
    import DM from '@/use/data-manager';

    const el = ref(null);
    const app = useApp();

    const props = defineProps({
        dataLeft: {
            type: Array,
            required: true
        },
        dataRight: {
            type: Array,
            required: true
        },
        connections: {
            type: Array,
            required: true
        },
        domainLeft: {
            type: Array,
            required: false
        },
        domainRight: {
            type: Array,
            required: false
        },
        width: {
            type: Number,
            default: 800
        },
        barHeight: {
            type: Number,
            default: 25
        },
        xAttr: {
            type: String,
            default: "x"
        },
        yAttr: {
            type: String,
            default: "y"
        },
    });
    const emit = defineEmits(["click-left", "click-right", "click-connection"])

    const height = computed(() => props.barHeight * Math.max(props.dataLeft.length, props.dataRight.length))
    let lg, rg;

    function draw() {
        const svg = d3.select(el.value);
        svg.selectAll("*").remove();

        const xdomain = [
            0,
            Math.max(d3.max(props.dataLeft, d => d[props.xAttr]) || 0, d3.max(props.dataRight, d => d[props.xAttr]) || 0),
        ]

        const x = d3.scaleLinear()
            .domain(xdomain)
            .range([5, (props.width * 0.33) - 10])

        const yLeft = d3.scaleBand()
            .domain(props.domainLeft ? props.domainLeft :props.dataLeft.map(d => d[props.yAttr]))
            .range([5, height.value-5])
            .padding(0.1)

        const yRight = d3.scaleBand()
            .domain(props.domainRight ? props.domainRight : props.dataRight.map(d => d[props.yAttr]))
            .range([5, height.value-5])
            .padding(0.1)

        const maxXPos = x.range()[1]
        const line = d3.line()
            .curve(d3.curveBumpX)
            .x(d => d[0])
            .y(d => d[1])

        const connData = [];
        props.connections.map(([from, to]) => {
            const l = props.dataLeft.find(dd => dd[props.yAttr] === from)
            const r = props.dataRight.find(dd => dd[props.yAttr] === to)
            connData.push({
                from: from,
                to: to,
                values: [
                    [x(l[props.xAttr]), yLeft(l[props.yAttr]) + yLeft.bandwidth()*0.5],
                    [maxXPos * 1, yLeft(l[props.yAttr]) + yLeft.bandwidth()*0.5],
                    [maxXPos * 2, yRight(r[props.yAttr]) + yRight.bandwidth()*0.5],
                    [maxXPos * 3 - x(r[props.xAttr]), yRight(r[props.yAttr]) + yRight.bandwidth()*0.5]
                ]
            });
        });

        svg.append("g")
            .attr("fill", "none")
            .attr("stroke", "#078766")
            .attr("stroke-width", 3)
            .selectAll("path")
            .data(connData)
            .join("path")
            .attr("d", d => line(d.values))
            .attr("cursor", "pointer")
            .on("click", function(e, d) { emit("click-connection", d.from, d.to, e) })
            .on("pointerenter", function() { d3.select(this).attr("stroke", "black") })
            .on("pointerleave", function() { d3.select(this).attr("stroke", null) })

        lg = svg.append("g")
            .selectAll("g")
            .data(props.dataLeft)
            .join("g")
            .attr("font-size", 13)
            .attr("transform", d => `translate(${x(0)},${yLeft(d[props.yAttr])})`)

        lg.append("rect")
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", d => x(d[props.xAttr]))
            .attr("height", yLeft.bandwidth())
            .attr("fill", "#078766")

        lg.append("text")
            .classed("background", true)
            .attr("x", 10)
            .attr("y", yLeft.bandwidth()*0.5 + 5)
            .attr("stroke", "#eee")
            .attr("stroke-width", 3)
            .text(d => d.name)
        lg.append("text")
            .classed("label", true)
            .attr("x", 10)
            .attr("y", yLeft.bandwidth()*0.5 + 5)
            .attr("cursor", "pointer")
            .attr("stroke-width", 2)
            .text(d => d.name)
            .on("click", function(e, d) { emit("click-left", d.y, e) })
            .on("pointerenter", function() { d3.select(this).attr("fill", "#078766") })
            .on("pointerleave", function() { d3.select(this).attr("fill", null) })

        rg = svg.append("g")
            .selectAll("g")
            .data(props.dataRight)
            .join("g")
            .attr("font-size", 13)
            .attr("transform", d => `translate(${maxXPos*2},${yRight(d[props.yAttr])})`)

        rg.append("rect")
            .attr("x", d => maxXPos - x(d[props.xAttr]))
            .attr("y", 0)
            .attr("width", d => x(d[props.xAttr]))
            .attr("height", yRight.bandwidth())
            .attr("fill", "#078766")

        rg.append("text")
            .classed("background", true)
            .attr("x", maxXPos - 10)
            .attr("y", yRight.bandwidth()*0.5 + 5)
            .attr("text-anchor", "end")
            .attr("stroke", "#eee")
            .attr("stroke-width", 3)
            .text(d => d.name)
        rg.append("text")
            .classed("label", true)
            .attr("x", maxXPos - 10)
            .attr("y", yRight.bandwidth()*0.5 + 5)
            .attr("text-anchor", "end")
            .attr("cursor", "pointer")
            .text(d => d.name)
            .on("click", function(e, d) { emit("click-right", d.y, e) })
            .on("pointerenter", function() { d3.select(this).attr("fill", "#078766") })
            .on("pointerleave", function() { d3.select(this).attr("fill", null) })

        highlight();

    }

    function highlight() {
        const sels = DM.getFilter("tags", "id");
        lg.selectAll("text").attr("font-weight", d => sels && sels.includes(d[props.yAttr]) ? "bold" : null)
        lg.selectAll("text.background").attr("stroke", d => sels && sels.includes(d[props.yAttr]) ? "#0acb99" : "#eee")
    }

    onMounted(draw);

    watch(props, draw, { deep: true })
    watch(() => app.selectionTime, highlight)
</script>