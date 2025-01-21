<template>
    <canvas ref="el"
        :style="{ cursor: selectable ? 'pointer' : 'default' }"
        :width="completeWidth"
        :height="completeHeight"
        @click="onClick"
        @contextmenu="onRightClick"
        @pointermove="onMove"
        @pointerleave="onLeave">
    </canvas>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTooltip } from '@/store/tooltip';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
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
            type: [String, Array],
            default: "interpolateCool"
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
        highlightPos: {
            type: String,
            default: "bottom",
            validator: d => d === "bottom" || d === "top"
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
        hideTooltip: {
            type: Boolean,
            default: false
        },
        categorical: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["click", "right-click", "hover"])

    const el = ref(null)
    const completeWidth = computed(() => (props.domain ? props.domain.length : props.data.length) * props.width)
    const completeHeight = computed(() => props.height + (props.hideHighlight ? 0 : 2*radius.value + offset))
    const radius = computed(() => scales.x ? Math.round(scales.x.bandwidth*0.5) : 4)

    const noCol = computed(() => props.noValueColor ? props.noValueColor : (settings.lightMode ? "white": "#121212"))
    const binCol = computed(() => props.binary && props.binaryColorFill ? props.binaryColorFill : (settings.lightMode ? "#121212" : "white"))

    let ctx, x, color, offset = 2;
    const scales = reactive({ x: null })

    const getV = d => props.showAbsolute && props.absValueAttr ? d[props.absValueAttr] : d[props.valueAttr]

    function draw() {
        ctx = ctx ? ctx : el.value.getContext("2d")

        if (props.data.length === 0) return;

        x = d3.scaleBand()
            .domain(props.domain ? props.domain : d3.range(props.data.length))
            .range([0, completeWidth.value])

        if (props.colorScale) {

            const colscale = Array.isArray(props.colorScale) ? props.colorScale : d3[props.colorScale]

            if (props.categorical) {
                const grouped = d3.group(props.data, getV)
                color = d3.scaleOrdinal(colscale).domain(Array.from(grouped.keys()))
            } else {
                const minval = props.minValue ? props.minValue : d3.min(props.data, getV)
                const maxval = props.maxValue ? props.maxValue : d3.max(props.data, getV)

                if (minval < 0 && maxval > 0) {
                    color = d3.scaleDiverging(colscale).domain([minval, 0, maxval])
                } else {
                    color = d3.scaleSequential(colscale).domain([minval, maxval])
                }
            }
        }

        drawBars();
    }

    function drawBars() {
        ctx.clearRect(0, 0, completeWidth.value, completeHeight.value)

        const top = props.highlightPos === "top"
        const hide = props.hideHighlight
        if (props.domain) {
            ctx.fillStyle = noCol.value
            ctx.fillRect(0, top && !hide ? 2*radius.value+offset : 0, completeWidth.value, props.height)
        }

        const sel = DM.getSelectedIds("tags")
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
                top && !hide ? 2*radius.value+offset : 0,
                x.bandwidth(),
                props.height
            );
        });

        if (!props.hideHighlight && sel.size > 0 ) {

            if (props.domain) {
                props.domain.forEach(id => {
                    if (isSel.has(id)) {
                        ctx.fillStyle = props.selectedColor;
                        ctx.beginPath()
                        ctx.arc(
                            x(id) + x.bandwidth()*0.5,
                            top ? radius.value : completeHeight.value - radius.value,
                            radius.value, 0, Math.PI*2
                        );
                        ctx.fill()
                    }
                })
            } else {

                props.data.forEach((d, i) => {
                    if (!isSel.has(d[props.idAttr])) return;

                    ctx.fillStyle = props.selectedColor;
                    ctx.beginPath()
                    ctx.arc(
                        x(props.domain ? d[props.idAttr] : i) + x.bandwidth()*0.5,
                        top ? radius.value : completeHeight.value - radius.value,
                        radius.value, 0, Math.PI*2
                    );
                    ctx.fill()
                });
            }
        }
    }

    function onMove(event) {
        if (!x) return false;

        const [rx, _] = d3.pointer(event, el.value)
        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)

            if (item) {
                const percent = item[props.valueAttr] * 100
                const absolute = props.absValueAttr ? item[props.absValueAttr] : null
                if (!props.hideTooltip) {
                    tt.show(
                        absolute ?
                            `${percent.toFixed(2)}% (${absolute.toFixed(0)})<br/>${item[props.nameAttr]}` :
                            `${percent.toFixed(2)}%<br/>${item[props.nameAttr]}`,
                        event.pageX + 10, event.pageY
                    )
                }
                emit("hover", item, event)
            } else {
                if (!props.hideTooltip) {
                    tt.hide()
                }
                emit("hover", null)
            }
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            const percent = item[props.valueAttr] * 100
            const absolute = props.absValueAttr ? item[props.absValueAttr] : null
            if (!props.hideTooltip) {
                tt.show(
                    absolute ?
                        `${percent.toFixed(2)}% (${absolute.toFixed(0)})<br/>${item[props.nameAttr]}` :
                        `${percent.toFixed(2)}%<br/>${item[props.nameAttr]}`,
                    event.pageX + 10, event.pageY
                )
                emit("hover", item, event)
            }
        }
    }
    function onLeave() {
        if (!props.hideTooltip) {
            tt.hide()
        }
        emit("hover", null)
    }

    function onClick(event) {
        if (!props.selectable) return;
        const [rx, _] = d3.pointer(event, el.value)
        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)
            if (item) emit("click", item)
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            if (item[props.valueAttr] > 0) emit("click", item)
        }
    }

    function onRightClick(event) {
        if (!props.selectable) return;
        event.preventDefault()
        const [rx, _] = d3.pointer(event, el.value)
        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)
            if (item) emit("right-click", item, event)
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            if (item[props.valueAttr] > 0) emit("right-click", item, event)
        }
    }

    onMounted(draw)

    watch(() => times.f_tags, drawBars)
    watch(() => settings.lightMode, drawBars)

    watch(props, draw, { deep: true })

</script>