<template>
    <svg ref="el" :width="size" :height="size"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { onMounted, ref, watch } from 'vue';

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        selected: {
            type: Array,
            required: false
        },
        color: {
            type: String,
            default: "grey"
        },
        size: {
            type: Number,
            default: 200
        },
        radius: {
            type: Number,
            default: 7
        },
    })

    const el = ref(null)

    const emit = defineEmits(["click", "hover"])

    function draw() {

        const nodes = props.data.map(d => Object.assign({}, d))
        d3.forceSimulation(nodes)
            .velocityDecay(0.2)
            .force("x", d3.forceX(props.size / 2 - props.radius*2).strength(0.005))
            .force("y", d3.forceY(props.size / 2 - props.radius*2).strength(0.005))
            .force("collide", d3.forceCollide(props.radius).iterations(3))
            .on("tick", ticked)

        const svg = d3.select(el.value)
        const set = new Set(props.selected)
        const g = svg.selectAll("circle")
            .data(nodes)
            .join("circle")
            .attr("cx", d => d.x)
            .attr("cy", d => d.y)
            .attr("fill", d => set.has(d.id) ? "red": props.color)
            .attr("r", props.radius)
            .on("pointermove", function(event, d) {
                emit("hover", d, event)
                d3.select(this).attr("stroke", "black")
            })
            .on("pointerleave", function() {
                emit("hover", null, null)
                d3.select(this).attr("stroke", "none")
            })
            .on("click", function(event, d) {
                emit("click", d, event)
            })

        function ticked() {
            g
                .attr("cx", d => props.size*0.25 + d.x)
                .attr("cy", d => props.size*0.25 + d.y)
        }
    }

    onMounted(draw)

    watch(props, draw)
</script>