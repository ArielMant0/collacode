<template>
    <svg :width="width" :height="height">
        <mask id='mask' patternUnits='userSpaceOnUse' width='50' height='50'>
            <rect x='0' y='0' width='100%' height='100%' fill='white'/>
            <path d='M14.498 16.858L0 8.488.002-8.257l14.5-8.374L29-8.26l-.002 16.745zm0 50.06L0 58.548l.002-16.745 14.5-8.373L29 41.8l-.002 16.744zM28.996 41.8l-14.498-8.37.002-16.744L29 8.312l14.498 8.37-.002 16.745zm-29 0l-14.498-8.37.002-16.744L0 8.312l14.498 8.37-.002 16.745z'  stroke-width='1' stroke='black' fill='none'/>
        </mask>
        <g ref="el"></g>
    </svg>
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
        highlightAttr: {
            type: String,
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
            .tile(d3.treemapBinary)
            .size([props.width, props.height])
            .paddingOuter(10)
            .paddingTop(props.fontSize + 10)
            .paddingInner(2)
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

        color = d3.scaleSequential([10, 0], d3.interpolateMagma);

        nodes = svg.selectAll("g")
            .data(d3.group(root, d => d.depth))
            .join("g")
            .selectAll("g")
            .data(d => d[1])
            .join("g")
            .style("font-size", props.fontSize)
            .attr("transform", d => `translate(${d.x0},${d.y0})`)

        nodes.filter(d => d.parent !== null)
            .style("cursor", d => !d.data.valid || d.data.is_leaf === 1 ? "pointer" : "default")
            .on("click", function(_, d) { emit("click", d.data) })
            .on("pointerenter", function() {
                d3.select(this).select("rect").attr("fill", "#0ad39f")
            })
            .on("pointerleave", function(_, d) {
                d3.select(this).select("rect").attr("fill", color(d.height))
            })

        nodes.filter(d => d.data.parent !== null)
            .append("title")
            .text(d => d.data.pathNames + "\n\n" + d.data.description);

        nodes.append("rect")
            .attr("id", d => (d.nodeUid = uid("node")).id)
            .attr("fill", d => color(d.height))
            .attr("mask", d => {
                if (!props.highlightAttr || !d.data[props.highlightAttr]) {
                    return null;
                }
                return d.data[props.highlightAttr] !== "default" ? "url(#mask)" : null
            })
            .attr("stroke", d => d.data.valid ? "none" : "#078766")
            .attr("width", d => d.x1 - d.x0)
            .attr("height", d => d.y1 - d.y0)

        nodes.append("clipPath")
            .attr("id", d => (d.clipUid = uid("clip")).id)
            .append("use")
            .attr("xlink:href", d => d.nodeUid.href);

        nodes.filter(d => d.parent !== null)
            .append("text")
            .classed("label", true)
            .attr("clip-path", d => d.clipUid)
            .selectAll("tspan")
            .data(d => d.data[props.nameAttr].split(" "))
            .join("tspan")
                .text(d => d)
        nodes
            .filter(d => d.parent !== null && d.children)
            .selectAll(".label tspan")
            .attr("dx", 5)
            .attr("y", 15);

        nodes
            .filter(d => d.parent !== null && !d.children)
            .selectAll(".label tspan")
            .attr("x", 5)
            .attr("y", (_, i, nodes) => `${(i === nodes.length - 1) * 0.3 + 1.1 + i * 0.9}em`);

        highlight();
    }

    function highlight() {
        if (selection.size > 0) {
            nodes.selectAll("rect")
                .style("filter", d => selection.has(d.data.id) ? null : "grayscale(0.75)")
            nodes.selectAll(".label")
                .attr("fill", d => d.height > 3 && !selection.has(d.data.id) ? "white" : null)
                .attr("font-weight", d => selection.has(d.data.id) ? "bold" : null)
        } else {
            nodes.selectAll("rect").style("filter", "grayscale(0.5)")
            nodes.selectAll(".label")
                .attr("font-weight", null)
                .attr("fill", d => d.height > 3 ? "lightgrey" : "black")
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

