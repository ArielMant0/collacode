<template>
    <svg ref="el" :width="width" :height="height" :style="{ minWidth: width+'px', minHeight: height+'px' }"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useSettings } from '@/store/settings';
    import { computed, onMounted, onUnmounted, ref, watch } from 'vue';

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
        height: {
            type: Number,
            default: 200
        },
        radius: {
            type: Number,
        },
    })

    const el = ref(null)

    const emit = defineEmits(["click", "hover"])

    const cr = computed(() => props.radius ? props.radius+1 : Math.ceil(Math.sqrt((props.width*props.height) / Math.max(1, props.data.length)))+1)
    const numRows = computed(() => Math.ceil(props.width / cr.value))
    const numCols = computed(() => Math.ceil(props.height / cr.value))

    function draw() {

        const svg = d3.select(el.value)
        svg.selectAll("*").remove()

        const set = new Set(props.selected)
        const high = new Set(props.highlights)

        svg.selectAll("rect")
            .data(props.data)
            .join("rect")
            .attr("x", (_d, i) => (i % numRows.value) * cr.value)
            .attr("y", (_d, i) => Math.floor(i / numCols.value) * cr.value)
            .attr("fill", d => set.has(d.id) ? props.selectedColor : (high.has(d.id) ? props.highlightsColor : props.color))
            .attr("width", cr.value-1)
            .attr("height", cr.value-1)
            .style("cursor", "pointer")
            .on("pointermove", function(event, d) {
                emit("hover", d, event)
                d3.select(this).attr("stroke", settings.lightMode ? "black" : "white")
            })
            .on("pointerleave", function() {
                emit("hover", null, null)
                d3.select(this).attr("stroke", "none")
            })
            .on("click", function(event, d) {
                emit("click", d, event)
            })
    }

    onMounted(draw)

    watch(props, draw)
    watch(cr, draw)
</script>