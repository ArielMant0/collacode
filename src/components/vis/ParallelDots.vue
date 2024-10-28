<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { watch, ref, onMounted } from 'vue';

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
            default: 500
        },
    });

    const el = ref(null)

    let x, y, dimValues, dimCat;
    let radius, diameter, size;

    let points = [];

    function makeDimVals() {
        const vals = new Set()
        const cats = {}
        props.data.forEach(d => props.dimensions.forEach(dim => d[dim].forEach(dd => {
            cats[dd] = dim;
            vals.add(dd)
        })))
        dimCat = {}
        for (const key in cats) {
            const c = cats[key]
            if (!dimCat[c]) dimCat[c] = []
            dimCat[c].push(key)
        }
        return Array.from(vals.values()).map(d => ({ name: d, dimension: cats[d] }))
    }

    function extractPoints() {
        const data = [];
        props.data.forEach(d => {
            props.dimensions.forEach(dim => {
                d[dim].forEach(dd => {
                    data.push({ ext_id: d.id, name: dim, value: dd })
                });
            });
        })
        return data
    }

    function getX(d) {
        return 85 + size * Math.floor(d.index / Math.floor(y[d.name].bandwidth() / size))
    }
    function getY(d) {
        return diameter + size * Math.floor(d.index % Math.floor(y[d.name].bandwidth() / size))
    }

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove();

        if (props.data.length === 0 || props.dimensions.length === 0) return;

        dimValues = props.dimValues ? props.dimValues : makeDimVals();

        x = d3.scaleBand()
            .domain(props.dimensions)
            .range([25, props.width-5])
            .paddingInner(0.1)

        y = {}
        for (const key in dimCat) {
            y[key] = d3.scaleBand()
                .domain(dimCat[key])
                .range([25, props.height-5])
                .paddingInner(0.15)
        }

        const color = d3.scaleOrdinal(d3[props.colorScale])
            .domain(props.dimensions)
            .unknown("#ccc")

        radius = 4, diameter = radius * 2, size = diameter + 2
        points = extractPoints()

        const path = d3.line()
            // .curve(d3.curveLinear)
            .curve(d3.curveBumpX)
            .x((d, i) => x(d.name) + getX(d) - (i > 0 ? 75 : 0))
            .y(d => y[d.name](d.value) + getY(d))

        const allDots = svg.append("g").classed("dot-c", true)
        // draw dots
        d3.group(points, d => d.name).forEach((array, category) => {

            allDots.append("g")
                .classed("dots", true)
                .attr("transform", `translate(${x(category)},0)`)
                .selectAll("g")
                .data(d3.group(array, d => d.value))
                .join("g")
                .attr("transform", ([name, _]) => `translate(0,${y[category](name)})`)
                .selectAll("circle")
                .data(([_, vals]) => {
                    vals.forEach((d, i) => d.index = i)
                    return vals
                })
                .join("circle")
                .attr("cx", d => getX(d))
                .attr("cy", d => getY(d))
                .attr("r", radius)
                .attr("fill", d => color(d.name))
                .on("pointerenter", (_, d) => hoverLine(d.ext_id))
                .on("pointerleave", () => hoverLine(null))
        })

        const byExt = d3.group(points, d => d.ext_id)

        function arc(d1, d2) {
            const y1 = y[d1.name](d1.value) + getY(d1)
            const y2 = y[d2.name](d2.value) + getY(d2)
            const r = 25; //Math.abs(y2 - y1) / 2;
            const marginLeft = x(d1.name) + getX(d1)
            return `M${marginLeft},${y1}A${r},${r} 0,0,${y1 < y2 ? 0 : 1} ${marginLeft},${y2}`;
        }
        function boxLine(d1, d2, index) {
            const y1 = y[d1.name](d1.value) + getY(d1)
            const y2 = y[d2.name](d2.value) + getY(d2)
            const xc = x(d1.name) + getX(d1) - radius
            return `M ${xc},${y1} H ${x(d1.name)+(index+1)*5} V ${y2} H ${x(d1.name)+getX(d2)-radius}`;
        }

        // draw lines with low opacity
        svg.append("g")
            .selectAll("g")
            .data(byExt)
            .join("g")
            .selectAll("path")
            .data(([_, data]) => {
                const array = []
                const grouped = d3.group(data, d => d.name)
                for (let i = 0; i < props.dimensions.length-1; ++i) {
                    const dim1 = props.dimensions[i]
                    const dim2 = props.dimensions[i+1]
                    if (grouped.has(dim1) && grouped.has(dim2)) {
                        const data1 = grouped.get(dim1)
                        const data2 = grouped.get(dim2)
                        data1.forEach(d1 => data2.forEach(d2 => array.push([d1, d2])))
                    }
                }
                return array
            })
            .join("path")
                .attr("d", d => path(d))
                .classed("line", true)
                .attr("stroke", "black")
                // .style("mix-blend-mode", "multiply")
                .attr("stroke-width", 1)
                .attr("fill", "none")
                .attr("opacity", 1)

        // draw rects
        svg.append("g")
            .selectAll("rect")
            .data(dimValues)
            .join("rect")
            .attr("x", d => x(d.dimension))
            .attr("y", d => y[d.dimension](d.name))
            .attr("width", 75)
            .attr("height", d => y[d.dimension].bandwidth())
            .attr("fill", d => color(d.dimension))

        const pis = new Map()
        // draw lines for nodes in same category
        svg.append("g")
            .selectAll("g")
            .data(byExt)
            .join("g")
            .classed("self-line-c", true)
            .selectAll("path")
            .data(([_, data]) => {
                const array = []
                let idx = 0;
                const grouped = d3.group(data, d => d.name)
                for (let i = 0; i < props.dimensions.length; ++i) {
                    const dim1 = props.dimensions[i]
                    if (grouped.has(dim1)) {
                        const pi = pis.has(dim1) ? pis.get(dim1) : 0
                        const data1 = grouped.get(dim1)
                        for (let j = 0; j < data1.length-1; j++) {
                            array.push([data1[j], data1[j+1], pi])
                        }

                        if (data1.length > 1) { pis.set(dim1, pi+1) }
                    }
                }

                return array
            })
            .join("path")
                .classed("self-line", true)
                .attr("d", d => boxLine(d[0], d[1], d[2]))
                .attr("stroke", "white")
                .attr("stroke-width", 1)
                .attr("fill", "none")

        // raise dots
        allDots.raise()

        svg.append("g")
            .attr("font-size", 12)
            .selectAll("text")
            .data(dimValues)
            .join("text")
            .attr("x", d => x(d.dimension))
            .attr("y", d => y[d.dimension](d.name) - 5)
            .attr("fill", d => color(d.dimension))
            .attr("stroke-width", 3)
            .attr("stroke", "white")
            .attr("paint-order", "stroke")
            .text(d => d.name)

    }

    function hoverLine(id) {
        const svg =  d3.select(el.value)

        svg.selectAll(".line")
            .attr("opacity", d => d[0].ext_id === id ? 1 : (id ? 0.05 : 1))
            .attr("stroke-width", d => d[0].ext_id === id ? 3 : 1)

        svg.selectAll(".self-line")
            .attr("stroke", d => d[0].ext_id === id ? "black" : "white")
            .attr("stroke-width", d => d[0].ext_id === id ? 3 : 1)
            .attr("opacity", d => id == null || d[0].ext_id === id ? 1 : 0.2)

        svg.selectAll(".self-line-c")
            .filter(d => d[0] === id)
            .raise()

        svg.selectAll(".dots circle")
            .attr("r", d => d.ext_id == id ? radius+3 : radius)
            .attr("stroke", d => d.ext_id == id ? "black" : "none")
            .filter(d => d.ext_id === id)
            .raise()

        // const p = points.filter(d => d.ext_id === id)
        // const path = d3.line()
        //     .curve(d3.curveLinear)
        //     .x(d => x(d.name) + getX(d))
        //     .y(d => y[d.name](d.value) + getY(d))

        // // draw lines (on demand)
        // const svg = d3.select(el.value)
        // svg.selectAll(".hover-line")
        //     .data(id ? [{ id: id, data: p }] : [])
        //     .join("path")
        //         .classed("hover-line", true)
        //         .attr("d", d => path(d.data))
        //         .attr("stroke", "black")
        //         .attr("stroke-width", 2)
        //         .attr("fill", "none")
    }

    onMounted(draw)

    watch(props, draw, { deep: true });

</script>