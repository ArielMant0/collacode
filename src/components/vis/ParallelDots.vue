<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import DM from '@/use/data-manager';
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
        spacing: {
            type: Number,
            default: 25
        },
    });

    const emit = defineEmits(["click-dot", "click-rect"])

    const el = ref(null)

    let x, y, dimValues, dimValIdx, dimCat;
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

    function getX(dim, name, index) {
        return 85 + size * Math.floor(index / Math.floor(y[dim](name) / size))
    }
    function getY(dim, name, index) {
        return diameter + size * Math.floor(index % Math.floor(y[dim](name) / size))
    }
    function getYPos(dim, name) {
        const tmp = dimValues.filter(dv => dv.dimension === dim)
        return props.spacing +
            tmp.slice(0, tmp.findIndex(dv => dv.name === name))
            .reduce((acc, dv) => acc + y[dv.dimension](dv.name) + props.spacing, 0)
    }

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove();

        if (props.data.length === 0 || props.dimensions.length === 0) return;

        dimValues = props.dimValues ? props.dimValues : makeDimVals();
        dimValIdx = new Map()
        dimValues.forEach((d, i) => dimValIdx.set(d.name, i))

        points = extractPoints()
        const byDim = d3.group(points, d => d.name);

        x = d3.scaleBand()
            .domain(props.dimensions)
            .range([25, props.width-5])
            .paddingInner(0.1)

        y = {}
        for (const key in dimCat) {
            y[key] = function() {
                let sum = 0;
                const values = new Map();
                dimCat[key].forEach(k => {
                    values.set(k, byDim.get(key).filter(d => d.value === k).length)
                    sum += values.get(k)
                })
                const scale = d3.scaleLinear()
                    .domain([0, sum])
                    .range([0, props.height - (props.spacing * (values.size+1))])

                return name => scale(values.get(name)) || 0
            }()
            // d3.scaleBand()
            //     .domain(dimCat[key])
            //     .range([25, props.height-5])
            //     .paddingInner(0.15)
        }

        const color = d3.scaleOrdinal(d3[props.colorScale])
            .domain(props.dimensions)
            .unknown("#ccc")

        radius = 4, diameter = radius * 2, size = diameter + 2

        const path = d3.line()
            .curve(d3.curveBumpX)
            .x((d, i) => x(d.name) + getX(d.name, d.value, d.index) - (i > 0 ? 85 : 0))
            .y(d => getYPos(d.name, d.value) + getY(d.name, d.value, d.index))

        const allDots = svg.append("g").classed("dot-c", true)

        // draw dots
        byDim.forEach((array, category) => {

            allDots.append("g")
                .classed("dots", true)
                .attr("transform", `translate(${x(category)},0)`)
                .selectAll("g")
                .data(d3.group(array, d => d.value))
                .join("g")
                .attr("transform", ([name, _]) => `translate(0,${getYPos(category, name)})`)
                .selectAll("circle")
                .data(([_, vals]) => {
                    vals.forEach((d, i) => d.index = i)
                    return vals
                })
                .join("circle")
                .attr("cx", d => getX(d.name, d.value, d.index))
                .attr("cy", d => getY(d.name, d.value, d.index))
                .attr("r", radius)
                .attr("fill", d => color(d.name))
                .on("pointerenter", (_, d) => hoverLine(d.ext_id))
                .on("pointerleave", () => hoverLine(null))
                .on("click", function(_, d) {
                    emit("click-dot", d.ext_id)
                    hoverLine(d.ext_id)
                })
        })

        const byExt = d3.group(points, d => d.ext_id)

        function arc(d1, d2) {
            const y1 = getYPos(d1.name, d1.value) + getY(d1.name, d1.value, d1.index)
            const y2 = getYPos(d2.name, d2.value) + getY(d2.name, d2.value, d2.index)
            const r = Math.abs(y2 - y1) / 2;
            const marginLeft = x(d1.name) + getX(d1.name, d1.value, d1.index)
            return `M${marginLeft},${y1}A${r},${r} 0,0,${y1 < y2 ? 0 : 1} ${marginLeft},${y2}`;
        }
        function boxLine(d1, d2, index) {
            const y1 = getYPos(d1.name, d1.value, d1.index) + getY(d1.name, d1.value, d1.index)
            const y2 = getYPos(d2.name, d2.value, d2.index) + getY(d2.name, d2.value, d2.index)
            const xc = x(d1.name) + getX(d1.name, d1.value, d1.index) - radius
            return `M ${xc},${y1} H ${x(d1.name) + 2 + index*4} V ${y2} H ${x(d1.name)+getX(d2.name, d2.value, d2.index)-radius}`;
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
                .attr("stroke-width", 1)
                .attr("fill", "none")
                .attr("opacity", 0.5)

        // draw rects
        svg.append("g")
            .selectAll("rect")
            .data(dimValues)
            .join("rect")
            .classed("category", true)
            .attr("x", d => x(d.dimension))
            .attr("y", d => getYPos(d.dimension, d.name))
            .attr("width", 75)
            .attr("height", d => y[d.dimension](d.name))
            .attr("fill", d => color(d.dimension))
            .on("click", function(_, d) {
                emit("click-rect", d.name)
                hoverLine(null)
            })

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
            .attr("y", d => getYPos(d.dimension, d.name) - 5)
            .attr("fill", d => color(d.dimension))
            .attr("stroke-width", 3)
            .attr("stroke", "white")
            .attr("paint-order", "stroke")
            .text(d => d.name)

    }

    function hoverLine(id) {
        const svg =  d3.select(el.value)

        const ids = new Set((id ? [id] : []).concat(DM.hasFilter("externalizations") ? DM.getSelectedIds("externalizations") : []))

        svg.selectAll(".line")
            .attr("opacity", d => ids.size === 0 || ids.has(d[0].ext_id) ? 1 : 0.1)
            .attr("stroke-width", d => ids.has(d[0].ext_id) ? 3 : 1)

        svg.selectAll(".self-line")
            .attr("stroke", d => ids.has(d[0].ext_id) ? "black" : "white")
            .attr("stroke-width", d => ids.has(d[0].ext_id) ? 3 : 1)
            .attr("opacity", d => ids.size === 0 || ids.has(d[0].ext_id) ? 1 : 0.5)

        svg.selectAll(".self-line-c")
            .attr("stroke-dasharray", null)
            .filter(d => ids.has(d[0]))
            .attr("stroke-dasharray", "2 2")
            .raise()

        svg.selectAll(".dots circle")
            .attr("r", d => ids.has(d.ext_id) ? radius+3 : radius)
            .attr("stroke", d => ids.has(d.ext_id) ? "black" : "none")
            .filter(d => ids.has(d.ext_id))
            .raise()

        let cats = new Set()
        if (DM.hasFilterData('externalizations', 'categories')) {
            cats = DM.getFilterData("externalizations", "categories")
        }

        svg.selectAll(".category")
            .attr("opacity", d => cats.size === 0 || cats.has(d.name) ? 1 : 0.25)
            // .style("filter", d => cats.size === 0 || cats.has(d.name) ? "saturation(1)" : "saturation(0.5)")
    }

    onMounted(draw)

    watch(props, draw, { deep: true });

</script>