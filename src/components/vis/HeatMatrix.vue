<template>
    <div>
        <v-slider v-model="threshold"
            :min="domainMin"
            :max="domainMax"
            :step="1"
            hide-details
            density="compact"
            :style="{ 'max-width': (width-100)+'px' }"
            show-ticks
            thumb-label="always"
            label="threshold"
            :thumb-size="4"
            thumb-color="primary"
            class="mt-4"
            @update:model-value="filterData"/>
        <div style="position: relative;">
            <canvas ref="el" :width="width" :height="height"></canvas>
            <svg ref="overlay" style="position: absolute; left: 0; top: 0;" :width="width" :height="height"></svg>
        </div>
    </div>
</template>

<script setup>

    import * as d3 from 'd3'
    import { ref, watch } from 'vue';
    import DM from '@/use/data-manager'

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        labels: {
            type: Object,
            required: true
        },
        time: {
            type: Number,
            required: true
        },
        width: {
            type: Number,
            default: 500
        },
        height: {
            type: Number,
            default: 500
        },
    })

    const el = ref(null)
    const overlay = ref(null)

    const data = ref([])
    const threshold = ref(1)

    let context, x, y, color;
    const maxRelatedVal = new Map();
    const domainMin = ref(0)
    const domainMax = ref(100);

    function init() {
        context  = el.value.getContext("2d");
        onHighlight();
    }

    function draw() {
        context.clearRect(0, 0, props.width, props.height)

        x = d3.scaleBand()
            .domain(data.value.map(d => d.source))
            .range([150, props.width-50])

        y = d3.scaleBand()
            .domain(data.value.map(d => d.source))
            .range([150, props.height-5])

        color = d3.scaleSequential(d3.interpolateViridis)
            .domain([1, d3.max(data.value, d => d.value)])

        data.value.forEach(d => {
            // if (visited[d.source] && visited[d.source][d.target]) return;

            // if (!visited[d.source]) {
            //     visited[d.source] = {}
            // }
            // visited[d.source][d.target] = true;
            // if (!visited[d.target]) {
            //     visited[d.target] = {}
            // }
            // visited[d.target][d.source] = true;

            context.beginPath()
            context.fillStyle = color(d.value)
            context.fillRect(x(d.target), y(d.source), x.bandwidth(), y.bandwidth())
            context.fillRect(x(d.source), y(d.target), x.bandwidth(), y.bandwidth())

            // context.beginPath()
            // context.translate(x(d.target) + x.bandwidth() * 0.5, 145)
            // context.rotate((-60 * Math.PI) / 180)
            // context.fillStyle = "#000"
            // context.strokeStyle = "none";
            // context.textAlign = "start"
            // context.textBaseline = "bottom"
            // context.fillText(props.labels[d.target], 0, 0)

            // context.setTransform()
            // context.beginPath()
            // context.fillStyle = "#000"
            // context.strokeStyle = "none";
            // context.textAlign = "end"
            // context.textBaseline = "top"
            // context.font = Math.max(8, Math.min(12, (y.bandwidth() - 6))) + "px Arial"
            // context.fillText(props.labels[d.source], 145, y(d.source) + y.bandwidth() * 0.5)
        });

        const svg = d3.select(overlay.value)
        svg.selectAll("*").remove()

        svg.append("g")
            .attr("transform", "translate(150, 0)")
            .call(d3.axisLeft(y).tickFormat(d => props.labels[d]))

        svg.append("g")
            .attr("transform", `translate(0, 150)`)
            .call(d3.axisTop(x).tickFormat(d => props.labels[d]))
            .selectAll(".tick text")
            .attr("text-anchor", "start")
            .attr("transform", d => `translate(${y.bandwidth()*0.5},-5)rotate(-45)`)
    }

    function onHighlight() {
        const sels = new Set(DM.getSelectedIds("tags"))

        maxRelatedVal.clear();

        if (sels.size === 0) {
            props.data.sort((a, b) => {
                const nameA = props.labels[a.source].toLowerCase(); // ignore upper and lowercase
                const nameB = props.labels[b.source].toLowerCase(); // ignore upper and lowercase
                if (nameA < nameB) { return -1; }
                if (nameA > nameB) { return 1; }
                // names must be equal
                return 0;
            })
        } else {
            const gs = d3.group(props.data.filter(d => sels.has(d.source) || sels.has(d.target)), d => d.source)
            gs.forEach((val, key) => {
                if (sels.has(key)) {
                    maxRelatedVal.set(key, 1)
                } else {
                    const matching = val.filter(d => sels.has(d.target));
                    maxRelatedVal.set(key, d3.max(matching, d => d.value))
                }
            })
            // reorder data
            props.data.sort((a, b) => {
                // if source is contained in selected tags
                if (sels.has(a.source) && sels.has(b.source)) {
                    return 0
                } else if (sels.has(a.source)) {
                    return -1
                } else if (sels.has(b.source)) {
                    return 1
                }

                return maxRelatedVal.get(b.target) > maxRelatedVal.get(a.target) ?
                    1 :
                    (maxRelatedVal.get(b.target) === maxRelatedVal.get(a.target) ? 0 : -1);
            })
        }

        const domain = d3.extent(props.data, d => d.value)
        threshold.value = domain[0]
        domainMin.value = 0
        domainMax.value = domain[1]

        filterData();
    }

    function filterData() {
        data.value = props.data.filter(d => maxRelatedVal.size === 0 || maxRelatedVal.get(d.target) >= threshold.value)
        draw();

    }

    onMounted(init)

    watch(() => [props.width, props.height], init, { deep: true });
    watch(() => props.time, onHighlight)
</script>