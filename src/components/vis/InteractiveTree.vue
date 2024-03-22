<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>

    import * as d3 from 'd3';
    import { ref, watch, onMounted } from 'vue';

    const props = defineProps({
        data: {
            type: Array,
            required: true
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
        }
    })
    const emit = defineEmits(["click", "drag"])

    const height = ref(100)
    const el = ref(null)

    function buildTagTree(data) {
        return d3.stratify()
            .id(d => d.id)
            .parentId(d => d.parent)
            (data)
    }

    function draw() {
        const svg = d3.select(el.value);
        svg.selectAll("*").remove();

        const root = buildTagTree(props.data);

        // Compute the layout.
        const dx = 10, padding = 5;
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

        svg
            .attr("viewBox", [padding - 25 - root.data.name.length*2, x0 - dx, props.width, height.value])
            .attr("style", "max-width: 100%; height: auto; height: intrinsic;")
            .attr("font-family", "sans-serif")
            .attr("font-size", 10);

        const line = d3.link(d3.curveBumpX)
            .x(d => d.y)
            .y(d => d.x)

        svg.append("g")
            .attr("fill", "none")
            .attr("stroke", "black")
            .selectAll("path")
            .data(root.links())
            .join("path")
                .attr("d", line);

        const node = svg.append("g")
            .selectAll("g")
            .data(root.descendants())
            .join("g")
            .attr("transform", d => `translate(${d.y},${d.x})`)

        node.append("circle")
            .attr("fill", d => d.children ? props.secondary : props.primary)
            .attr("r", 3);

        node.append("title").text(d => d.data.description);

        node.append("text")
            .attr("dy", "0.32em")
            .attr("x", d => d.children ? -6 : 6)
            .attr("text-anchor", d => d.children ? "end" : "start")
            .attr("paint-order", "stroke")
            .attr("stroke", "white")
            .attr("stroke-width", 3)
            .style("cursor", "pointer")
            .text(d => d.data.name)
            .on("click", (e, d) => emit("click", d.data, e))
            .on("pointerenter", function() {
                d3.select(this).attr("font-weight", "bold")
            })
            .on("pointerleave", function() {
                d3.select(this).attr("font-weight", null)
            })
    }

    onMounted(draw);

    watch(props, draw, { deep: true })
</script>