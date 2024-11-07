<template>
    <canvas ref="el" :width="width" :height="height" @pointermove="onMove" @click="onClick"></canvas>
</template>

<script setup>
    import * as d3 from 'd3'
    import DM from '@/use/data-manager';
    import { ref, onMounted, computed, watch } from 'vue';

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
        }
    });

    const emit = defineEmits(["click-dot", "click-rect", "hover-dot", "hover-rect"])

    const el = ref(null)

    let x, y, dimValues, dimCat, dimSum;
    let ctx, byExt, dims;

    let hoverDot = null, hoverRect = null, links;

    let diameter, size;

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

            if (props.linkBy !== "ext_id") {
                const byLink = d3.group(props.data.filter(d => d[props.valueAttr] === props.dimensions[0]), d => d[props.linkBy])
                byLink.forEach(vals1 => {
                    maxLevel.value = Math.max(maxLevel.value, d3.group(vals1, d => d.ext_id).size + 2)
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

    function init(delay=0) {
        ctx = ctx ? ctx : el.value.getContext("2d")

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
            .range([5, props.width-5])
            .paddingInner(0.1)

        x.range([5, props.width-5+x.bandwidth()*0.5])
        diameter = props.radius * 2, size = diameter + 2

        byExt = d3.group(props.data, d => d.ext_id)
        links = []

        setTimeout(draw, delay)
    }

    function draw() {
        if (!x || !y || !byExt) return init()
        ctx.clearRect(0, 0, props.width, props.height)

        const color = d3.scaleOrdinal(d3[props.colorScale])
            .domain(dims)
            .unknown("#ccc")

        const path = d3.line()
            .curve(d3.curveBumpX)
            .context(ctx)
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

        function boxLineCanvas(d1, d2, index) {
            const dim1 = d1[props.nameAttr], val1 = d1[props.valueAttr];
            const dim2 = d2[props.nameAttr], val2 = d2[props.valueAttr];

            const y1 = getYPos(dim1, val1, d1.index) + getY(dim1, val1, d1.index)
            const y2 = getYPos(dim2, val2, d2.index) + getY(dim2, val2, d2.index)
            ctx.moveTo(x(dim1) + getX(dim1, val1, d1.index) - props.radius, y1)
            ctx.lineTo(x(dim1) + (index+1)*props.levelSize, y1)
            ctx.lineTo(x(dim1) + (index+1)*props.levelSize, y2)
            ctx.lineTo(x(dim1) + getX(dim2, val2, d2.index)-props.radius, y2)
        }

        const dimValIdx = new Map()

        const ids = new Set((hoverDot ? [hoverDot] : [])
            .concat(DM.hasFilter("externalizations") ? DM.getSelectedIds("externalizations") : []))

        const cats = new Set(hoverRect ? [hoverRect] : [])
        if (DM.hasFilterData('externalizations', 'categories')) {
            DM.getFilterData("externalizations", "categories").forEach(cid => cats.add(cid))
        }

        const hasHover = hoverDot !== null || hoverRect !== null;
        const noSel = ids.size === 0;
        const selected = (eids, cids) => eids.some(d => ids.has(d)) || cids.some(d => d === hoverRect)
        const selectedDot = eid => ids.has(eid)

        byExt.forEach((points, extId) => {
            const grouped = d3.group(points, d => d[props.nameAttr])
            ctx.strokeStyle = "black"
            ctx.fillStyle = "none"

            // draw connecting links
            for (let i = 0; i < dims.length-1; ++i) {
                const dim1 = dims[i]
                const dim2 = dims[i+1]
                if (grouped.has(dim1) && grouped.has(dim2)) {
                    const data1 = grouped.get(dim1)
                    const data2 = grouped.get(dim2)
                    data1.forEach(d1 => data2.forEach(d2 => {
                        ctx.beginPath()
                        const sel = selected([extId], [d1.cat_id, d2.cat_id])
                        ctx.lineWidth = sel ? 2 : 1
                        ctx.globalAlpha = sel ? 1 : 0.2
                        path([d1, d2])
                        ctx.stroke()
                        ctx.closePath()
                    }))
                }
            }
            // assign index and position for each data point (circles)
            points.forEach(d => {
                const dim = d[props.nameAttr]
                const val = d[props.valueAttr]

                const perDim = dimValIdx.get(dim) || {}
                const idx = perDim[val] || 0
                d.index = idx;
                d.selected = selectedDot(d.ext_id)
                d.x = x(dim) + getX(dim, val, d.index);
                d.y = getYPos(dim, val) + getY(dim, val, d.index)
                perDim[val] = idx+1
                dimValIdx.set(dim, perDim)
            });
        });


        // draw rectangles
        dimValues.forEach(d => {
            const dim = d.dimension
            const val = d.name
            d.x = x(dim)
            d.y = getYPos(dim, val)
            d.height = y[dim](val) || 3

            ctx.globalAlpha = cats.size === 0 || cats.has(d.cat_id) ? 1 : 0.5;
            ctx.fillStyle = color(dim)
            ctx.strokeStyle = "black"
            ctx.lineWidth = 1

            ctx.beginPath()
            ctx.rect(d.x, d.y, rectWidth.value, d.height)
            ctx.fill()
            if (cats.has(d.cat_id)) ctx.stroke();
            ctx.closePath()
        })

        if (props.linkBy) {

            const grouped = props.linkBy === "ext_id" ? byExt :
                d3.group(props.data, d => d[props.linkBy])

            const pis = new Map()

            ctx.strokeStyle = "white"
            ctx.lineWidth = 1;
            grouped.forEach(vals => {
                if (props.linkBy !== "ext_id") {
                    const numExts = d3.group(vals, d => d.ext_id)
                    if (numExts.size < 2) return;
                }

                const g2 = d3.group(vals, d => d[props.nameAttr])
                for (let i = 0; i < dims.length; ++i) {
                    const dim1 = dims[i]
                    if (g2.has(dim1)) {
                        const pi = pis.has(dim1) ? pis.get(dim1) : 0
                        const data1 = g2.get(dim1)
                        for (let j = 0; j < data1.length-1; j++) {
                            const sel = selected(
                                [data1[j].ext_id, data1[j+1].ext_id],
                                [data1[j].cat_id, data1[j+1].cat_id],
                            )
                            ctx.globalAlpha = noSel || sel ? 1 : 0.2
                            ctx.beginPath()
                            boxLineCanvas(data1[j], data1[j+1], pi)
                            ctx.stroke()
                            ctx.closePath();
                        }
                        if (data1.length > 1) { pis.set(dim1, pi+1) }
                    }
                }
            })
        }

        ctx.globalAlpha = 1
        ctx.strokeStyle = "white"
        ctx.lineWidth = 3
        ctx.font = "12px sans-serif";
        // draw text for each category
        dimValues.forEach(d => {
            ctx.fillStyle = color(d.dimension)
            ctx.strokeText(d.name, d.x, d.y-5, x.bandwidth())
            ctx.fillText(d.name, d.x, d.y-5, x.bandwidth())
        })

        ctx.strokeStyle = "black"
        ctx.lineWidth = 1
        // draw circles
        props.data.forEach(d => {
            const dim = d[props.nameAttr]

            ctx.globalAlpha = d.selected || (ids.size === 0 && !hasHover) || hoverRect === d.cat_id ? 1 : 0.2;
            ctx.fillStyle = color(dim)

            ctx.beginPath()
            ctx.arc(d.x, d.y, props.radius + (d.selected ? 2 : 0), 0, Math.PI*2)
            if (d.selected || hoverRect === d.cat_id) ctx.stroke()
            ctx.fill()
            ctx.closePath()
        })

        ctx.globalAlpha = 1;
        ctx.font = "16px sans-serif";
        dims.forEach(d => {
            ctx.fillStyle = color(d)
            ctx.fillText(d, x(d), 15)
        })
    }

    function onMove(event) {
        const [mx, my] = d3.pointer(event, el.value)

        const lookForRect =  Math.floor(mx) % Math.floor(x.step()) <= rectWidth.value + 2
        const prevRect = hoverRect
        const prevDot = hoverDot

        if (lookForRect) {
            const findRect = dimValues.find(d => {
                return mx >= d.x && mx <= d.x+rectWidth.value &&
                    my >= d.y && my <= d.y+d.height
            })
            hoverDot = null
            hoverRect = findRect ? findRect.cat_id : null;
            if (prevDot !== null || hoverRect !== prevRect) {
                draw();
                if (findRect) { emit("hover-rect", event, findRect.cat_id) }
                else { emit("hover-rect", null, null) }
            }
        } else {
            const findDot = props.data.find(d => {
                const r = props.radius + (d.selected ? 2 : 0)
                return mx >= d.x-r && mx <= d.x+r && my >= d.y-r && my <= d.y+r
            })
            hoverRect = null
            hoverDot = findDot ? findDot.ext_id : null
            if (prevRect !== null || hoverDot !== prevDot) {
                draw();
                if (findDot) { emit("hover-dot", event, findDot.ext_id) }
                else { emit("hover-dot", null, null) }
            }
        }
    }

    function onClick(event) {
        const [mx, my] = d3.pointer(event, el.value)

        const lookForRect =  Math.floor(mx) % Math.floor(x.step()) <= rectWidth.value + 2

        if (lookForRect) {
            const findRect = dimValues.find(d => {
                return mx >= d.x && mx <= d.x+rectWidth.value &&
                    my >= d.y && my <= d.y+d.height
            })
            if (findRect) {
                emit("click-rect", findRect.cat_id)
            }
        } else {
            const findDot = props.data.find(d => {
                const r = props.radius + (d.selected ? 2 : 0)
                return mx >= d.x-r && mx <= d.x+r && my >= d.y-r && my <= d.y+r
            })
            if (findDot) {
                emit("click-dot", findDot.ext_id)
            }
        }
    }

    onMounted(init.bind(null, 250))

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
    ]), init.bind(null, 250))
    watch(() => ([props.time, props.colorScale]), draw, { deep: true })

</script>