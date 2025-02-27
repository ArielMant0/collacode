<template>
    <div style="position: relative; text-align: left;">
        <canvas ref="under" :width="width" :height="height"></canvas>
        <svg ref="underlay" style="position: absolute; top:0;left:0;" :width="width" :height="height"></svg>
        <canvas ref="over" style="pointer-events:none; position:absolute; top:0;left:0;" :width="width" :height="height"></canvas>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import DM from '@/use/data-manager';
    import { ref, onMounted, computed, watch, onUpdated } from 'vue';

    const props = defineProps({
        time: {
            type: Number,
            default: 0
        },
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
            default: 650
        },
        spacing: {
            type: Number,
            default: 25
        },
        levelSize: {
            type: Number,
            default: 3
        },
        radius: {
            type: Number,
            default: 4
        },
        nameAttr: {
            type: String,
            default: "dim"
        },
        valueAttr: {
            type: String,
            default: "value"
        },
        arrows: {
            type: Boolean,
            default: false
        }
    });

    const emit = defineEmits([
        "click-dot", "click-rect",
        "hover-dot", "hover-rect",
        "right-click-dot", "right-click-rect", "right-click-dim"
    ])

    const under = ref(null)
    const over = ref(null)
    const underlay = ref(null)

    let x, y, dimValues, dimCat, dimSum;
    let ctxU, ctxO, byExt, dims;

    let diameter, size, path;
    let dots, rects;

    let hoverDot = null, hoverRect = null;
    let hoverDim = null, hoverCat = null;

    const maxLevel = ref(1)
    const rectWidth = computed(() => props.linkBy ? Math.max(15 , props.levelSize * maxLevel.value) : 15)

    function makeDimVals() {
        dimCat = {}
        dimSum = {}

        const array = []
        const byDim = d3.group(props.data, d => d[props.nameAttr])
        byDim.forEach((vals, dim) => {
            const byValue = d3.group(vals, d => d[props.valueAttr])
            dimCat[dim] = Array.from(byValue.keys())
            dimCat[dim].sort()
            let sum = 0;
            byValue.forEach((vals2, name) => {
                array.push({
                    name: name,
                    dimension: dim,
                    value: vals2.length,
                    cat_id: vals2[0].cat_id
                });
                sum += vals2.length
            });
            dimSum[dim] = sum;
        })
        dimValues = array;
    }

    function calcMaxLevel() {

        maxLevel.value = 1;
        if (props.linkBy) {

            if (props.linkBy !== "meta_id") {
                const byLink = d3.group(props.data.filter(d => d[props.valueAttr] === props.dimensions[0]), d => d[props.linkBy])
                byLink.forEach(vals1 => {
                    maxLevel.value = Math.max(maxLevel.value, d3.group(vals1, d => d.meta_id).size + 2)
                });
            } else {

                const perName = new Map();
                const byLink = d3.group(props.data, d => d[props.linkBy])

                byLink.forEach(vals1 => {
                    const byName = d3.group(vals1, d => d[props.valueAttr])
                    byName.forEach((vals2, dim) => {
                        const prev = perName.get(dim) || 0
                        perName.set(dim, prev + (vals2.length > 1 ? 1 : 0))
                    });
                });

                maxLevel.value = d3.max(Array.from(perName.values())) + 2
            }
        }
    }

    function getX(dim, name, index) {
        const v = Math.floor(y[dim](name) / size)
        return rectWidth.value + size * (1 + (v === 0 ? v : Math.floor(index / v)))
    }
    function getY(dim, name, index) {
        const v = Math.floor(y[dim](name) / size)
        return diameter - 2 + size * (v < 1 ? 0 : index % v)
    }
    function getYPos(dim, name) {
        const tmp = dimValues.filter(dv => dv.dimension === dim)
        return tmp.slice(0, tmp.findIndex(dv => dv.name === name))
            .reduce((acc, dv) => acc + y[dv.dimension](dv.name) + props.spacing, 15 + props.spacing)
    }

    function init() {
        if (!under.value || !over.value)
        ctxU = ctxU ? ctxU : under.value.getContext("2d")
        ctxO = ctxO ? ctxO : over.value.getContext("2d")

        if (props.data.length === 0 || props.dimensions.length === 0) return;

        makeDimVals();
        calcMaxLevel();

        y = {}
        for (const key in dimCat) {
            y[key] = function() {
                const values = new Map();
                dimValues.filter(d => d.dimension === key).forEach(d => values.set(d.name, d.value))
                const scale = d3.scaleLinear()
                    .domain([0, Math.max(1, dimSum[key])])
                    .range([0, props.height - 15 - (props.spacing * (values.size+1))])

                return name => scale(values.get(name)) || 0
            }()
        }

        const ORDER = [
            "make sense", "why", "how long",
            "what", "encoding 2", "encoding 1",
            "mechanics", "level of expression", "automation",
            "mechanics coupling"
        ]
        dims = props.dimensions.slice()
        dims.sort((a, b) => ORDER.indexOf(a)-ORDER.indexOf(b))

        x = d3.scaleBand()
            .domain(dims)
            .range([15, props.width-15])
            .paddingInner(0.1)

        x.range([15, props.width-15+x.bandwidth()*0.5])
        diameter = props.radius * 2, size = diameter + 2

        byExt = d3.group(props.data, d => d.meta_id)

        draw()
    }

    function boxLineCanvas(ctx, d1, d2, index) {
        const dim1 = d1[props.nameAttr], val1 = d1[props.valueAttr];
        const dim2 = d2[props.nameAttr], val2 = d2[props.valueAttr];

        const y1 = getYPos(dim1, val1, d1.index) + getY(dim1, val1, d1.index)
        const y2 = getYPos(dim2, val2, d2.index) + getY(dim2, val2, d2.index)
        ctx.moveTo(x(dim1) + getX(dim1, val1, d1.index) - props.radius, y1)
        ctx.lineTo(x(dim1) + (index+1)*props.levelSize, y1)
        ctx.lineTo(x(dim1) + (index+1)*props.levelSize, y2)
        ctx.lineTo(x(dim1) + getX(dim2, val2, d2.index)-props.radius, y2)
    }

    function draw() {
        if (!x || !y || !byExt) return init()

        x = d3.scaleBand()
            .domain(dims)
            .range([15, props.width-15])
            .paddingInner(0.1)

        x.range([15, props.width-15+x.bandwidth()*0.5])
        diameter = props.radius * 2, size = diameter + 2

        // clear canvases
        ctxU.clearRect(0, 0, props.width, props.height)
        ctxO.clearRect(0, 0, props.width, props.height)
        // clear svg
        const svg = d3.select(underlay.value);
        svg.selectAll("*").remove();

        const color = d3.scaleOrdinal(d3[props.colorScale])
            .domain(dims)
            .unknown("#ccc")

        path = d3.line()
            // .curve(d3.curveBumpX)
            .context(ctxU)
            .x((d, i) => {
                const a = x(d[props.nameAttr])
                const b = getX(d[props.nameAttr], d[props.valueAttr], i > 0 ? 0 : d.index)
                return a + b - (i > 0 ? size+rectWidth.value : 0)
            })
            .y(d => {
                const a = getYPos(d[props.nameAttr], d[props.valueAttr])
                const b = getY(d[props.nameAttr], d[props.valueAttr], d.index)
                return a + b
            })


        const dimValIdx = new Map()
        byExt.forEach(points => {
            // assign index and position for each data point (circles)
            points.forEach(d => {
                const dim = d[props.nameAttr]
                const val = d[props.valueAttr]

                const perDim = dimValIdx.get(dim) || {}
                const idx = perDim[val] || 0
                d.index = idx;
                d.x = x(dim) + getX(dim, val, d.index);
                d.y = getYPos(dim, val) + getY(dim, val, d.index)
                perDim[val] = idx+1
                dimValIdx.set(dim, perDim)
            });
        });

        // draw rectangles
        rects = svg.append("g")
            .attr("stroke", "none")
            .attr("opacity", 1)
            .selectAll("rect")
            .data(dimValues)
            .join("rect")
            .attr("x", d => d.x = x(d.dimension))
            .attr("y", d => d.y = getYPos(d.dimension, d.name))
            .attr("width", rectWidth.value)
            .attr("height", d => d.height = y[d.dimension](d.name) || 3)
            .attr("fill", d => color(d.dimension))
            .style("cursor", "pointer")
            .on("pointerenter", (event, d) => {
                hoverRect = d.cat_id
                hoverCat = d.cat_id
                hoverDot = null
                emit("hover-rect", d.cat_id, event)
                highlight();
            })
            .on("pointerleave", () => {
                hoverRect = null
                hoverCat = null
                hoverDot = null
                emit("hover-rect", null, null)
                highlight();
            })
            .on("click", (event, d) => emit("click-rect", d.cat_id, event))
            .on("contextmenu", (event, d) => {
                event.preventDefault();
                emit("right-click-rect", d.cat_id, event)
            })

        // category names
        const catnames = svg.append("g")
            .selectAll("g")
            .data(dimValues)
            .join("g")
            .attr("stroke", "white")
            .attr("stroke-width", 3)
            .style("font-size", 12)
            .style("font-family", "sans-serif")
            .attr("transform", d => `translate(${d.x},${d.y-5})`)

        catnames
            .append("text")
            .attr("fill", d => color(d.dimension))
            .attr("paint-order", "stroke")
            .text(d => d.name)
            .on("pointerenter", function(_, d) {
                d3.select(this).attr("font-weight", "bold")
                hoverCat = d.cat_id;
            })
            .on("pointerleave", function() {
                d3.select(this).attr("font-weight", "normal")
                hoverCat = null;
            })
            .on("contextmenu", (event, d) => {
                event.preventDefault();
                emit("right-click-rect", d.cat_id, event)
            })

        if (props.arrows) {
            catnames
                .append("path")
                .attr("d", "M7.41,15.41L12,10.83L16.59,15.41L18,14L12,8L6,14L7.41,15.41Z")
                .attr("transform", `translate(-3,2)scale(0.85)`)
                .attr("fill", "black")
                .attr("stroke", "none")
                .on("click", (_, d) => moveUp(d.cat_id))

            catnames
                .append("path")
                .attr("d", "M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z")
                .attr("transform", `translate(-3,12)scale(0.85)`)
                .attr("fill", "black")
                .attr("stroke", "none")
                .on("click", (_, d) => moveDown(d.cat_id))
        }

        // dots
        dots = svg.append("g")
            .attr("stroke-width", 1)
            .attr("stroke", "none")
            .attr("opacity", 1)
            .selectAll("circle")
            .data(props.data)
            .join("circle")
            .attr("cx", d => d.x)
            .attr("cy", d => d.y)
            .attr("r", props.radius)
            .attr("fill", d => color(d[props.nameAttr]))
            .style("cursor", "pointer")
            .on("pointerenter", (event, d) => {
                hoverDot = d.meta_id;
                hoverRect = null;
                emit("hover-dot", d.meta_id, event)
                highlight();
            })
            .on("pointerleave", () => {
                hoverDot = null
                hoverRect = null
                emit("hover-dot", null, null)
                highlight();
            })
            .on("click", (event, d) => emit("click-dot", d.meta_id, event))
            .on("contextmenu", (event, d) => {
                event.preventDefault();
                emit("right-click-dot", d.meta_id, event)
            })

        // dimensions names
        const dimgs = svg.append("g")
            .selectAll("g")
            .data(dims)
            .join("g")
            .attr("transform", d => `translate(${x(d)},15)`)
            .style("font-size", 14)
            .style("font-family", "sans-serif")
            .attr("fill", d => color(d))

        dimgs
            .append("text")
            .attr("x", (_,i) => props.arrows ? (i == 0 || i == dims.length-1 ? 12 : 22) : 0)
            .text(d => d.length > 12 ? d.slice(0, 12)+'..' : d)
            .on("pointerenter", function(_, d) {
                d3.select(this).attr("font-weight", "bold")
                hoverDim = d;
            })
            .on("pointerleave", function() {
                d3.select(this).attr("font-weight", "normal")
                hoverDim = null;
            })
            .on("contextmenu", (event, d) => {
                event.preventDefault();
                emit("right-click-dim", d, event)
            })


        if (props.arrows) {
            dimgs
                .filter((_,i) => i > 0)
                .append("path")
                .attr("d", "M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z")
                .attr("transform", (_, i, nodes) => `translate(${i < nodes.length-1 ? -6 : -4},-15)scale(0.9)`)
                .attr("stroke", "none")
                .style("cursor", "pointer")
                .on("click", (_, d) => moveLeft(d))

            dimgs
                .filter((_,i) => i < dims.length-1)
                .append("path")
                .attr("d", "M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z")
                .attr("transform", (_, i) => `translate(${i > 0 ? 4 : -4},-15)scale(0.9)`)
                .attr("stroke", "none")
                .style("cursor", "pointer")
                .on("click", (_, d) => moveRight(d))
        }

        highlight()
    }

    function moveLeft(dim) {
        const idx = dims.indexOf(dim)
        dims.splice(idx, 1)
        dims.splice(idx-1, 0, dim)
        draw();
    }
    function moveRight(dim) {
        const idx = dims.indexOf(dim)
        dims.splice(idx, 1)
        dims.splice(idx+1, 0, dim)
        draw();
    }
    function moveUp(id) {
        const idx = dimValues.findIndex(d => d.cat_id === id)
        if (idx >= 0) {
            const item = dimValues.splice(idx, 1)[0]
            const newIdx = dimValues.findLastIndex((d, i) => d.dimension === item.dimension && i < idx)
            if (newIdx > 0) {
                dimValues.splice(newIdx, 0, item)
            } else {
                dimValues.splice(0, 0, item)
            }
            draw();
        }
    }
    function moveDown(id) {
        const idx = dimValues.findIndex(d => d.cat_id === id)
        if (idx >= 0) {
            const item = dimValues.splice(idx, 1)[0]
            const newIdx = dimValues.findIndex((d, i) => d.dimension === item.dimension && i >= idx)
            if (newIdx >= 0 && newIdx < dimValues.length-1) {
                dimValues.splice(newIdx+1, 0, item)
            } else {
                dimValues.push(item)
            }
            draw();
        }
    }

    function highlight() {
        if (!dots || !rects) return;

        const ids = new Set(hoverDot ? [hoverDot] : []).union(DM.getSelectedIds("meta_items"))

        const cats = new Set(hoverRect ? [hoverRect] : [])
        if (DM.hasFilter('meta_categories')) {
            DM.getSelectedIdsArray("meta_categories").forEach(cid => cats.add(cid))
        }

        const hasHover = hoverDot !== null || hoverRect !== null;
        const noSel = ids.size === 0;
        const selected = (eids, cids) => eids.some(d => ids.has(d)) || cids.some(d => d === hoverRect)
        const selectedDot = eid => ids.has(eid)

        const color = d3.scaleOrdinal(d3[props.colorScale])
            .domain(dims)
            .unknown("#ccc")

        dots
            .each(d => d.selected = selectedDot(d.meta_id))
            .attr("r", d => props.radius + (d.selected ? 2 : 0))
            .attr("fill", d => color(d[props.nameAttr]))
            .attr("stroke", d => d.selected || hoverRect === d.cat_id ? "black" : "none")
            .attr("opacity", d => d.selected || (ids.size === 0 && !hasHover) || hoverRect === d.cat_id ? 1 : 0.2)

        rects
            .attr("stroke", d => cats.has(d.cat_id) ? "black" : "none")
            .attr("opacity", d => cats.size === 0 || cats.has(d.cat_id) ? 1 : 0.5)

        ctxU.clearRect(0, 0, props.width, props.height)
        // draw links
        byExt.forEach((points, extId) => {
            const grouped = d3.group(points, d => d[props.nameAttr])
            ctxU.strokeStyle = "black"
            ctxU.fillStyle = "none"

            // draw connecting links
            for (let i = 0; i < dims.length-1; ++i) {
                const dim1 = dims[i]
                const dim2 = dims[i+1]
                if (grouped.has(dim1) && grouped.has(dim2)) {
                    const data1 = grouped.get(dim1)
                    const data2 = grouped.get(dim2)
                    data1.forEach(d1 => data2.forEach(d2 => {
                        ctxU.beginPath()
                        const sel = selected([extId], [d1.cat_id, d2.cat_id])
                        ctxU.lineWidth = sel ? 2 : 1
                        ctxU.globalAlpha = sel ? 1 : 0.2
                        path([d1, d2])
                        ctxU.stroke()
                        ctxU.closePath()
                    }))
                }
            }
        });

        if (props.linkBy) {
            ctxO.clearRect(0, 0, props.width, props.height)

            const grouped = props.linkBy === "meta_id" ? byExt :
                d3.group(props.data, d => d[props.linkBy])

            const pis = new Map()

            grouped.forEach(vals => {
                if (props.linkBy !== "meta_id") {
                    const numMetas = d3.group(vals, d => d.meta_id)
                    if (numMetas.size < 2) return;
                }

                const g2 = d3.group(vals, d => d[props.nameAttr])
                for (let i = 0; i < dims.length; ++i) {
                    const dim1 = dims[i]
                    if (g2.has(dim1)) {
                        const pi = pis.has(dim1) ? pis.get(dim1) : 0
                        const data1 = g2.get(dim1)
                        for (let j = 0; j < data1.length-1; j++) {
                            const sel = selected(
                                [data1[j].meta_id, data1[j+1].meta_id],
                                [data1[j].cat_id, data1[j+1].cat_id],
                            )
                            ctxO.lineWidth = sel ? 2 : 1;
                            ctxO.strokeStyle = sel ? "black" : "white"
                            ctxO.globalAlpha = noSel || sel ? 1 : 0.2
                            ctxO.beginPath()
                            boxLineCanvas(ctxO, data1[j], data1[j+1], pi)
                            ctxO.stroke()
                            ctxO.closePath();
                        }
                        if (data1.length > 1) { pis.set(dim1, pi+1) }
                    }
                }
            })
        }
    }

    onMounted(function() {
        window.addEventListener("keyup", (event) => {
            if (hoverDim) {
                switch(event.code) {
                    case "KeyA":
                    case "ArrowLeft":
                        moveLeft(hoverDim)
                        break;
                    case "KeyD":
                    case "ArrowRight":
                        moveRight(hoverDim)
                        break;
                }
            } else if (hoverCat) {
                switch(event.code) {
                    case "KeyW":
                    case "ArrowUp":
                        moveUp(hoverCat)
                        break;
                    case "KeyS":
                    case "ArrowDown":
                        moveDown(hoverCat)
                        break;
                }
            }
        })
        init()
    })
    onUpdated(draw)

    watch(() => ([
        props.data,
        props.dimensions,
        props.dimValues,
        props.width,
        props.height,
        props.levelSize,
        props.linkBy,
        props.radius,
        props.spacing,
        props.nameAttr,
        props.valueAttr
    ]), init.bind(null, 150))
    watch(() => ([props.time, props.colorScale]), highlight, { deep: true })

</script>