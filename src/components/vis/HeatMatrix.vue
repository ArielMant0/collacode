<template>
    <div>
        <v-range-slider v-if="rangeSlider"
            v-model="threshold"
            :min="domainMin"
            :max="domainMax"
            hide-details
            hide-spin-buttons
            :step="0.01"
            style="max-width: 50%;"
            density="compact"
            thumb-label="always"
            label="value range"
            class="mt-4"
            @update:model-value="drawCells"/>

        <div style="position: relative;">
            <canvas ref="el" :width="realWidth" :height="realHeight"></canvas>
            <svg ref="overlay" style="position: absolute; left: 0; top: 0;"
                :width="realWidth"
                :height="realHeight"
                @pointermove="onMove"
                @pointerleave="tt.hide()"
                @click="onClick"></svg>
        </div>
    </div>
</template>

<script setup>

    import * as d3 from 'd3'
    import { useTooltip } from '@/store/tooltip';
    import { computed, onUpdated, ref, watch } from 'vue';
    import { useSettings } from '@/store/settings';

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        labels: {
            type: Object,
            required: true
        },
        size: {
            type: Number,
            default: 500
        },
        hideXLabels: {
            type: Boolean,
            default: false
        },
        hideYLabels: {
            type: Boolean,
            default: false
        },
        hideTooltip: {
            type: Boolean,
            default: false
        },
        rangeSlider: {
            type: Boolean,
            default: false
        },
        colorScale: {
            type: String,
            default: "interpolatePlasma"
        },
        minValue: {
            type: Number,
            default: 0
        },
        maxValue: { type: Number },
    })

    const emit = defineEmits(["hover", "click", "right-click"])

    const tt = useTooltip();
    const settings = useSettings()

    const el = ref(null)
    const overlay = ref(null)

    let context, x, y, color;

    const threshold = ref([0, 1])
    const domainMin = ref(0)
    const domainMax = ref(100);

    const domain = computed(() => props.labels ? Object.keys(props.labels).map(d => +d) : [])

    const maxLabelLen = computed(() => d3.max(Object.values(props.labels), d => d.length))
    const offsetX = computed(() => props.hideYLabels ? 15 : Math.min(15 + maxLabelLen.value*5, 150))
    const offsetY = computed(() => props.hideXLabels ? 15 : Math.min(15 + maxLabelLen.value*5, 150))
    const realWidth = computed(() => props.size + offsetX.value - 5)
    const realHeight = computed(() => props.size + offsetY.value - 5)

    let zoom, zoomTrans = d3.zoomIdentity
    let highlightItem

    function init() {
        if (el.value) {
            context = el.value.getContext("2d");
            draw();
        } else {
            setTimeout(init, 200)
        }
    }

    function draw() {
        x = d3.scaleBand()
            .domain(domain.value)
            .range([offsetX.value, realWidth.value-5])
            .paddingInner(0.01)

        y = d3.scaleBand()
            .domain(domain.value)
            .range([offsetY.value, realHeight.value-5])
            .paddingInner(0.01)

        domainMax.value = props.maxValue ? props.maxValue : d3.max(props.data, d => d.value)

        color = d3.scaleSequential(d3[props.colorScale])
            .domain([props.minValue, domainMax.value])

        drawCells()

        const extent = [[offsetX.value, offsetY.value], [realWidth.value-5, realHeight.value-5]]

        zoom = d3.zoom()
            .scaleExtent([1, 8])
            .translateExtent(extent)
            .extent(extent)
            .filter(event => event.shiftKey)
            .on("zoom", onZoom)

        d3.select(overlay.value)
            .call(zoom)
            .on("dblclick.zoom", resetZoom)

        drawAxes()
    }
    function drawAxes() {
        const svg = d3.select(overlay.value)
        svg.selectAll("*").remove()

        if (!x || !y) return

        x.range([offsetX.value, realWidth.value-5].map(d => zoomTrans.applyX(d)))
        y.range([offsetY.value, realHeight.value-5].map(d => zoomTrans.applyY(d)))

        if (!props.hideYLabels) {
            svg.append("g")
                .attr("transform", `translate(${offsetX.value}, 0)`)
                .call(d3.axisLeft(y).tickFormat(d => props.labels[d]))
                .select(".domain").remove()
        }

        if (!props.hideXLabels) {
            svg.append("g")
                .attr("transform", `translate(0, ${offsetY.value})`)
                .call(d3.axisTop(x).tickFormat(d => props.labels[d]))
                .select(".domain").remove()
                .selectAll(".tick text")
                .attr("text-anchor", "middle")
                .attr("transform", `rotate(-45 ${x.bandwidth()*0.5}) 0`)
        }
    }
    function drawCells() {
        context.clearRect(0, 0, realWidth.value, realHeight.value)
        props.data.forEach(d => {
            const dx = x(d.target), dy = y(d.source)
            if (dx < offsetX.value || dx > realWidth.value || dy < offsetY.value || dy > realHeight.value) return

            context.fillStyle = color(d.value)
            context.globalAlpha = d.value < threshold.value[0] || d.value >= threshold.value[1] ? 0.1 : 1
            context.fillRect(x(d.target), y(d.source), x.bandwidth(), y.bandwidth())
        });
    }
    function resetZoom() {
        d3.select(overlay.value)
            .transition()
            .duration(750)
            .call(zoom.transform, d3.zoomIdentity)
        drawAxes()
        drawCells()
    }
    function onZoom(event) {
        zoomTrans = event.transform
        drawAxes()
        drawCells()
        if (highlightItem) {
            highlight(highlightItem)
        }
    }

    function itemFromCoords(event) {
        let item;
        const [mx, my] = d3.pointer(event, overlay.value)
        if (mx < offsetX.value || my < offsetY.value) return item

        let i = -1, j = -1;

        for (let idx = 0; idx < domain.value.length && (i < 0 || j < 0); ++idx) {
            const dx = x(domain.value[idx])
            const dy = y(domain.value[idx])
            if (mx >= dx && mx <= dx + x.bandwidth()) {
                i = idx;
            }
            if (my >= dy && my <= dy + y.bandwidth()) {
                j = idx;
            }
        }

        if (i >= 0 && i < domain.value.length && j >= 0 && j < domain.value.length) {
            const dt = domain.value[i]
            const ds = domain.value[j]
            item = props.data.find(d => d.target === dt && d.source === ds)
        }

        return item ? item : null
    }
    function onMove(event) {
        const item = itemFromCoords(event)
        if (item) {
            highlight(item)
            const [wx, wy] = d3.pointer(event, document.body)
            tt.show(`${props.labels[item.source]} -> ${props.labels[item.target]}: ${item.value.toFixed(2)}`, wx+10, wy)
            emit("hover", item, event)
        } else {
            highlight()
            tt.hide()
            emit("hover", null)
        }
    }
    function onClick(event) {
        if (event.shiftKey) return
        const item = itemFromCoords(event)
        if (item) {
            emit("click", item, event)
        } else {
            emit("click", null)
        }
    }
    function highlight(item) {
        const svg = d3.select(overlay.value)
        svg.selectAll(".tmp").remove()
        highlightItem = item
        if (item) {
            svg.append("rect")
                .classed("tmp", true)
                .attr("x", x(item.target)-1)
                .attr("y", y(item.source)-1)
                .attr("width", x.bandwidth()+2)
                .attr("height", y.bandwidth()+1)
                .attr("stroke-width", 2)
                .attr("fill", color(item.value))
                .attr("stroke", settings.lightMode ? "white" : "black")
        }
    }

    onMounted(init)
    onUpdated(function() {
        drawCells()
        drawAxes()
    })

    watch(props, init, { deep: true });
</script>