<template>
    <svg ref="el" :width="width" :height="height" @pointermove="onMove" @pointerleave="onLeave"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTimes } from '@/store/times'
    import DM from '@/use/data-manager'
    import { onMounted, watch, ref } from 'vue'
    import { DateTime } from 'luxon'
    import { useTooltip } from '@/store/tooltip'

    const times = useTimes()
    const tt = useTooltip()

    const props = defineProps({
        id: {
            type: Number,
            required: true
        },
        source: {
            type: String,
            required: true
        },
        idAttr: {
            type: String,
            required: true
        },
        width: {
            type: Number,
            default: 120
        },
        height: {
            type: Number,
            default: 50
        },
        color: {
            type: String,
            default: "black"
        },
    })

    const el = ref(null)

    let x, y, data, dots;

    function draw(domain) {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove()

        if (data.length === 0) return

        x = d3.scaleTime()
            .domain(domain)
            .range([5, props.width-5])

        y = d3.scaleLinear()
            .domain([0, 100])
            .range([props.height-5, 5])

        const path = d3.line()
            // .curve(d3.curveNatural)
            .x(d => x(d.x))
            .y(d => y(d.y))

        const bg = d3.color(props.color)
        bg.opacity = 0.05

        svg.style("background-color", bg.formatRgb())
        if (data.length > 1) {
            svg.append("path")
                .attr("d", path(data))
                .attr("stroke", props.color)
                .attr("stroke-width", 2)
                .attr("fill", "none")
        }

        dots = svg.selectAll(".dot")
            .data(data.filter(d => d.total > 0))
            .join("circle")
            .classed("dot", true)
            .attr("cx", d => x(d.x))
            .attr("cy", d => y(d.y))
            .attr("r", 3)
            .attr("stroke", "none")
            .attr("fill", props.color)
    }

    function onMove(event) {
        if (data.length === 0) return
        const [mx, _] = d3.pointer(event)
        const [bx, by] = d3.pointer(event, document.body)
        const mouseTime = x.invert(mx).valueOf()

        let dp = null;
        let dist = Number.MAX_VALUE

        data.forEach(d => {
            if (d.total > 0) {
                const diff = Math.abs(mouseTime - d.x.valueOf())
                if (diff < dist) {
                    dist = diff;
                    dp = d
                }
            }
        });

        if (dp !== null) {
            const time = DateTime.fromJSDate(dp.x)
            tt.show(
                `${time.toRelative()}</br>${dp.y.toFixed(2)}% (${dp.wins} / ${dp.total})`,
                bx,
                by-10
            )
            dots
                .attr("fill", d => d.id === dp.id ? "red" : props.color)
                .attr("r", d => d.id === dp.id ? 4 : 3)
        } else {
            onLeave()
        }
    }
    function onLeave() {
        if (data.length === 0) return
        tt.hide()
        dots
            .attr("fill", props.color)
            .attr("r", 3)
    }

    function read(calculate=false) {
        let tmp, binned, domain;

        if (!calculate && DM.hasData(props.source+"_extent")) {
            domain = DM.getData(props.source+"_extent", false)
            tmp = DM.getDataBy(props.source, d => d[props.idAttr] === props.id)

            binned = d3.bin()
                .thresholds(5)
                .domain(domain)
                .value(d => d.created)
                (tmp)

        } else {

            const all = DM.getData(props.source, false)
            if (all.length === 0) {
                data = []
                return draw()
            }

            domain = d3.extent(all, d => d.created)
            tmp = all.filter(d => d[props.idAttr] === props.id)

            binned = d3.bin()
                .thresholds(5)
                .domain(domain)
                .value(d => d.created)
                (tmp)

            DM.setData(props.source+"_extent", domain)
        }

        data = []

        const count = Math.max(1, tmp.length)
        let lastWinrate = 0, idx = 0, wins = 0;

        binned.forEach(d => {
            if (d.length > 0) {
                wins = d.reduce((acc, dd) => acc + dd.win, 0)
                lastWinrate = Math.round((wins / count) * 100)
            } else {
                wins = 0
            }
            if (d.length > 0 || data.length > 0) {
                data.push({
                    id: idx++,
                    x: new Date(d.x0),
                    y: lastWinrate,
                    total: d.length,
                    wins: wins
                })
            }
        })

        // if (data.length === 1) {
        //     data.push({
        //         id: idx++,
        //         x: new Date(binned.at(-1).x1),
        //         y: lastWinrate,
        //         total: 0,
        //         wins: 0
        //     })
        // }

        draw(domain)
    }

    onMounted(read)

    watch(() => props, read, { deep: true })
    watch(() => times.game_scores, () => read(true))
</script>