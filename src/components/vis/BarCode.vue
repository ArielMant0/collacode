<template>
    <div style="position: relative;">
        <canvas ref="el"
            :style="{ cursor: selectable ? 'pointer' : 'default' }"
            :width="completeWidth"
            :height="completeHeight"
            @click="onClick"
            @contextmenu="onRightClick"
            @pointermove="onMove"
            @pointerleave="onLeave">
        </canvas>
        <svg style="pointer-events: none; position: absolute; top:0; left:0;" ref="overlay" :width="completeWidth" :height="completeHeight"></svg>
    </div>

</template>

<script setup>
    import * as d3 from 'd3'
    import { useTooltip } from '@/store/tooltip';
    import { computed, onMounted, onUpdated, reactive, ref, watch } from 'vue';
    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import { useSettings } from '@/store/settings';
    import { isVideo, mediaPath } from '@/use/utility';
    import { useApp } from '@/store/app';

    const app = useApp()
    const tt = useTooltip()
    const times = useTimes()
    const settings = useSettings()

    const props = defineProps({
        itemId: {
            type: Number,
            required: false
        },
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
        descAttr: {
            type: String,
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
        hoverColor: {
            type: String,
            default: "red"
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
        hideValue: {
            type: Boolean,
            default: false
        },
        hideEvidence: {
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
    const overlay = ref(null)

    const completeWidth = computed(() => (props.domain ? props.domain.length : props.data.length) * props.width)
    const completeHeight = computed(() => props.height + (props.hideHighlight ? 0 : 2*radius.value + offset))
    const radius = computed(() => Math.max(3, Math.min(6, scales.x ? Math.floor(scales.x.bandwidth()*0.5) : 4)))

    const noCol = computed(() => props.noValueColor ? props.noValueColor : (settings.lightMode ? "#ffffff": "#121212"))
    const binCol = computed(() => props.binary && props.binaryColorFill ? props.binaryColorFill : (settings.lightMode ? "#121212" : "#ffffff"))

    let ctx, x, color, offset = 2;
    const scales = reactive({ x: null })
    const itemEv = ref([])

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

            ctx.fillStyle = props.binary ?
                (getV(d) !== props.noValue ? binCol.value : noCol.value) :
                (getV(d) !== props.noValue && color ? color(getV(d)) : noCol.value)

            ctx.beginPath()
            ctx.rect(
                x(props.domain ? d[props.idAttr] : i),
                top && !hide ? 2*radius.value+offset : 0,
                x.bandwidth(),
                props.height
            )
            ctx.fill()

            if (isSelected) {
                ctx.strokeStyle = selColor.value
                ctx.stroke()
            }

            ctx.closePath()
        })

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

                    // ctx.fillStyle = selColor.value
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

    function drawOverlay(xAttr) {
        const svg = d3.select(overlay.value)

        const top = props.highlightPos === "top"
        const hide = props.hideHighlight

        svg.selectAll(".bar")
            .data(xAttr ? [xAttr] : [])
            .join("rect")
            .classed("bar", true)
            .attr("x", x(xAttr))
            .attr("y", top && !hide ? 2*radius.value+offset : 1)
            .attr("width", x.bandwidth())
            .attr("height", props.height)
            .attr("fill", "none")
            .attr("stroke-width", 1)
            .attr("stroke", props.hoverColor)
    }

    function getObjections(id) {
        let objs = []
        if (props.itemId) {
            // if we have an item id
            const tmp = DM.getDataItem("objections_items", props.itemId)
            if (tmp) {
                objs = tmp.filter(d => d.tag_id === id)
            }
        } else {
            // if we only have a tag
            const tmp = DM.getDataItem("objections_tags", id)
            if (tmp) {
                objs = tmp
            }
        }
        return objs
    }
    function getEvidence(id) {
        return itemEv.value
            .filter(d => d.tag_id === id)
            .map(d => d.filepath)
    }

    function makeTooltip(item) {
        const desc = props.descAttr ? `</br>${item[props.descAttr]}` : "</br>"+DM.getDataItem("tags_desc", item[props.idAttr])
        const percent = item[props.valueAttr] * 100
        const absolute = props.absValueAttr ? item[props.absValueAttr] : null
        const objs = getObjections(item[props.idAttr])
        const objStr = `</br>${objs.length} objections`
        let evStr =  ""
        const matchingEv = getEvidence(item[props.idAttr])
        if (!props.hideEvidence && matchingEv.length > 0) {
            evStr = "</br>" + matchingEv.reduce((acc, url) => {
                return acc + (isVideo(url) ?
                    `<video src=${mediaPath('evidence', url)}
                        width="80"
                        height="80"
                        class="mr-1 mb-1 bordered-grey-thin"
                        autoplay="true"
                        loop="true"
                        style="object-fit: contain;"/>` :
                    `<img src=${mediaPath('evidence', url)}
                        width="80"
                        height="80"
                        class="mr-1 mb-1 bordered-grey-thin"
                        style="object-fit: contain;"/>`)
            }, "")
        }

        if (props.binary || props.hideValue) {
            return `<b>${item[props.nameAttr]}</b>${objStr}${desc}${evStr}`
        } else {
            const value = absolute !== null ? absolute.toFixed(props.discrete ? 0 : 2) : ""
            return props.showAbsolute ?
                `<b>${item[props.nameAttr]}</b> (${absolute !== null ? value : '<none>'})${objStr}${desc}` :
                absolute !== null ?
                    `${percent.toFixed(2)}% (${value})<br/>${item[props.nameAttr]}${objStr}${desc}` :
                    `${percent.toFixed(2)}%<br/>${item[props.nameAttr]}${objStr}${desc}`
        }
    }

    function onMove(event) {
        if (!x) return false;

        const [rx, _] = d3.pointer(event, el.value)
        const [mx, my] = d3.pointer(event, document.body)

        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)

            if (item) {
                if (!props.hideTooltip) {
                    tt.show(makeTooltip(item), mx, my)
                }
                drawOverlay(item[props.idAttr])
                emit("hover", item, event)
            } else {
                if (!props.hideTooltip) {
                    const tag = DM.getDataItem("tags", id)
                    if (tag) {
                        const desc = tag.description ? `</br>${tag.description}` : ""
                        const objs = getObjections(id)
                        const objStr = `</br>${objs.length} objections`
                        tt.show(`${tag.name}${objStr}${desc}`, mx, my)
                        drawOverlay(id)
                    } else {
                        tt.hide()
                    }
                }
                emit("hover", null)
            }
        } else {
            const index = Math.min(props.data.length-1, Math.floor(rx / x.bandwidth()))
            const item = props.data.at(index)

            if (!props.hideTooltip) {
                tt.show(makeTooltip(item), mx, my)
            }
            drawOverlay(index)
            emit("hover", item, event)
        }
    }
    function onLeave() {
        if (!props.hideTooltip) {
            tt.hide()
        }
        drawOverlay(null)
        emit("hover", null)
    }

    function onClick(event) {
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
            emit("click", item, event)
        }
    }

    function onRightClick(event) {
        event.preventDefault()
        const [rx, _] = d3.pointer(event, el.value)
        if (props.domain) {
            const id = props.domain.at(Math.min(props.domain.length-1, Math.floor(rx / x.bandwidth())))
            const item = props.data.find(d => d[props.idAttr] === id)
            if (item) {
                emit("right-click", item, event, true)
            } else {
                const copy = Array.isArray(props.data[0]) ? [] : {}
                copy[props.idAttr] = id
                copy[props.nameAttr] = DM.getDataItem("tags_name", id)
                emit("right-click", copy, event, false)
            }
        } else {
            const item = props.data.at(Math.min(props.data.length-1, Math.floor(rx / x.bandwidth())))
            if (item[props.valueAttr] > 0) emit("right-click", item, event, true)
        }
    }

    function readItem() {
        if (props.itemId) {
            itemEv.value = DM.getDataBy("evidence", d => {
                return d.filepath &&
                    d.item_id === props.itemId &&
                    d.code_id === app.activeCode
            })
        } else {
            itemEv.value = []
        }
    }

    onMounted(function() {
        readItem()
        draw()
    })
    onUpdated(drawBars)

    watch(() => props.itemId, readItem)

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