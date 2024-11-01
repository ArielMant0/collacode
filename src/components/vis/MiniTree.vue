<template>
    <canvas ref="el" :width="width" :height="height"></canvas>
</template>

<script setup>
    import * as d3 from 'd3'
    import DM from '@/use/data-manager';
    import { onMounted, watch, ref } from 'vue';
    import { useTimes } from '@/store/times';

    const times = useTimes()
    const props = defineProps({
        time: {
            type: Number,
            required: true
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
        }
    })

    const el = ref(null)

    let ctx, root, data;

    const width = ref(10)
    const height = ref(10)

    function draw() {

        data = DM.getData("tags", false).map(d => Object.assign({}, d))
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
        height.value = props.levelHeight * root.height
        ctx = el.value.getContext("2d")

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
                node.y0 = height.value
                node.y1 = height.value - props.levelHeight
            }
        })

        drawTree()
    }

    function drawTree() {

        ctx.clearRect(0, 0, width.value, height.value)

        ctx.lineWidth = 1;
        ctx.strokeStyle = "black";
        ctx.fillStyle = "black";

        root.eachAfter(node => {
            // non-leaf node
            if (node.children && node.children.length > 0) {

                const y0 = node.y0
                const y1 = node.y1
                ctx.beginPath();

                // ctx.moveTo(node.start, y - props.levelHeight*0.5)
                // ctx.moveTo(node.start, y + props.levelHeight*0.5)

                // ctx.moveTo(node.end, y - props.levelHeight*0.5)
                // ctx.moveTo(node.end, y + props.levelHeight*0.5)

                ctx.moveTo(node.start, y0)
                ctx.lineTo(node.end, y0)

                ctx.moveTo(node.start, y0)
                ctx.moveTo(node.start, y1)

                ctx.moveTo(node.end, y0)
                ctx.moveTo(node.end, y1)

                ctx.moveTo(node.pos, y0)
                ctx.lineTo(node.pos, y1)
                ctx.stroke()
                ctx.closePath()

                ctx.arc(node.pos, y1, 3, 0, 2*Math.PI)
                ctx.fill();

            } else {
                ctx.beginPath();
                ctx.moveTo(node.pos, node.y0)
                ctx.lineTo(node.pos, node.y1)
                ctx.stroke()
            }
        });
    }

    onMounted(draw)

    watch(() => ([props.nodeWidth, props.levelHeight]), drawTree, { deep: true })
    watch(() => ([times.tags, times.tagging, props.time, props.idAttr, props.parentAttr]), draw, { deep: true })
</script>