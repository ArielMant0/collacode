<template>
    <canvas v-if="canvas" ref="el1" :width="width" :height="height"></canvas>
    <svg v-else ref="el2" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ref, onMounted, onUpdated, watch } from 'vue';


    const props = defineProps({
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
            default: "fill"
        },
        strokeAttr: {
            type: String,
            default: "stroke"
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
        }
    })

    const emit = defineEmits(["hover", "click", "right-click"])

    const el1 = ref(null)
    const el2 = ref(null)

    let ctx;

    const getX = d => d[props.xAttr]
    const getY = d => d[props.yAttr]
    const getF = d => d[props.fillAttr]
    const getS = d => d[props.strokeAttr]

    function draw() {
        if (props.canvas) {
            drawToCanvas()
        } else {
            drawToSVG()
        }
    }

    function drawToCanvas() {
        ctx = ctx ? ctx : el1.getContext("2d")
        ctx.clearRect(0, 0, props.width, props.height)

        const x = d3.scaleLinear()
            .domain(d3.extent(props.data, getX))
            .range([5+props.radius, props.width-props.radius-5])
        const y = d3.scaleLinear()
            .domain(d3.extent(props.data, getY))
            .range([props.height-props.radius-5, 5+props.radius])

        ctx.fillStyle = "black"
        ctx.strokeStyle = "white"
        props.data.forEach(d => {
            ctx.arc(x(getX(d)), y(getY(d)), props.radius, 0, Math.PI*2)
            ctx.fill()
            ctx.stroke()
        });
    }

    function drawToSVG() {
        ctx = null;
        const svg = d3.select(el2.value)
        svg.selectAll("*").remove()

        const x = d3.scaleLinear()
            .domain(d3.extent(props.data, getX))
            .range([5+props.radius*2, props.width-props.radius*2-5])
        const y = d3.scaleLinear()
            .domain(d3.extent(props.data, getY))
            .range([props.height-props.radius*2-5, 5+props.radius*2])

        let fillColor, strokeColor;
        if (props.fillAttr) {
            const colvals = new Set(props.data.map(getF))
            fillColor = d3.scaleOrdinal(d3.schemeCategory10)
                .domain(Array.from(colvals.values()))
                .unknown("#ccc")
        }
        if (props.strokeAttr) {
            const colvals = new Set(props.data.map(getS))
            strokeColor = d3.scaleOrdinal(["white", "red", "magenta"])
                .domain(Array.from(colvals.values()))
                .unknown("#ccc")
        }

        svg.append("g")
            .selectAll("circle")
            .data(props.data)
            .join("circle")
            .attr("cx", d => x(getX(d)))
            .attr("cy", d => y(getY(d)))
            .attr("r", props.radius)
            .attr("fill", d => fillColor ? fillColor(getF(d)) : "black")
            .attr("stroke", d => strokeColor ? strokeColor(getS(d)) : "white")
            .on("pointerenter", function(event, d) {
                emit("hover", d, event)
                d3.select(this).raise()
            })
            .on("pointerleave", () => emit("hover", null, null))
            .on("click", (_, d) => emit("click", d))
    }

    onMounted(draw)

    watch(props, draw)
</script>