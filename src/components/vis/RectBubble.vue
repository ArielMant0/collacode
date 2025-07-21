<template>
    <svg ref="el" :width="width" :height="height" :style="{ minWidth: width+'px', minHeight: height+'px' }"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useSettings } from '@/store/settings';
    import { computed, onMounted, ref, watch } from 'vue';

    const settings = useSettings()

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
    })

    const el = ref(null)

    const emit = defineEmits(["click", "hover"])

    const cols = computed(() => Math.floor(props.width / props.rectSize))
    const rows = computed(() => Math.max(1, Math.ceil(props.data.length / cols.value)))
    const height = computed(() => props.rectSize * rows.value)

    function draw() {

        const svg = d3.select(el.value)
        svg.selectAll("*").remove()

        if (props.data.length === 0) return

        const set = new Set(props.selected)
        const high = new Set(props.highlights)

        const w = props.rectSize
        const h = props.rectSize

        svg.selectAll("rect")
            .data(props.data)
            .join("rect")
            .attr("x", (_d, i) => (i % cols.value) * w)
            .attr("y", (_d, i) => (Math.floor(i / cols.value)) * h)
            .attr("fill", d => {
                const c = d3.color(set.has(d.id) ? props.selectedColor : (high.has(d.id) ? props.highlightsColor : props.color))
                return c.brighter(1.25)
            })
            .attr("stroke", d => set.has(d.id) ? props.selectedColor : (high.has(d.id) ? props.highlightsColor : props.color))
            .attr("width", 0)
            .attr("height", 0)
            .style("cursor", "pointer")
            .on("pointermove", function(event, d) {
                emit("hover", d, event)
                d3.select(this).attr("stroke", settings.lightMode ? "black" : "white")
            })
            .on("pointerleave", function(d) {
                emit("hover", null, null)
                const c = d3.color(set.has(d.id) ? props.selectedColor : (high.has(d.id) ? props.highlightsColor : props.color))
                d3.select(this).attr("stroke", c.darker(1.5))
            })
            .on("click", function(event, d) {
                emit("click", d, event)
            })
            .transition()
            .duration(1500)
            .ease(d3.easeElasticOut.amplitude(1.05))
            .delay((_d, i) => i * 100)
            .attr("width", w - props.padding)
            .attr("height", h - props.padding)
            .attr("fill", d => set.has(d.id) ? props.selectedColor : (high.has(d.id) ? props.highlightsColor : props.color))
            .attr("stroke", d => {
                const c = d3.color(set.has(d.id) ? props.selectedColor : (high.has(d.id) ? props.highlightsColor : props.color))
                return c.darker(1.5)
            })
    }

    onMounted(draw)

    watch(props, draw)
</script>