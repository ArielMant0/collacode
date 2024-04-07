<template>
    <svg ref="el" :width="width" :height="height">
        <g ref="treeLinks"></g>
        <g ref="assigLinks"></g>
        <g ref="treeNodes"></g>
        <g ref="assigNodes"></g>
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
        },
        fontSize: {
            type: Number,
            default: 12
        }
    })
    const emit = defineEmits(["click", "drag", "click-assign"])

    const height = ref(100)
    const el = ref(null)
    const treeLinks = ref(null)
    const treeNodes = ref(null)
    const assigLinks = ref(null)
    const assigNodes = ref(null)
    const app = useApp();

    function buildTagTree(data) {
        return d3.stratify()
            .id(d => d.id)
            .parentId(d => d.parent)
            (data)
    }

    let nodes, aNodes, root, line;

    function draw() {
        d3.select(treeLinks.value).selectAll("*").remove();
        d3.select(treeNodes.value).selectAll("*").remove();

        root = buildTagTree(props.data);

        // Compute the layout.
        const dx = props.fontSize + 5, padding = 4;
        const dy = props.width / (root.height + padding);
        d3.cluster().nodeSize([dx, dy])(root);

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
            .attr("font-size", props.fontSize);

        line = d3.link(d3.curveBumpX)
            .x(d => d.y)
            .y(d => d.x)

        d3.select(treeLinks.value).append("g")
            .attr("fill", "none")
            .attr("stroke", "black")
            .attr("opacity", 0.5)
            .selectAll("path")
            .data(root.links())
            .join("path")
                .attr("d", line);

        nodes = d3.select(treeNodes.value).append("g")
            .selectAll("g")
            .data(root.descendants())
            .join("g")
            .attr("transform", d => `translate(${d.y},${d.x})`)

        nodes.append("circle")
            .attr("fill", d => d.children ? "black" : "white")
            .attr("stroke", d => d.data[props.assignAttr] && d.data[props.assignAttr].length > 0 ? props.secondary : "none")
            .attr("stroke-width", 2)
            .attr("r", 4)

        nodes.append("title").text(d => d.data.description);

        nodes.append("text")
            .attr("dy", "0.32em")
            .attr("x", d => d.children ? -8 : 8)
            .attr("paint-order", "stroke")
            .attr("stroke", "white")
            .attr("stroke-width", 3)
            .attr("text-anchor", d => d.children ? "end" : "start")
            .attr("fill", d => d.data.valid ? "black" : "red")
            .style("cursor", "pointer")
            .text(d => (d.data.valid ? "" : "! ") + d.data.name)
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
                .attr("fill", d => otherSels.has(d.id) ? "black": "#078766")
                .attr("font-weight", d => otherSels.has(d.id) ? "bold": null)
        }
    }

    function drawAssigned() {
        d3.select(assigLinks.value).selectAll("*").remove();
        d3.select(assigNodes.value).selectAll("*").remove();

        if (props.showAssigned) {

            let emptyIndex = 0;

            const aData = Object.keys(props.assignment).map(d => {
                const others = props.data.filter(dd => dd[props.assignAttr] && dd[props.assignAttr].includes(+d))
                const inTree = others.map(o => root.find(dd => dd.data.id === o.id))
                return {
                    id: +d,
                    name: props.assignment[d].name,
                    x: inTree.length > 0 ? d3.mean(inTree, dd => dd.x) : (emptyIndex++) * 25 - height.value*0.5,
                    y: others.length > 0 && others.every(o => o.is_leaf === 1) ? props.width - 150 : root.y + 25,
                    others : others.map(dd => dd.id)
                }
            });

            d3.select(assigLinks.value).append("g")
                .selectAll("g")
                .data(aData.filter(d => d.others.length > 0))
                .join("g")
                .attr("fill", "none")
                .attr("stroke", props.primary)
                .attr("stroke-width", 1)
                .selectAll("path")
                .data(d => d.others.map(dd => {
                    const o = root.find(node => node.data.id === dd);
                    return { source: { x: d.x, y: d.y }, target: { x: o.x, y: o.y-5 } }
                }))
                .join("path")
                .attr("d", line)

            aNodes = d3.select(assigNodes.value).append("g")
                .selectAll("g")
                .data(aData)
                .join("g")
                .attr("transform", d => `translate(${d.y},${d.x})`)
                .style("cursor", "default")

            aNodes.append("circle")
                .attr("fill", props.primary)
                .attr("r", 4)


            aNodes.append("text")
                .text(d => d.name)
                .attr("dy", "0.32em")
                .attr("x", 8)
                .attr("paint-order", "stroke")
                .attr("stroke", "white")
                .attr("stroke-width", 3)
                .attr("text-anchor", "start")
                .attr("fill", props.primary)
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