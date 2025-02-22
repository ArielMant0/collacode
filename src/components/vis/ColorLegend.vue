<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3';
    import { ref, computed, onMounted, watch } from 'vue';

    const props = defineProps({
        colors: { type: Array },
        ticks: { type: Array },
        scaleName: { type: String },
        scaleType: {
            type: String,
            default: "sequential"
        },
        minValue:{ type: Number },
        maxValue:{ type: Number },
        numTicks:{
            type: Number,
            default: 30
        },
        size: {
            type: Number,
            default: 100
        },
        rectSize: {
            type: Number,
            default: 25
        },
        rectBorder: {
            type: Boolean,
            default: false
        },
        vertical: {
            type: Boolean,
            default: false
        },
        clickable: {
            type: Boolean,
            default: false
        },
        hideDomain: {
            type: Boolean,
            default: false
        },
        everyTick: {
            type: Number,
            default: 1
        },
    })

    const emit = defineEmits(["click"])

    let scale;
    const padding = 50, offset = 5;

    const el = ref(null);

    const width = computed(() => props.vertical ? props.rectSize + padding : props.size)
    const height = computed(() => props.vertical ? props.size : props.rectSize + padding)

    let theTicks, colorvals, rectOtherSize;

    function scaleFromTicks() {
        scale = d3.scaleBand()
            .domain(d3.range(props.colors.length))
            .range([offset, props.size-offset])
            .paddingInner(props.rectBorder ? 0.1 : 0)

        theTicks = props.ticks
        rectOtherSize = scale.bandwidth()
        colorvals = props.colors
    }
    function scaleFromName() {
        switch (props.scaleType) {
            case "ordinal":
                theTicks = d3.range(0, props.numTicks)
                const tmp = d3.scaleOrdinal(d3[props.scaleName]).domain(theTicks)
                colorvals = theTicks.map(tmp)
                break;
            case "diverging": {
                const tmp = d3.scaleDiverging(d3[props.scaleName]).domain([props.minValue, 0, props.maxValue])
                const step = (props.maxValue - props.minValue) / (props.numTicks-1)
                const vals = d3.range(props.minValue, props.maxValue+step, step)
                vals.push(props.maxValue)
                theTicks = vals.map(d => +d.toFixed(Number.isInteger(d) ? 0 : 2))
                colorvals = theTicks.map(tmp)
                break;
            }
            default:
            case "sequential": {
                const tmp = d3.scaleSequential(d3[props.scaleName]).domain([props.minValue, props.maxValue])
                const step = (props.maxValue - props.minValue) / (props.numTicks-1)
                const vals = d3.range(props.minValue, props.maxValue+step, step)
                vals.push(props.maxValue)
                theTicks = vals.map(d => +d.toFixed(Number.isInteger(d) ? 0 : 2))
                colorvals = theTicks.map(tmp)
                break;
            }
        }

        scale = d3.scaleBand()
            .domain(d3.range(0, theTicks.length))
            .range([offset, props.size-offset])
            .paddingInner(props.rectBorder ? 0.1 : 0)

        rectOtherSize = scale.bandwidth()
    }
    function draw() {
        const svg = d3.select(el.value);
        svg.selectAll("*").remove();

        if (props.colors !== undefined && props.ticks !== undefined) {
            scaleFromTicks()
        } else if (props.scaleName !== undefined && props.minValue !== undefined && props.maxValue !== undefined) {
            scaleFromName()
        } else {
            return;
        }

        const rects = svg.append("g")
            .selectAll("rect")
            .data(colorvals)
            .join("rect")
            .attr("x", (_, i) => props.vertical ? offset : scale(i))
            .attr("y", (_, i) => props.vertical ? scale(i) : offset)
            .attr("width", props.vertical ? props.rectSize : rectOtherSize)
            .attr("height", props.vertical ? rectOtherSize : props.rectSize)
            .attr("fill", d => d)
            .attr("stroke", d => props.rectBorder ? d3.color(d).darker(0.5) : "none")

        if (props.clickable) {
            rects
                .style("cursor", "pointer")
                .on("pointerenter", function() {
                    d3.select(this).style("filter", "saturate(3)")
                })
                .on("pointerleave", function() {
                    d3.select(this).style("filter", "none")
                })
                .on("click", function(_, d) {
                    const idx = colorvals.indexOf(d)
                    emit("click", theTicks[idx], d)
                })
        }

        const ticks = svg.append("g")
            .attr("transform", `translate(${props.vertical ? props.rectSize+offset : 0}, ${props.vertical ? 0 : props.rectSize+offset})`)
            .call(props.vertical ? d3.axisRight(scale) : d3.axisBottom(scale))

        const lastNum = colorvals.length-1;

        if (props.everyTick > 1) {
            ticks.selectAll(".tick")
                .filter((_, i) => {
                    if (i === 0 || i === lastNum) {
                        return false;
                    } else if (i >= props.everyTick || i <= lastNum - props.everyTick) {
                        return i % props.everyTick !== 0;
                    }
                    return true;
                }).remove()
        }

        if (props.hideDomain) ticks.select(".domain").remove()

        if (!props.vertical) {
            ticks.selectAll(".tick text")
                .filter(d => (""+theTicks[d]).length*5 <= rectOtherSize)
                .text(d => theTicks[d])

            ticks.selectAll(".tick text")
                .filter(d => (""+theTicks[d]).length*5 > rectOtherSize)
                .text(() => "")
                .attr("dx", 0)
                .selectAll("tspan")
                .data(d => (""+theTicks[d]).split(" "))
                .join("tspan")
                .text(d => d)
                .attr("x", props.vertical ? "2em" : 0)
                .attr("dy", (_, i) => (0.75+i*0.35)+"em")
                .attr("text-anchor", "middle")
        } else {
            ticks.selectAll(".tick text").text(d => theTicks[d])
        }
    }

    onMounted(draw)

    watch(props, draw, { deep: true })

</script>