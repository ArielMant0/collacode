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
    import { computed, onMounted, onUpdated, reactive, ref, watch } from 'vue';
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
        selected: {
            type: Set,
            required: false
        },
        hidden: {
            type: Set,
            required: false
        },
        hiddenOpacity: {
            type: Number,
            default: 0.15
        },
        colorDomain: {
            type: Array,
        },
        colorScale: {
            type: [String, Array],
            default: "interpolatePlasma"
        },
        colorScaleReverse: {
            type: Boolean,
            default: false
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
        noValue: {
            type: Number,
            default: 0
        },
        noValueColor: {
            type: String,
        },
        selectedColor: {
            type: String,
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
        discrete: {
            type: Boolean,
            default: false
        },
        quantiles: {
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
    const radius = computed(() => Math.max(3, Math.min(6, scales.x ? Math.floor(scales.x.bandwidth()*0.5) : 4)))

    const noCol = computed(() => props.noValueColor ? props.noValueColor : (settings.lightMode ? "#ffffff": "#121212"))
    const binCol = computed(() => props.binary && props.binaryColorFill ? props.binaryColorFill : (settings.lightMode ? "#121212" : "#ffffff"))

    let ctx, x, color, offset = 2;
    const scales = reactive({ x: null })

    const getV = d => props.showAbsolute && props.absValueAttr ? d[props.absValueAttr] : d[props.valueAttr]

    const selColor = computed(() => {
        return props.selectedColor ? props.selectedColor : (settings.lightMode ? "black" : "white")
    })

    function makeColorScale() {


        if (props.colorScale) {

            let colscale = Array.isArray(props.colorScale) ? props.colorScale : d3[props.colorScale]

            if (props.categorical) {
                const grouped = d3.group(props.data, getV)
                const categories = Array.from(grouped.keys())
                categories.sort()
                if (props.colorScaleReverse) colscale = colscale.reverse()
                color = d3.scaleOrdinal(colscale).domain(props.colorDomain ? props.colorDomain : categories)
            } else if (props.quantiles) {
                const minval = props.minValue ? props.minValue : d3.min(props.data, getV)
                const maxval = props.maxValue ? props.maxValue : d3.max(props.data, getV)
                if (Array.isArray(colscale.at(-1))) {
                    colscale = colscale.at(Math.max(3, Math.min(maxval-minval+1, colscale.length-1)))
                }
                if (props.colorScaleReverse) colscale = colscale.reverse()
                color = d3.scaleQuantile(colscale).domain(props.colorDomain ? props.colorDomain : [minval, maxval])
            } else {
                const minval = props.minValue ? props.minValue : d3.min(props.data, getV)
                const maxval = props.maxValue ? props.maxValue : d3.max(props.data, getV)
                if (props.colorScaleReverse) colscale = colscale.reverse()

                if (minval < 0 && maxval > 0) {
                    color = d3.scaleDiverging(colscale).domain(props.colorDomain ? props.colorDomain : [minval, 0, maxval])
                } else {
                    color = d3.scaleSequential(colscale).domain(props.colorDomain ? props.colorDomain : [minval, maxval])
                }
            }
        } else {
            color = null;
        }
    }

    function draw() {
        if (!el.value) return
        ctx = ctx ? ctx : el.value.getContext("2d")

        x = d3.scaleBand()
            .domain(props.domain ? props.domain : d3.range(props.data.length))
            .range([0, completeWidth.value])

        scales.x = x;

        ctx.clearRect(0, 0, completeWidth.value, completeHeight.value)
        if (props.data.length === 0) return;

        makeColorScale()
        drawBars();
    }

    function drawBars() {
        if (!el.value || !ctx) return
        ctx.clearRect(0, 0, completeWidth.value, completeHeight.value)

        const top = props.highlightPos === "top"
        const hide = props.hideHighlight
        if (props.domain) {
            ctx.fillStyle = noCol.value
            ctx.fillRect(0, top && !hide ? 2*radius.value+offset : 0, completeWidth.value, props.height)
        }

        const sel = props.selected ? props.selected : DM.getSelectedIds("tags")
        const hidden = props.hidden ? props.hidden : new Set()

        const isSel = new Set(sel)
        const isHidden = new Set(hidden)

        ctx.globalAlpha = 1;

        props.data.forEach((d, i) => {

            let p;
            if (!isSel.has(d[props.idAttr])) {
                p = DM.getDerivedItem("tags_path", d[props.idAttr])
                if (p && p.path.some(dd => sel.has(dd))) {
                    isSel.add(d[props.idAttr])
                }
            }

            let isSelected = isSel.has(d[props.idAttr])

            if (!isSelected && !isHidden.has(d[props.idAttr])) {
                p = p ? p : DM.getDerivedItem("tags_path", d[props.idAttr])
                if (p && p.path.some(dd => sel.has(dd))) {
                    isHidden.add(d[props.idAttr])
                }
            }

            ctx.globalAlpha = !isSelected && isHidden.has(d[props.idAttr]) ? props.hiddenOpacity : 1;

            ctx.fillStyle = isSelected ? selColor.value :
                props.binary ?
                    binCol.value : (getV(d) !== props.noValue ? color(getV(d))
                : noCol.value
            );
            ctx.fillRect(
                x(props.domain ? d[props.idAttr] : i),
                top && !hide ? 2*radius.value+offset : 0,
                x.bandwidth(),
                props.height
            );
        });

        ctx.globalAlpha = 1;
        ctx.beginPath()
        ctx.fillStyle = selColor.value;

        if (!props.hideHighlight && isSel.size > 0) {

            if (props.domain) {
                props.domain.forEach(id => {
                    if (isSel.has(id)) {
                        ctx.arc(
                            x(id) + x.bandwidth()*0.5,
                            top ? radius.value : completeHeight.value - radius.value,
                            radius.value, 0, Math.PI*2
                        );
                    }
                })
            } else {
                props.data.forEach((d, i) => {
                    if (!isSel.has(d[props.idAttr])) return;

                    ctx.fillStyle = selColor.value
                    ctx.arc(
                        x(props.domain ? d[props.idAttr] : i) + x.bandwidth()*0.5,
                        top ? radius.value : completeHeight.value - radius.value,
                        radius.value, 0, Math.PI*2
                    );
                });
            }
        }
        ctx.fill()
    }

    function onMove(event) {
        if (!x) return false;

        const [rx, _] = d3.pointer(event, el.value)
        const [mx, my] = d3.pointer(event, document.body)

        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)

            if (item) {
                const percent = item[props.valueAttr] * 100
                const absolute = props.absValueAttr ? item[props.absValueAttr] : null
                if (!props.hideTooltip) {
                    if (props.binary) {
                        tt.show(`<b>${item[props.nameAttr]}</b>`, mx, my)
                    } else {
                        tt.show(
                            props.showAbsolute ?
                                `<b>${item[props.nameAttr]}</b> (${absolute !== null ? absolute.toFixed(props.discrete ? 0 : 2) : '<none>'})` :
                                absolute !== null ?
                                    `${percent.toFixed(2)}% (${absolute.toFixed(props.discrete ? 0 : 2)})<br/>${item[props.nameAttr]}` :
                                    `${percent.toFixed(2)}%<br/>${item[props.nameAttr]}`,
                            mx, my
                        )
                    }
                }
                emit("hover", item, event)
            } else {
                if (!props.hideTooltip) {
                    const n = DM.getDataItem("tags_name", id)
                    if (n) {
                        tt.show(n, mx, my)
                    } else {
                        tt.hide()
                    }
                }
                emit("hover", null)
            }
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            const percent = item[props.valueAttr] * 100
            const absolute = props.absValueAttr ? item[props.absValueAttr] : null
            if (!props.hideTooltip) {
                if (props.binary) {
                    tt.show(item[props.nameAttr], mx, my)
                } else {
                    tt.show(
                        props.showAbsolute ?
                            `<b>${item[props.nameAttr]}</b> (${absolute !== null ? absolute.toFixed(props.discrete ? 0 : 2) : '<none>'})` :
                            absolute !== null ?
                                `${percent.toFixed(2)}% (${absolute.toFixed(props.discrete ? 0 : 2)})<br/>${item[props.nameAttr]}` :
                                `${percent.toFixed(2)}%<br/>${item[props.nameAttr]}`,
                        mx, my
                    )
                }
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
            if (item) {
                emit("click", item, event)
            } else {
                const copy = Array.isArray(props.data[0]) ? [] : {}
                copy[props.idAttr] = id
                copy[props.nameAttr] = DM.getDataItem("tags_name", id)
                emit("click", copy, event)
            }
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            if (item[props.valueAttr] > 0) emit("click", item, event)
        }
    }

    function onRightClick(event) {
        if (!props.selectable) return;
        event.preventDefault()
        const [rx, _] = d3.pointer(event, el.value)
        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)
            if (item) {
                emit("right-click", item, event)
            } else {
                const copy = Array.isArray(props.data[0]) ? [] : {}
                copy[props.idAttr] = id
                copy[props.nameAttr] = DM.getDataItem("tags_name", id)
                emit("right-click", copy, event)
            }
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            if (item[props.valueAttr] > 0) emit("right-click", item, event)
        }
    }

    onMounted(draw)
    onUpdated(drawBars)

    watch(() => times.f_tags, drawBars)
    watch(() => settings.lightMode, drawBars)
    watch(() => ([
        props.selected,
        props.selectedColor,
        props.binaryColorFill,
        props.noValueColor,
        props.binary,
        props.hideHighlight,
        props.highlightPos,
    ]), drawBars, { deep: true })

    watch(() => ([
        props.categorical,
        props.colorScale
    ]), function() {
        makeColorScale()
        drawBars()
    }, { deep: true })

    watch(() => ([
        props.data,
        props.domain,
        props.width,
        props.height,
        props.idAttr,
        props.nameAttr,
        props.valueAttr,
        props.absValueAttr,
        props.minValue,
        props.maxValue,
        props.showAbsolute
    ]), draw, { deep: true })

</script>