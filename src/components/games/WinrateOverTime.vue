<template>
    <svg ref="el" :width="width" :height="height" @pointermove="onMove" @pointerleave="onLeave"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTimes } from '@/store/times'
    import DM from '@/use/data-manager'
    import { onMounted, watch, ref, computed } from 'vue'
    import { DateTime } from 'luxon'
    import { useTooltip } from '@/store/tooltip'
    import { useSettings } from '@/store/settings'
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'

    const app = useApp()
    const times = useTimes()
    const tt = useTooltip()
    const settings = useSettings()

    const { showAllUsers } = storeToRefs(app)

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
        hoverColor: {
            type: String,
            default: "red"
        },
        colorScale: {
            type: [String, Array],
            default: "interpolateRdYlGn"
        },
        curve: {
            type: String,
            default: "curveMonotoneX"
        },
        drawAxisY: {
            type: Boolean,
            default: false
        }
    })

    const el = ref(null)

    const baseColor = computed(() => settings.lightMode ? "black" : "white")

    let x, y, data, dots, domain;

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove()

        if (data.length === 0) return

        const xOffset = props.drawAxisY ? 25 : 0

        x = d3.scaleTime()
            .domain(domain)
            .range([xOffset+5, props.width-5])

        y = d3.scaleLinear()
            .domain([0, 100])
            .range([props.height-5, 5])


        let curve = d3[props.curve]
        if (props.curve.includes("curveCardinal")) {
            curve = curve.tension(0.25)
        }

        const path = d3.line()
            .curve(curve)
            .x(d => x(d.x))
            .y(d => y(d.y))

        const bg = d3.color(baseColor.value)
        bg.opacity = 0.05

        let scale;
        switch(typeof props.colorScale) {
            case 'string':
                scale = d3[props.colorScale]
                break
            case 'object':
                scale = props.colorScale
                break
            case 'function':
                scale = props.colorScale()
                break;
        }
        const colors = d3.scaleSequential(scale)
            .domain([0, 1])

        svg
            .append("rect")
            .attr("x", x.range()[0])
            .attr("y", y.range()[1])
            .attr("width", x.range()[1] - x.range()[0])
            .attr("height", y.range()[0] - y.range()[1])
            .attr("stroke", "none")
            .attr("fill", bg.formatRgb())

        if (props.drawAxisY) {
            const axis = svg.append("g")
                .attr("transform", `translate(${x.range()[0]},0)`)
                .call(d3.axisLeft(y).tickValues([50, 100]))

            axis.selectAll(".domain").remove()
        }

        if (data.length > 1) {
            svg.append("path")
                .attr("d", path(data))
                .attr("stroke", baseColor.value)
                .attr("stroke-width", 2)
                .attr("fill", "none")

            dots = svg.selectAll(".dot")
                .data(data.filter(d => d.total > 0))
                .join("circle")
                .classed("dot", true)
                .attr("cx", d => x(d.x))
                .attr("cy", d => y(d.y))
                .attr("r", 3)
                .attr("stroke", d => {
                    const c = d3.color(colors(d.wins / d.total))
                    return settings.lightMode ? c.darker(2) : c.brighter(2)
                })
                .attr("fill", d => colors(d.wins / d.total))
            }
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
                `${time.toRelative()}</br>${dp.y.toFixed(2)}% total winrate</br>${dp.wins} wins / ${dp.total} games`,
                bx,
                by-10
            )
            dots.attr("r", d => d.id === dp.id ? 4 : 3)
        } else {
            onLeave()
        }
    }
    function onLeave() {
        if (data.length === 0) return
        tt.hide()
        dots.attr("r", 3)
    }

    function read(calculate=false) {
        let tmp, binned;

        if (!calculate && DM.hasData(props.source+"_extent")) {
            domain = DM.getData(props.source+"_extent", false)
            tmp = DM.getDataBy(props.source, d => d[props.idAttr] === props.id && (showAllUsers.value || d.user_id === app.activeUserId))

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
            tmp = all.filter(d => d[props.idAttr] === props.id && (showAllUsers.value || d.user_id === app.activeUserId))

            binned = d3.bin()
                .thresholds(5)
                .domain(domain)
                .value(d => d.created)
                (tmp)

            DM.setData(props.source+"_extent", domain)
        }

        data = []

        let lastWinrate = 0;
        let idx = 0, wins = 0;
        let totalWins = 0, totalItems = 0;

        binned.forEach(d => {
            if (d.length > 0) {
                wins = d.reduce((acc, dd) => acc + dd.win, 0)
                totalWins += wins
                totalItems += d.length
            } else {
                wins = 0
            }

            if (d.length > 0 || data.length > 0) {
                lastWinrate = Math.round((totalWins / Math.max(totalItems, 1)) * 100)
                data.push({
                    id: idx++,
                    x: new Date(d.x0),
                    y: lastWinrate,
                    total: d.length,
                    wins: wins
                })
            }
        })

        if (binned.length > 1) {
            data.push({
                id: idx++,
                x: new Date(binned.at(-1).x1),
                y: lastWinrate,
                total: 0,
                wins: 0
            })
        }

        draw()
    }

    onMounted(read)

    watch(showAllUsers, read)
    watch(() => props, read, { deep: true })
    watch(() => times.game_scores, () => read(true))
    watch(() => settings.lightMode, draw)
</script>