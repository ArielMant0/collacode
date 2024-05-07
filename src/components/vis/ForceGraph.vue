<template>
    <canvas ref="el" :width="width" :height="height"></canvas>
</template>

<script setup>

    import * as d3 from 'd3'
    import { ref } from 'vue';
    import forceBoundary from 'd3-force-boundary'

    const props = defineProps({
        nodes: {
            type: Array,
            required: true
        },
        links: {
            type: Array,
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
    let context, simulation, color, lineWidth;

    function init() {
        if (!context) {
            context = el.value.getContext("2d")
        }

        if (simulation) {
            simulation.stop()
        }

        color = d3.scaleSequential(d3.interpolateMagma)
            .domain([1, d3.max(props.nodes, d => d.value)])

        lineWidth = d3.scaleLinear()
            .domain([1, d3.max(props.links, d => d.value)])
            .range([1, 10])

        // Create a simulation with several forces.
        simulation = d3.forceSimulation(props.nodes)
            .force("link", d3.forceLink(props.links).id(d => d.id).strength(d => d.value > 5 ? 2 / d.value : 0.01))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter(props.width / 2, props.height / 2))
            .force("boundary", forceBoundary(10, 10, props.width-10, props.height-10))
            .alphaDecay(0.01)
            .on("tick", draw)

        simulation.restart()
    }

    function draw() {
        if (!context) return;
        context.clearRect(0, 0, props.width, props.height);

        context.save();
        context.globalAlpha = 0.4;
        context.strokeStyle = "#999";
        context.beginPath();
        props.links.forEach(link => {
            if (link.value > 10) {
                context.lineWidth = lineWidth(link.value)
                drawLink(link)
            }
        });
        context.stroke();
        context.restore();

        context.save();
        context.strokeStyle = "#fff";
        context.globalAlpha = 1;
        props.nodes.forEach(node => {
            if (node.value > 0) {
                context.beginPath();
                drawNode(node)
                context.fillStyle = color(node.value)
                context.strokeStyle = "#fff";
                context.fill();
                context.stroke();
            }
        });
        context.restore();
    }

    function drawLink(d) {
        context.moveTo(d.source.x, d.source.y);
        context.lineTo(d.target.x, d.target.y);
    }

    function drawNode(d) {
        context.moveTo(d.x + 5, d.y);
        context.arc(d.x, d.y, 5, 0, 2 * Math.PI);
        context.fillStyle = "#000"
        if (d.value > 0) {
            const offX = d.x > props.width * 0.5 ? -d.name.length * 5 : 5;
            const offY = d.y > props.height * 0.5 ? -10 : 10;
            context.fillText(d.name, d.x + offX, d.y + offY)
        }
    }

    onMounted(init)

    watch(() => props.time, init)
</script>