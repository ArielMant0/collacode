<template>
    <div class="d-flex">
        <div class="d-flex flex-column">
            <v-select v-model="relativeTo"
                :items="['source', 'target']"
                class="mr-2 mb-2"
                density="compact"
                label="color elements relative to"
                @update:model-value="highlight"
                hide-details
                hide-spin-buttons
                mandatory/>
            <svg ref="el" :width="size" :height="size"></svg>
        </div>
        <ColorLegend :colors="legendColors" :ticks="legendCTicks" :size="size" :every-tick="5" vertical/>
    </div>
</template>

<script setup>

    import * as d3 from 'd3';
    import { onMounted, ref, watch } from 'vue';

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        matrix: {
            type: Object,
            required: true
        },
        sums: {
            type: Object,
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
    });

    const el = ref(null);

    function makeTree(data) {
        return d3.stratify()
            .id(d => d.id)
            .parentId(d => d.parent)
            (data)
    }

    let root, links, nodes;
    const radius = props.size * 0.5 - 10;

    let selected = null, clicked = null;

    let colorScale;

    const legendColors = ref([]);
    const legendCTicks = ref([]);


    const relativeTo = ref("source")

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

        resetNodeValues()

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
            // .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`)
            .on("mouseenter", function(_, d) {
                if (d.data.id !== -1) {
                    selected = selected === d.data.id ? null : d.data.id;
                    highlight();
                }
            })
            .on("mouseleave", function(_, d) {
                selected = null;
                highlight();
            })
            .on("click", function(_, d) {
                if (d.data.id !== -1) {
                    clicked = clicked === d.data.id ? null : d.data.id;
                    highlight();
                }
            })


        nodes.append("circle")
            .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`)
            .attr("fill", d => d.children ? "black" : "grey")
            .attr("r", d => d.children ? 4 : 3)

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
            .text(d => d.x >= Math.PI ? `${d.data.name} (${d.value})` : `(${d.value}) ${d.data.name}`)

        colorScale = d3.scaleSequential()
            .domain([0, 1])
            .interpolator(t => d3.interpolatePlasma(1 - t))

        legendColors.value = d3.range(0, 50).map(d => colorScale(d / 49))
        legendCTicks.value = d3.range(0, 50).map(d => `${Math.round((d / 50) * 100)}% to ${Math.round(((d+1) / 50) * 100)}%`)

        highlight();
    }

    function highlight() {

        const which = selected ? selected : clicked;

        if (!which) {
            resetNodeValues()

            links
                .transition()
                .duration(200)
                .attr("stroke-width", 1)
                .attr("stroke", "black")
                .attr("stroke-opacity", 1)

            nodes
                .transition()
                .duration(200)
                .attr("opacity", 1)
            nodes.selectAll("circle")
                .transition()
                .duration(200)
                .attr("fill", d => d.children ? "black" : "grey")
                .attr("r", d => d.children ? 4 : 3)

            nodes.selectAll("text")
                .text(d => d.x >= Math.PI ? `${d.data.name} (${d.value})` : `(${d.value}) ${d.data.name}`)
                .transition()
                .duration(200)
                .attr("font-weight", null)
                .attr("font-size", null)

            return;
        }

        computeNodeValues(which, relativeTo.value==="source")

        links
            .transition()
            .duration(200)
            .attr("stroke-width", d => d.target.value > 0 ? 3 : 1)
            .attr("stroke-opacity", d => d.target.value > 0 ? 1 : 0.05)
            .attr("stroke", d => d.target.value > 0 ? colorScale(d.target.valueRel) : "black")

        nodes
            .transition()
            .duration(200)
            .attr("opacity", d => d.data.id === which || d.value > 0 ? 1 : 0.25)
        nodes.selectAll("circle")
            .transition()
            .duration(200)
            .attr("fill", d => colorScale(d.valueRel))
            .attr("r", d => d.data.id === which ? 6 : (d.children ? 4 : 3))

        nodes.selectAll("text")
            .attr("font-size", 10)
            .text(d => d.x >= Math.PI ? `${d.data.name} (${d.value} | ${d.valueMax})` : `(${d.value} | ${d.valueMax}) ${d.data.name}`)
            .transition()
            .duration(200)
            .attr("font-size", d => d.data.id === which ? 14 : null)
            .attr("font-weight", d => d.data.id === which ? "bold" : null)
    }

    function cooccurrence(a, b) {
        const min = Math.min(a, b)
        const max = Math.max(a, b)
        return props.matrix[min] && props.matrix[min][max] ? props.matrix[min][max] : 0
    }

    function resetNodeValues() {
        root.eachAfter(node => {
            if (node.children) {
                node.value = node.children.reduce((sum, d) => sum + d.value, 0)
                node.valueMax = node.value
                node.valueRel = 1;
                props.sums[node.data.id] = node.value;
                return;
            }
            node.value = props.sums[node.data.id]
            node.valueMax = node.value
            node.valueRel = 1
        })
    }
    function computeNodeValues(which, useSource) {
        const isLeaf = props.matrix[which] !== undefined;
        const children = isLeaf ? null : props.data.filter(d => d.is_leaf === 1 && d.path.includes(which))
        const whichSum = props.sums[which];

        root.eachAfter(node => {
            // node in question
            if ((isLeaf && node.data.id === which) ||
                (!isLeaf && node.data.path.includes(which))
            ) {
                node.value = props.sums[node.data.id]
                node.valueMax = node.value;
                node.valueRel = 1;
                return;
            }

            // intermediate node
            if (node.children) {
                node.value = useSource && isLeaf ?
                    d3.max(node.children, d => d.value) :
                    node.children.reduce((sum, d) => sum + d.value, 0)

                node.valueMax = node.children.reduce((sum, d) => sum + d.valueMax, 0);
                node.valueRel = node.value / (useSource ? whichSum : node.valueMax);
                return;
            }

            // leaf node
            node.value = isLeaf ?
                cooccurrence(which, node.data.id) :
                children.reduce((sum, d) => sum + cooccurrence(d.id, node.data.id), 0)

            node.valueMax = props.sums[node.data.id];
            node.valueRel = node.value / (useSource ? whichSum : props.sums[node.data.id])
        })
    }

    onMounted(draw);

    watch(() => props.time, draw);
    watch(() => props.size, draw);
</script>