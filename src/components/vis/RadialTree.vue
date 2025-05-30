<template>
    <svg ref="el" :width="size" :height="size">
        <g ref="linkEl"></g>
        <g ref="nodeEl"></g>
    </svg>
</template>

<script setup>

    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import * as d3 from 'd3';
    import { storeToRefs } from 'pinia';
    import { onMounted, ref, watch } from 'vue';

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        time: {
            type: Number,
            required: true
        },
        size: {
            type: Number,
            default: 600
        },
        radius: {
            type: Number,
            default: 3
        },
        nameAttr: {
            type: String,
            default: "name"
        },
        titleAttr: {
            type: String,
            default: "description"
        },
        primary: {
            type: String,
            default: "#078766"
        },
        secondary: {
            type: String,
            default: "#0ad39f"
        },
        flash: {
            type: Boolean,
            default: false
        },
    });

    const emit = defineEmits(["click", "right-click"])

    const times = useTimes();
    const settings = useSettings();
    const { treeHidden } = storeToRefs(settings);

    const el = ref(null);
    const linkEl = ref(null)
    const nodeEl = ref(null)

    function makeTree(data) {
        return d3.stratify()
            .id(d => d.id)
            .parentId(d => d.parent)
            (data)
    }

    let root, links, nodes;
    const radius = props.size * 0.5 - 10;

    let hovered = null;

    function draw() {
        const svg = d3.select(el.value);
        d3.select(linkEl.value).selectAll("*").remove();
        d3.select(nodeEl.value).selectAll("*").remove();

        svg
            .attr("viewBox", [-(radius-25), -(radius-25), props.size-50, props.size-50])
            .attr("font-family", "sans-serif")
            .attr("font-size", 10)

        root = makeTree(props.data);
        root.each(d => {
            if (d.children) {
                d._children = d.children
                if (treeHidden.value.has(d.data.id)) {
                    d.children = null;
                }
            }
        });

        update(root)
        highlight();
    }

    function update(source=root) {
        const separation = (a, b) => (a.parent == b.parent ? 2 : 4) / a.depth
        d3.tree().size([2 * Math.PI, radius]).separation(separation)(root);

        const animate = !nodes || !links || source.id !== root.id

        const line = d3.linkRadial()
            .angle(d => d.x)
            .radius(d => d.y)

        links = d3.select(linkEl.value)
            .attr("fill", "none")
            .attr("stroke", "currentColor")
            .attr("stroke-width", 1)
            .selectAll("path")
            .data(root.links(), d => d.target.id)

        if (animate) {
            const transition = d3.select(el.value)
                .transition()
                .duration(1000)

            const o1 = {x: source.x0, y: source.y0};
            const enterLinks = links.enter()
                .append("path")
                .attr("d", line({ source: o1, target: o1 }))
                .attr("stroke-opacity", 0)

            links.merge(enterLinks)
                .attr("d", line)
                .transition(transition)
                .delay(800)
                .attr("stroke-opacity", 1)

            const o2 = {x: source.x, y: source.y};
            links.exit()
                .transition(transition)
                .remove()
                .attr("d", line({ source: o2, target: o2 }));

            const nodeG = d3.select(nodeEl.value)
                .selectAll("g")
                .data(root.descendants(), d => d.data.id)

            const enter = nodeG.enter().append("g")

            enter
                .filter(d => d.parent)
                .append("circle")
                .style("cursor", d => d.parent && d._children ? "pointer" : "default")
                .attr("transform", `rotate(${source.x0 * 180 / Math.PI - 90}) translate(${source.y0},0)`)
                .attr("fill", d => d._children ? "#666" : "currentColor")
                .attr("stroke", "currentColor")
                .attr("r", d => d._children ? props.radius+1 : props.radius)
                .classed("node-effect", true)
                .on("click", function(_, d) {
                    if (!d.parent || !d._children) return;
                    d.children = d.children ? null : d._children;
                    settings.toggleTreeHidden(d.data.id)
                    update(d);
                })

            enter
                .filter(d => d.parent)
                .append("text")
                .style("cursor", "pointer")
                .attr("transform", d => {
                    return d.children ?
                        `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${90 - d.x * 180 / Math.PI})` :
                        `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${d.x >= Math.PI ? 180 : 0})`
                })
                .attr("x", d => d.x < Math.PI === !d.children ? 6 : -6)
                .attr("text-anchor", d => d.x < Math.PI === !d.children ? "start" : "end")
                .attr("paint-order", "stroke")
                .attr("stroke", settings.lightMode ? "white" : "black")
                .attr("fill", "currentColor")
                .attr("opacity", 0)
                .attr("stroke-width", 2)
                .text(d => d.data[props.nameAttr])
                .on("click", function(_, d) {
                    if (d.parent) { emit("click", d.data) }
                })
                .on("contextmenu", function(event, d) {
                    event.preventDefault();
                    emit("right-click", d.data, event)
                })
                .on("mouseenter", function(_, d) {
                    if (d.parent) {
                        hovered = d.data.id;
                        highlight();
                    }
                })
                .on("mouseleave", function(_, d) {
                    if (d.parent) {
                        hovered = null;
                        highlight();
                    }
                })
                .append("title")
                .text(d => d.data[props.titleAttr])

            nodes = nodeG.merge(enter)
            nodes.selectAll("circle")
                .transition(transition)
                .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`)

            nodes.selectAll("text")
                .transition(transition)
                .delay(800)
                .attr("opacity", 1)

            const exit = nodeG.exit()
            exit.transition(transition).remove()

            exit.selectAll("circle")
                .transition(transition)
                .attr("transform", `rotate(${source.x * 180 / Math.PI - 90}) translate(${source.y},0)`)

            exit.selectAll("text")
                .transition(transition)
                .attr("opacity", 0)

        } else {

            links
                .join("path")
                .attr("d", line);

            nodes = d3.select(nodeEl.value)
                .selectAll("g")
                .data(root.descendants())
                .join("g")

            nodes
                .filter(d => d.parent)
                .append("circle")
                .style("cursor", d => d._children ? "pointer" : "default")
                .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`)
                .attr("fill", d => d._children ? "#666" : "currentColor")
                .attr("stroke", "currentColor")
                .attr("r", d => d._children ? props.radius+1 : props.radius)
                .classed("node-effect", d => d.parent !== null)
                .on("click", function(_, d) {
                    if (!d.parent || !d._children) return;
                    d.children = d.children ? null : d._children;
                    settings.toggleTreeHidden(d.data.id)
                    update(d);
                })

            nodes
                .filter(d => d.parent)
                .append("text")
                .style("cursor", "pointer")
                .attr("transform", d => {
                    return d.children ?
                        `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${90 - d.x * 180 / Math.PI})` :
                        `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${d.x >= Math.PI ? 180 : 0})`
                })
                .attr("dy", "0.32em")
                .attr("x", d => d.x < Math.PI === !d.children ? 6 : -6)
                .attr("text-anchor", d => d.x < Math.PI === !d.children ? "start" : "end")
                .attr("paint-order", "stroke")
                .attr("stroke", "currentColor")
                .attr("fill", "currentColor")
                .attr("stroke-width", 2)
                .text(d => d.data[props.nameAttr])
                .on("mouseenter", function(_, d) {
                    if (d.parent) {
                        hovered = d.data.id;
                        highlight();
                    }
                })
                .on("mouseleave", function(_, d) {
                    if (d.parent) {
                        hovered = null;
                        highlight();
                    }
                })
                .on("click", function(_, d) {
                    if (d.parent) { emit("click", d.data) }
                })
                .on("contextmenu", function(event, d) {
                    event.preventDefault();
                    emit("right-click", d.data, event)
                })
                .append("title")
                .text(d => d.data[props.titleAttr])
        }

        root.eachBefore(d => {
            d.x0 = d.x;
            d.y0 = d.y;
        });
    }

    function highlight() {
        if (!nodes || !links) return

        const selected = DM.getSelectedIds("tags")
        const which = hovered ? new Set([hovered]).union(selected) : selected

        links.attr("opacity", selected.size === 0 ? 1 : 0.33)
        nodes.attr("opacity", d => selected.size === 0 || which.has(d.data.id) ? 1 : 0.33)

        nodes.selectAll("circle")
            .attr("r", d => props.radius + (selected.has(d.data.id) ? 2 : (d._children ? 1 : 0)))
            // .attr("fill", d => selected.has(d.data.id) ? props.secondary : (d._children ? "black" : "grey"))

        nodes.selectAll("text")
            .attr("font-size", d => which.has(d.data.id) ? 12 : 10)
            .attr("font-weight", d => which.has(d.data.id) ? "bold" : null)
    }

    function flash() {
        if (props.flash && settings.focusTag !== null) {
            const rect = nodes.filter(d => d.data.id === settings.focusTag)

            if (rect.size() > 0) {
                const { y } =  rect.node().getBoundingClientRect()
                window.scrollTo({ top: Math.max(0, (y+window.scrollY)-50), behavior: "smooth"})

                let cycles = 0;

                const it = rect.select("circle")
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
                            .attr("r", props.radius*3)
                        .transition()
                            .duration(100)
                            .delay(100)
                            .attr("r", props.radius)
                            .attr("fill", d => d._children ? "#666" : "currentColor")
                        .transition()
                            .delay(200)
                            .on("start", repeat);
                    });
            }
        }
    }

    onMounted(draw);

    watch(() => settings.focusTime, flash)
    watch(() => ([props.time, props.size, settings.lightMode]), draw, { deep: true });
    watch(() => times.f_tags, highlight)
</script>

<style>
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