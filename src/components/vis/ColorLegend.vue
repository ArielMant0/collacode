<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3';
    import { ref, computed, onMounted, watch } from 'vue';

    const props = defineProps({
        colors: {
            type: Array,
            required: true
        },
        ticks: {
            type: Array,
            required: true
        },
        size: {
            type: Number,
            default: 100
        },
        rectSize: {
            type: Number,
            default: 25
        },
        vertical: {
            type: Boolean,
            default: false
        },
        everyTick: {
            type: Number,
            default: 1
        }
    })

    let scale = d3.scaleBand();
    const padding = 75, offset = 5;

    const el = ref(null);

    const width = computed(() => props.vertical ? props.rectSize + padding : props.size)
    const height = computed(() => props.vertical ? props.size : props.rectSize + padding)

    function draw() {
        const svg = d3.select(el.value);
        svg.selectAll("*").remove();

        scale
            .domain(d3.range(props.colors.length))
            .range([offset, props.size-offset])

        svg.append("g")
            .selectAll("rect")
            .data(props.colors)
            .join("rect")
            .attr("x", (_, i) => props.vertical ? offset : scale(i))
            .attr("y", (_, i) => props.vertical ? scale(i) : offset)
            .attr("width", props.vertical ? props.rectSize : scale.bandwidth())
            .attr("height", props.vertical ? scale.bandwidth() : props.rectSize)
            .attr("fill", d => d)

        svg.append("g")
            .selectAll("rect")
            .data(props.colors)
            .join("rect")
            .attr("x", (_, i) => props.vertical ? offset : scale(i))
            .attr("y", (_, i) => props.vertical ? scale(i) : offset)
            .attr("width", props.vertical ? props.rectSize : scale.bandwidth())
            .attr("height", props.vertical ? scale.bandwidth() : props.rectSize)
            .attr("fill", d => d)


        const ticks = svg.append("g")
            .attr("transform", `translate(${props.vertical ? props.rectSize+offset : 0}, ${props.vertical ? 0 : props.rectSize+offset})`)
            .call(props.vertical ? d3.axisRight(scale) : d3.axisBottom(scale))

        const lastNum = props.colors.length-1;

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

        if (!props.vertical) {
            ticks.selectAll(".tick text")
                .text(() => "")
                .attr("dx", 0)
                .attr("text-anchor", "middle")
                .selectAll("tspan")
                .data(d => props.ticks[d].split(" "))
                .join("tspan")
                .text(d => d)
                .attr("x", props.vertical ? "2em" : 0)
                .attr("dy", (_, i) => (0.75+i*0.35)+"em")
                .attr("text-anchor", "middle")
        } else {
            ticks.selectAll(".tick text").text(d => props.ticks[d])
        }
    }

    onMounted(draw)

    watch(props, draw, { deep: true })

</script>