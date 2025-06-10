<template>
    <div>
        <svg ref="el" :width="width" :height="height"></svg>
        <div>
            <h3>Current Result</h3>
            <BarCode v-if="barCode.length > 0"
                :data="barCode"
                selectable
                id-attr="id"
                name-attr="name"
                value-attr="value"
                abs-value-attr="value"
                show-absolute
                :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                :min-value="0"
                :max-value="1"
                :width="barCodeNodeSize"
                :height="15"/>

            <div class="d-flex flex-wrap" :style="{ maxWidth: width+'px' }">
                <v-chip v-for="t in barCodeFiltered"
                    :key="t.id"
                    :color="colScale(t.value)"
                    rounded
                    density="compact"
                    :variant="excluded.has(t.id) ? 'outlined' : 'flat'"
                    @click="toggleExcludeTag(t.id)"
                    class="mr-1 mb-1 text-caption">
                    {{ t.name }}
                </v-chip>
            </div>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ref, onMounted, computed, reactive } from 'vue';
    import { randomItems, randomItemsDissimilar } from '@/use/random';
    import { capitalize, mediaPath } from '@/use/utility';
    import { euclidean } from '@/use/metrics';
    import BarCode from '../vis/BarCode.vue';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import DM from '@/use/data-manager';
    import { useTooltip } from '@/store/tooltip';
    import { useApp } from '@/store/app';

    const app = useApp()
    const tt = useTooltip()
    const settings = useSettings()

    const { barCodeNodeSize } = storeToRefs(settings)

    const props = defineProps({
        imageWidth: {
            type: Number,
            default: 100
        },
        imageHeight: {
            type: Number,
            default: 50
        },
    })

    const emit = defineEmits(["update"])

    const el = ref(null)

    const items = ref([])
    const sims = ref([])
    // const choices = ref([])
    const excluded = reactive(new Set())
    const once = new Set()

    const MAX_ITEMS = 5
    const ANGLE_PETAL = 180 / (MAX_ITEMS - 1)
    const ANGLES = d3.range(5).map(i =>  (i * ANGLE_PETAL + 180) % 360)

    const threshold = ref(0.05)
    const barCode = ref([])
    const barCodeFiltered = computed(() => barCode.value.filter(d => d.value > 0))
    const width = computed(() => Math.max(300, barCodeNodeSize.value * barCode.value.length))
    const height = computed(() => width.value * 0.33)

    const colScale = d3.scaleSequential(d3.interpolatePlasma).domain([0, 1])


    function toggleExcludeTag(tid) {
        if (excluded.has(tid)) {
            excluded.delete(tid)
        } else {
            excluded.add(tid)
        }
        updateBarCode()
    }

    function nextItem() {
        if (items.value.length === MAX_ITEMS) return

        const next = items.value.length > 0 ?
            randomItemsDissimilar(items.value, 1) :
            randomItems(1, 3)
        items.value.push(next)
        sims.value.push(0)
        updateBarCode()
        draw()
    }

    function onCircle(angle, rX, rY, cX, cY) {
        const rad = angle * Math.PI / 180
        return [cX + rX * Math.cos(rad), cY + rY * Math.sin(rad)]
    }

    function maxLen(angle, rX, rY, cX, cY) {
        const rad = angle * Math.PI / 180
        return euclidean(
            [cX + rX * Math.cos(rad), cY + rY * Math.sin(rad)],
            [cX, cY],
        )
    }

    let ds

    function draw() {
        const off = 10
        const rx = Math.floor(width.value * 0.5) - props.imageWidth - off
        const ry = height.value - props.imageHeight - off
        const cx = Math.floor(width.value * 0.5)
        const cy = height.value - off

        d3.select(el.value).selectAll("*").remove()

        const drawItems = items.value.map((d, i) => {
            const obj = Object.assign({}, d)
            obj._i = i
            obj._a = ANGLES[i]
            obj._ml = maxLen(ANGLES[i], rx, ry, cx, cy)
            obj._s = sims.value[i]
            obj._p = onCircle(ANGLES[i], rx, ry, cx, cy)
            return obj
        })

        const petals = d3.select(el.value)
            .selectAll(".petal")
            .data(drawItems)
            .join("g")
            .classed("petal", true)
            .attr("opacity", (_, i) => i < items.length ? 0.5 : 1)


        const img = petals.append("g")
            .attr("transform", d => `translate(${d._p[0]-props.imageWidth}, ${d._p[1]-props.imageHeight})`)
            .on("pointerenter", function() {
                d3.select(this).select("rect").attr("stroke", "red")
            })
            .on("pointermove", function(event, d) {
                const [mx, my] = d3.pointer(event, document.body)
                const extra = app.itemColumns.reduce((acc, c) => acc + `<div><b>${capitalize(c.name)}:</b> ${d[c.name]}</div>`, "")
                tt.show(
                    `<div>
                        <img src="${mediaPath('teaser', d.teaser)}" style="max-height: 150px; object-fit: contain;"/>
                        <div class="mt-1 text-caption">
                            <div>${d.name}</div>
                            ${d.description ? '<div><b>Description:</b> '+d.description+'</div>' : ''}
                            ${extra}
                        </div>
                    </div>`,
                    mx, my
                )
            })
            .on("pointerleave", function() {
                d3.select(this).select("rect").attr("stroke", "currentColor")
                tt.hide()
            })

        img.append("image")
            .attr("x", d => d._a >= 225 ? props.imageWidth*0.5 : (d._a <= 90 ? props.imageWidth : 0))
            .attr("width", props.imageWidth)
            .attr("height", props.imageHeight)
            .attr("preserveAspectRatio", "xMidYMid slice")
            .attr("href", d => mediaPath("teaser", d.teaser))

        img.append("rect")
            .attr("x", d => d._a >= 225 ? props.imageWidth*0.5 : (d._a <= 90 ? props.imageWidth : 0))
            .attr("width", props.imageWidth)
            .attr("height", props.imageHeight)
            .attr("stroke", "currentColor")
            .attr("stroke-width", 2)
            .attr("fill", "none")

        petals.append("line")
            .attr("x1", cx)
            .attr("y1", cy)
            .attr("x2", d => d._p[0])
            .attr("y2", d => d._p[1])
            .attr("stroke-width", 2)
            .attr("stroke", "currentColor")
            .on("click", function(event, d) {
                // TODO: this is not yet correct (need to map point to line)
                const now = euclidean([cx, cy], [event.x, event.y]) / d._ml
                d._s = Math.max(Math.min(1, now), 0)
                sims.value[d._i] = d._s
                updateBarCode(d._i)
            })

        const drag = d3
            .drag()
            .on("start", dragstart)
            .on("drag", dragged)
            .on("end", dragend)

        function dragstart(_event, d) {
            d3.select(this).attr("fill", "red")
            ds = d._s
        }
        function dragged(event, d) {
            const dx = cx * (1 - ds) + ds * d._p[0]
            const dy = cy * (1 - ds) + ds * d._p[1]
            // TODO: this is not yet correct (need to map point to line)
            const now = euclidean([dx, dy], [event.x, event.y]) / d._ml
            d._s = Math.min(1, Math.max(0, now))
            sims.value[d._i] = d._s
            ds = d._s
            d3.select(this)
                .attr("cx", dx)
                .attr("cy", dy)
        }
        function dragend(_event, d) {
            d3.select(this).attr("fill", "grey")
            ds = null
            updateBarCode(d._i)
        }

        petals.append("circle")
            .attr("cx", d => cx * (1 - d._s) + d._s * d._p[0])
            .attr("cy", d => cy * (1 - d._s) + d._s * d._p[1])
            .attr("r", 5)
            .attr("stroke-width", 1)
            .attr("stroke", "currentColor")
            .attr("fill", "grey")
            .call(drag)


        if (items.value.length > 1) {
            const path = d3.line().curve(d3.curveLinearClosed)

            d3.select(el.value)
                .append("path")
                .classed("radar", true)
                .style("pointer-events", "none")
                .attr("d", path(drawItems.map(d => ([cx * (1 - d._s) + d._s * d._p[0], cy * (1 - d._s) + d._s * d._p[1]])).concat([[cx, cy]])))
                .attr("stroke", "currentColor")
                .attr("fill", "currentColor")
                .attr("fill-opacity", 0.1)
        }

    }

    function updateBarCode(index=-1) {
        const vals = new Map()
        items.value.forEach((d, i) => {
            d.allTags.forEach(t => {
                vals.set(t.id, (vals.get(t.id) || 0) + sims.value[i])
            })
        })
        const data = []
        barCode.value.forEach(t => {
            const v = vals.has(t.id) ? vals.get(t.id) / items.value.length : 0
            t.value = v > threshold.value ? v : 0
            if (v > threshold.value && !excluded.has(t.id)) {
                data.push(t.id)
            }
        })

        if (index >= 0) {
            if (!once.has(index)) {
                once.add(index)
                if (index < MAX_ITEMS-1) {
                    nextItem()
                } else {
                    draw()
                }
            } else {
                draw()
            }
        }
        emit("update", data)
    }

    function read() {
        const domain = DM.getDataBy("tags_tree", d => d.is_leaf === 1)
        barCode.value = domain.map(d => {
            const obj = Object.assign({}, d)
            obj.value = 0
            return obj
        })
    }

    onMounted(function() {
        read()
        setTimeout(nextItem, 250)
    })
</script>