<template>
    <svg ref="el" :width="size" :height="size"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { watch, ref, onMounted, computed } from 'vue';

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        dimensions: {
            type: Array,
            required: true
        },
        dimValues: {
            type: Object,
            required: false
        },
        colorScale: {
            type: String,
            default: "schemeCategory10"
        },
        width: {
            type: Number,
            default: 1000
        },
        height: {
            type: Number,
            default: 600
        },
    });

    const el = ref(null)
    let dimValues, dimCat;

    const size = computed(() => Math.min(props.width, props.height))

    function makeDimVals() {
        const vals = new Set()
        dimCat = {}
        props.data.forEach(d => props.dimensions.forEach(dim => d[dim].forEach(dd => {
            dimCat[dd] = dim;
            vals.add(dd)
        })))
        return Array.from(vals.values())
    }
    function makeMatrix() {
        const n = dimValues.length
        const mat = new Array(n)
        for (let i = 0; i < n; ++i) {
            mat[i] = new Array(n)
            mat[i].fill(0)
        }
        props.data.forEach(d => {
            props.dimensions.forEach((d1, i) => {
                for (let j = i; j < props.dimensions.length; ++j) {
                    const d2 = props.dimensions[j]
                    const all = d3.cross(d[d1], d[d2])
                    all.forEach(([v1, v2]) => {
                        const idx1 = dimValues.indexOf(v1)
                        const idx2 = dimValues.indexOf(v2)
                        mat[idx1][idx2]++
                    });
                }
            });
        });
        return mat
    }

    function groupTicks(d, step=1) {
        const k = (d.endAngle - d.startAngle) / d.value;
        return d3.range(0, d.value, step).map(value => {
            return {value: value, angle: value * k + d.startAngle};
        });
    }

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove();

        if (props.data.length === 0 || props.dimensions.length === 0) return;

        dimValues = props.dimValues ? props.dimValues : makeDimVals();
        dimValues.sort((a, b) => props.dimensions.indexOf(dimCat[a])-props.dimensions.indexOf(dimCat[b]))

        const outerRadius = size.value * 0.5 - 60;
        const innerRadius = outerRadius - 10;
        svg.attr("viewBox", [-outerRadius, -outerRadius, size.value, size.value])

        const matrix = makeMatrix()

        const chord = d3.chord()
            .padAngle(10 / innerRadius)
            .sortSubgroups(d3.descending)
            .sortChords(d3.descending)

        const arc = d3.arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius);

        const ribbon = d3.ribbon()
            .radius(innerRadius - 1)
            .padAngle(1 / innerRadius);

        const formatValue = d3.format(".0f")
        const color = d3.scaleOrdinal(d3[props.colorScale])
            .domain(props.dimensions)
            .unknown("#ccc")

        const chords = chord(matrix);

        const group = svg.append("g")
            .selectAll()
            .data(chords.groups)
            .join("g");

        group.append("path")
            .attr("fill", d => color(dimCat[dimValues[d.index]]))
            .attr("d", arc);

        group.append("title").text(d => `${dimCat[dimValues[d.index]]} -> ${dimValues[d.index]}\n${formatValue(d.value)}`);

        // const groupTick = group.append("g")
        //     .selectAll()
        //     .data(d => groupTicks(d, tickStep))
        //     .join("g")
        //     .attr("transform", d => `rotate(${d.angle * 180 / Math.PI - 90}) translate(${outerRadius},0)`);

        // groupTick.append("line")
        //     .attr("stroke", "currentColor")
        //     .attr("x2", 6);

        // groupTick.append("text")
        //     .attr("x", 8)
        //     .attr("dy", "0.35em")
        //     .attr("transform", d => d.angle > Math.PI ? "rotate(180) translate(-16)" : null)
        //     .attr("text-anchor", d => d.angle > Math.PI ? "end" : null)
        //     .text(d => formatValue(d.value));

        // group.select("text")
        //     .attr("font-weight", "bold")
        //     .text(function(d) {
        //         return this.getAttribute("text-anchor") === "end"
        //             ? `↑ ${dimCat[dimValues[d.index]]}`
        //             : `${dimCat[dimValues[d.index]]} ↓`;
        //     });

        svg.append("g")
            .attr("fill-opacity", 0.8)
            .selectAll("path")
            .data(chords)
            .join("path")
            .style("mix-blend-mode", "multiply")
            .attr("fill", d => color(dimCat[dimValues[d.source.index]]))
            .attr("d", ribbon)
            .append("title")
            .text(d => `${formatValue(d.source.value)} ${dimValues[d.target.index]} → ${dimValues[d.source.index]}${d.source.index === d.target.index ? "" : `\n${formatValue(d.target.value)} ${dimValues[d.source.index]} → ${dimValues[d.target.index]}`}`);
    }

    onMounted(draw)

    watch(props, draw, { deep: true });

</script>
