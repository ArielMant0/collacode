<template>
    <canvas v-if="canvas" ref="el1" :width="width" :height="height" @pointermove="onMove"></canvas>
    <svg v-else ref="el2" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { gridify_dgrid } from '@saehrimnir/hagrid';
    import { ref, onMounted, watch } from 'vue';

    const props = defineProps({
        time: {
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
        canvas: {
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
    })

    const emit = defineEmits(["hover", "click", "right-click"])

    const el1 = ref(null)
    const el2 = ref(null)

    let ctx, tree, x, y, data;
    let fillColor;

    const getX = d => d[props.xAttr]
    const getY = d => d[props.yAttr]
    const getF = d => d[props.fillAttr]

    function getGridData() {
        // return gridify_dgrid(props.data, { rows: 25, cols: 50 })
        return gridify_dgrid(props.data, { aspect_ratio: 2 })
    }

    function draw() {

        data = props.grid ? getGridData() : props.data
        if (props.grid) {
            data.forEach((d, i) => {
                if (props.idAttr !== undefined) d[props.idAttr] = props.data[i][props.idAttr]
                if (props.urlAttr !== undefined) d[props.urlAttr] = props.data[i][props.urlAttr]
            })
        }

        const w = props.grid ? 20 : props.radius
        const h = props.grid ? 10 : props.radius

        x = d3.scaleLinear()
            .domain(d3.extent(data, getX))
            .range([5+w, props.width-w-5])
        y = d3.scaleLinear()
            .domain(d3.extent(data, getY))
            .range([props.height-h-5, 5+h])

        tree = d3.quadtree()
            .x(d => x(getX(d)))
            .y(d => y(getY(d)))
            .addAll(data)

        if (props.fillAttr) {
            const colvals = Array.from(new Set(data.map(getF)).values())
            colvals.sort()
            const range = typeof props.fillColorScale === "string" ?
                d3[props.fillColorScale] :
                props.fillColorScale

            console.log(colvals)
            fillColor = d3.scaleOrdinal(range)
                .domain(colvals)
                .unknown("#ccc")
        } else {
            fillColor = null
        }

        if (props.canvas) {
            drawToCanvas()
        } else {
            drawToSVG()
        }
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
        ctx = ctx ? ctx : el1.value.getContext("2d")
        ctx.clearRect(0, 0, props.width, props.height)

        ctx.lineWidth = 1;
        const sel = new Set(props.selected)

        data.forEach(d => {
            const isSel = sel.has(d[props.idAttr])
            if (props.grid) {
                const img = new Image();
                img.addEventListener("load", function () {
                    ctx.filter = sel.size === 0 || isSel ? "none" : "grayscale(1) opacity(0.5)"
                    ctx.drawImage(img, x(getX(d))-20, y(getY(d))-10, 40, 20);
                    // ctx.filter = "none"
                    if (isSel) {
                        ctx.strokeStyle = props.selectedColor
                        ctx.beginPath()
                        ctx.rect(x(getX(d))-20, y(getY(d))-10, 40, 20)
                        ctx.stroke()
                        ctx.closePath()
                    }
                });
                img.setAttribute("src", d[props.urlAttr]);
            } else {
                ctx.filter = sel.size === 0 || isSel ? "none" : "opacity(0.5)"
                ctx.fillStyle = fillColor ? fillColor(getF(d)) : "black"
                ctx.beginPath()
                ctx.arc(x(getX(d)), y(getY(d)), props.radius, 0, Math.PI*2)
                ctx.closePath()
                ctx.fill()
                ctx.strokeStyle = isSel ? props.selectedColor : "white"
                ctx.stroke()
            }
            ctx.filter = "none"
        });
    }

    function drawToSVG() {
        ctx = null;
        const svg = d3.select(el2.value)
        svg.selectAll("*").remove()

        svg.append("g")
            .selectAll("circle")
            .data(data)
            .join("circle")
            .attr("cx", d => x(getX(d)))
            .attr("cy", d => y(getY(d)))
            .attr("r", props.radius)
            .attr("fill", d => fillColor ? fillColor(getF(d)) : "black")
            .attr("stroke", d => strokeColor ? strokeColor(getS(d)) : "white")
            .on("pointerenter", function(event, d) {
                const data = findInCirlce(x(getX(d)), y(getY(d)), props.radius)
                if (data.length > 0) {
                    emit("hover", data, event)
                } else {
                    emit("hover", [], null)
                }
                d3.select(this).raise()
            })
            .on("pointerleave", () => emit("hover", [], null))
            .on("click", (_, d) => emit("click", d))
    }

    function onMove(event) {
        const [mx, my] = d3.pointer(event, el1.value)
        let res;
        if (props.grid) {
            res = findInRectangle(mx, my, 40, 10)
        } else {
            res = findInCirlce(mx, my, props.radius)
        }

        if (res.length > 0) {
            emit("hover", res, event)
        } else {
            emit("hover", [], null)
        }
    }

    onMounted(draw)

    watch(props, draw, { deep: true })
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

        if (props.canvas) {
            drawToCanvas()
        } else {
            drawToSVG()
        }
    })
</script>