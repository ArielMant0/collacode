<template>
    <div style="position: relative;">
        <canvas ref="el" :width="width" :height="height" @pointermove="onMove" @click="onClick" @contextmenu="onRightClick"></canvas>
        <canvas ref="overlay" :width="width" :height="height" style="position: absolute; top:0; left:0; pointer-events: none;"></canvas>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { gridify_dgrid } from '@saehrimnir/hagrid';
    import { ref, onMounted, watch } from 'vue';
import simplify from 'simplify-js';

    const props = defineProps({
        time: {
            type: Number,
            default: 0
        },
        refresh: {
            type: Number,
            default: 0
        },
        data: {
            type: Array,
            required: true
        },
        xAttr: {
            type: String,
            default: "x"
        },
        yAttr: {
            type: String,
            default: "y"
        },
        fillAttr: {
            type: String,
        },
        fillColorScale: {
            type: [String, Array],
            default: "schemeSet2"
        },
        fillColorBins: {
            type: Number,
            default: 0
        },
        selected: {
            type: Array,
            default: () => ([])
        },
        selectedColor: {
            type: String,
            default: "red"
        },
        width: {
            type: Number,
            default: 500
        },
        height: {
            type: Number,
            default: 500
        },
        radius: {
            type: Number,
            default: 5
        },
        idAttr: {
            type: String,
        },
        urlAttr: {
            type: String,
        },
        grid: {
            type: Boolean,
            default: false
        },
    })

    const emit = defineEmits(["hover", "lasso", "click", "right-click"])

    const el = ref(null)
    const overlay = ref(null)

    let ctx, ctxO, tree, x, y, data;
    let fillColor;

    let drawing = false;
    let lasso = null;

    const getX = d => d[props.xAttr]
    const getY = d => d[props.yAttr]
    const getF = d => d[props.fillAttr]

    function getGridData() {
        // return gridify_dgrid(props.data, { rows: 25, cols: 50 })
        return gridify_dgrid(props.data, { aspect_ratio: 2 })
    }

    function draw() {

        data = props.grid ? getGridData() : props.data

        const w = props.grid ? 20 : props.radius
        const h = props.grid ? 10 : props.radius

        x = d3.scaleLinear()
            .domain(d3.extent(data, getX))
            .range([5+w, props.width-w-5])
        y = d3.scaleLinear()
            .domain(d3.extent(data, getY))
            .range([props.height-h-5, 5+h])

        data.forEach((d, i) => {
            if (props.grid) {
                if (props.idAttr !== undefined) d[props.idAttr] = props.data[i][props.idAttr]
                if (props.urlAttr !== undefined) d[props.urlAttr] = props.data[i][props.urlAttr]
            }
            d.px = x(getX(d))
            d.py = y(getY(d))
        })

        tree = d3.quadtree()
            .x(d => d.px)
            .y(d => d.py)
            .addAll(data)

        if (props.fillAttr) {
            const colvals = Array.from(new Set(data.map(getF)).values())
            colvals.sort()
            const range = typeof props.fillColorScale === "string" ?
                d3[props.fillColorScale] :
                props.fillColorScale

            if (props.fillColorBins > 0) {
                fillColor = d3.scaleQuantile(range)
                    .domain(colvals)
                    .unknown("#fff")

            } else {
                fillColor = d3.scaleOrdinal(range)
                    .domain(colvals)
                    .unknown("#fff")
            }
        } else {
            fillColor = null
        }

        drawToCanvas()
    }

    function findInCirlce(px, py, r, filter) {
        const result = [],
            radius2 = r * r,
            accept = filter ?
                d => filter(d) && result.push(d) :
                d => result.push(d);

        tree.visit(function(node, x1, y1, x2, y2) {
            if (node.length) {
                return x1 >= px + r || y1 >= py + r || x2 < px - r || y2 < py - r;
            }

            const dx = +tree._x.call(null, node.data) - px,
                dy = +tree._y.call(null, node.data) - py;

            if (dx * dx + dy * dy < radius2) {
                do { accept(node.data); } while (node = node.next);
            }
        });

        return result;
    }

    function findInRectangle(px, py, rw, rh, filter) {
        const result = [],
            accept = filter ?
                d => filter(d) && result.push(d) :
                d => result.push(d);

        tree.visit(function(node, x1, y1, x2, y2) {
            if (node.length) {
                return x1 >= px + rw || y1 >= py + rh || x2 < px - rh || y2 < py - rh;
            }

            const dx = +tree._x.call(null, node.data),
                dy = +tree._y.call(null, node.data);

            if (dx <= px + rw && dy <= py + rh && dx >= px - rh && dy >= py - rh) {
                do { accept(node.data); } while (node = node.next);
            }
        });

        return result;
    }


    function drawToCanvas() {
        ctx = ctx ? ctx : el.value.getContext("2d")
        ctx.clearRect(0, 0, props.width, props.height)

        ctx.lineWidth = 1;
        const sel = new Set(props.selected)

        data.forEach(d => {
            d.selected = sel.has(d[props.idAttr])
            if (props.grid) {
                const img = new Image();
                img.addEventListener("load", function () {
                    ctx.filter = sel.size === 0 || d.selected ? "none" : "grayscale(1) opacity(0.25)"
                    ctx.drawImage(img, d.px-20, d.py-10, 40, 20);
                    // ctx.filter = "none"
                    if (d.selected) {
                        ctx.strokeStyle = props.selectedColor
                        ctx.beginPath()
                        ctx.rect(d.px-20, d.py-10, 40, 20)
                        ctx.stroke()
                        ctx.closePath()
                    }
                });
                img.setAttribute("src", d[props.urlAttr]);
            } else {
                if (sel.size > 0 && d.selected) return;
                ctx.filter = sel.size === 0 ? "none" : "grayscale(0.75) opacity(0.25)"
                const fill = getF(d)
                ctx.fillStyle = fillColor && (fill > 0 || props.fillColorBins === 0) ? fillColor(fill) : (fillColor ? "white" : '#555')
                ctx.beginPath()
                ctx.arc(d.px, d.py, props.radius, 0, Math.PI*2)
                ctx.closePath()
                ctx.fill()
                ctx.strokeStyle = fillColor ? d3.color(fillColor(fill)).darker() : "black"
                ctx.stroke()
            }
            ctx.filter = "none"
        });

        if (!props.grid && sel.size > 0) {
            ctx.lineWidth = 2
            ctx.strokeStyle = props.selectedColor
            data.forEach(d => {
                if (!d.selected) return;
                ctx.filter = "none"
                ctx.fillStyle = fillColor ? fillColor(getF(d)) : "black"
                ctx.beginPath()
                ctx.arc(d.px, d.py, props.radius + d.selected*2, 0, Math.PI*2)
                ctx.closePath()
                ctx.fill()
                ctx.stroke()
            })
        }
    }

    function drawLasso() {
        ctxO = ctxO ? ctxO : overlay.value.getContext("2d")
        ctxO.clearRect(0, 0, props.width, props.height)

        const path = d3.line()
            .context(ctxO)
            .curve(d3.curveLinearClosed)
            .x(d => d.x)
            .y(d => d.y)

        ctxO.strokeStyle = "red"
        ctxO.fillStyle = "red"
        ctxO.beginPath()
        path(lasso)
        ctxO.stroke()
        ctxO.globalAlpha = 0.2
        ctxO.fill()
        ctxO.closePath()
    }
    function selectByLasso() {
        if (lasso.length > 0) {
            const simple = simplify(lasso)
            const poly = simple.map(d => ([d.x, d.y]))
            const array = []
            data.forEach(d => {
                if (d3.polygonContains(poly, [d.px, d.py])) {
                    array.push(d)
                }
            })
            lasso = [];
            drawLasso();
            emit("lasso", array)
        }
    }

    function onMove(event) {
        if (drawing) {
            // drawing
            const [mx, my] = d3.pointer(event, el.value)
            lasso.push({ x: mx, y: my })
            drawLasso();
        } else {
            // hovering
            const [mx, my] = d3.pointer(event, el.value)
            let res;
            if (props.grid) {
                res = findInRectangle(mx, my, 20, 10)
            } else {
                res = findInCirlce(mx, my, props.radius)
            }

            emit("hover", res, res.length > 0 ? event : null)
        }
    }
    function onClick(event) {
        if (drawing) {
            // drawing
            drawing = false;
            selectByLasso()
        } else if (event.getModifierState("Shift")) {
            lasso = []
            drawing = true;
        } else {
            // selecting
            const [mx, my] = d3.pointer(event, el.value)
            let res;
            if (props.grid) {
                res = findInRectangle(mx, my, 20, 10)
            } else {
                res = findInCirlce(mx, my, props.radius)
            }

            emit("click", res)
        }
    }
    function onRightClick(event) {
        event.preventDefault();
        const [mx, my] = d3.pointer(event, el.value)
        let res;
        if (props.grid) {
            res = findInRectangle(mx, my, 20, 10)
        } else {
            res = findInCirlce(mx, my, props.radius)
        }

        emit("right-click", res, res.length > 0 ? event : null)
    }

    function coords(index) {
        return index >= 0 && index < data.length ? [data[index].px, data[index].py] : null
    }

    defineExpose({ coords })

    onMounted(draw)

    watch(() => ([
        props.refresh,
        props.width,
        props.height,
        props.fillAttr,
        props.idAttr,
        props.urlAttr,
        props.xAttr,
        props.yAttr,
        props.fillColorScale,
        props.selectedColor,
        props.grid
    ]), draw, { deep: true })

    watch(() => props.time, function() {
        if (props.fillAttr) {
            const colvals = Array.from(new Set(data.map(getF)).values())
            colvals.sort()
            const range = typeof props.fillColorScale === "string" ?
                d3[props.fillColorScale] :
                props.fillColorScale

            fillColor = d3.scaleOrdinal(range)
                .domain(colvals)
                .unknown("#ccc")
        } else {
            fillColor = null
        }

        drawToCanvas()
    })
</script>