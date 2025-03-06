<template>
    <svg ref="el" :width="width">
        <g ref="treeLinks"></g>
        <g ref="assigLinks"></g>
        <g ref="treeNodes"></g>
        <g ref="assigNodes"></g>
    </svg>
</template>

<script setup>

    import * as d3 from 'd3';
    import { ref, watch, onMounted } from 'vue';
    import DM from '@/use/data-manager';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import { useTimes } from '@/store/times';

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        assignment: {
            type: Object,
            default: () => ({})
        },
        time: {
            type: Number,
            required: true
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
        layout: {
            type: String,
            default: "cluster"
        },
        showAssigned: {
            type: Boolean,
            default: false
        },
        radius: {
            type: Number,
            default: 5
        },
        fontSize: {
            type: Number,
            default: 12
        },
        horizontal: {
            type: Boolean,
            default: false
        },
        showValid: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["click", "right-click", "drag", "click-assign"])

    const height = ref(100)
    const el = ref(null)
    const treeLinks = ref(null)
    const treeNodes = ref(null)
    const assigLinks = ref(null)
    const assigNodes = ref(null)

    const times = useTimes()
    const settings = useSettings();

    const { treeHidden } = storeToRefs(settings);

    function buildTagTree(data) {
        let datapoints = data;
        if (!data.find(d => d.parent === null)) {
            datapoints = data.slice()
            datapoints.push({ id: -1, name: "root", parent: null })
        }

        const tree = d3.stratify()
            .id(d => d.id)
            .parentId(d => d.parent)(datapoints)

        if (props.layout === "cluster") {
            tree
                .count()
                .sum(d => d.value)
                .sort((a, b) => b.height - a.height || b.value - a.value);
        }
        return tree
    }

    let nodes, aNodes, root, line;

    function draw() {
        root = buildTagTree(props.data);
        d3.select(treeLinks.value).selectAll("*").remove();
        d3.select(treeNodes.value).selectAll("*").remove();
        root.x0 = 0;
        root.y0 = Math.max(25, props.width) / 2;
        root.each(d => {
            if (d.children) {
                d._children = d.children
                if (treeHidden.value.has(d.data.id)) {
                    d.children = null;
                }
            }
        });

        d3.select(el.value)
            .attr("style", "max-width: 100%; height: auto; height: intrinsic;")
            .attr("font-family", "sans-serif")
            .attr("font-size", props.fontSize);

        update();
    }

    function collapsedStr(node) {
        const sizes = {};
        node._children.forEach(d => {
            d.each(c => {
                if (!sizes[c.depth]) {
                    sizes[c.depth] = 0;
                }
                sizes[c.depth]++;
            })
        })
        return " ("+Object.values(sizes).join(", ")+")"
    }

    function update(source=root) {

        // Compute the layout.
        const dx = props.fontSize + 5, padding = 2;
        const dy = Math.max(25, props.width / (root.height + 1));

        if (props.layout === "cluster") {
            d3.cluster().nodeSize(props.horizontal ? [dy, dx] : [dx, dy])(root);
        } else {
            d3.tree().nodeSize(props.horizontal ? [dy, dx] : [dx, dy])(root);
        }

        // Center the tree.
        let x0 = Infinity;
        let x1 = -x0;
        root.each(d => {
            if (d.x > x1) x1 = d.x;
            if (d.x < x0) x0 = d.x;
        });
        const animate = source.id !== root.id

        // Compute the default height.
        height.value = x1 - x0 + dx * 2;

        let transition;
        if (animate) {
            let left = root;
            let right = root;
            root.eachBefore(node => {
                if (node.x < left.x) left = node;
                if (node.x > right.x) right = node;
            });

            transition = d3.select(el.value)
                .transition()
                .duration(1000)
                .attr("height", height.value)
                .attr("viewBox", [
                    padding - 35 - root.data.name.length*2,
                    x0 - dx,
                    props.width,
                    height.value
                ])
        } else {
            d3.select(el.value)
                .attr("height", height.value)
                .attr("viewBox", [
                    padding - 35 - root.data.name.length*2,
                    x0 - dx,
                    props.width,
                    height.value
                ])
        }

        line = d3.link(d3.curveBumpX)
            .x(d => d.y)
            .y(d => d.x)

        const links = d3.select(treeLinks.value)
            .attr("fill", "none")
            .attr("stroke", settings.lightMode ? "#121212" : "#fefefe")
            .attr("opacity", 0.5)
            .selectAll("path")
            .data(root.links(), d => d.target.id)

        if (animate) {
            const enterLinks = links.enter()
                .append("path")
                .attr("d", _ => {
                    const o = {x: source.x0, y: source.y0};
                    return line({source: o, target: o});
                })

            links.merge(enterLinks)
                .transition(transition)
                .attr("d", line);

            links.exit()
                .transition(transition)
                .remove()
                .attr("d", _ => {
                    const o = {x: source.x, y: source.y};
                    return line({source: o, target: o});
                });
        } else {
            links
                .join("path")
                .attr("d", line);
        }

        const darkPrimary = d3.color(props.primary).darker()

        if (animate) {

            const nodeG = d3.select(treeNodes.value)
                .selectAll("g")
                .data(root.descendants(), d => d.data.id)

            const enterNodes = nodeG.enter()
                .append("g")
                .attr("transform", `translate(${source.y0},${source.x0})`)

            enterNodes.append("circle")
                .attr("fill", d => d._children ? "#666" : (settings.lightMode ? "white" : "black"))
                .attr("stroke", d => d.data[props.assignAttr] && d.data[props.assignAttr].length > 0 ? props.secondary : darkPrimary)
                .attr("stroke-width", 2)
                .attr("r", props.radius)
                .style("cursor", d => d.parent ? "pointer" : 'default')
                .classed("node-effect", d => d.parent !== null)

            enterNodes.append("title").text(d => d.data.description);

            enterNodes.append("text")
                .attr("dy", "0.32em")
                .attr("x", d => d.children ? -10 : 12)
                .attr("paint-order", "stroke")
                .attr("stroke", settings.lightMode ? "white" : "black")
                .attr("stroke-width", 3)
                .attr("text-anchor", d => d.children ? "end" : "start")
                .attr("fill", d => !props.showValid || d.data.valid ? (settings.lightMode ? "black" : "white") : "red")
                .style("cursor", d => d.parent ? "pointer" : 'default')
                .text(d => (!props.showValid || d.data.valid ? "" : "! ") + d.data.name + (treeHidden.value.has(d.data.id) ? collapsedStr(d) : ''))
                .classed("thick", d => d.parent !== null)
                .on("click", (e, d) => {
                    if (e.defaultPrevented) return; // dragged
                    emit("click", d.data, e)
                })

            nodes = nodeG.merge(enterNodes)

            nodes.selectAll("circle")
                .on("click", (_, d) => {
                    if (!d.parent) return;
                    d.children = d.children ? null : d._children;
                    settings.toggleTreeHidden(d.data.id)
                    update(d);
                });

            nodes.raise()
                .transition(transition)
                .attr("transform", d => `translate(${d.y},${d.x})`)
                .on("end", () => {
                    nodes
                        .selectAll("text")
                        .attr("x", d => d.children ? -10 : 12)
                        .attr("text-anchor", d => d.children ? "end" : "start")
                        .text(d => (!props.showValid || d.data.valid ? "" : "! ") + d.data.name + (treeHidden.value.has(d.data.id) ? collapsedStr(d) : ''))
                })

            nodeG.exit()
                .transition(transition)
                .remove()
                .attr("transform", _ => `translate(${source.y},${source.x})`)

        } else {
            nodes = d3.select(treeNodes.value)
                .selectAll("g")
                .data(root.descendants(), d => d.data.id)
                .join("g")
                .attr("transform", d => `translate(${d.y},${d.x})`)

            nodes.append("circle")
                .attr("fill", d => d._children ? "#666" : (settings.lightMode ? "white" : "black"))
                .attr("stroke", d => d.data[props.assignAttr] && d.data[props.assignAttr].length > 0 ? props.secondary : darkPrimary)
                .attr("stroke-width", 2)
                .attr("r", props.radius)
                .style("cursor", d => d.parent ? "pointer" : 'default')
                .classed("node-effect", d => d.parent !== null)
                .on("click", (_, d) => {
                    if (!d.parent) return;
                    d.children = d.children ? null : d._children;
                    settings.toggleTreeHidden(d.data.id)
                    update(d);
                });

            nodes.append("title").text(d => d.data.description);

            nodes.append("text")
                .attr("dy", "0.32em")
                .attr("x", d => d.children ? -10 : 12)
                .attr("paint-order", "stroke")
                .attr("stroke", settings.lightMode ? "white" : "black")
                .attr("stroke-width", 3)
                .attr("text-anchor", "start")
                .attr("stroke-width", 3)
                .attr("text-anchor", d => d.children ? "end" : "start")
                .attr("fill", d => !props.showValid || d.data.valid ? (settings.lightMode ? "black" : "white") : "red")
                .style("cursor", d => d.parent ? "pointer" : 'default')
                .text(d => (!props.showValid || d.data.valid ? "" : "! ") + d.data.name + (treeHidden.value.has(d.data.id) ? collapsedStr(d) : ''))
                .classed("thick", d => d.parent !== null)
                .on("click", (e, d) => {
                    if (e.defaultPrevented) return; // dragged
                    emit("click", d.data, e)
                })
                .on("contextmenu", function(event, d) {
                    event.preventDefault();
                    emit("right-click", d.data, event)
                })
        }

        root.eachBefore(d => {
            d.x0 = d.x;
            d.y0 = d.y;
        });

        drawAssigned();
        highlight()
    }

    function highlight() {
        const sels = DM.getSelectedIds("tags")
        nodes.classed("selected", d => sels.has(d.data.id))
            .attr("opacity", d => sels.size === 0 || sels.has(d.data.id) ? 1 : 0.33)
            .selectAll("circle")
            .attr("r", d => props.radius + (sels.has(d.data.id) ? 2 : 0))

        if (props.showAssigned && aNodes) {
            const otherSels = DM.getSelectedIds("tags_old")
            aNodes.selectAll("text")
                .attr("font-weight", d => otherSels.has(d.id) ? "bold" : null)
        }
    }

    function isVisible(node) {
        if (treeHidden.value.size === 0 || !node || !node.parent) return true;
        return !treeHidden.value.has(node.parent.data.id) && isVisible(node.parent)
    }
    function drawAssigned() {
        d3.select(assigLinks.value).selectAll("*").remove();
        d3.select(assigNodes.value).selectAll("*").remove();

        if (props.showAssigned) {

            let emptyIndex = 0;

            const aData = Object.keys(props.assignment).map(d => {
                const others = props.data
                    .filter(dd => dd[props.assignAttr] && dd[props.assignAttr].includes(+d))
                    .filter(dd => {
                        const int = root.find(t => t.data.id === dd.id)
                        return int ? isVisible(int) : false
                    })
                const inTree = others.map(o => root.find(dd => dd.data.id === o.id))
                return {
                    id: +d,
                    name: props.assignment[d].name,
                    x: inTree.length > 0 ? d3.mean(inTree, dd => dd.x ? dd.x : 0) : (emptyIndex++) * 25 - height.value*0.5,
                    y: others.length > 0 && others.every(o => o.is_leaf === 1) ? props.width - 150 : root.y + 25,
                    others : others.map(dd => dd.id)
                }
            });

            d3.select(assigLinks.value).append("g")
                .selectAll("g")
                .data(aData.filter(d => d.others.length > 0))
                .join("g")
                .attr("fill", "none")
                .attr("stroke", props.secondary)
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
                .attr("fill", "black")
                .attr("r", props.radius)


            aNodes.append("text")
                .text(d => d.name)
                .attr("dy", "0.32em")
                .attr("x", 10)
                .attr("paint-order", "stroke")
                .attr("stroke", settings.lightMode ? "white" : "black")
                .attr("stroke-width", 3)
                .attr("text-anchor", "start")
                .attr("fill", settings.lightMode ? "black" : "white")
                .style("cursor", "pointer")
                .on("pointerenter", function() {
                    d3.select(this).attr("font-weight", "bold")
                })
                .on("pointerleave", function(_, d) {
                    const sels = DM.getSelectedIds("tags_old")
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

    function moveToTag() {
        const id = settings.focusTag;
        if (id !== null) {
            const n = nodes.filter(d => d.data.id === id)
            if (n) {
                const { x, y } = n.node().getBoundingClientRect()
                window.scrollTo({ left: x, top: Math.max(0, (y+window.scrollY)-50), behavior: "smooth"})
            }
        }
    }

    onMounted(draw);

    watch(() => props.time, draw)
    watch(() => settings.lightMode, draw)
    watch(() => settings.focusTime, moveToTag)
    watch(() => ({
        width: props.width,
        assignAttr: props.assignAttr,
        primary: props.primary,
        secondary: props.secondary,
        showAssigned: props.showAssigned,
        fontSize: props.fontSize,
        radius: props.radius,
        layout: props.layout
    }), update, { deep: true })
    watch(() => Math.max(times.f_tags_old, times.f_tags), highlight)
</script>

<style>
g.selected text {
    font-weight: bold;
}
.v-theme--customLight .node-effect:hover {
    filter: drop-shadow(0 0 4px black)
}
.v-theme--customDark .node-effect:hover {
    filter: drop-shadow(0 0 4px white)
}
.thick:hover {
    font-weight: bold;
}
</style>