<template>
    <svg ref="el" :width="width" :height="height" :style="{ minWidth: width+'px', minHeight: height+'px' }"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { computed, onMounted, ref, watch } from 'vue';
    import { mediaPath } from '@/use/utility';

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        selected: {
            type: Array,
            required: false
        },
        highlights: {
            type: Array,
            required: false
        },
        imageAttr: {
            type: String,
        },
        mediaPathType: {
            type: String,
            default: "teaser"
        },
        color: {
            type: String,
            default: "grey"
        },
        selectedColor: {
            type: String,
            default: "red"
        },
        highlightsColor: {
            type: String,
            default: "blue"
        },
        width: {
            type: Number,
            default: 200
        },
        rectSize: {
            type: Number,
            default: 25
        },
        padding: {
            type: Number,
            default: 3
        },
        draggable: {
            type: Boolean,
            default: false
        }
    })

    const el = ref(null)

    const emit = defineEmits(["click", "hover", "dragstart", "drag"])

    const cols = computed(() => Math.floor(props.width / props.rectSize))
    const rows = computed(() => Math.max(1, Math.ceil(props.data.length / cols.value)))
    const height = computed(() => props.rectSize * rows.value)

    let rects

    function getColor(id) {
        const inSel = props.selected ? props.selected.includes(id) : false
        const inHigh = props.highlights ? props.highlights.includes(id) : false
        return d3.color(inSel ? props.selectedColor : (inHigh ? props.highlightsColor : props.color))
    }

    function draw() {

        const svg = d3.select(el.value)
        svg.selectAll("*").remove()

        if (props.data.length === 0) return

        const w = props.rectSize
        const h = props.rectSize

        rects = svg.selectAll("rect")
            .data(props.data)
            .join("rect")
            .attr("x", (_d, i) => (i % cols.value) * w)
            .attr("y", (_d, i) => (Math.floor(i / cols.value)) * h)
            .attr("fill", d => {
                const c = getColor(d.id)
                return c.brighter(0.5)
            })
            .attr("stroke", d => getColor(d.id))
            .attr("width", 0)
            .attr("height", 0)
            .style("cursor", "pointer")
            .attr("draggable", props.draggable)
            .on("dragstart", function(event, d) {
                if (!props.draggable) return
                if (props.imageAttr) {
                    const img = new Image(160, 80)
                    img.src = mediaPath(props.mediaPathType, d[props.imageAttr])
                    event.dataTransfer.setDragImage(img, 80, 40)
                }
                emit("dragstart", d, event)
            })
            .on("drag", function(event, d) {
                if (!props.draggable) return
                emit("drag", d, event)
            })
            .on("pointerenter", function(_event, d) {
                emit("hover", null, null)
                d3.select(this)
                    .transition(50)
                    .attr("fill", getColor(d.id).brighter(0.5))
            })
            .on("pointermove", function(event, d) {
                emit("hover", d, event)
            })
            .on("pointerleave", function(_event, d) {
                emit("hover", null, null)
                d3.select(this)
                    .transition(50)
                    .attr("fill", getColor(d.id))
            })
            .on("click", function(event, d) {
                emit("click", d, event)
            })

        rects
            .transition()
            .duration(1500)
            .ease(d3.easeElasticOut.amplitude(1.05))
            .delay((_d, i) => i * 100)
            .attr("width", w - props.padding)
            .attr("height", h - props.padding)
            .attr("fill", d => getColor(d.id))
            .attr("stroke", d => {
                const c = getColor(d.id)
                return c.darker(1)
            })
    }

    function highlight() {
        rects
            .transition(250)
            .attr("fill", d => getColor(d.id))
            .attr("stroke", d => {
                const c = getColor(d.id)
                return c.darker(1)
            })
    }

    onMounted(draw)

    watch(() => props.data, draw)
    watch(() => props.color, highlight)
    watch(() => props.highlights, highlight)
    watch(() => props.selected, highlight)

</script>