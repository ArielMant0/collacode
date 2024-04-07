<template>
    <svg ref="el" :width="width" :height="height">
        <g ref="treeG"></g>
        <g ref="assigG"></g>
    </svg>
</template>

<script setup>

    import * as d3 from 'd3';
    import { useApp } from '@/store/app';
    import { ref, watch, onMounted } from 'vue';
    import DM from '@/use/data-manager';

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        assignment: {
            type: Object,
            default: () => ({})
        },
        assignAttr: {
            type: String,
            default: "assigned"
        },
        width: {
            type: Number,
            default: 500
        },
        primary: {
            type: String,
            default: "#078766"
        },
        secondary: {
            type: String,
            default: "#0ad39f"
        },
        showAssigned: {
            type: Boolean,
            default: false
        }
    })
    const emit = defineEmits(["click", "drag", "click-assign"])

    const height = ref(100)
    const el = ref(null)
    const treeG = ref(null)
    const assigG = ref(null)
    const app = useApp();

    function buildTagTree(data) {
        return d3.stratify()
            .id(d => d.id)
            .parentId(d => d.parent)
            (data)
    }

    let nodes, aNodes, root, aRoot, line;

    function draw() {
        const svg = d3.select(treeG.value);
        svg.selectAll("*").remove();

        root = buildTagTree(props.data);

        // Compute the layout.
        const dx = 15, padding = 4;
        const dy = props.width / (root.height + padding);
        d3.tree().nodeSize([dx, dy])(root);

        // Center the tree.
        let x0 = Infinity;
        let x1 = -x0;
        root.each(d => {
            if (d.x > x1) x1 = d.x;
            if (d.x < x0) x0 = d.x;
        });

        // Compute the default height.
        height.value = x1 - x0 + dx * 2;

        d3.select(el.value)
            .attr("viewBox", [padding - 25 - root.data.name.length*2, x0 - dx, props.width, height.value])
            .attr("style", "max-width: 100%; height: auto; height: intrinsic;")
            .attr("font-family", "sans-serif")
            .attr("font-size", 10);

        line = d3.link(d3.curveBumpX)
            .x(d => d.y)
            .y(d => d.x)

        svg.append("g")
            .attr("fill", "none")
            .attr("stroke", "black")
            .attr("opacity", 0.5)
            .selectAll("path")
            .data(root.links())
            .join("path")
                .attr("d", line);

        nodes = svg.append("g")
            .selectAll("g")
            .data(root.descendants())
            .join("g")
            .attr("transform", d => `translate(${d.y},${d.x})`)

        nodes.append("circle")
            .attr("fill", d => {
                if (d.data.delete) return "darkred"
                return d.children ? props.secondary : props.primary
            })
            .attr("stroke", d => d.data[props.assignAttr] && d.data[props.assignAttr].length > 0 ? "red" : "none")
            .attr("r", 4)

        nodes.append("title").text(d => d.data.description);

        nodes.append("text")
            .attr("dy", "0.32em")
            .attr("x", d => d.children ? -8 : 8)
            .attr("paint-order", "stroke")
            .attr("stroke", "white")
            .attr("stroke-width", 3)
            .attr("text-anchor", d => d.children ? "end" : "start")
            .attr("fill", d => d.data.delete ? "grey" : "black")
            .style("cursor", "pointer")
            .text(d => d.data.name)
            .on("click", (e, d) => {
                if (e.defaultPrevented) return; // dragged
                emit("click", d.data, e)
            })
            .on("pointerenter", function() {
                d3.select(this).attr("font-weight", "bold")
            })
            .on("pointerleave", function() {
                d3.select(this).attr("font-weight", null)
            })

        drawAssigned();

        highlight()
    }

    function highlight() {
        const sels = new Set(DM.getFilter("tags", "id"))
        nodes.classed("selected", d => sels.has(d.data.id))
            .selectAll("circle")
            .attr("r", d => sels.has(d.data.id) ? 6 : 4)

        if (props.showAssigned && aNodes) {
            const otherSels = new Set(DM.getFilter("tags_old", "id"))
            aNodes.selectAll("text")
                .attr("fill", d => otherSels.has(d.id) ? "black": "red")
                .attr("font-weight", d => otherSels.has(d.id) ? "bold": null)
        }
    }

    function drawAssigned() {
        const svg = d3.select(assigG.value);
        svg.selectAll("*").remove();

        if (props.showAssigned) {



            const aData = Object.keys(props.assignment).map(d => {
                const others = props.data.filter(dd => dd[props.assignAttr] && dd[props.assignAttr].includes(+d))
                return {
                    id: +d,
                    name: props.assignment[d].name,
                    x: 0,
                    y: root.y + 25,
                    others : others.map(dd => dd.id)
                }
            });
            aData.sort((a, b) => {
                const nameA = a.name.toLowerCase(); // ignore upper and lowercase
                const nameB = b.name.toLowerCase(); // ignore upper and lowercase
                if (nameA < nameB) { return -1; }
                if (nameA > nameB) { return 1; }
                // names must be equal
                return 0;
            });

            const yScale = d3.scalePoint()
                .domain(aData.map(d => d.id))
                .range([-height.value*0.5+10, height.value*0.5-10])

            aData.forEach(d => d.x = yScale(d.id))

            svg.append("g")
                .selectAll("g")
                .data(aData.filter(d => d.others.length > 0))
                .join("g")
                .attr("fill", "none")
                .attr("stroke", "red")
                .attr("stroke-width", 1)
                .selectAll("path")
                .data(d => d.others.map(dd => {
                    const o = root.find(node => node.data.id === dd);
                    return { source: { x: d.x, y: d.y }, target: { x: o.x, y: o.y-5 } }
                }))
                .join("path")
                .attr("d", line)

            aNodes = svg.append("g")
                .selectAll("g")
                .data(aData)
                .join("g")
                .attr("transform", d => `translate(${d.y},${d.x})`)
                .style("cursor", "default")

            aNodes.append("circle")
                .attr("fill", "red")
                .attr("r", 4)


            aNodes.append("text")
                .text(d => d.name)
                .attr("dy", "0.32em")
                .attr("x", 8)
                .attr("paint-order", "stroke")
                .attr("stroke", "white")
                .attr("stroke-width", 3)
                .attr("text-anchor", "start")
                .attr("fill", "red")
                .style("cursor", "pointer")
                .on("pointerenter", function() {
                    d3.select(this).attr("font-weight", "bold")
                })
                .on("pointerleave", function(_, d) {
                    const sels = new Set(DM.getFilter("tags_old", "id"))
                    if (!sels.has(d.id)) {
                        d3.select(this).attr("font-weight", null)
                    }
                })
                .on("click", function(e, d) {
                    if (e.defaultPrevented) return; // dragged
                    emit("click-assign", d, e)
                })
        }
    }

    onMounted(draw);

    watch(props, draw, { deep: true })
    watch(() => app.selectionTime, highlight)
</script>

<style>
g.selected text {
    font-weight: bold;
}
</style>