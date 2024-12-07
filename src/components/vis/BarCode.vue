<template>
    <canvas ref="el" :width="completeWidth" :height="completeHeight" @click="onClick"@pointermove="onMove" @pointerleave="tt.hide()"></canvas>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTooltip } from '@/store/tooltip';
    import { computed, onMounted, ref, watch } from 'vue';
    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import { useSettings } from '@/store/settings';

    const tt = useTooltip()
    const times = useTimes()
    const settings = useSettings()

    const props = defineProps({
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
        absValueAttr: {
            type: String,
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
        minValue: {
            type: Number,
        },
        maxValue: {
            type: Number
        },
        noValueColor: {
            type: String,
        }
    })
    const emit = defineEmits(["select"])

    const el = ref(null)
    const completeWidth = computed(() => (props.domain ? props.domain.length : props.data.length) * props.width)
    const completeHeight = computed(() => props.height + 2*props.highlight)

    const noCol = computed(() => props.noValueColor ? props.noValueColor : (settings.lightMode ? "white": "black"))
    const binCol = computed(() => settings.lightMode ? "black" : "white")

    let ctx, x, color, allTags;

    function draw() {
        ctx = ctx ? ctx : el.value.getContext("2d")

        if (props.data.length === 0) return;

        x = d3.scaleBand()
            .domain(props.domain ? props.domain : d3.range(props.data.length))
            .range([0, completeWidth.value])

        const minval = props.minValue ? props.minValue : d3.min(props.data, d => d[props.valueAttr])
        const maxval = props.maxValue ? props.maxValue : d3.max(props.data, d => d[props.valueAttr])
        if (minval < 0 && maxval > 0) {
            color = d3.scaleDiverging(d3[props.colorScale])
                .domain([minval, 0, maxval])
        } else {
            color = d3.scaleSequential(d3[props.colorScale])
                .domain([minval, maxval])
        }

        drawBars();
    }

    function drawBars() {
        ctx.clearRect(0, 0, completeWidth.value, completeHeight.value)
        if (props.domain) {
            ctx.fillStyle = noCol.value
            ctx.fillRect(0, props.highlight, completeWidth.value, props.height)
        }

        const sel = DM.getSelectedIds("tags")
        if (!allTags) allTags = DM.getData("tags", false);

        props.data.forEach((d, i) => {
            d.selected = sel.has(d[props.idAttr]);
            if (!d.selected) {
                const t = allTags.find(dd => dd.id === d[props.idAttr])
                d.selected = t ? t.path.some(dd => sel.has(dd)) : false;
            }
            if (sel.size > 0 && d.selected) return;

            ctx.fillStyle = props.domain ? binCol.value : (d[props.valueAttr] !== 0 ? color(d[props.valueAttr]) : noCol.value);
            ctx.fillRect(
                x(props.domain ? d[props.idAttr] : i),
                props.highlight,
                x.bandwidth(),
                props.height
            );
        });

        props.data.forEach((d, i) => {
            if (sel.size === 0 || !d.selected) return;

            const col = props.domain ? "red" : (d[props.valueAttr] !== 0 ? color(d[props.valueAttr]) : noCol.value)
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
        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)
            if (item) {
                tt.show(item[props.valueAttr], event.pageX + 10, event.pageY)
            } else {
                tt.hide()
            }
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            const percent = item[props.valueAttr] * 100
            const absolute = props.absValueAttr ? item[props.absValueAttr] : null
            tt.show(
                absolute ?
                    `${percent.toFixed(2)}% (${absolute.toFixed(0)})<br/>${item[props.nameAttr]}` :
                    `${percent.toFixed(2)}%<br/>${item[props.nameAttr]}`,
                event.pageX + 10, event.pageY
            )
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

    watch(() => times.f_tags, drawBars)
    watch(() => settings.lightMode, drawBars)

    watch(() => ([
        props.data,
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