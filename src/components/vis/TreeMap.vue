<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>

    import DM from '@/use/data-manager';
    import { uid } from '@/use/utility';
    import * as d3 from 'd3';
    import { onMounted, ref, watch } from 'vue';

    const el = ref(null);

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        width: {
            type: Number,
            default: 800
        },
        height: {
            type: Number,
            default: 600
        },
        nameAttr: {
            type: String,
            default: "name"
        },
        fontSize: {
            type: Number,
            default: 12
        },
        selected: {
            type: Array,
        },
        selectedSource: {
            type: String,
        }
    })
    const emit = defineEmits(["click"])

    let root, nodes, color;
    let selection = new Set();

    function stratify_rec(data, node, parent, id, parentId) {
        // find all nodes with the passed parent
        const matching = data.filter(d => d[parentId] === parent)
        if (matching.length > 0) {
            if (!node.children) {
                node.children = []
            }
            matching.forEach(d => {
                const newNode = Object.assign({}, d);
                node.children.push(newNode);
                stratify_rec(data, newNode, d[id], id, parentId)
            });
        }
        return node;
    }

    function stratify(data, id, parentId) {
        const node = { name: "root", children: [] }
        node[id] = -1;
        node[parentId] = null;
        const inData = data.find(d => d[id] === -1);
        if (inData) { Object.assign(node, inData) }
        stratify_rec(data, node, -1, id, parentId)
        return node
    }

    function makeTree(data) {
        const tree = stratify(data, "id", "parent")
        return d3.treemap()
            .size([props.width, props.height])
            .paddingOuter(3)
            .paddingTop(19)
            .paddingInner(1)
            .round(true)(
                d3.hierarchy(tree)
                .count()
                .sort((a, b) => b.value - a.value))
    }

    function updateSelected() {
        if (props.selected) {
            selection = new Set(props.selected);
        } else if (props.selectedSource) {
            selection = new Set(DM.getSelectedIds(props.selectedSource))
        }
        highlight();
    }

    function draw() {
        const svg = d3.select(el.value);
        svg.selectAll("*").remove();

        root = makeTree(props.data);

        color = d3.scaleSequential([8, 0], d3.interpolateMagma);

        nodes = svg.selectAll("g")
            .data(d3.group(root, d => d.height))
            .join("g")
            .selectAll("g")
            .data(d => d[1])
            .join("g")
            .attr("font-size", props.fontSize)
            .attr("transform", d => `translate(${d.x0},${d.y0})`)
            .style("cursor", "pointer")
            .on("click", function(_, d) { emit("click", d.data) })

        nodes.append("title")
            .text(d => d.data.pathNames + "\n" + d.data.description);

        nodes.append("rect")
            .attr("id", d => (d.nodeUid = uid("node")).id)
            .attr("fill", d => color(d.height))
            .attr("width", d => d.x1 - d.x0)
            .attr("height", d => d.y1 - d.y0)
            .on("pointerenter", function() { d3.select(this).attr("stroke", "black") })
            .on("pointerleave", function() { d3.select(this).attr("stroke", "none") })

        nodes.append("clipPath")
            .attr("id", d => (d.clipUid = uid("clip")).id)
            .append("use")
            .attr("xlink:href", d => d.nodeUid.href);

        nodes.append("text")
            .classed("label", true)
            .filter(d => d.parent !== null)
            .attr("clip-path", d => d.clipUid)
            .text(d => d.data[props.nameAttr])
            // .selectAll("tspan")
            // .data(d => d.data[props.nameAttr].split(/(?=[A-Z][^A-Z])/g))
            // .join("tspan")
            // .attr("fill-opacity", (_, i, nodes) => i === nodes.length - 1 ? 0.7 : null)
            // .text(d => d);

        nodes.filter(d => d.children).selectAll(".label")
            .attr("dx", 3)
            .attr("y", 13);

        nodes.filter(d => !d.children).selectAll(".label")
            .attr("x", 3)
            .attr("y", (_, i, nodes) => `${(i === nodes.length - 1) * 0.3 + 1.1 + i * 0.9}em`);

        highlight();
    }

    function highlight() {
        if (selection.size > 0) {
            nodes.selectAll("rect").style("filter", d => selection.has(d.data.id) ? null : "grayscale(1)")
            nodes.selectAll(".label").attr("font-weight", d => selection.has(d.data.id) ? "bold" : null)
        } else {
            nodes.selectAll("rect").style("filter", null)
            nodes.selectAll(".label").attr("font-weight", null)
        }
    }1

    onMounted(function() {
        draw()
        updateSelected();
    })

    watch(() => props.selected, updateSelected, { deep: true })
    watch(() => props.selectedSource, updateSelected)
    watch(() => ([props.width, props.height]), draw, { deep : true })
</script>
