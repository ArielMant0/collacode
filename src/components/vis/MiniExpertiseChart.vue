<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTooltip } from '@/store/tooltip';
    import { onMounted, watch } from 'vue';
    import { useApp } from '@/store/app';

    const app = useApp()
    const tt = useTooltip()

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        width: {
            type: Number,
            default: 150
        },
        height: {
            type: Number,
            default: 50
        },
    })

    const el = ref(null)

    const labels = {
        0: "none",
        1: "basic research",
        2: "knowledgeable",
        3: "expert"
    }

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove()

        const counts = new Map()
        props.item.expertise.forEach(d => {
            if (!counts.has(d.value)) {
                counts.set(d.value, [d.user_id])
            } else {
                counts.get(d.value).push(d.user_id)
            }
        })

        const data = [];
        let before = 0, sum = 0;
        counts.forEach((users, v) => data.push({ value: v, users: users, before: 0 }))
        data.sort((a, b) => a.value - b.value)
        data.forEach(d => {
            d.before = before
            before += d.users.length;
            sum += d.users.length
        })

        const x = d3.scaleLinear()
            .domain([0, sum])
            .range([0, props.width])

        const colors = d3.scaleOrdinal()
            .domain([0, 1, 2, 3])
            .range(["#ffffff", "#e31a1c", "#e8e120", "#238b45"])

        svg.append("g")
            .selectAll("rect")
            .data(data)
            .join("rect")
            .attr("x", d => x(d.before))
            .attr("y", 0)
            .attr("width", d => x(d.users.length))
            .attr("height", props.height)
            .attr("fill", d => colors(d.value))
            .on("pointermove", function(event, d) {
                let chips = ""
                d.users.forEach(u => {
                    chips += `<div class="d-flex align-center mb-1">
                        <div class="mr-1" style="background-color: ${app.getUserColor(u)}; width: 15px; height: 15px; border-radius: 50%"></div>
                        <div>${app.getUserName(u)}</div>
                    </div>`
                })
                const [mx, my] = d3.pointer(event, document.body)
                tt.show(`<div class="text-caption"><b>${labels[d.value]}:</b></br>${chips}</div>`, mx+15, my)
            })
            .on("pointerleave", () => tt.hide())
    }

    onMounted(draw)

    watch(() => props.item.id, draw)
    watch(() => props.item.expertise, draw, { deep: true })
</script>