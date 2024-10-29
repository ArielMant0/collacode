<template>
    <div class="d-flex flex-column" :style="{ 'width': size+'px' }">
        <div v-if="matrix" class="d-flex">
            <v-select v-model="relativeTo"
                :items="['source', 'target']"
                class="mr-2 mb-2"
                density="compact"
                label="color elements relative to"
                @update:model-value="highlight"
                hide-details
                hide-spin-buttons
                mandatory/>
            <v-select v-model="combine"
                :items="['or', 'and']"
                class="mr-2 mb-2"
                density="compact"
                label="multi-selection mode"
                @update:model-value="highlight"
                hide-details
                hide-spin-buttons
                mandatory/>
        </div>
        <div class="d-flex">
            <svg ref="el" :width="size" :height="size"></svg>
            <ColorLegend v-if="matrix" :colors="legendColors" :ticks="legendCTicks" :size="size-5" :every-tick="5" vertical/>
        </div>
    </div>
</template>

<script setup>

    import * as d3 from 'd3';
    import DM from '@/use/data-manager';
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

    let hovered = null;
    const selected = new Set();

    let colorScale;

    const legendColors = ref([]);
    const legendCTicks = ref([]);

    const relativeTo = ref("source")
    const combine = ref("or")

    let sumAND = 0;
    const matrixAND = {}

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
                if (d.data.id !== -1 && !selected.has(d.data.id)) {
                    hovered = hovered === d.data.id ? null : d.data.id;
                    highlight();
                }
            })
            .on("mouseleave", function(_, d) {
                if (d.data.id !== -1) {
                    hovered = null;
                    if (!selected.has(d.data.id)) {
                        highlight();
                    }
                }
            })
            .on("click", function(_, d) {
                if (d.data.id !== -1) {
                    if (hovered === d.data.id) { hovered = null; }
                    if (selected.has(d.data.id)) {
                        selected.delete(d.data.id);
                    } else {
                        selected.add(d.data.id)
                    }
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

        const which = hovered ? new Set([hovered].concat(Array.from(selected.values()))) : selected;

        if (which.size === 0) {

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
                // .transition()
                // .duration(200)
                .attr("font-weight", null)
                .attr("font-size", null)

            return;
        }

        computeNodeValues(which, relativeTo.value==="source", combine.value==="or")

        links
            .transition()
            .duration(200)
            .attr("stroke-width", d => d.target.value > 0 ? 3 : 1)
            .attr("stroke-opacity", d => d.target.value > 0 ? 1 : 0.05)
            .attr("stroke", d => d.target.value > 0 ? colorScale(d.target.valueRel) : "black")

        nodes
            .transition()
            .duration(200)
            .attr("opacity", d => which.has(d.data.id) || d.value > 0 ? 1 : 0.25)
        nodes.selectAll("circle")
            .transition()
            .duration(200)
            .attr("fill", d => colorScale(d.valueRel))
            .attr("r", d => which.has(d.data.id) ? 6 : (d.children ? 4 : 3))

        nodes.selectAll("text")
            .attr("font-size", 10)
            .text(d => d.x >= Math.PI ? `${d.data.name} (${d.value} | ${d.valueMax})` : `(${d.value} | ${d.valueMax}) ${d.data.name}`)
            // .transition()
            // .duration(200)
            .attr("font-size", d => which.has(d.data.id) ? 14 : null)
            .attr("font-weight", d => which.has(d.data.id) ? "bold" : null)
    }

    function resetNodeValues() {
        root.eachAfter(node => {
            if (node.children) {
                node.value = node.children.reduce((sum, d) => sum + d.value, 0)
                node.valueMax = node.value
                node.valueRel = 1;
                if (props.sums) {
                    props.sums[node.data.id] = node.value;
                }
                return;
            }
            node.value = props.sums ? props.sums[node.data.id] : 1;
            node.valueMax = node.value
            node.valueRel = 1
        })
    }

    function div(a, b) {
        if (Number.isNaN(b) || b === 0) {
            return 0;
        }
        return a / b;
    }
    function getTagValue(a, b, useOr=true) {
        const min = Math.min(a, b)
        const max = Math.max(a, b)
        return useOr ?
            (props.matrix[min] && props.matrix[min][max] ? props.matrix[min][max] : 0) :
            matrixAND[a] ? matrixAND[a] : 0
    }
    function getTagSum(id) {
        return props.sums[id]
    }

    function computeANDValues(which) {
        const tags = Array.from(which.values())
        const games = DM.getData("games", false)
            .filter(g => tags.every(t => g.allTags.find(d => d.id === t || d.path.includes(t)) !== undefined))

        for (const from in props.matrix) {
            matrixAND[from] = 0;
            for (const to in props.matrix[from]) {
                matrixAND[to] = 0;
            }
        }

        sumAND = games.length;
        games.forEach(g => g.allTags.forEach(t => matrixAND[t.id]++));
    }

    function computeNodeValues(which, useSource=true, useOr=true) {
        if (!useOr) {
            computeANDValues(which);
        }

        const vals = Array.from(which.values())
        const isLeaf = which.size === 1 && props.matrix[vals[0]] !== undefined;
        const children = isLeaf ? null : props.data.filter(d => d.is_leaf === 1 && d.path.some(id => which.has(id)))
        const whichSum = useOr ? vals.reduce((sum, d) => sum + getTagSum(d), 0) : sumAND;


        root.eachAfter(node => {
            // nodes in question
            if ((isLeaf && vals[0] === node.data.id) ||
                (!isLeaf && node.data.path.some(id => which.has(id)))
            ) {
                node.value = whichSum;
                node.valueMax = getTagSum(node.data.id);
                node.valueRel = useOr ? 1 : div(node.value, node.valueMax);
                return;
            }

            // intermediate node
            if (node.children) {
                node.value = useSource && isLeaf ?
                    d3.max(node.children, d => d.value) :
                    node.children.reduce((sum, d) => sum + d.value, 0)

                node.valueMax = node.children.reduce((sum, d) => sum + d.valueMax, 0);
                node.valueRel = div(node.value, useSource ? whichSum : node.valueMax);
                return;
            }

            node.value = isLeaf || !useOr ?
                getTagValue(node.data.id, vals[0], useOr) :
                children.reduce((sum, d) => sum + getTagValue(node.data.id, d.id, useOr), 0)

            node.valueMax = getTagSum(node.data.id);
            node.valueRel = div(node.value,  useSource ? whichSum : getTagSum(node.data.id))
        })
    }

    onMounted(draw);

    watch(() => props.time, draw);
    watch(() => props.size, draw);
</script>