<template>
    <canvas ref="el" :width="completeWidth" :height="completeHeight" @click="onClick"@pointermove="onMove" @pointerleave="tt.hide()"></canvas>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTooltip } from '@/store/tooltip';
    import { computed, onMounted, ref, watch } from 'vue';

    const tt = useTooltip()

    const props = defineProps({
        time: {
            type: Number,
            default: 0
        },
        data: {
            type: Array,
            required: true
        },
        selected: {
            type: Array,
            default: () => ([])
        },
        domain: {
            type: Array,
            required: false
        },
        colorScale: {
            type: String,
            default: "interpolateViridis"
        },
        idAttr: {
            type: String,
            default: "id"
        },
        nameAttr: {
            type: String,
            default: "name"
        },
        valueAttr: {
            type: String,
            default: "value"
        },
        width: {
            type: Number,
            default: 6
        },
        height: {
            type: Number,
            default: 50
        },
        highlight: {
            type: Number,
            default: 3
        },
        maxValue: {
            type: Number
        }
    })
    const emit = defineEmits(["select"])

    const el = ref(null)
    const completeWidth = computed(() => (props.domain ? props.domain.length : props.data.length) * props.width)
    const completeHeight = computed(() => props.height + 2*props.highlight)

    let ctx, x, color;

    function draw() {
        ctx = ctx ? ctx : el.value.getContext("2d")

        if (props.data.length === 0) return;

        x = d3.scaleBand()
            .domain(props.domain ? props.domain : d3.range(props.data.length))
            .range([0, completeWidth.value])

        color = d3.scaleSequential(d3[props.colorScale])
            .domain([1, props.maxValue ? props.maxValue : d3.max(props.data, d => d[props.valueAttr])])

        drawBars();
    }

    function drawBars() {
        ctx.clearRect(0, 0, completeWidth.value, completeHeight.value)
        if (props.domain) {
            ctx.fillStyle = "#ddd"
            ctx.fillRect(0, props.highlight, completeWidth.value, props.height)
        }

        props.data.forEach((d, i) => {
            if (props.selected.length > 0 && props.selected.includes(d[props.idAttr])) return;
            ctx.fillStyle = props.domain ? "black" : (d[props.valueAttr] > 0 ? color(d[props.valueAttr]) : "#ddd");
            ctx.fillRect(
                x(props.domain ? d[props.idAttr] : i),
                props.highlight,
                x.bandwidth(),
                props.height
            );
        });

        props.data.forEach((d, i) => {
            if (props.selected.length === 0 || !props.selected.includes(d[props.idAttr])) return;
            const col = props.domain ? "red" : (d[props.valueAttr] > 0 ? color(d[props.valueAttr]) : "#ddd")
            ctx.strokeStyle = props.domain ? col : "white";
            ctx.fillStyle = col;
            ctx.beginPath()
            ctx.rect(
                x(props.domain ? d[props.idAttr] : i),
                0,
                x.bandwidth(),
                completeHeight.value
            );
            ctx.fill()
            ctx.stroke()
        });
    }

    function onMove(event) {
        const [rx, _] = d3.pointer(event, el.value)
        const [mx, my] = d3.pointer(event, document.body)
        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)
            if (item) {
                tt.show(item[props.nameAttr], mx + 10, my + 10)
            } else {
                tt.hide()
            }
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            tt.show(`${item[props.valueAttr]} (${(item[props.valueAttr] / props.maxValue * 100).toFixed(2)}%) - ${item[props.nameAttr]}`, mx + 10, my + 10)
        }
    }

    function onClick(event) {
        const [rx, _] = d3.pointer(event, el.value)
        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)
            if (item) emit("select", id)
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            if (item[props.valueAttr] > 0) emit("select", item[props.idAttr])
        }
    }

    onMounted(draw)

    watch(() => props.selected, drawBars, { deep: true })

    watch(() => ([
        props.time,
        props.width,
        props.height,
        props.highlight,
        props.colorScale,
        props.idAttr,
        props.nameAttr,
        props.valueAttr,
        props.maxValue
    ]), draw, { deep: true })

</script>