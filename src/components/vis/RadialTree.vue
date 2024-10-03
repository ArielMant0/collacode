<template>
    <svg ref="el" :width="size" :height="size"></svg>
</template>

<script setup>

    import { useApp } from '@/store/app';
import DM from '@/use/data-manager';
    import * as d3 from 'd3';
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
    });

    const emit = defineEmits(["click", "right-click"])
    const app = useApp()
    const el = ref(null);

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
        svg.selectAll("*").remove();

        svg
            .attr("viewBox", [-(radius+25), -(radius+25), props.size-25, props.size-25])
            .attr("font-family", "sans-serif")
            .attr("font-size", 10)

        root = makeTree(props.data);

        const separation = (a, b) => (a.parent == b.parent ? 2 : 4) / a.depth
        d3.tree().size([2 * Math.PI, radius]).separation(separation)(root);

        links = svg.append("g")
            .attr("fill", "none")
            .attr("stroke", "black")
            .attr("stroke-opacity", 1)
            .attr("stroke-width", 1)
            .selectAll("path")
            .data(root.links())
            .join("path")
            .attr("d", d3.linkRadial()
                .angle(d => d.x)
                .radius(d => d.y));

        nodes = svg.append("g")
            .selectAll("g")
            .data(root.descendants())
            .join("g")
            .style("cursor", d => d.parent ? "pointer" : "default")
            .on("mouseenter", function(_, d) {
                if (d.data.id !== -1) {
                    hovered = hovered === d.data.id ? null : d.data.id;
                    highlight();
                }
            })
            .on("mouseleave", function(_, d) {
                if (d.data.id !== -1) {
                    hovered = null;
                    highlight();
                }
            })
            .on("click", function(_, d) {
                if (d.data.id !== -1) {
                    emit("click", d.data)
                }
            })
            .on("contextmenu", function(event, d) {
                event.preventDefault();
                emit("right-click", d.data, event)
            })


        nodes.append("circle")
            .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`)
            .attr("fill", d => d.children ? "black" : "grey")
            .attr("r", d => d.children ? props.radius+1 : props.radius)

        nodes
            .filter(d => d.data.id !== -1)
            .append("text")
            .attr("transform", d => {
                return d.children ?
                    `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${90 - d.x * 180 / Math.PI})` :
                    `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${d.x >= Math.PI ? 180 : 0})`
            })
            .attr("dy", "0.32em")
            .attr("x", d => d.x < Math.PI === !d.children ? 6 : -6)
            .attr("text-anchor", d => d.x < Math.PI === !d.children ? "start" : "end")
            .attr("paint-order", "stroke")
            .attr("stroke", "white")
            .attr("fill", "black")
            .attr("stroke-width", 2)
            .text(d => d.data[props.nameAttr])
            .append("title")
            .text(d => d.data[props.titleAttr])

        highlight();
    }

    function highlight() {
        const selected = new Set(DM.getFilter("tags", "id"))
        const which = hovered ? new Set([hovered]).union(selected) : selected

        links.attr("opacity", selected.size === 0 ? 1 : 0.33)
        nodes.attr("opacity", d => which.size === 0 || which.has(d.data.id) ? 1 : 0.33)

        nodes.selectAll("circle")
            .attr("r", d => props.radius + (selected.has(d.data.id) ? 2 : (d.children ? 1 : 0)))
            .attr("fill", d => selected.has(d.data.id) ? props.secondary : "black")

        nodes.selectAll("text")
            .attr("font-size", d => which.has(d.data.id) ? 12 : 10)
            .attr("font-weight", d => which.has(d.data.id) ? "bold" : null)
    }

    onMounted(draw);

    watch(() => props.time, draw);
    watch(() => props.size, draw);
    watch(() => app.selectionTime, highlight)
</script>