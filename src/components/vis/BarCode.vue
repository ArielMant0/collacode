<template>
    <canvas ref="el"
        :style="{ cursor: selectable ? 'pointer' : 'default' }"
        :width="completeWidth"
        :height="completeHeight"
        @click="onClick"
        @pointermove="onMove"
        @pointerleave="tt.hide()">
    </canvas>
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
        selected: {
            type: Array,
        },
        domain: {
            type: Array,
            required: false
        },
        colorScale: {
            type: [String, Array],
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
            default: 8
        },
        minValue: {
            type: Number,
        },
        maxValue: {
            type: Number
        },
        noValueColor: {
            type: String,
        },
        selectedColor: {
            type: String,
            default: "black"
        },
        binaryColorFill: {
            type: String,
            default: "red"
        },
        showAbsolute: {
            type: Boolean,
            default: false
        },
        hideHighlight: {
            type: Boolean,
            default: false
        },
        binary: {
            type: Boolean,
            default: false
        },
        selectable: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["select"])

    const el = ref(null)
    const completeWidth = computed(() => (props.domain ? props.domain.length : props.data.length) * props.width)
    const completeHeight = computed(() => props.height + (props.hideHighlight ? 0 : props.highlight))

    const noCol = computed(() => props.noValueColor ? props.noValueColor : (settings.lightMode ? "white": "#121212"))
    const binCol = computed(() => props.binary && props.binaryColorFill ? props.binaryColorFill : (settings.lightMode ? "#121212" : "white"))

    let ctx, x, color;

    const getV = d => props.showAbsolute && props.absValueAttr ? d[props.absValueAttr] : d[props.valueAttr]

    function draw() {
        ctx = ctx ? ctx : el.value.getContext("2d")

        if (props.data.length === 0) return;

        x = d3.scaleBand()
            .domain(props.domain ? props.domain : d3.range(props.data.length))
            .range([0, completeWidth.value])

        const minval = props.minValue ? props.minValue : d3.min(props.data, getV)
        const maxval = props.maxValue ? props.maxValue : d3.max(props.data, getV)

        const colscale = Array.isArray(props.colorScale) ? props.colorScale : d3[props.colorScale]

        if (minval < 0 && maxval > 0) {
            color = d3.scaleDiverging(colscale)
                .domain([minval, 0, maxval])
        } else {
            color = d3.scaleSequential(colscale)
                .domain([minval, maxval])
        }

        drawBars();
    }

    function drawBars() {
        ctx.clearRect(0, 0, completeWidth.value, completeHeight.value)
        if (props.domain) {
            ctx.fillStyle = noCol.value
            ctx.fillRect(0, 0, completeWidth.value, props.height)
        }

        const sel = props.selected ? new Set(props.selected) : DM.getSelectedIds("tags")

        const isSel = new Set(sel)

        props.data.forEach((d, i) => {
            if (!isSel.has(d[props.idAttr])) {
                const p = DM.getDerivedItem("tags_path", d[props.idAttr])
                if (p && p.path.some(dd => sel.has(dd))) {
                    isSel.add(d[props.idAttr])
                }
            }

            ctx.fillStyle = props.binary ? binCol.value : (getV(d) !== 0 ? color(getV(d)) : noCol.value);
            ctx.fillRect(
                x(props.domain ? d[props.idAttr] : i),
                0,
                x.bandwidth(),
                props.height
            );
        });

        if (!props.hideHighlight) {

            const r = Math.min(Math.max(3, x.bandwidth()*0.5-1), props.highlight*0.5-1)
            props.data.forEach((d, i) => {
                if (sel.size === 0 || !isSel.has(d[props.idAttr])) return;

                ctx.fillStyle = props.selectedColor;
                ctx.beginPath()
                ctx.arc(
                    x(props.domain ? d[props.idAttr] : i) + x.bandwidth()*0.5,
                    completeHeight.value - r,
                    r, 0, Math.PI*2
                );
                ctx.fill()
            });
        }
    }

    function onMove(event) {
        const [rx, _] = d3.pointer(event, el.value)
        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)
            if (item) {
                const percent = item[props.valueAttr] * 100
                const absolute = props.absValueAttr ? item[props.absValueAttr] : null
                tt.show(
                    absolute ?
                        `${percent.toFixed(2)}% (${absolute.toFixed(0)})<br/>${item[props.nameAttr]}` :
                        `${percent.toFixed(2)}%<br/>${item[props.nameAttr]}`,
                    event.pageX + 10, event.pageY
                )
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
        if (!props.selectable) return;
        const [rx, _] = d3.pointer(event, el.value)
        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)
            if (item) emit("select", item)
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            if (item[props.valueAttr] > 0) emit("select", item)
        }
    }

    onMounted(draw)

    watch(() => times.f_tags, drawBars)
    watch(() => props.selected ? props.selected : [], drawBars, { deep: true })
    watch(() => settings.lightMode, drawBars)

    watch(() => ([
        props.data,
        props.width,
        props.height,
        props.highlight,
        props.hideHighlight,
        props.selectable,
        props.selectedColor,
        props.binary,
        props.binaryColorFill,
        props.colorScale,
        props.idAttr,
        props.nameAttr,
        props.valueAttr,
        props.maxValue,
        props.showAbsolute
    ]), draw, { deep: true })

</script>