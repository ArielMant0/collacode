<template>
    <svg :width="width" :height="height" :view-box="[0, 0, width, height]">
        <mask id='mask' patternUnits='userSpaceOnUse' width='50' height='50'>
            <rect x='0' y='0' width='100%' height='100%' fill='white'/>
            <path d='M14.498 16.858L0 8.488.002-8.257l14.5-8.374L29-8.26l-.002 16.745zm0 50.06L0 58.548l.002-16.745 14.5-8.373L29 41.8l-.002 16.744zM28.996 41.8l-14.498-8.37.002-16.744L29 8.312l14.498 8.37-.002 16.745zm-29 0l-14.498-8.37.002-16.744L0 8.312l14.498 8.37-.002 16.745z'  stroke-width='1' stroke='black' fill='none'/>
        </mask>
        <g ref="el" :transform="transform"></g>
    </svg>
</template>

<script setup>

    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { useTooltip } from '@/store/tooltip';
    import DM from '@/use/data-manager';
    import { uid } from '@/use/utility';
    import * as d3 from 'd3';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useDisplay } from 'vuetify';

    const el = ref(null);
    const app = useApp();
    const tt = useTooltip()

    const settings = useSettings();
    const { treeHidden } = storeToRefs(settings)
    const { mobile } = useDisplay()

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
        colorAttr: {
            type: String,
        },
        dotAttr: {
            type: String,
        },
        iconAttr: {
            type: String,
        },
        iconSize: {
            type: Number,
            default: 30
        },
        iconScale: {
            type: Number,
            default: 1
        },
        hideHeaders: {
            type: Boolean,
            default: false
        },
        highlightAttr: {
            type: String,
        },
        validAttr: {
            type: String,
        },
        baseFontSize: {
            type: Number,
            default: 14
        },
        colorPrimary: {
            type: String,
            default: "#0ad39f"
        },
        colorSecondary: {
            type: String,
            default: "#078766"
        },
        colorInvalid: {
            type: String,
            default: "red"
        },
        selected: {
            type: Array,
        },
        frozen: {
            type: Array,
        },
        frozenColor: {
            type: String,
            default: "#ccc"
        },
        hidden: {
            type: [Array, Set],
        },
        hiddenOpacity: {
            type: Number,
            default: 0.15
        },
        selectedSource: {
            type: String,
        },
        colorMap: {
            type: [String, Array, Function],
            default: () => (d3obj, h, light) => {
                const n = Math.max(3,Math.min(9,h))
                const r = d3obj.range(1, n+1)
                return r.map(d3obj.scaleSequential([light ? "#ffffff" : "#000000", "#078766"]).domain([0, n]))
            }
        },
        collapsible: {
            type: Boolean,
            default: false
        },
        flash: {
            type: Boolean,
            default: false
        },
        hideColorFilter: {
            type: Boolean,
            default: false
        },
        hideTooltip: {
            type: Boolean,
            default: false
        },
        selectable: {
            type: Boolean,
            default: true
        },
    })
    const emit = defineEmits(["click", "hover", "right-click", "hover-dot", "click-dot", "right-click-dot"])

    const { smAndDown, mdAndDown } = useDisplay()

    let hierarchy, root, nodes, color;
    let selection = new Set();
    let frozenIds = new Set();

    const scale = computed(() => smAndDown.value ? 4 : mdAndDown.value ? 2 : 1)
    const transform = computed(() => scale.value !== 1 ? `scale(${1/scale.value})` : "")

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
            .size([props.width*scale.value, props.height*scale.value])
            .paddingOuter(props.hideHeaders ? 5 : 10)
            .paddingTop(props.hideHeaders ? 5 : props.baseFontSize+5)
            .paddingInner(3)
            .round(true)(hierarchy
                .count()
                .sort((a, b) => b.value - a.value)
            )
    }

    function getFontSize(d, isLeaf=false) {
        const minSize = Math.min(d.y1 - d.y0, d.x1 - d.x0)
        const add = isLeaf && scale.value !== 1 ? scale.value*3 : 0
        if (minSize < 100) {
            return add + Math.max(8, props.baseFontSize - 4)
        } else if (minSize < 150) {
            return add + Math.max(10, props.baseFontSize - 2)
        } else {
            return add + props.baseFontSize
        }
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

        update();
    }

    function getFillColor(d) {
        return props.colorAttr !== undefined && d.data[props.colorAttr] ? d.data[props.colorAttr] : color(d.height)
    }

    function update(source=null) {
        root = makeTree()

        const colmap = typeof props.colorMap === "string" ?
            d3[props.colorMap] : (
                Array.isArray(props.colorMap) ?
                    props.colorMap :
                    props.colorMap(d3, root.height+1, settings.lightMode))

        color = d3.scaleOrdinal()
            .domain(d3.range(0, root.height+1))
            .unknown(settings.lightMode ? "white" : "black")
            .range(colmap);

        const animate = props.collapsible && source && source.data.id === root.data.id;

        const hiddenSet = props.hidden ?
            (Array.isArray(props.hidden) ? new Set(props.hidden) : props.hidden) :
            new Set()

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
                .style("font-size", props.baseFontSize)
                .style("opacity", d => isHidden(d.data, hiddenSet) ? props.hiddenOpacity : 1)
                .attr("transform", `translate(${source.x0},${source.y0})`)

            enterNodes
                .filter(d => d.parent !== null)
                .classed("cursor-pointer", true)
                .on("click", function(event, d) {
                    if (!props.selectable) return
                    if (!event.target.classList.contains("dot")) {
                        emit("click", d.data)
                    }
                })
                .on("contextmenu", function(event, d) {
                    event.preventDefault();
                    if (!props.selectable) return
                    if (!event.target.classList.contains("dot")) {
                        emit("right-click", d.data, event)
                    }
                })
                .on("pointerenter", function(event, d) {
                    if (!props.selectable) return
                    if (!event.target.classList.contains("dot")) {
                        d3.select(this)
                            .select(".tree-node")
                            .attr("fill", selection.has(d.data.id) ? props.colorSecondary : props.colorPrimary)

                        if (!props.hideTooltip && !mobile.value) {
                            const desc = d.data.description ? d.data.description : DM.getDataItem("tags_desc", d.data.id)
                            const [mx, my] = d3.pointer(event, document.body)
                            tt.showAfterDelay(`${d.data[props.nameAttr]}</br><div class="text-caption mb-1">${d.data[props.titleAttr]}</div>${desc}`, mx, my)
                        }
                    }
                })
                .on("pointermove", function(event, d) {
                    if (!props.hideTooltip && !mobile.value) {
                        const desc = d.data.description ? d.data.description : DM.getDataItem("tags_desc", d.data.id)
                        const [mx, my] = d3.pointer(event, document.body)
                        tt.showAfterDelay(`${d.data[props.nameAttr]}</br><div class="text-caption mb-1">${d.data[props.titleAttr]}</div>${desc}`, mx, my)
                    }
                })
                .on("pointerleave", function(event, d) {
                    if (!props.selectable) return
                    if (!event.target.classList.contains("dot")) {
                        d3.select(this)
                            .select(".tree-node")
                            .attr("fill", frozenIds.size > 0 && frozenIds.has(d.data.id) ?
                                props.frozenColor:
                                (selection.has(d.data.id) ? props.colorPrimary : getFillColor(d))
                            )

                        if (!props.hideTooltip && !mobile.value) {
                            tt.hide()
                        }
                    }
                })

            enterNodes
                .append("rect")
                .classed("tree-node", true)
                .attr("id", d => (d.nodeUid = uid("node")).id)
                .attr("fill", d => getFillColor(d))
                .attr("mask", d => {
                    if (!props.highlightAttr || !d.data[props.highlightAttr]) {
                        return null;
                    }
                    return d.data[props.highlightAttr] !== "default" ? "url(#mask)" : null
                })
                .attr("stroke", d => {
                    if (d.data.id === -1) {
                        return "none"
                    }
                    return !props.validAttr || d.data[props.validAttr] ?
                        "none" :
                        (!props.validAttr &&  props.colorAttr ? "black" : props.colorInvalid)
                })
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
                .style("font-size", d => getFontSize(d, !d.children))
                .attr("clip-path", d => d.clipUid)
                .attr("transform", d => `translate(${d.data.collapsed ? 10 : 0})`)
                .attr("fill", d => {
                    const c = d3.hsl(getFillColor(d))
                    return c.l < 0.33 ? "#eee" : "black"
                })
                .selectAll("tspan")
                .data(d => d.data[props.nameAttr].split(" "))
                .join("tspan")
                    .classed("label-part", true)
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
                                parent: d.data,
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
                    .on("click", (event, d) => emit(
                        "click-dot",
                        d.data,
                        event,
                        d.parent[props.dotAttr].map(dd => dd.id),
                        d.parent[props.dotAttr].findIndex(dd => dd.id === d.data.id)
                    ))
                    .on("contextmenu", (event, d) => {
                        event.preventDefault();
                        event.stopPropagation();
                        emit("right-click-dot", d.data, event)
                    })
            } else if (props.iconAttr) {
                const size = props.iconScale * props.iconSize
                const off = size * 0.5

                const icons = enterNodes
                    .filter(d => d.parent !== null)
                    .selectAll(".icon")
                    .data(d => {
                        const w = d.x1 - d.x0;
                        const h = d.y1 - d.y0;
                        const v = w < h;
                        const numRow = Math.floor(Math.max(8, (w - 10)) / 8);
                        const numCol = Math.floor(Math.max(8, (h - 10)) / 8);
                        return d.data[props.iconAttr].map((dd, i) => {
                            return {
                                data: dd,
                                parent: d,
                                x: v ? w - 8 - Math.floor(i / numCol) : w - 8 * (1 + i % numRow),
                                y: v ? h - 8 * (1 + i % numCol) : h - 8 - Math.floor(i / numRow)
                            }
                        }
                    )})
                    .join("g")
                    .classed("icon", true)
                    .attr("transform", d => `translate(${d.x-off-2},${d.y-off-2})`)


                icons.append("rect")
                    .attr("width", size-4)
                    .attr("height", size-4)
                    .attr("fill", dd => getFillColor(dd.parent))

                icons.append("path")
                    .attr("d", d => d.data)
                    .attr("stroke", "none")
                    .attr("transform", `scale(${props.iconScale})`)
                    .attr("fill", dd => {
                        const c = d3.lch(getFillColor(dd.parent))
                        return c.l < 60 ? "#efefef" : "black"
                    })
            }

            if (props.collapsible) {
                enterNodes
                    .filter(d => d.parent !== null && d.data._children)
                    .append("circle")
                    .attr("cx", 7)
                    .attr("cy", Math.floor(props.baseFontSize*0.85))
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
                .style("font-size", props.baseFontSize)
                .style("opacity", d => isHidden(d.data, hiddenSet) ? props.hiddenOpacity : 1)
                .attr("transform", d => `translate(${d.x0},${d.y0})`)

            nodes.append("rect")
                .classed("tree-node", true)
                .attr("id", d => (d.nodeUid = uid("node")).id)
                .attr("fill", d => getFillColor(d))
                .attr("mask", d => {
                    if (!props.highlightAttr || !d.data[props.highlightAttr]) {
                        return null;
                    }
                    return d.data[props.highlightAttr] !== "default" ? "url(#mask)" : null
                })
                .attr("stroke", d => {
                    if (d.data.id === -1) {
                        return "none"
                    }
                    return !props.validAttr || d.data[props.validAttr] ?
                        "none" :
                        (!props.validAttr &&  props.colorAttr ? "black" : props.colorInvalid)
                })
                .attr("width", d => d.x1 - d.x0)
                .attr("height", d => d.y1 - d.y0)

            nodes.filter(d => d.parent !== null)
                .classed("cursor-pointer", true)
                .on("click", function(event, d) {
                    if (!props.selectable) return
                    if (!event.target.classList.contains("dot")) {
                        emit("click", d.data)
                    }
                })
                .on("contextmenu", function(event, d) {
                    event.preventDefault();
                    if (!props.selectable) return
                    if (!event.target.classList.contains("dot")) {
                        emit("right-click", d.data, event)
                    }
                })
                .on("pointerenter", function(event, d) {
                    if (!props.selectable) return
                    if (!event.target.classList.contains("dot")) {
                        d3.select(this)
                            .select(".tree-node")
                            .attr("fill", selection.has(d.data.id) ? props.colorSecondary : props.colorPrimary)

                        if (!props.hideTooltip && !mobile.value) {
                            const desc = d.data.description ? d.data.description : DM.getDataItem("tags_desc", d.data.id)
                            const [mx, my] = d3.pointer(event, document.body)
                            tt.showAfterDelay(`${d.data[props.nameAttr]}</br><div class="text-caption mb-1">${d.data[props.titleAttr]}</div>${desc}`, mx, my)
                        }
                    }
                })
                .on("pointermove", function(event, d) {
                    if (!props.hideTooltip && !mobile.value) {
                        const desc = d.data.description ? d.data.description : DM.getDataItem("tags_desc", d.data.id)
                        const [mx, my] = d3.pointer(event, document.body)
                        tt.showAfterDelay(`${d.data[props.nameAttr]}</br><div class="text-caption mb-1">${d.data[props.titleAttr]}</div>${desc}`, mx, my)
                    }
                })
                .on("pointerleave", function(event, d) {
                    if (!props.selectable) return
                    if (!event.target.classList.contains("dot")) {
                        d3.select(this)
                            .select(".tree-node")
                            .attr("fill", frozenIds.size > 0 && frozenIds.has(d.data.id) ?
                                props.frozenColor:
                                (selection.has(d.data.id) ? props.colorPrimary : getFillColor(d))
                            )

                        if (!props.hideTooltip && !mobile.value) {
                            tt.hide()
                        }
                    }
                })

            nodes.append("clipPath")
                .attr("id", d => (d.clipUid = uid("clip")).id)
                .append("use")
                .attr("xlink:href", d => d.nodeUid.href);

            nodes.filter(d => props.hideHeaders ? !d.children : d.parent !== null)
                .append("text")
                .classed("label", true)
                .style("font-size", d => getFontSize(d, !d.children))
                .attr("transform", d => `translate(${d.data.collapsed || d._children ? 10 : 0})`)
                .attr("fill", d => {
                    const c = d3.hsl(getFillColor(d))
                    return c.l < 0.33 ? "#eee" : "black"
                })
                .attr("clip-path", d => d.clipUid)
                .selectAll("tspan")
                .data(d => d.data[props.nameAttr].split(" "))
                .join("tspan")
                    .classed("label-part", true)
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
                                parent: d.data,
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
                    .on("click", (event, d) => emit(
                        "click-dot",
                        d.data,
                        event,
                        d.parent[props.dotAttr].map(dd => dd.id),
                        d.parent[props.dotAttr].findIndex(dd => dd.id === d.data.id)
                    ))
                    .on("contextmenu", (event, d) => {
                        event.preventDefault();
                        event.stopPropagation();
                        emit("right-click-dot", d.data, event)
                    })
            } else if (props.iconAttr) {
                const size = props.iconScale * props.iconSize
                const off = size * 0.5

                const icons = nodes
                    .filter(d => d.parent !== null)
                    .selectAll(".icon")
                    .data(d => {
                        const w = d.x1 - d.x0;
                        const h = d.y1 - d.y0;
                        const v = w < h;
                        const numRow = Math.floor(Math.max(8, (w - 10)) / 8);
                        const numCol = Math.floor(Math.max(8, (h - 10)) / 8);
                        return d.data[props.iconAttr].map((dd, i) => {
                            return {
                                data: dd,
                                parent: d,
                                x: v ? w - 8 - Math.floor(i / numCol) : w - 8 * (1 + i % numRow),
                                y: v ? h - 8 * (1 + i % numCol) : h - 8 - Math.floor(i / numRow)
                            }
                        }
                    )})
                    .join("g")
                    .classed("icon", true)
                    .attr("transform", d => `translate(${d.x-off-2},${d.y-off-2})`)

                    icons.append("rect")
                        .attr("width", size-4)
                        .attr("height", size-4)
                        .attr("fill", dd => getFillColor(dd.parent))

                    icons.append("path")
                        .attr("d", d => d.data)
                        .attr("stroke", "none")
                        .attr("transform", `scale(${props.iconScale})`)
                        .attr("fill", dd => {
                            const c = d3.lch(getFillColor(dd.parent))
                            return c.l < 60 ? "#efefef" : "black"
                        })
            }

            if (props.collapsible) {
                nodes
                    .filter(d => d.parent !== null && d._children)
                    .append("circle")
                    .attr("cx", 7)
                    .attr("cy", Math.floor(props.baseFontSize*0.85))
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

    function isHidden(d, idSet) {
        return idSet.has(d.id) || (d.path && d.path.some(id => idSet.has(id)))
    }

    function highlight(read=false) {

        let hiddenIds = new Set()

        if (read) {
            if (props.selected) {
                selection = new Set(props.selected);
            } else if (props.selectedSource) {
                selection = DM.getSelectedIds(props.selectedSource)
            }

            if (props.frozen) {
                frozenIds = new Set(props.frozen)
            } else {
                frozenIds.clear()
            }

            if (props.hidden) {
                hiddenIds = Array.isArray(props.hidden) ? new Set(props.hidden) : props.hidden
            }
        }

        nodes.style("opacity", d => isHidden(d.data, hiddenIds) ? props.hiddenOpacity : 1)

        if (selection.size > 0) {
            nodes.selectAll(".tree-node")
                .style("filter", d => props.hideColorFilter ? "saturate(1)" : (selection.has(d.data.id) ? "saturate(0.75)" : "saturate(0.33)"))
                .attr("fill", d => frozenIds.size > 0 && frozenIds.has(d.data.id) ? props.frozenColor : (selection.has(d.data.id) ? props.colorPrimary : getFillColor(d)))
            nodes.selectAll(".label")
                .attr("fill", d => {
                    const c = d3.lch(frozenIds.size > 0 && frozenIds.has(d.data.id) ?
                        props.frozenColor :
                        (selection.has(d.data.id) ? props.colorPrimary : getFillColor(d))
                    )
                    return c.l < 60 ? "#efefef" : "black"
                })
                .attr("font-weight", d => selection.has(d.data.id) ? "bold" : null)
        } else {
            nodes.selectAll(".tree-node")
                .style("filter", props.hideColorFilter ? "saturate(1)" : "saturate(0.75)")
                .attr("fill", d => frozenIds.size > 0 && frozenIds.has(d.data.id) ? props.frozenColor : getFillColor(d))
            nodes.selectAll(".label")
                .attr("font-weight", null)
                .attr("fill", d => {
                    const c = d3.lch(frozenIds.size > 0 && frozenIds.has(d.data.id) ? props.frozenColor : getFillColor(d))
                    return c.l < 60 ? "#efefef" : "black"
                })
        }
    }

    function flash() {
        if (props.flash && settings.focusTag !== null) {
            const rect = nodes.filter(d => d.data.id === settings.focusTag)

            if (rect.size() > 0) {
                const { y } =  d3.select(el.value).node().getBoundingClientRect()
                window.scrollTo({ top: Math.max(0, (y+window.scrollY)-50), behavior: "smooth"})

                let cycles = 0;

                const it = rect.select(".tree-node")
                it.interrupt()
                it
                    .transition()
                    .ease(d3.easeLinear)
                    .on("start", function repeat() {
                        if (cycles >= 3) return highlight();
                        cycles++;
                        d3.active(this)
                            .duration(100)
                            .attr("fill", "red")
                        .transition()
                            .duration(100)
                            .delay(100)
                            .attr("fill", d => getFillColor(d))
                        .transition()
                            .delay(200)
                            .on("start", repeat);
                    });
            }
        }
    }

    onMounted(draw)

    watch(() => settings.focusTime, flash)
    watch(() => settings.lightMode, draw)
    watch(() => props.frozen, highlight.bind(null, true), { deep: true })
    watch(() => props.selected, highlight.bind(null, true), { deep: true })
    watch(() => props.hidden, highlight.bind(null, true), { deep: true })
    watch(() => props.selectedSource, highlight.bind(null, true))
    watch(() => ([props.time, props.width, props.height, props.colorMap]), draw, { deep : true })
</script>

<style>
.node-effect:hover {
    filter: drop-shadow(0 0 4px black)
}
.thick:hover {
    font-weight: bold;
}
</style>