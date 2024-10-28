<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { sankey, sankeyCenter, sankeyLinkHorizontal } from 'd3-sankey';
    import { watch, ref, onMounted } from 'vue';

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        dimensions: {
            type: Array,
            required: true
        },
        colorScale: {
            type: String,
            default: "schemeCategory10"
        },
        width: {
            type: Number,
            default: 1000
        },
        height: {
            type: Number,
            default: 600
        },
    });

    const el = ref(null)

    const allData = []

    function makeGraph() {
        const keys = props.dimensions.slice();
        const nodes = [];
        const nodeByKey = new d3.InternMap([], JSON.stringify);;
        const indexByKey = new d3.InternMap([], JSON.stringify);;
        const links = [];

        let index = -1;
        for (const k of keys) {
            props.data.forEach(d => {
                const key = [k, getVal(d, k)];
                if (nodeByKey.has(key)) return;
                const node = { name: getVal(d, k), dim: k };
                nodes.push(node);
                nodeByKey.set(key, node);
                indexByKey.set(key, ++index);
            })
        }

        nodes.sort((a, b) => {
            let iA = keys.indexOf(a.dim)
            let iB = keys.indexOf(b.dim)
            if (iA !== iB) return iA - iB

            iA = a.name
            iB = b.name
            // compare name second
            if (iA < iB) { return -1; }
            if (iA > iB) { return 1; }
            // names must be equal
            return 0
        });

        indexByKey.clear()
        nodes.forEach((d, i) => indexByKey.set([d.dim, d.name], i))

        for (let i = 1; i < keys.length; ++i) {
            const a = keys[i - 1];
            const b = keys[i];
            const prefix = keys.slice(0, i + 1);
            const linkByKey = new d3.InternMap([], JSON.stringify);
            props.data.forEach(d => {
                const names = prefix.map(k => getVal(d, k));
                const value = d.value || 1;
                let link = linkByKey.get(names);
                if (link) {
                    link.value += value;
                    return;
                }
                link = {
                    source: indexByKey.get([a, getVal(d, a)]),
                    target: indexByKey.get([b, getVal(d, b)]),
                    names,
                    value
                };
                links.push(link);
                linkByKey.set(names, link);
            });
        }

        links.sort((a, b) => {
            const nameA = a.name
            const nameB = b.name
            if (nameA < nameB) { return -1; }
            if (nameA > nameB) { return 1; }
            // names must be equal
            return 0;
        });
        links.forEach((d, i) => d.id = i)

        return {nodes, links};
    }

    function getVal(d, key) { return d[key].join("+") }

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove();

        if (props.data.length === 0 || props.dimensions.length === 0) return;

        const graph = makeGraph();

        const mysankey = sankey()
            .nodeSort((a, b) => {
                const iA = graph.nodes.findIndex(d => d.name === a.name)
                const iB = graph.nodes.findIndex(d => d.name === b.name)
                return iA - iB
            })
            .linkSort((a, b) => {
                const iA = graph.nodes.findIndex(d => d.name === a.names[0])
                const iB = graph.nodes.findIndex(d => d.name === b.names[0])
                if (iA === iB) return b.value - a.value
                return iA - iB
            })
            .nodeWidth(6)
            .nodePadding(15)
            .extent([[5, 25], [props.width-5, props.height - 5]])

        const first = Array.from(d3.group(props.data, d => getVal(d, props.dimensions[0])).keys())
        const color = d3.scaleOrdinal(d3[props.colorScale])
            .domain(first)
            .unknown("#ccc")


        const {nodes, links} = mysankey({
            nodes: graph.nodes.map(d => Object.assign({}, d)),
            links: graph.links.map(d => Object.assign({}, d))
        })

        svg.append("g")
            .selectAll("text")
            .data(props.dimensions)
            .join("text")
            .attr("x", (_, i) => {
                const child = nodes.find(dd => dd.layer === i)
                return child ? (child.x0+child.x1)/2 : 0
            })
            .attr("y", 15)
            .attr("text-anchor", (_, i) => {
                if (i === 0) return "start"
                if (i === props.dimensions.length-1) return "end"
                return "middle"
            })
            .text(d => d)

        svg.append("g")
            .selectAll("rect")
            .data(nodes)
            .join("rect")
            .attr("x", d => d.x0)
            .attr("y", d => d.y0)
            .attr("height", d => d.y1 - d.y0)
            .attr("width", d => d.x1 - d.x0)
            .append("title")
            .text(d => `${d.name}\n${d.value.toLocaleString()}`);

        svg.append("g")
            .attr("fill", "none")
            .attr("opacity", 0.25)
            .selectAll("g")
            .data(links)
            .join("path")
            .attr("d", sankeyLinkHorizontal())
            .attr("stroke", d => color(d.names[0]))
            .attr("stroke-width", d => d.width)
            .style("mix-blend-mode", "lighten")
            .append("title")
            .text(d => `${d.names.join(" → ")}\n${d.value.toLocaleString()}`);

        svg.append("g")
            .style("font", "10px sans-serif")
            .selectAll("text")
            .data(nodes)
            .join("text")
            .attr("x", d => d.x0 < props.width / 2 ? d.x1 + 6 : d.x0 - 6)
            .attr("y", d => (d.y1 + d.y0) / 2)
            .attr("dy", "0.35em")
            .attr("text-anchor", d => d.x0 < props.width / 2 ? "start" : "end")
            .text(d => d.name)
            .append("tspan")
            .attr("fill-opacity", 0.7)
            .text(d => ` ${d.value.toLocaleString()}`);
    }

    onMounted(draw)

    watch(props, draw, { deep: true });

</script>
