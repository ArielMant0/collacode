<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import DM from '@/use/data-manager';
    import { watch, ref, onMounted, computed } from 'vue';

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        linkBy: {
            type: String,
            default: "",
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
        levelSize: {
            type: Number,
            default: 4
        },
        radius: {
            type: Number,
            default: 4
        },
    });

    const emit = defineEmits(["click-dot", "click-rect", "hover-dot", "hover-rect"])

    const el = ref(null)

    let x, y, dimValues, dimValIdx, dimCat;
    let diameter, size;

    const maxLevel = ref(1)
    const rectWidth = computed(() => props.linkBy ? Math.max(15 , props.levelSize * maxLevel.value) : 15)

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
                    data.push({ ext_id: d.id, group_id: d.group_id, name: dim, value: dd })
                });
            });
        })

        maxLevel.value = 1;
        if (props.linkBy) {

            if (props.linkBy !== "ext_id") {
                const byLink = d3.group(data.filter(d => d.name === props.dimensions[0]), d => d[props.linkBy])
                byLink.forEach(vals1 => {
                    maxLevel.value = Math.max(maxLevel.value, d3.group(vals1, d => d.ext_id).size + 2)
                });
            } else {

                const perName = new Map();
                const byLink = d3.group(data, d => d[props.linkBy])

                byLink.forEach(vals1 => {
                    const byName = d3.group(vals1, d => d.name)
                    byName.forEach((vals2, dim) => {
                        if (props.linkBy === "ext_id") {
                            const prev = perName.get(dim) || 0
                            perName.set(dim, prev + (vals2.length > 1 ? 1 : 0))
                        }
                    });
                });

                maxLevel.value = d3.max(Array.from(perName.values())) + 2
            }
        }

        return data
    }

    function getX(dim, name, index) {
        return rectWidth.value + size * (1+Math.floor(index / Math.floor(y[dim](name) / size)))
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

        x.range([25, props.width-5+x.bandwidth()*0.5])

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

        diameter = props.radius * 2, size = diameter + 2

        const path = d3.line()
            .curve(d3.curveBumpX)
            .x((d, i) => x(d.name) + getX(d.name, d.value, d.index) - (i > 0 ? rectWidth.value+size : 0))
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
                .attr("r", props.radius)
                .attr("fill", d => color(d.name))
                .on("pointerenter", (event, d) => {
                    emit("hover-dot", event, d.ext_id)
                    hoverLine(d.ext_id)
                })
                .on("pointerleave", (event) => {
                    emit("hover-dot", event, null)
                    hoverLine()
                })
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
            const xc = x(d1.name) + getX(d1.name, d1.value, d1.index) - props.radius
            return `M ${xc},${y1} H ${x(d1.name) + (index+1)*props.levelSize} V ${y2} H ${x(d1.name)+getX(d2.name, d2.value, d2.index)-props.radius}`;
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
            .attr("width", rectWidth.value)
            .attr("height", d => y[d.dimension](d.name))
            .attr("fill", d => color(d.dimension))
            .on("pointerenter", (event, d) => {
                emit("hover-rect", event, d.name)
                hoverLine(null, d.name)
            })
            .on("pointerleave", (event) => {
                emit("hover-rect", event, null)
                hoverLine()
            })
            .on("click", function(_, d) {
                emit("click-rect", d.name)
                hoverLine()
            })

        if (props.linkBy) {

            const grouped = props.linkBy === "ext_id" ?
                byExt :
                d3.group(points, d => d[props.linkBy])

            const pis = new Map()
            // draw lines for nodes in same category
            svg.append("g")
                .selectAll("g")
                .data(grouped)
                .join("g")
                .classed("self-line-c", true)
                .selectAll("path")
                .data(([_, data]) => {
                    const array = []
                    if (props.linkBy !== "ext_id") {
                        const numExts = d3.group(data, d => d.ext_id)
                        if (numExts.size < 2) return array;
                    }

                    const g2 = d3.group(data, d => d.name)
                    for (let i = 0; i < props.dimensions.length; ++i) {
                        const dim1 = props.dimensions[i]
                        if (g2.has(dim1)) {
                            const pi = pis.has(dim1) ? pis.get(dim1) : 0
                            const data1 = g2.get(dim1)
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

                pis.forEach(num => maxLevel.value = Math.max(maxLevel.value, num))
        }
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

    function hoverLine(id=null, rect=null) {
        const svg =  d3.select(el.value)

        const ids = new Set((id ? [id] : []).concat(DM.hasFilter("externalizations") ? DM.getSelectedIds("externalizations") : []))

        const cats = new Set(rect ? [rect] : [])
        if (DM.hasFilterData('externalizations', 'categories')) {
            DM.getFilterData("externalizations", "categories").forEach(name => cats.add(name))
        }

        const hasHover = id !== null || rect !== null;

        const selected = (eids, names) => eids.some(d => ids.has(d)) || names.some(d => cats.has(d))

        svg.selectAll(".line")
            .each(d => d.selected = selected([d[0].ext_id, d[1].ext_id], [d[0].value, d[1].value]))
            .attr("opacity", d => ids.size === 0 && !hasHover || d.selected ? 1 : 0.1)
            .attr("stroke-width", d => d.selected  ? 3 : 1)

        svg.selectAll(".self-line")
            .each(d => d.selected = selected([d[0].ext_id, d[1].ext_id], [d[0].value, d[1].value]))
            .attr("stroke", d => d.selected ? "black" : "white")
            .attr("stroke-width", d => d.selected ? 3 : 1)
            .attr("opacity", d => ids.size === 0 && !hasHover || d.selected ? 1 : 0.5)

        svg.selectAll(".self-line-c")
            .each(d => d.selected = selected([d[0].ext_id, d[1].ext_id], [d[0].value, d[1].value]))
            .attr("stroke-dasharray", null)
            .filter(d => d.selected)
            .attr("stroke-dasharray", "2 2")
            .raise()

        svg.selectAll(".dots circle")
            .each(d => d.selected = selected([d.ext_id], [d.value]))
            .attr("r", d => d.selected ? props.radius+2 : props.radius)
            .attr("stroke", d => d.selected ? "black" : "none")
            .filter(d => d.selected)
            .raise()

        svg.selectAll(".category")
            .attr("opacity", d => cats.size === 0 || cats.has(d.name) ? 1 : 0.25)
            .attr("stroke", d => cats.has(d.name) ? "black" : "none")
    }

    onMounted(draw)

    watch(props, draw, { deep: true });

</script>