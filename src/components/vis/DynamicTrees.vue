<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTooltip } from '@/store/tooltip';
    import { onMounted, ref, watch } from 'vue';

    const tt = useTooltip()

    const props = defineProps({
        dataLeft: {
            type: Array,
            required: true
        },
        dataRight: {
            type: Array,
            required: true
        },
        dataCenter: {
            type: Array,
            required: true
        },
        maxValue: {
            type: Number,
            required: false
        },
        colorScale: {
            type: [String, Array, Function],
            default: "interpolateCool"
        },
        nameAttr: {
            type: String,
            default: "name"
        },
        valueAttr: {
            type: String,
            default: "value"
        },
        colorAttr: {
            type: String,
            default: "color"
        },
        width: {
            type: Number,
            default: 1400
        },
        height: {
            type: Number,
            default: 300
        },
        textSize: {
            type: Number,
            default: 25
        },
        highlight: {
            type: Boolean,
            default: false
        },
        reverse: {
            type: Boolean,
            default: false
        }
    })

    const el = ref(null)

    const value = d => d[props.valueAttr]
    const name = d => d[props.nameAttr]
    const color = d => d[props.colorAttr]

    const linkMap = new Map()

    let rl, rr, links;

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove()
        linkMap.clear()

        const size = Math.floor((props.height - props.textSize * 2) / 3);

        const maxDepthLeft = d3.max(props.dataLeft, d => value(d))
        const maxDepthRight =  d3.max(props.dataRight, d => value(d))

        const y = d3.scaleLinear()
            .domain([0, Math.max(maxDepthLeft, maxDepthRight)+1])
            .range(props.reverse ? [size, 0] : [0, size])

        const xl = d3.scaleBand()
            .domain(props.dataLeft.map(name))
            .range([5, props.width-50])
            .padding(0.05)

        const xr = d3.scaleBand()
            .domain(props.dataRight.map(name))
            .range([5, props.width-50])
            .padding(0.05)

        let colDomain;
        switch(typeof props.colorScale) {
            default:
            case 'string':
                colDomain = d3[props.colorScale]
                break;
            case 'object':
                colDomain = props.colorScale
                break;
            case 'function':
                colDomain = props.colorScale(d3)
                break;
        }

        const colScale = d3.scaleSequential(colDomain)
            .domain([
                Math.min(d3.min(props.dataLeft, d => color(d)), d3.min(props.dataRight, d => color(d))),
                props.maxValue ? props.maxValue : Math.max(d3.max(props.dataLeft, d => color(d)), d3.max(props.dataRight, d => color(d)))
            ])

        const path = d3.line()
            .curve(d3.curveBumpY)

        // draw connections
        links = svg.append("g")
            .attr("stroke", "black")
            .attr("fill", "none")
            .attr("opacity", 0.5)
            .selectAll("path")
            .data(props.dataCenter
                .map(d => {
                    const l = props.dataLeft.find(dd => dd.id === d.source)
                    const r = props.dataRight.find(dd => dd.id === d.target)
                    if (l && r) {
                        linkMap.set(l.id, d)
                        linkMap.set(r.id, d)
                        return {
                            id: d.id,
                            source: name(l),
                            sourceValue: value(l),
                            target: name(r),
                            targetValue: value(r),
                            changes: d.changes
                        }
                    }
                    return null
                })
                .filter(d => d !== null && d.changes)
            )
            .join("path")
            .attr("opacity", 0.25)
            .attr("d", d => path([
                [xl(d.source) + xl.bandwidth()*0.5, props.textSize + y(d.sourceValue)],
                [xr(d.target) + xr.bandwidth()*0.5, props.height - props.textSize - y(d.targetValue)],
            ]))

        // draw bars on the left
        rl = svg.append("g")
            .selectAll("rect")
            .data(props.dataLeft)
            .join("rect")
            .attr("x", d => xl(name(d)))
            .attr("y", props.textSize)
            .attr("width", xl.bandwidth())
            .attr("height", d => y(value(d)))
            .attr("fill", d => d.is_leaf === 1 ? colScale(color(d)) : 0)
            .on("pointerenter", (event, d) => {
                if (linkMap.has(d.id)) {
                    const c = linkMap.get(d.id)
                    const r = props.dataRight.find(dd => dd.id === c.target)
                    if (r) {
                        tt.show(`${name(d)} (${color(d)}) -> ${name(r)} (${color(r)})`, event.pageX+10, event.pageY)
                        hover(d.id, r.id)
                    } else {
                        tt.show(`${name(d)} (${color(d)})`, event.pageX+10, event.pageY)
                        hover(d.id, null)
                    }
                } else {
                    tt.show(`${name(d)} (${color(d)})`, event.pageX+10, event.pageY)
                    hover(d.id)
                }
            })
            .on("pointerleave", () => {
                tt.hide()
                hover();
            })

        // draw bars on the right
        rr = svg.append("g")
            .selectAll("rect")
            .data(props.dataRight)
            .join("rect")
            .attr("x", d => xr(name(d)))
            .attr("y", d => props.height - props.textSize - y(value(d)))
            .attr("width", xr.bandwidth())
            .attr("height", d => y(value(d)))
            .attr("fill", d => d.is_leaf === 1 ? colScale(color(d)) : 0)
            .on("pointerenter", (event, d) => {
                if (linkMap.has(d.id)) {
                    const c = linkMap.get(d.id)
                    const r = props.dataLeft.find(dd => dd.id === c.source)
                    if (r) {
                        tt.show(`${name(d)} (${color(d)}) -> ${name(r)} (${color(r)})`, event.pageX+10, event.pageY)
                        hover(r.id, d.id)
                    } else {
                        tt.show(`${name(d)} (${color(d)})`, event.pageX+10, event.pageY)
                        hover(null, d.id)
                    }
                } else {
                    tt.show(`${name(d)} (${color(d)})`, event.pageX+10, event.pageY)
                    hover(null, d.id)
                }
            })
            .on("pointerleave", () => {
                tt.hide()
                hover();
            })

        if (maxDepthLeft > 3) {
            const tmp = svg.append("g")
                .attr("transform", `translate(0,${props.textSize})`)
                .call(d3.axisTop(xl).tickValues(props.dataLeft.filter(d => value(d) == 1).map(d => name(d))))

            tmp.select(".domain").remove()
            tmp.select(".tick text")
                .attr("text-anchor", "start")
        }

        if (maxDepthRight > 3) {
            const tmp = svg.append("g")
                .attr("transform", `translate(0,${props.height - props.textSize})`)
                .call(d3.axisBottom(xr).tickValues(props.dataRight.filter(d => value(d) == 1).map(d => name(d))))

            tmp.select(".domain").remove()
            tmp.select(".tick text")
                .attr("text-anchor", "start")
        }

        svg.append("text")
            .attr("font-size", 10)
            .attr("x", props.width-45)
            .attr("y", props.textSize+15)
            .text(`${props.dataLeft.length} tags`)

        svg.append("text")
            .attr("font-size", 10)
            .attr("x", props.width-45)
            .attr("y", props.height-props.textSize-10)
            .text(`${props.dataRight.length} tags`)

        highlight()
    }

    function hover(left=null, right=null) {
        const conns = left !== null || right !== null ?
            props.dataCenter.filter(d => d.source === left || d.target === right) :
            []

        rl.attr("stroke", d => left !== null && d.id === left ? "black" : "none")
        rr.attr("stroke", d => right !== null && d.id === right ? "black" : "none")

        const cSet = new Set(conns.map(d => d.id))
        links
            .attr("stroke-width", d => cSet.has(d.id) ? 3 : 1)
            .attr("opacity", d => cSet.has(d.id) ? 1 : 0.25)
    }

    function highlight() {
        rl.attr("opacity", d => props.highlight && linkMap.has(d.id) ? 0.25 : 1)
        rr.attr("opacity", d => props.highlight && linkMap.has(d.id) ? 0.25 : 1)
    }

    onMounted(draw)

    watch(props, function(now, old) {
        if (now.highlight !== old.highlight) {
            highlight()
        } else {
            draw()
        }
    }, { deep: true })
</script>