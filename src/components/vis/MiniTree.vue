<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import DM from '@/use/data-manager';
    import { onMounted, watch, ref } from 'vue';
    import { useTimes } from '@/store/times';
    import { useTooltip } from '@/store/tooltip';

    const times = useTimes()
    const tt = useTooltip()

    const props = defineProps({
        time: {
            type: Number,
            required: true
        },
        selected: {
            type: Array,
            default: () => ([])
        },
        radius:{
            type: Number,
            default: 3
        },
        nodeWidth: {
            type: Number,
            default: 6
        },
        levelHeight: {
            type: Number,
            default: 10
        },
        idAttr: {
            type: String,
            default: "id"
        },
        parentAttr: {
            type: String,
            default: "parent"
        },
        nameAttr: {
            type: String,
            default: "name"
        }
    })

    const emit = defineEmits(["click-node"])
    const el = ref(null)

    let root, links, nodes;

    const width = ref(10)
    const height = ref(10)

    function draw() {
        const data = DM.getData("tags", false).map(d => Object.assign({}, d))
        if (data.length === 0) return;

        data.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return a.path.length-b.path.length
        });

        const fakeRoot = {}
        fakeRoot[props.idAttr] = -1
        fakeRoot[props.parentAttr] = null
        data.push(fakeRoot)

        let idx = 0;
        data.forEach(d => d.order = d.is_leaf == 1 ? idx++ : -1)

        root = d3.stratify()
            .id(d => d[props.idAttr])
            .parentId(d => d[props.parentAttr])
            (data)

        width.value = props.nodeWidth * idx
        height.value = props.levelHeight * (root.height+1) + props.radius

        root.eachAfter(node => {
            if (!node.parent) return;
            if (node.children && node.children.length > 0) {
                const [start, end] = d3.extent(node.children, d => d.pos)
                node.start = start;
                node.end = end;
                node.pos = (start + end) / 2
                node.y0 = d3.min(node.children, d => d.y1)
                node.y1 = node.depth * props.levelHeight;
            } else {
                node.pos = (node.data.order + 0.5) * props.nodeWidth
                node.y0 = height.value - props.radius - 1
                node.y1 = node.y0 - props.levelHeight
            }
        })

        drawTree()
    }

    function drawTree() {

        const sel = new Set(props.selected)
        root.eachAfter(node => {
            if (!node.parent) return;
            // non-leaf node
            if (node.children) {
                node.selected = sel.has(node.data[props.idAttr]) || node.children.some(c => c.selected)
            } else {
                node.selected = sel.has(node.data[props.idAttr]) || node.data.path.some(p => sel.has(p))
            }
        });

        const svg = d3.select(el.value)
        svg.selectAll("*").remove();

        const g = svg.selectAll("g")
            .data(root.descendants().filter(d => d.parent !== null))
            .join("g")

        links = g.append("path")
            .attr("d", d => {
                if (d.children) {
                    return `M ${d.start},${d.y0} H ${d.end} M ${d.pos},${d.y0} V ${d.y1}`
                } else {
                    return `M ${d.pos},${d.y0} V ${d.parent.y0}`
                }
            })
            .attr("stroke", d => d.selected ? "red" : "black")

        nodes = g.append("circle")
            .attr("cx", d => d.pos)
            .attr("cy", d => d.children ? d.y1 : d.y0)
            .attr("r", d => props.radius - (d.children ? 0 : 1))
            .attr("fill", d => d.selected ? "red" : "black")
            .on("pointerenter", (e, d) => tt.show(d.data[props.nameAttr], e.pageX+10, e.pageY))
            .on("pointerleave", () => tt.hide())
            .on("click", (_, d) => emit("click-node", d.data.id))
    }

    function highlight() {
        const sel = new Set(props.selected)
        root.eachAfter(node => {
            if (!node.parent) return;
            // non-leaf node
            if (node.children) {
                node.selected = sel.has(node.data[props.idAttr]) || node.children.some(c => c.selected)
            } else {
                node.selected = sel.has(node.data[props.idAttr]) || node.data.path.some(p => sel.has(p))
            }
        });

        links.attr("stroke", d => d.selected ? "red" : "black")
        nodes.attr("fill", d => d.selected ? "red" : "black")
    }

    onMounted(draw)

    watch(() => props.selected, highlight)
    watch(() => Math.max(times.tags, times.tagging), draw)
    watch(() => ([
        props.idAttr, props.nameAttr, props.parentAttr,
        props.levelHeight, props.nodeWidth, props.radius,
        props.time
    ]), draw, { deep: true })

</script>