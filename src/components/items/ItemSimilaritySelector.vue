<template>
    <div ref="wrapper">
        <svg ref="el" :width="size*2" :height="size"></svg>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ref, reactive, onMounted } from 'vue';
    import { randomItems, randomItemsDissimilar } from '@/use/random';
import { mediaPath } from '@/use/utility';

    const props = defineProps({
        size: {
            type: Number,
            default: 300
        },
        imageWidth: {
            type: Number,
            default: 160
        },
        imageHeight: {
            type: Number,
            default: 80
        },
    })

    const el = ref(null)

    const items = ref([])
    const sims = ref([])
    const choices = ref([])
    const selected = ref(0)

    const removed = reactive(new Set())

    const MAX_ITEMS = 5
    const ANGLE_PETAL = 180 / MAX_ITEMS
    const ANGLES = d3.range(5).map(i =>  90 - i * ANGLE_PETAL)

    const scale = d3.scaleLinear().domain([0, 1])

    function nextItem() {
        const next = items.value.length > 0 ?
            randomItemsDissimilar(items.value, 1, Array.from(removed.values())) :
            randomItems(1, 3)
        items.value.push(next)
        sims.value.push(0)
        selected.value = items.value.length - 1
        removed.add(next.id)
        draw()
    }

    function onCircle(angle, radius) {
        const rad = angle * Math.PI / 180
        return [radius * Math.cos(rad), radius * Math.sin(rad)]
    }

    function draw() {
        const offX = props.size*0.5
        const size = props.size - props.imageHeight
        scale.range([5, props.size-5-props.imageHeight])

        const petals = d3.select(el.value)
            .selectAll(".petal")
            .data(items.value.map((d, i) => {
                const obj = Object.assign({}, d)
                obj._s = sims.value[i]
                obj._p = onCircle(ANGLES[i], size)
                return obj
            }))
            .join("g")
            .classed("petal", true)

        const [cx, cy] = onCircle(scale.range()[0], size)

        petals.append("line")
            .attr("x1", offX + cx)
            .attr("y1", props.imageHeight + cy)
            .attr("x2", d => offX + d._p[0])
            .attr("y2", d => props.imageHeight + d._p[1])
            .attr("stroke", 2)

        petals.append("circle")
            .attr("cx", d => offX + d._p[0])
            .attr("cy", d => props.imageHeight + d._p[1])
            .attr("r", 5)
            .attr("stroke", 1)
            .attr("fill", "grey")

        const [ex, _ey] = onCircle(scale.range()[1], size)

        petals.append("image")
            .attr("x", offX + ex)
            .attr("y", 0)
            .attr("width", props.imageWidth)
            .attr("height", props.imageHeight)
            .attr("href", d => mediaPath("teaser", d.teaser))
    }

    onMounted(function() {
        setTimeout(nextItem, 500)
    })
</script>