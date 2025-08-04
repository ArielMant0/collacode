<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { watch, onMounted, onBeforeUnmount, useTemplateRef } from 'vue'

    const props = defineProps({
        nodes: { type: Array, required: true },
        links: { type: Array, required: true },
        target: { type: Number, required: false },
        weightAttr: { type: String, required: false },
        imageAttr: { type: String, required: false },
        colorAttr: { type: String, required: false },
        targetColor: { type: String, default: "red" },
        highlightColor: { type: String, default: "HotPink" },
        fillColor: { type: String, default: "grey" },
        width: { type: Number, default: 600 },
        height: { type: Number, default: 400 },
        radius: { type: Number, default: 10 },
        transitionDuration: { type: Number, default: 1000 },
    })

    const emit = defineEmits(["click", "hover", "right-click"])

    let simulation
    let ng, lg
    let nodes, links

    let x, y, zoom, zoomTransform = d3.zoomIdentity
    const el = useTemplateRef("el")

    function resetZoom() {
        d3.select(el.value)
            .transition()
            .duration(props.transitionDuration)
            .call(zoom.transform, d3.zoomIdentity)
    }

    function focus(target=props.target) {
        if (!target) return
        const node = nodes.find(d => d.id === target)
        if (node) {
            d3.select(el.value)
                .transition()
                .duration(props.transitionDuration)
                .call(
                    zoom.transform,
                    d3.zoomIdentity
                        .translate(props.width / 2, props.height / 2)
                        .scale(8)
                        .translate(-node.x, -node.y)
                )
        }
    }

    function updateNodesAndLinks(transform=null) {

        const zx = transform ?
            transform.rescaleX(x).interpolate(d3.interpolateRound) :
            zoomTransform.rescaleX(x).interpolate(d3.interpolateRound)

        const zy = transform ?
            transform.rescaleY(y).interpolate(d3.interpolateRound) :
            zoomTransform.rescaleY(y).interpolate(d3.interpolateRound)

        if (transform) {
            zoomTransform = transform
        }

        ng.attr("transform", d => `translate(${zx(d.x)},${zy(d.y)}) scale(${Math.max(0.66, zoomTransform.k / 5)})`)

        lg
            .attr("x1", d => zx(d.source.x))
            .attr("x2", d => zx(d.target.x))
            .attr("y1", d => zy(d.source.y))
            .attr("y2", d => zy(d.target.y))
    }

    function highlight(id) {
        const match = new Set()
        const matchLink = new Set()
        if (id) {
            links.forEach(d => {
                if (d.source.id === id || d.target.id === id) {
                    matchLink.add(d.id)
                    match.add(d.source.id)
                    match.add(d.target.id)
                }
            })
        }

        ng.selectAll(".outline").attr("stroke", d => match.has(d.id) ? props.highlightColor : (d.id === props.target ? props.targetColor : "currentColor"))
        lg.attr("stroke", d => matchLink.has(d.id) ? props.highlightColor : "currentColor")
    }

    function draw() {
        if (simulation) {
            simulation.stop()
            simulation = null
        }

        nodes = props.nodes.map(d => ({ ...d }))
        links = props.links.map(d => ({ ...d }))

        zoom = d3.zoom()
            .scaleExtent([0.5, 32])
            .on("zoom", ({transform}) => updateNodesAndLinks(transform))

        const svg = d3.select(el.value)
        svg.selectAll('*').remove()

        lg = svg.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("x1", d => d.source.x)
            .attr("x2", d => d.target.x)
            .attr("y1", d => d.source.y)
            .attr("y2", d => d.target.y)
            .attr("stroke", "currentColor")
            .attr("stroke-width", 3)

        ng = svg.append("g")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .attr("transform", `translate(${props.width/2}, ${props.height/2})`)
            .on("click", function(event, d) {
                emit("click", d, event)
            })
            .on("contextmenu", function(event, d) {
                event.preventDefault()
                emit("right-click", d, event)
            })
            .on("pointerenter", function(_event, d) {
                d3.select(this).raise()
                highlight(d.id)
            })
            .on("pointermove", function(event, d) {
                emit("hover", d, event)
            })
            .on("pointerleave", function(event, d) {
                emit("hover", null)
                highlight(null)
            })

        if (props.imageAttr) {

            ng.append("rect")
                .classed("outline", true)
                .attr("x", -props.radius-1)
                .attr("y", -props.radius*0.5-1)
                .attr("width", props.radius*2+2)
                .attr("height", props.radius+2)
                .attr("stroke", d => d.id === props.target ? props.targetColor : "currentColor")
                .attr("stroke-width", 3)
                .attr("fill", "white")

            ng.append("image")
                .attr("x", -props.radius)
                .attr("y", -props.radius*0.5)
                .attr("width", props.radius*2)
                .attr("height", props.radius)
                .attr("href", d => d[props.imageAttr])

        } else {
            ng.append("circle")
                .classed("outline", true)
                .attr("r", props.radius)
                .attr("fill", props.colorAttr ? d[props.colorAttr] : props.fillColor)
                .attr("stroke", d => d.id === props.target ? props.targetColor : "currentColor")
        }

        x = d3.scaleLinear()
            .domain([0, props.width])
            .range([0, props.width])

        y = d3.scaleLinear()
            .domain([0, props.height])
            .range([0, props.height])

        let maxWeight = 1
        if (props.weightAttr) {
            maxWeight = d3.max(links, d => d[props.weightAttr])
        }

        function distanceFunction(d) {
            return props.weightAttr ?
                (1 + ((maxWeight - d[props.weightAttr]) / maxWeight)) * props.radius * 0.5 :
                props.radius
        }

        simulation = d3.forceSimulation(nodes)
            .alphaMin(0.01)
            .force('link', d3.forceLink(links).id(d => d.id).distance(distanceFunction))
            .force('charge', d3.forceManyBody())
            .force('center', d3.forceCenter(props.width / 2, props.height / 2))
            .on('tick', () => updateNodesAndLinks())
            .on("end", () => focus(props.target))

        svg.call(zoom)
    }

    defineExpose({ resetZoom, focus })

    onMounted(draw)
    onBeforeUnmount(() => {
        if (simulation) {
            simulation.stop()
            simulation = null
        }
    })

    watch(() => props.target, focus)
    watch(() => ([
        props.nodes,
        props.links,
        props.width,
        props.height,
        props.radius,
        props.weightAttr,
        props.imageAttr
    ]), draw, { deep: true })
</script>

<style scoped>
svg {
  background: #fafafa;
  border: 1px solid #eee;
}
text {
  pointer-events: none;
}
</style>