<template>
    <canvas ref="el" :width="width" :height="height" @pointermove="onMove" @click="onClick"></canvas>
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

    let ctx, root;

    const width = ref(10)
    const height = ref(10)

    function draw() {

        ctx = ctx ? ctx : el.value.getContext("2d")

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

        ctx.clearRect(0, 0, width.value, height.value)

        const sel = new Set(props.selected)

        ctx.lineWidth = 1;
        root.eachAfter(node => {
            if (!node.parent) return;
            // non-leaf node
            if (node.children && node.children.length > 0) {

                node.selected = sel.has(node.data[props.idAttr]) ||
                    node.children.some(c => c.selected)

                ctx.strokeStyle = node.selected ? "red": "black";
                ctx.fillStyle = node.selected ? "red": "black";

                ctx.beginPath();
                ctx.moveTo(node.start, node.y0)
                ctx.lineTo(node.end, node.y0)

                ctx.moveTo(node.start, node.y0)
                ctx.moveTo(node.start, node.y1)

                ctx.moveTo(node.end, node.y0)
                ctx.moveTo(node.end, node.y1)

                ctx.moveTo(node.pos, node.y0)
                ctx.lineTo(node.pos, node.y1)

                ctx.stroke()
                ctx.closePath()

                ctx.arc(node.pos, node.y1, props.radius, 0, 2*Math.PI)
                ctx.fill();

            } else {
                node.selected = sel.has(node.data[props.idAttr]) ||
                    node.data.path.some(p => sel.has(p))

                ctx.strokeStyle = node.selected ? "red": "black";
                ctx.fillStyle = node.selected ? "red": "black";

                ctx.beginPath();
                ctx.moveTo(node.pos, node.y0)
                ctx.lineTo(node.pos, node.parent.y0)
                ctx.stroke()
                ctx.closePath()

                ctx.arc(node.pos, node.y0, props.radius-1, 0, 2*Math.PI)
                ctx.fill();
            }
        });
    }

    function onMove(event) {
        const [mx, my] = d3.pointer(event, el.value);
        const node = root.find(n => {
            const r = props.radius - (n.children ? 0 : 1)
            const y = n.children ? n.y1 : n.y0
            return mx >= n.pos-r && mx <= n.pos+r &&
                my >= y-r && my <= y+r
        })
        if (node) {
            tt.show(node.data[props.nameAttr], event.pageX+5, event.pageY+5)
        } else {
            tt.hide()
        }
    }
    function onClick(event) {
        const [mx, my] = d3.pointer(event, el.value);
        const node = root.find(n => {
            const r = props.radius - (n.children ? 0 : 1)
            const y = n.children ? n.y1 : n.y0
            return mx >= n.pos-r && mx <= n.pos+r &&
                my >= y-r && my <= y+r
        })
        if (node) {
            emit("click-node", node.data.id)
        }
    }

    onMounted(draw)

    watch(() => props.selected, drawTree)
    watch(() => ([times.tags, times.tagging]), draw, { deep: true })
    watch(() => ([
        props.idAttr, props.nameAttr, props.parentAttr,
        props.levelHeight, props.nodeWidth, props.radius,
        props.time
    ]), draw, { deep: true })

</script>