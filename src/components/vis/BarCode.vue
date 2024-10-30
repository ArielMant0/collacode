<template>
    <canvas ref="el" :width="completeWidth" :height="height" @pointermove="onMove" @pointerleave="tt.hide()"></canvas>
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
        domain: {
            type: Array,
            required: false
        },
        colorScale: {
            type: String,
            default: "interpolateViridis"
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
            default: 5
        },
        height: {
            type: Number,
            default: 50
        },
        maxValue: {
            type: Number
        }
    })

    const el = ref(null)
    const completeWidth = computed(() => (props.domain ? props.domain.length : props.data.length) * props.width)

    let ctx, x;

    function draw() {
        ctx = ctx ? ctx : el.value.getContext("2d")
        ctx.clearRect(0, 0, completeWidth.value, props.height)

        if (props.data.length === 0) return;

        x = d3.scaleBand()
            .domain(props.domain ? props.domain : d3.range(props.data.length))
            .range([0, completeWidth.value])

        const color = d3.scaleSequential(d3[props.colorScale])
            .domain([1, props.maxValue ? props.maxValue : d3.max(props.data, d => d[props.valueAttr])])

        if (props.domain) {
            ctx.fillStyle = "#ddd"
            ctx.fillRect(0, 0, completeWidth.value, props.height)
        }

        props.data.forEach((d, i) => {
            ctx.fillStyle = props.domain ? "black" : (d[props.valueAttr] > 0 ? color(d[props.valueAttr]) : "#ddd");
            ctx.fillRect(x(props.domain ? d[props.valueAttr] : i), 0, x.bandwidth(), props.height);
        });
    }

    function onMove(event) {
        const [rx, _] = d3.pointer(event, el.value)
        const [mx, my] = d3.pointer(event, document.body)
        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.valueAttr] === id)
            if (item) {
                tt.show(item[props.nameAttr], mx + 10, my + 10)
            } else {
                tt.hide()
            }
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            tt.show(`${item[props.nameAttr]}: ${item[props.valueAttr]}`, mx + 10, my + 10)
        }
    }

    onMounted(draw)

    watch(() => ([
        props.time,
        props.width,
        props.height,
        props.colorScale,
        props.nameAttr,
        props.valueAttr,
        props.maxValue
    ]), draw, { deep: true })

</script>