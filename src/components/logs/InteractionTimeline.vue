<template>
    <div ref="wrapper" style="width: 100%; max-width: 100%;">
        <svg ref="el" :width="width" :height="height"></svg>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ACTION_TYPE } from '@/use/log-utils'
    import { computed, onMounted, onUpdated, useTemplateRef, watch } from 'vue'
    import { useTooltip } from '@/store/tooltip'
    import { isVideo, mediaPath } from '@/use/utility'
    import { useElementSize } from '@vueuse/core'
    import { DateTime } from 'luxon'

    const tt = useTooltip()

    const props = defineProps({
        data: { type: Array, required: true },
        xAttr: { type: String, default: "timestamp" },
        actionAttr: { type: String, default: "actionType" },
        height: { type: Number, default: 40 },
    })

    const el = useTemplateRef("el")
    const wrapper = useTemplateRef("wrapper")

    const wSize = useElementSize(wrapper)
    const width = computed(() => Math.max(200, Math.round(wSize.width.value*0.99)))

    let x;

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove()

        x = d3.scaleLinear()
            .domain(d3.extent(props.data, d => d[props.xAttr]))
            .range([5, width.value-5])

        // background
        svg.append("rect")
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", props.width)
            .attr("height", props.height-25)
            .attr("fill", "#efefef")

        const g = svg.append("g")
        drawEventType(g, ACTION_TYPE.DATATAG, d3.schemeAccent[0])
        drawEventType(g, ACTION_TYPE.WARNINGS, d3.schemeAccent[1])
        drawEventType(g, ACTION_TYPE.EVIDENCE, d3.schemeAccent[2])

        const formatter = d => DateTime.fromMillis(d).toFormat("dd.MM - HH:mm")

        svg.append("g")
            .attr("transform", `translate(0,${props.height-25})`)
            .call(d3.axisBottom(x).tickFormat(formatter))
    }

    function drawEventType(g, action, color) {
        const subset = props.data.filter(d => d[props.actionAttr] === action)

        g.selectAll(".rect"+action)
            .data(subset)
            .join("rect")
            .classed(".rect"+action, true)
            .attr("x", d => x(d[props.xAttr])-2)
            .attr("y", 0)
            .attr("width", 4)
            .attr("height", props.height-25)
            .attr("fill", color)
            .on("mouseenter", function(event, d) {
                showTooltip(action, d, event)
                d3.select(this).raise().style("filter", "brightness(0.75)")
            })
            .on("mouseleave", function() {
                tt.hide()
                d3.select(this).style("filter", null)
            })
    }

    function showTooltip(action, datum, event) {
        const [mx, my] = d3.pointer(event, document.body)
        switch(action) {
            case ACTION_TYPE.EVIDENCE: {
                let str = ""
                let itemStr = ""
                const data = Array.isArray(datum.data) ? datum.data : [datum.data]
                data.forEach((d, j) => {
                    itemStr += (j > 0 ? ", " : "") + d.item.name
                    const mp = mediaPath("evidence", d.filepath)
                    const media = isVideo(d.filepath) ?
                        `<video src="${mp}" height="100" width="auto"/>` :
                        `<img src="${mp}" height="100" width="auto"/>`

                    str += `<div><div>${d.description}</div>${media}</div>`
                })
                tt.show(`<div>
                    <div>${datum.action}</div>
                    <div class="text-caption"><b>${itemStr}</b></div>
                    <div class="d-flex flex-wrap text-caption">${str}</div></div>`,
                    mx, my
                )
            }
            break

            case ACTION_TYPE.DATATAG: {
                let str = ""
                let itemStr = ""
                datum.data.forEach((tmp, j) => {
                    itemStr += (j > 0 ? ", " : "") + tmp.item.name
                    tmp.datatags.forEach((d, i) => str += `<span>${i > 0 ? " - " : ""}${d.tag.name}</span>`)
                })

                tt.show(`<div>
                    <div>${datum.action}</div>
                    <div class="text-caption"><b>${itemStr}</b></div>
                    <div class="text-caption">${str}</div>
                </div>`, mx, my)
            }
            break

            case ACTION_TYPE.WARNINGS: {
                let str = ""
                if (datum.data.warnings) {
                    datum.data.warnings.forEach((d, i) => {
                        str += `<span>${i > 0 ? " - " : ""}${d.tag_name}</span>`
                    })
                    const itemStr = datum.data.item ? datum.data.item.name : "??"
                    tt.show(`<div>
                        <div>${datum.action}</div>
                        <div class="text-caption"><b>${itemStr}, ${datum.data.warnings.length} warnings</b></div>
                        <div class="text-caption">${str}</div>
                    </div>`, mx, my)
                } else if (datum.data.enable_warnings) {
                    tt.show(`${datum.action}: ${datum.data.enable_warnings ? 'enabled' : 'disabled'}`, mx, my)
                }
            }
            break
        }
    }

    onMounted(draw)

    onUpdated(draw)

    watch(width, draw)
</script>