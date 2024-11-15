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

    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import DM from '@/use/data-manager';
    import { uid } from '@/use/utility';
    import * as d3 from 'd3';
    import { storeToRefs } from 'pinia';
    import { onMounted, ref, watch } from 'vue';

    const el = ref(null);
    const app = useApp();

    const settings = useSettings();
    const { treeHidden } = storeToRefs(settings)

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        time: {
            type: Number,
            default: 0
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
        titleAttr: {
            type: String,
            default: "pathNames"
        },
        dotAttr: {
            type: String,
        },
        hideHeaders: {
            type: Boolean,
            default: false
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
        frozen: {
            type: Array,
        },
        selectedSource: {
            type: String,
        },
        colorMap: {
            type: String,
            default: "interpolateMagma"
        },
        collapsible: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["click", "right-click", "hover-dot", "click-dot", "right-click-dot"])

    let hierarchy, root, nodes, color;
    let selection = new Set();
    let frozenIds = new Set();

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

    function makeTree() {
        return d3.treemap()
            .tile(d3.treemapBinary)
            .size([props.width, props.height])
            .paddingOuter(props.hideHeaders ? 5 : 10)
            .paddingTop(props.hideHeaders ? 5 : props.fontSize + 10)
            .paddingInner(3)
            .round(true)(hierarchy
                .count()
                .sort((a, b) => b.value - a.value)
            )
    }

    function draw() {
        d3.select(el.value)
            .selectAll("*")
            .remove();

        hierarchy = d3.hierarchy(stratify(props.data, "id", "parent"))
        hierarchy.each(d => {
            if (d.children) {
                d._children = d.children
                if (treeHidden.value.has(d.data.id)) {
                    d.children = null;
                }
                d.data.collapsed = d.children !== null;
            }
        });
        color = d3.scaleSequential([10, 0], d3[props.colorMap]);

        update();
    }

    function update(source=null) {
        root = makeTree()

        const animate = props.collapsible && source && source.data.id === root.data.id;

        if (animate) {

            const transition = d3.select(el.value)
                .transition()
                .duration(1000)

            const nodeG = d3.select(el.value)
                .selectAll("g")
                .data(d3.group(root, d => d.depth), d => d[0])

            const enterNodes = nodeG.enter()
                .append("g")
                .selectAll("g")
                .data(d => d[1], d => d.data.id)
                .join("g")
                .style("font-size", props.fontSize)
                .attr("transform", `translate(${source.x0},${source.y0})`)

            enterNodes
                .filter(d => d.parent !== null)
                .classed("cursor-pointer", d => d.data.is_leaf === 1)
                .on("click", function(_, d) { emit("click", d.data) })
                .on("contextmenu", function(event, d) {
                    event.preventDefault();
                    if (!event.target.classList.contains("dot")) {
                        emit("right-click", d.data, event)
                    }
                })
                .on("pointerenter", function(event, d) {
                    if (!event.target.classList.contains("dot")) {
                        d3.select(this)
                            .select("rect")
                            .attr("fill", "#0ad39f")
                    }
                })
                .on("pointerleave", function(event, d) {
                    if (!event.target.classList.contains("dot")) {
                        d3.select(this)
                            .select("rect")
                            .attr("fill", frozenIds.size > 0 && frozenIds.has(d.data.id) ? "#ccc": color(d.height))
                    }
                })
                .append("title")
                .text(d =>  d.data[props.titleAttr] + "\n\n" + d.data.description);

            enterNodes
                .append("rect")
                .attr("id", d => (d.nodeUid = uid("node")).id)
                .attr("fill", d => color(d.height))
                .attr("mask", d => {
                    if (!props.highlightAttr || !d.data[props.highlightAttr]) {
                        return null;
                    }
                    return d.data[props.highlightAttr] !== "default" ? "url(#mask)" : null
                })
                .attr("stroke", d => d.data.valid === undefined || d.data.valid ? "none" : "#078766")
                .attr("width", d => d.x1 - d.x0)
                .attr("height", d => d.y1 - d.y0)

            enterNodes
                .append("clipPath")
                .attr("id", d => (d.clipUid = uid("clip")).id)
                .append("use")
                .attr("xlink:href", d => d.nodeUid.href);

            enterNodes
                .filter(d => props.hideHeaders ? !d.children : d.parent !== null)
                .append("text")
                .classed("label", true)
                .attr("clip-path", d => d.clipUid)
                .attr("transform", d => `translate(${d.data.collapsed ? 10 : 0},0)`)
                .selectAll("tspan")
                .data(d => d.data[props.nameAttr].split(" "))
                .join("tspan")
                    .text(d => d)

            enterNodes
                .filter(d => d.parent !== null && d.children)
                .selectAll(".label tspan")
                .attr("dx", 5)
                .attr("y", 15);

            enterNodes
                .filter(d => d.parent !== null && !d.children)
                .selectAll(".label tspan")
                .attr("x", 5)
                .attr("y", (_, i, nodes) => `${(i === nodes.length - 1) * 0.3 + 1.1 + i * 0.9}em`);

            if (props.dotAttr) {
                enterNodes
                    .filter(d => d.parent !== null && !d.children && !d.data._children)
                    .selectAll(".dot")
                    .data(d => {
                        const w = d.x1 - d.x0;
                        const h = d.y1 - d.y0;
                        const v = w < h;
                        const numRow = Math.floor(Math.max(8, (w - 10)) / 8);
                        const numCol = Math.floor(Math.max(8, (h - 10)) / 8);
                        return d.data[props.dotAttr].map((dd, i) => {
                            return {
                                data: dd,
                                x: v ? w - 8 - Math.floor(i / numCol) : w - 8 * (1 + i % numRow),
                                y: v ? h - 8 * (1 + i % numCol) : h - 8 - Math.floor(i / numRow)
                            }
                        }
                    )})
                    .join("circle")
                    .classed("dot", true)
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y)
                    .attr("r", 3)
                    .attr("stroke", "black")
                    .attr("fill", d => app.getUserColor(d.data.created_by))
                    .on("pointerenter", (event, d) => emit("hover-dot", d.data, event))
                    .on("pointerleave", () => emit("hover-dot", null))
                    .on("click", (event, d) => emit("click-dot", d.data, event))
                    .on("contextmenu", (event, d) => {
                        event.preventDefault();
                        event.stopPropagation();
                        emit("right-click-dot", d.data, event)
                    })
            }

            if (props.collapsible) {
                enterNodes
                    .filter(d => d.parent !== null && d.data._children)
                    .append("circle")
                    .attr("cx", 7)
                    .attr("cy", 7)
                    .attr("r", 4)
                    .style("cursor", "pointer")
                    .attr("fill", "black")
                    .classed("node-effect", true)
                    .on("click", function(event, d) {
                        event.stopPropagation();
                        const node = hierarchy.find(node => node.data.id === d.data.id)
                        if (node) {
                            node.children = node.children ? null : node._children;
                            node.data.collapsed = node.children !== null;
                            settings.toggleTreeHidden(node.data.id);
                            update(d)
                        }
                    })
            }

            nodes = nodeG.merge(enterNodes)

            nodes
                .selectAll("g")
                .transition(transition)
                .attr("transform", d => `translate(${d.x0},${d.y0})`)
                .selectAll(".label")
                .attr("transform", d => `translate(${d.data.collapsed ? 10 : 0},0)`)

            nodeG.exit().transition(transition).remove()

        } else {

            nodes = d3.select(el.value)
                .selectAll("g")
                .data(d3.group(root, d => d.depth), d => d[0])
                .join("g")
                .selectAll("g")
                .data(d => d[1])
                .join("g")
                .style("font-size", props.fontSize)
                .attr("transform", d => `translate(${d.x0},${d.y0})`)

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
                .append("title")
                .text(d => d.data[props.titleAttr] + "\n\n" + d.data.description);

            nodes.filter(d => d.parent !== null)
                .classed("cursor-pointer", d => d.data.is_leaf === 1)
                .on("click", function(_, d) { emit("click", d.data) })
                .on("contextmenu", function(event, d) {
                    event.preventDefault();
                    if (!event.target.classList.contains("dot")) {
                        emit("right-click", d.data, event)
                    }
                })
                .on("pointerenter", function(event, d) {
                    if (!event.target.classList.contains("dot")) {
                        d3.select(this)
                            .select("rect")
                            .attr("fill", "#0ad39f")
                    }
                })
                .on("pointerleave", function(event, d) {
                    if (!event.target.classList.contains("dot")) {
                        d3.select(this)
                            .select("rect")
                            .attr("fill", frozenIds.size > 0 && frozenIds.has(d.data.id) ? "#ccc": color(d.height))
                    }
                })

            nodes.append("clipPath")
                .attr("id", d => (d.clipUid = uid("clip")).id)
                .append("use")
                .attr("xlink:href", d => d.nodeUid.href);

            nodes.filter(d => props.hideHeaders ? !d.children : d.parent !== null)
                .append("text")
                .classed("label", true)
                .attr("clip-path", d => d.clipUid)
                .attr("transform", d => `translate(${d.data.collapsed ? 10 : 0},0)`)
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

            if (props.dotAttr) {
                nodes
                    .filter(d => d.parent !== null && !d.children && !d.data._children)
                    .selectAll(".dot")
                    .data(d => {
                        const w = d.x1 - d.x0;
                        const h = d.y1 - d.y0;
                        const v = w < h;
                        const numRow = Math.floor(Math.max(8, (w - 10)) / 8);
                        const numCol = Math.floor(Math.max(8, (h - 10)) / 8);
                        return d.data[props.dotAttr].map((dd, i) => {
                            return {
                                data: dd,
                                x: v ? w - 8 - Math.floor(i / numCol) : w - 8 * (1 + i % numRow),
                                y: v ? h - 8 * (1 + i % numCol) : h - 8 - Math.floor(i / numRow)
                            }
                        }
                    )})
                    .join("circle")
                    .classed("dot", true)
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y)
                    .attr("r", 3)
                    .attr("stroke", "black")
                    .attr("fill", d => app.getUserColor(d.data.created_by))
                    .on("pointerenter", (event, d) => emit("hover-dot", d.data, event))
                    .on("pointerleave", () => emit("hover-dot", null))
                    .on("contextmenu", (event, d) => {
                        event.preventDefault();
                        event.stopPropagation();
                        emit("right-click-dot", d.data, event)
                    })
            }

            if (props.collapsible) {
                nodes
                    .filter(d => d.parent !== null && d._children)
                    .append("circle")
                    .attr("cx", 7)
                    .attr("cy", 7)
                    .attr("r", 4)
                    .style("cursor", "pointer")
                    .attr("fill", "black")
                    .classed("node-effect", true)
                    .on("click", function(event, d) {
                        event.stopPropagation();
                        const node = hierarchy.find(node => node.data.id === d.data.id)
                        if (node) {
                            node.children = node.children ? null : node._children;
                            node.data.collapsed = node.children !== null;
                            settings.toggleTreeHidden(node.data.id);
                            update(d)
                        }
                    })
            }
        }
        highlight(source===null);
    }

    function highlight(read=false) {
        if (read) {
            if (props.selected) {
                selection = new Set(props.selected);
            } else if (props.selectedSource) {
                selection = new Set(DM.getSelectedIds(props.selectedSource))
            }

            if (props.frozen) {
                frozenIds = new Set(props.frozen)
            } else {
                frozenIds.clear()
            }
        }

        if (selection.size > 0) {
            nodes.selectAll("rect")
                .style("filter", d => selection.has(d.data.id) ? null : "grayscale(0.75)")
                .attr("fill", d => frozenIds.size > 0 && frozenIds.has(d.data.id) ? "#ccc": color(d.height))
            nodes.selectAll(".label")
                .attr("fill", d => d.height > 3 && !selection.has(d.data.id) ? "white" : null)
                .attr("font-weight", d => selection.has(d.data.id) ? "bold" : null)
        } else {
            nodes.selectAll("rect")
                .style("filter", "grayscale(0.5)")
                .attr("fill", d => frozenIds.size > 0 && frozenIds.has(d.data.id) ? "#ccc": color(d.height))
            nodes.selectAll(".label")
                .attr("font-weight", null)
                .attr("fill", d => d.height > 3 ? "lightgrey" : "black")
        }
    }

    onMounted(draw)

    watch(() => props.frozen, highlight.bind(null, true), { deep: true })
    watch(() => props.selected, highlight.bind(null, true), { deep: true })
    watch(() => props.selectedSource, highlight.bind(null, true))
    watch(() => ([props.time, props.width, props.height]), draw, { deep : true })
</script>

<style>
.node-effect:hover {
    filter: drop-shadow(0 0 4px black)
}
.thick:hover {
    font-weight: bold;
}
</style>