<template>
    <div class="d-flex">
        <svg ref="el" :width="size" :height="size"></svg>
        <div class="d-flex flex-column">
            <WidthLegend :values="legendWidths" :ticks="legendWTicks"/>
            <ColorLegend :colors="legendColors" :ticks="legendCTicks" :size="size-110" :every-tick="5" vertical/>
        </div>
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

    let root, links, nodes, extras;
    const radius = props.size * 0.5 - 10;

    let selected = null, clicked = null;

    let colorScale, widthScale;

    const legendColors = ref([]);
    const legendCTicks = ref([]);

    const legendWidths = ref([]);
    const legendWTicks = ref([]);

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
            .text(d => d.data.name);

        extras = svg.append("g")

        colorScale = d3.scaleSequential()
            .domain([0, 1])
            .interpolator(t => d3.interpolatePlasma(1 - t))

        legendColors.value = d3.range(0, 50).map(d => colorScale(d / 49))
        legendCTicks.value = d3.range(0, 50).map(d => `${Math.round((d / 50) * 100)}% to ${Math.round(((d+1) / 50) * 100)}%`)

        widthScale = d3.scaleThreshold()
            .domain([0.2, 0.4, 0.6, 0.8])
            .range(d3.range(2, 11, 2))

        legendWidths.value = [1].concat(d3.range(2, 11, 2))
        legendWTicks.value = ["0", "1", "2", "3", "4", "5"]

        highlight();
    }

    function highlight() {

        const which = selected ? selected : clicked;

        if (!which) {
            links
                .attr("stroke-width", 1)
                .attr("stroke", "black")
                .attr("stroke-opacity", 1)

            nodes.attr("opacity", 1)
            nodes.selectAll("circle")
                .attr("fill", d => d.children ? "black" : "grey")
                .attr("r", d => d.children ? 4 : 3)

            nodes.selectAll("text").attr("font-weight", null).attr("font-size", null)
            return;
        }

        const isLeaf = props.matrix[which] !== undefined;
        const children = isLeaf ? null : props.data.filter(d => d.is_leaf === 1 && d.path.includes(which))

        root.eachAfter(node => {
            if (node.children) {
                node.value = node.children.reduce((sum, d) => sum + d.value, 0);
                node.valueMax = node.children.reduce((sum, d) => sum + (props.sums[d.data.id] ? props.sums[d.data.id] : d.valueMax), 0);
                node.valueRel = node.value / node.valueMax;
                return;
            }
            if (node.data.id === which) {
                node.value = props.sums[node.data.id]
                node.valueRel = 1;
                return;
            }

            const min = Math.min(which, node.data.id)
            const max = Math.max(which, node.data.id)
            node.value = isLeaf ? (props.matrix[min] && props.matrix[min][max] ? props.matrix[min][max] : 0) :
                children.reduce((sum, d) => {
                    const min = Math.min(d.id, node.data.id)
                    const max = Math.max(d.id, node.data.id)
                    return sum + (props.matrix[min] && props.matrix[min][max] ? props.matrix[min][max] : 0)
                }, 0)
            node.valueMax = props.sums[node.data.id] ? props.sums[node.data.id] : 0;
            node.valueRel = node.value / (props.sums[node.data.id] ? props.sums[node.data.id] : node.value)
        })

        const wDomain = d3.range(1, root.value+1, Math.floor((root.value-1) / 5))
        widthScale.domain(wDomain)

        const tmpTicks = ["0"]
        for (let i = 0; i < wDomain.length-1; ++i) {
            tmpTicks.push(`${wDomain[i]} to ${wDomain[i+1]}`)
        }
        legendWTicks.value = tmpTicks

        links.filter(d => d.target.value > 0)
            .transition()
            .duration(200)
            .attr("stroke-width", d => widthScale(d.target.value))
            .attr("stroke-opacity", 0.75)
            .attr("stroke", d => colorScale(d.target.valueRel))

        links.filter(d => d.target.value === 0)
            .transition()
            .duration(200)
            .attr("stroke-width", 1)
            .attr("stroke-opacity", 0.05)
            .attr("stroke", "black")

        nodes
            .transition()
            .duration(200)
            .attr("opacity", d => d.data.id === which || d.valueRel > 0 ? 1 : 0.25)
        nodes.selectAll("circle")
            .transition()
            .duration(200)
            .attr("fill", d => colorScale(d.valueRel))
            .attr("r", d => d.data.id === which ? 6 : (d.children ? 4 : 3))

        nodes.selectAll("text")
            .attr("font-size", 10)
            .transition()
            .duration(200)
            .attr("font-size", d => d.data.id === which ? 14 : null)
            .attr("font-weight", d => d.data.id === which ? "bold" : null)
    }

    onMounted(draw);

    watch(() => props.time, draw);
    watch(() => props.size, draw);
</script>