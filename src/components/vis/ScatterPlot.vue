<template>
    <div :class="['d-flex', colorScalePos == 'left' || colorScalePos == 'right' ? 'flex-row' : 'flex-column align-center']">
        <ColorLegend v-if="hasColorScale && (colorScalePos === 'left' || colorScalePos === 'top')"
            :size="colorScalePos === 'left' ? colorValues.length*25 : width-20"
            :colors="colorValues"
            :ticks="colorTicks"
            @click="selectByColor"
            :selected="legendSelected"
            hide-domain
            clickable
            :vertical="colorScalePos === 'left'"/>
        <div v-else-if="colorScale && (colorScalePos === 'left' || colorScalePos === 'top')" style="width: 100px"></div>

        <div style="position: relative;">
            <svg ref="svg" class="prevent-select" :width="width" :height="height" style="pointer-events: none;"></svg>
            <canvas ref="el" :width="width" :height="height" style="position: absolute; top:0; left:0;" @pointermove="onMove" @pointerleave="onLeave" @click="onClick" @contextmenu="onRightClick"></canvas>
            <canvas ref="overlay" :width="width" :height="height" style="position: absolute; top:0; left:0; pointer-events: none;"></canvas>
        </div>

        <ColorLegend v-if="hasColorScale && (colorScalePos === 'right' || colorScalePos === 'bottom')"
            :size="colorScalePos === 'right' ? colorValues.length*25 : width-20"
            :colors="colorValues"
            :ticks="colorTicks"
            @click="selectByColor"
            :selected="legendSelected"
            hide-domain
            clickable
            :vertical="colorScalePos === 'right'"/>
        <div v-else-if="colorScale && (colorScalePos === 'right' || colorScalePos === 'bottom')" style="width: 100px"></div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { gridify_dgrid } from '@saehrimnir/hagrid';
    import { ref, onMounted, watch, computed, onUpdated } from 'vue';
    import simplify from 'simplify-js';
    import ColorLegend from './ColorLegend.vue';
    import { formatNumber } from '@/use/utility';
    import imgUrlS from '@/assets/__placeholder__s.png'

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
            default: ""
        },
        glyphAttr: {
            type: String,
            default: ""
        },

        xDomain: { type: Array },
        yDomain: { type: Array },

        colorScale: {
            type: Boolean,
            default: false
        },
        colorScalePos: {
            type: String,
            validator: value => ["left", "right", "top", "bottom"].includes(value),
            default: "right"
        },

        fillColorScale: {
            type: [String, Array],
            default: "schemeSet2"
        },
        fillColorBins: {
            type: Number,
            default: 0
        },
        fillDomain: {
            type: Array,
            default: () => ([])
        },

        glyphDomain: {
            type: Array,
            default: () => ([])
        },
        glyphColorScale: {
            type: [String, Array],
            default: "schemeSet2"
        },

        selected: {
            type: Array,
            default: () => ([])
        },
        legendSelected: {
            type: Array,
            default: () => ([])
        },
        selectable: {
            type: Boolean,
            default: false
        },
        highlighted: {
            type: Array,
            default: () => ([])
        },
        highlightedBandwidth: {
            type: Number,
            default: 8
        },
        selectedColor: {
            type: String,
            default: "red"
        },
        highlightedColor: {
            type: String,
            default: "red"
        },
        highlightedColorDot: {
            type: String,
            default: "grey"
        },
        lassoColor: {
            type: String,
            default: "red"
        },
        unselectedOpacity: {
            type: Number,
            default: 0.1
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
            default: 7
        },
        searchRadius: { type: Number },
        showSearchRadius: {
            type: Boolean,
            default: false
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
        hideAxes: {
            type: Boolean,
            default: false
        },
        xLabel: { type: String },
        yLabel: { type: String },
    })

    const emit = defineEmits(["hover", "lasso", "click", "click-color", "right-click"])

    const el = ref(null)
    const overlay = ref(null)
    const svg = ref(null)

    let ctx, ctxO, tree, x, y;
    let data;
    let fillColor, glyphs;

    const gridRows = ref(10)
    const gridCols = ref(10)
    const rectWidth = computed(() => (props.width-10) / (gridCols.value+1))
    const rectHeight = computed(() => rectWidth.value * 0.5)

    const colorValues = ref([])
    const colorTicks = ref([])
    const hasColorScale = computed(() => props.colorScale && (props.fillAttr || props.glyphAttr))

    let drawing = false;
    let lasso = null;

    const getX = d => d[props.xAttr]
    const getY = d => d[props.yAttr]
    const getF = d => d[props.fillAttr]
    const getG = d => d[props.glyphAttr]

    let imageCache = []

    function getGridData() {
        // return gridify_dgrid(props.data, { rows: 25, cols: 50 })
        return gridify_dgrid(props.data, { aspect_ratio: 2 })
    }

    function makeColorScale() {
        if (props.glyphAttr && props.glyphDomain.length > 0) {
            const range = typeof props.glyphColorScale === "string" ?
                d3[props.glyphColorScale] : props.glyphColorScale

            glyphs = d3.scaleOrdinal(range)
                .domain(props.glyphDomain)
                .unknown("#fff")

            colorTicks.value = props.glyphDomain;
            colorValues.value = props.glyphDomain.map(glyphs);

            fillColor = null

        } else if (props.fillAttr) {
            const colvals = Array.from(new Set(data.map(getF)).values())
            colvals.sort()

            const range = typeof props.fillColorScale === "string" ?
                d3[props.fillColorScale] : props.fillColorScale

            if (props.fillColorBins > 0) {
                fillColor = d3.scaleQuantile(range)
                    .domain(colvals)
                    .unknown("#fff")

                colorTicks.value = [0].concat(range.map((d, i) => {
                    const q = fillColor.invertExtent(d)
                    return i > 0 ?
                        `${formatNumber(q[0])} to ${formatNumber(q[1])}` :
                        `less than ${formatNumber(q[1])}`
                }))
                colorValues.value = ["#ffffff"].concat(range);

            } else {
                fillColor = d3.scaleOrdinal(range)
                    .domain(props.fillDomain.length > 0 ? props.fillDomain : colvals)
                    .unknown("#fff")

                colorTicks.value = fillColor.domain()
                colorValues.value = colorTicks.value.map(fillColor)
            }

            glyphs = null

        } else {
            fillColor = null
            glyphs = null
        }
    }

    function draw() {

        if (props.grid) {
            data = getGridData()
            const N = data.length
            gridRows.value = Math.floor(Math.sqrt(N * 2));
            gridCols.value = Math.ceil(N / gridRows.value);
        } else {
            data = props.data
        }

        imageCache = []

        const axisOffset = props.hideAxes ? 0 : 40

        const w = props.grid ? rectWidth.value*0.5 : props.radius
        const h = props.grid ? rectHeight.value*0.5 : props.radius

        x = d3.scaleLinear()
            .domain(props.xDomain ? props.xDomain : d3.extent(data, getX))
            .range([w + axisOffset, props.width - w])
        y = d3.scaleLinear()
            .domain(props.yDomain ? props.yDomain : d3.extent(data, getY))
            .range([props.height - h - axisOffset, h])

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

        makeColorScale()

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
        if (!el.value) return
        ctx = ctx ? ctx : el.value.getContext("2d")
        ctx.clearRect(0, 0, props.width, props.height)

        ctx.lineWidth = 1;
        const sel = new Set(props.selected)
        const high = new Set(props.highlighted)

        // if there highlighted points, draw contours
        if (high.size > 0 && !props.grid) {
            const contour = d3.contourDensity()
                .size([props.width, props.height])
                .x(d => d.px)
                .y(d => d.py)
                .thresholds(1)
                .bandwidth(props.highlightedBandwidth)
                .contours(data.filter(d => high.has(d[props.idAttr])))

            ctx.fillStyle = props.highlightedColor
            // ctx.strokeStyle = props.highlightedColor
            ctx.beginPath()
            d3.geoPath().context(ctx)(contour(Math.min(contour.max, 0.0001)))
            // ctx.globalAlpha = 1;
            // ctx.stroke()
            ctx.globalAlpha = 0.25;
            ctx.fill()
            ctx.closePath()
        }

        ctx.globalAlpha = 1;

        data.forEach((d, idx) => {
            d.selected = sel.has(d[props.idAttr])

            if (props.grid) {
                const isHigh = high.has(d[props.idAttr])
                const fullOpacity = high.size > 0 ? isHigh : sel.size === 0 || d.selected

                const wh = Math.floor(rectWidth.value * 0.5)
                const hh = Math.floor(rectHeight.value * 0.5)
                if (imageCache[idx]) {
                    ctx.filter = fullOpacity ? "none" : `grayscale(0.75) opacity(${props.unselectedOpacity})`
                    ctx.drawImage(imageCache[idx], d.px-wh, d.py-hh, rectWidth.value, rectHeight.value);
                    // ctx.filter = "none"
                    if (d.selected || isHigh) {
                        ctx.strokeStyle = d.selected ? props.selectedColor : props.highlightedColor
                        ctx.beginPath()
                        ctx.rect(d.px-wh, d.py-hh, rectWidth.value, rectHeight.value)
                        ctx.stroke()
                        ctx.closePath()
                    }
                } else {
                    const img = new Image();
                    img.addEventListener("load", function () {
                        ctx.filter = fullOpacity ? "none" : `grayscale(0.75) opacity(${props.unselectedOpacity})`
                        ctx.drawImage(img, d.px-wh, d.py-hh, rectWidth.value, rectHeight.value);
                        imageCache[idx] = img;
                        // ctx.filter = "none"
                        if (d.selected || isHigh) {
                            ctx.strokeStyle = d.selected ? props.selectedColor : props.highlightedColor
                            ctx.beginPath()
                            ctx.rect(d.px-wh, d.py-hh, rectWidth.value, rectHeight.value)
                            ctx.stroke()
                            ctx.closePath()
                        }
                    });
                    img.setAttribute("src", d[props.urlAttr] ? d[props.urlAttr] : imgUrlS);
                }
            } else {
                if (sel.size > 0 && d.selected) return;
                drawSinglePoint(ctx, d)
            }
            ctx.filter = "none"
        });

        if (!props.grid && sel.size > 0) {
            ctx.lineWidth = 1
            ctx.strokeStyle = props.selectedColor
            data.forEach(d => {
                if (!d.selected) return;
                drawSinglePoint(ctx, d, props.radius+2)
            })
        }

        drawAxes()
    }

    function drawAxes() {
        const g = d3.select(svg.value)
        g.selectAll("*").remove()

        if (!props.hideAxes) {
            g.append("g")
                .attr("transform", `translate(40,0)`)
                .call(d3.axisLeft(y))

            if (props.yLabel) {
                g.append("text")
                    .attr("font-size", "small")
                    .attr("y", (props.height-10) * 0.5)
                    .attr("x", 10)
                    .attr("fill", "currentColor")
                    .attr("text-anchor", "middle")
                    .attr("transform", `rotate(-90 10 ${(props.height-10) * 0.5})`)
                    .text(props.yLabel)
            }

            g.append("g")
                .attr("transform", `translate(0,${props.height-40})`)
                .call(d3.axisBottom(x))

            if (props.xLabel) {
                g.append("text")
                    .attr("font-size", "small")
                    .attr("fill", "currentColor")
                    .attr("y", props.height-10)
                    .attr("x", 25 + (props.width-10) * 0.5)
                    .attr("text-anchor", "middle")
                    .text(props.xLabel)
            }
        }
    }

    function drawPoints(context, points) {
        points.forEach(d => drawSinglePoint(context, d, props.radius+3, true))
    }

    function drawSinglePoint(context, d, radius=props.radius, fullOpacity=false) {
        const pie = d3.pie().value(d => d.value)
        const arc = d3.arc()
            .context(context)
            .padAngle(0)
            .innerRadius(0)
            .outerRadius(radius)

        context.filter = d.selected || props.selected.length === 0 ? "none" : `opacity(${fullOpacity ? 1 : props.unselectedOpacity})`
        if (glyphs) {
            const sections = getG(d)
            context.strokeStyle = "black"

            if (sections.length < 2) {
                context.fillStyle = sections.length === 0 ? "#555" : glyphs(sections[0].name)
                context.beginPath()
                context.arc(d.px, d.py, radius, 0, Math.PI*2)
                context.closePath()
                context.fill()
                context.stroke()
            } else {
                // lets draw a tiny pie chart
                const slices = pie(sections)
                context.translate(d.px, d.py)
                slices.forEach(s => {
                    context.fillStyle = glyphs(s.data.name)
                    context.beginPath()
                    arc(s)
                    context.fill()
                    context.stroke()
                    context.closePath()
                })
                context.translate(-d.px, -d.py)
            }
        } else {
            const fill = getF(d)
            context.fillStyle = fillColor && (fill != 0 || props.fillColorBins === 0) ? fillColor(fill) : (fillColor ? "white" : '#555')
            context.beginPath()
            context.arc(d.px, d.py, radius, 0, Math.PI*2)
            context.closePath()
            context.fill()
            context.strokeStyle = !d.selected && fillColor ? d3.color(fillColor(fill)).darker() : "black"
            context.stroke()
        }
    }

    function drawLasso() {
        if (!ctxO) ctxO = overlay.value.getContext("2d")
        ctxO.clearRect(0, 0, props.width, props.height)

        const path = d3.line()
            .context(ctxO)
            .curve(d3.curveLinearClosed)
            .x(d => d.x)
            .y(d => d.y)

        ctxO.strokeStyle = props.lassoColor
        ctxO.fillStyle = props.lassoColor
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

            // if (props.showSearchRadius) {
            //     if (!ctxO) ctxO = overlay.value.getContext("2d")
            //     ctxO.clearRect(0, 0, props.width, props.height)
            //     ctxO.filter = "none"
            //     ctxO.globalAlpha = 1;
            //     ctxO.strokeStyle = props.highlightedColor;
            //     ctxO.arc(mx, my, props.searchRadius, 0, Math.PI*2)
            //     ctxO.stroke()
            // }

            let res;
            if (props.grid) {
                res = findInRectangle(mx, my, Math.floor(rectWidth.value*0.5), Math.floor(rectHeight.value*0.5))
            } else {
                res = findInCirlce(mx, my, props.searchRadius ? props.searchRadius : props.radius+2)
            }

            if (!props.grid) {
                if (!ctxO) ctxO = overlay.value.getContext("2d")
                if (!props.showSearchRadius) ctxO.clearRect(0, 0, props.width, props.height)
                ctxO.filter = "none"
                ctxO.globalAlpha = 1;
                drawPoints(ctxO, res)
            }

            emit("hover", res, event)
        }
    }
    function onLeave(event) {
        emit("hover", [], event)
    }
    function onClick(event) {
        if (!props.selectable) return
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
                res = findInRectangle(mx, my, Math.floor(rectWidth.value*0.5), Math.floor(rectHeight.value*0.5))
            } else {
                res = findInCirlce(mx, my, props.searchRadius ? props.searchRadius : props.radius+2)
            }

            emit("click", res, event)
        }
    }
    function onRightClick(event) {
        event.preventDefault();
        if (!props.selectable) return
        const [mx, my] = d3.pointer(event, el.value)
        let res;
        if (props.grid) {
            res = findInRectangle(mx, my, Math.floor(rectWidth.value*0.5), Math.floor(rectHeight.value*0.5))
        } else {
            res = findInCirlce(mx, my, props.searchRadius ? props.searchRadius : props.radius+2)
        }

        emit("right-click", res, event)
    }

    function selectByColor(value, color) {
        if (glyphs) {
            emit("click-color", value)
        } else if (fillColor) {
            if (value == 0) return emit("click-color", 0)
            if (props.fillColorBins > 0) {
                const extent = fillColor.invertExtent(color)
                return emit("click-color", extent)
            }
            emit("click-color", value)
        }
    }

    function coords(index) {
        return index >= 0 && index < data.length ? [data[index].px, data[index].py] : null
    }
    function coordsById(id) {
        const it = data.find(d => d[props.idAttr] === id)
        return it ? [it.px, it.py] : null
    }

    defineExpose({ coords, coordsById })

    onMounted(draw)
    onUpdated(drawToCanvas)

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
        makeColorScale()
        drawToCanvas()
    })
</script>