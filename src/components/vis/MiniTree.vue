<template>
    <svg ref="el"
        :width="vertical ? height : width"
        :height="vertical ? width : height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import DM from '@/use/data-manager';
    import { onMounted, watch, ref } from 'vue';
    import { useTimes } from '@/store/times';
    import { useTooltip } from '@/store/tooltip';
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';

    const times = useTimes()
    const tt = useTooltip()
    const app = useApp()
    const settings = useSettings();

    const props = defineProps({
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
        },
        valueAttr: {
            type: String,
        },
        valueScale: {
            type: String,
            default: "interpolatePlasma"
        },
        valueDomain: {
            type: Array,
            default: () => ([0, 1])
        },
        valueData: {
            type: Object,
        },
        valueAgg: {
            type: String,
            default: "none"
        },
        vertical: {
            type: Boolean,
            default: false
        },
    })

    const emit = defineEmits(["click-node"])
    const el = ref(null)

    let root, links, nodes, colScale;

    const width = ref(10)
    const height = ref(10)

    function getTagValue(tag) {
        switch (props.valueAttr) {
            default: return 0
            case "from_id":
                if (!props.valueData) return 0
                return props.valueData[tag.id] ? props.valueData[tag.id] : 0
            case "count": return DM.getDataItem("tags_counts", tag.id)
            case "irr": return DM.getDataItem("tags_irr", tag.id)
        }
    }

    function draw() {
        const data = DM.getData("tags_tree", false)
            .map(d => {
                const obj = Object.assign({}, d)
                if (props.valueAttr) {
                    obj[props.valueAttr] = getTagValue(d)
                }
                return obj
            })

        if (data.length === 0) return;

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
                if (props.valueAttr) {
                    switch (props.valueAgg) {
                        default:
                        case "none":
                            node.data[props.valueAttr] = getTagValue(node.data)
                            break;
                        case "mean":
                            node.data[props.valueAttr] = d3.mean(node.children, d => d.data[props.valueAttr])
                            break;
                        case "median":
                            node.data[props.valueAttr] = d3.median(node.children, d => d.data[props.valueAttr])
                            break;
                        case "sum":
                            node.data[props.valueAttr] = d3.sum(node.children, d => d.data[props.valueAttr])
                            break;
                        case "max":
                            node.data[props.valueAttr] = d3.max(node.children, d => d.data[props.valueAttr])
                            break;
                        case "min":
                            node.data[props.valueAttr] = d3.max(node.children, d => d.data[props.valueAttr])
                            break;
                    }
                }
            } else {
                node.pos = (node.data.order + 0.5) * props.nodeWidth

                node.y0 = height.value - props.radius - 1
                node.y1 = node.y0 - props.levelHeight
            }

        })

        if (props.valueAttr) {
            if (props.valueDomain.length === 3) {
                colScale = d3.scaleDiverging(d3[props.valueScale])
                    .domain(props.valueDomain)
            } else {
                colScale = d3.scaleSequential(d3[props.valueScale])
                    .domain(props.valueDomain)
            }
        }

        drawTree()
    }

    function drawTree() {

        const sel = DM.getSelectedIds("tags")
        root.eachAfter(node => {
            if (!node.parent) return;
            // non-leaf node
            if (node.children) {
                node.selectedDirect = sel.has(node.data[props.idAttr])
                node.selected = node.selectedDirect || node.children.some(c => c.selected)
            } else {
                node.selectedDirect = sel.has(node.data[props.idAttr])
                node.selected = node.selectedDirect || node.data.path.some(p => sel.has(p))
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
                    return props.vertical ?
                        `M ${d.y0},${d.start} V ${d.end} M ${d.y0},${d.pos} H ${d.y1}` :
                        `M ${d.start},${d.y0} H ${d.end} M ${d.pos},${d.y0} V ${d.y1}`
                } else {
                    return props.vertical ?
                        `M ${d.y0},${d.pos} H ${d.parent.y0}` :
                        `M ${d.pos},${d.y0} V ${d.parent.y0}`
                }
            })
            .attr("stroke", d => d.selected ? "red" : (settings.lightMode ? "black" : "white"))

        nodes = g.append("circle")
            .classed("cursor-pointer", true)
            .attr("cx", d => props.vertical ? (d.children ? d.y1 : d.y0) : d.pos)
            .attr("cy", d => props.vertical ? d.pos : (d.children ? d.y1 : d.y0))
            .attr("r", d => props.radius - (d.children ? 0 : 1))
            .attr("stroke", settings.lightMode ? "black" : "white")
            .attr("fill", d => {
                if (props.valueAttr) return colScale(d.data[props.valueAttr])
                return d.selectedDirect ? "red" : (settings.lightMode ? "black" : "white")
            })
            .on("pointerenter", (event, d) => {
                let extra = ""
                if (props.valueAttr && d.data[props.valueAttr]) {
                    extra = ` - ${d.data[props.valueAttr].toFixed(2)} (${props.valueAgg})`
                }
                const [mx, my] = d3.pointer(event, document.body)
                tt.show(d.data[props.nameAttr] + extra, mx, my)
            })
            .on("pointerleave", () => tt.hide())
            .on("click", (_, d) => {
                emit("click-node", d.data.id)
                app.toggleSelectByTag([d.data.id])
            })
    }

    function highlight() {
        const sel = DM.getSelectedIds("tags")
        root.eachAfter(node => {
            if (!node.parent) return;
            // non-leaf node
            if (node.children) {
                node.selectedDirect = sel.has(node.data[props.idAttr])
                node.selected = node.selectedDirect || node.children.some(c => c.selected)
            } else {
                node.selectedDirect = sel.has(node.data[props.idAttr])
                node.selected = node.selectedDirect || node.data.path.some(p => sel.has(p))
            }
        });

        links.attr("stroke", d => d.selected ? "red" : (settings.lightMode ? "black" : "white"))
        nodes
            .attr("fill", d => {
                if (props.valueAttr) return colScale(d.data[props.valueAttr])
                return d.selectedDirect ? "red" : (settings.lightMode ? "black" : "white")
            })
    }

    onMounted(draw)

    watch(() => times.f_tags, highlight)
    watch(() => settings.lightMode, draw)
    watch(() => Math.max(times.tags, times.tagging), draw)
    watch(props, draw, { deep: true })

</script>