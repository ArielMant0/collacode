<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTooltip } from '@/store/tooltip';
    import { onMounted, ref, watch } from 'vue';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { useSettings } from '@/store/settings';

    const tt = useTooltip()
    const times = useTimes()
    const settings = useSettings()

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
        linkMode: {
            type: String,
            default: "all"
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
        codeLeft: { type: Number },
        codeRight: { type: Number },
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
        highlightMode: {
            type: String,
            default: ""
        },
        reverse: {
            type: Boolean,
            default: false
        },
        clickableLeft: {
            type: Boolean,
            default: false
        },
        clickableRight: {
            type: Boolean,
            default: false
        }
    })

    const emit = defineEmits(["click", "right-click"])

    const el = ref(null)

    const value = d => d[props.valueAttr]
    const name = d => d[props.nameAttr]
    const color = d => d[props.colorAttr]

    const linkMap = new Map()
    const linksVisible = new Set()

    let rl, rr, xl, xr, y, dots;
    let links, tmpLinks, colScale;

    let connections;

    function getLeft(id) { return props.dataLeft.find(d => d.id === id) }
    function getRight(id) { return props.dataRight.find(d => d.id === id) }

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove()
        linkMap.clear()
        linksVisible.clear()

        const size = Math.floor((props.height - props.textSize * 2) / 3);

        const maxDepthLeft = d3.max(props.dataLeft, d => value(d))
        const maxDepthRight =  d3.max(props.dataRight, d => value(d))

        y = d3.scaleLinear()
            .domain([0, Math.max(maxDepthLeft, maxDepthRight)+1])
            .range(props.reverse ? [size, 0] : [0, size])

        xl = d3.scaleBand()
            .domain(props.dataLeft.map(name))
            .range([5, props.width-50])
            .padding(0.1)

        xr = d3.scaleBand()
            .domain(props.dataRight.map(name))
            .range([5, props.width-50])
            .padding(0.1)

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

        colScale = d3.scaleSequential(colDomain)
            .domain([
                Math.min(d3.min(props.dataLeft, d => color(d)), d3.min(props.dataRight, d => color(d))),
                props.maxValue ? props.maxValue : Math.max(d3.max(props.dataLeft, d => color(d)), d3.max(props.dataRight, d => color(d)))
            ])

        const path = d3.line().curve(d3.curveBumpY)


        connections = props.dataCenter
            .map(d => {
                const l = props.dataLeft.find(dd => dd.id === d.source)
                const r = props.dataRight.find(dd => dd.id === d.target)
                if (l && r) {
                    // store link for left node
                    if (linkMap.has(d.source)) {
                        linkMap.set(d.source, linkMap.get(d.source).concat(d))
                    } else {
                        linkMap.set(d.source, [d])
                    }
                    // store link for right node
                    if (linkMap.has(d.target)) {
                        linkMap.set(d.target, linkMap.get(d.target).concat(d))
                    } else {
                        linkMap.set(d.target, [d])
                    }
                    return {
                        id: d.id,
                        s: d.source,
                        t: d.target,
                        source: name(l),
                        sourceValue: value(l),
                        target: name(r),
                        targetValue: value(r),
                        changes: d.changes
                    }
                }
                return null
            })
            .filter(d => d !== null)

        const col = settings.lightMode ? "black" : "#dedede"
        // draw connections
        links = svg.append("g")
            .attr("stroke", col)
            .attr("fill", "none")
            .attr("opacity", settings.lightMode ? 0.5 : 1)
            .selectAll("path")
            .data(connections.filter(linkVisible))
            .join("path")
            .attr("opacity", 0.25)
            .attr("d", d => path([
                [xl(d.source) + xl.bandwidth()*0.5, props.textSize + y(d.sourceValue)],
                [xr(d.target) + xr.bandwidth()*0.5, props.height - props.textSize - y(d.targetValue)],
            ]))
            .on("pointerenter", (event, d) => {
                const l = props.dataLeft.find(dd => dd.id === d.s)
                const r = props.dataRight.find(dd => dd.id === d.t)
                tt.show(`${name(l)} (${color(l)}) -> ${name(r)} (${color(r)})`, event.pageX+10, event.pageY)
                hover(l.id, r.id)
            })
            .on("pointerleave", () => {
                tt.hide()
                hover();
            })

        tmpLinks = svg.append("g")

        // draw bars on the left
        rl = svg.append("g")
            .selectAll("rect")
            .data(props.dataLeft)
            .join("rect")
            .classed("cursor-pointer", props.clickableLeft)
            .attr("x", d => xl(name(d)))
            .attr("y", props.textSize)
            .attr("width", xl.bandwidth())
            .attr("height", d => y(value(d)))
            .attr("fill", d => d.is_leaf === 1 ? colScale(color(d)) : col)
            .on("pointerenter", (event, d) => {
                if (linkMap.has(d.id)) {
                    const cs = linkMap.get(d.id)
                    const str = cs
                        .filter(l => linksVisible.has(l.id) && l.source === d.id)
                        .map(l => `-> ${name(getRight(l.target))} (${color(getRight(l.target))})`)
                        .join("</br>")

                    tt.show(`${name(d)} (${color(d)})</br>${str}`, event.pageX+10, event.pageY)
                } else {
                    tt.show(`${name(d)} (${color(d)})`, event.pageX+10, event.pageY)
                }
                tt.show(`${name(d)} (${color(d)})`, event.pageX+10, event.pageY)
                hover(d.id)
            })
            .on("pointerleave", () => {
                tt.hide()
                hover();
            })
            .on("click", function(_, d) {
                if (props.clickableLeft) {
                    emit("click", { data: d, side: "left" })
                }
            })
            .on("contextmenu", function(e, d) {
                e.preventDefault();
                if (props.clickableLeft) {
                    emit("right-click", { data: d, side: "left", event: e })
                }
            })

        // draw bars on the right
        rr = svg.append("g")
            .selectAll("rect")
            .data(props.dataRight)
            .join("rect")
            .classed("cursor-pointer", props.clickableRight)
            .attr("x", d => xr(name(d)))
            .attr("y", d => props.height - props.textSize - y(value(d)))
            .attr("width", xr.bandwidth())
            .attr("height", d => y(value(d)))
            .attr("fill", d => d.is_leaf === 1 ? colScale(color(d)) : col)
            .on("pointerenter", (event, d) => {
                if (linkMap.has(d.id)) {
                    const cs = linkMap.get(d.id)
                    const str = cs
                        .filter(l => linksVisible.has(l.id) && l.target === d.id)
                        .map(l => `${name(getLeft(l.source))} (${color(getLeft(l.source))})`)
                        .join("</br>")

                    tt.show(`${str}</br>-> ${name(d)} (${color(d)})`, event.pageX+10, event.pageY)
                } else {
                    tt.show(`${name(d)} (${color(d)})`, event.pageX+10, event.pageY)
                }
                hover(null, d.id)
            })
            .on("pointerleave", () => {
                tt.hide()
                hover();
            })
            .on("click", function(_, d) {
                if (props.clickableRight) {
                    emit("click", { data: d, side: "right" })
                }
            })
            .on("contextmenu", function(e, d) {
                e.preventDefault();
                if (props.clickableRight) {
                    emit("right-click", { data: d, side: "right", event: e })
                }
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

        dots = svg.append("g")

        svg.append("text")
            .attr("fill", "currentColor")
            .attr("font-size", 10)
            .attr("x", props.width-45)
            .attr("y", props.textSize+15)
            .text(`${props.dataLeft.length} tags`)

        svg.append("text")
            .attr("fill", "currentColor")
            .attr("font-size", 10)
            .attr("x", props.width-45)
            .attr("y", props.height-props.textSize-10)
            .text(`${props.dataRight.length} tags`)

        highlight()
        showSelected()
    }

    function hover(left=null, right=null) {
        const conns = left !== null || right !== null ?
            connections.filter(d => d.s === left || d.t === right) :
            []

        rl.attr("stroke", d => left !== null && d.id === left ? "red" : "none")
        rr.attr("stroke", d => right !== null && d.id === right ? "red" : "none")

        const path = d3.line().curve(d3.curveBumpY)
        tmpLinks.selectAll("path")
            .data(conns)
            .join("path")
            .attr("stroke-width", 2)
            .attr("stroke", "red")
            .attr("fill", "none")
            .attr("d", d => path([
                [xl(d.source) + xl.bandwidth()*0.5, props.textSize + y(d.sourceValue)],
                [xr(d.target) + xr.bandwidth()*0.5, props.height - props.textSize - y(d.targetValue)],
            ]))
    }

    function linkVisible(d) {
        let visible;
        switch(props.linkMode) {
            case "changes":
                visible = d.changes;
                break;
            case "same":
                visible = !d.changes;
                break;
            default:
            case "all":
                visible = true;
                break;
        }

        if (visible) {
            linksVisible.add(d.id)
        } else {
            linksVisible.delete(d.id)
        }

        return visible
    }

    function highlight() {
        const isSplit = id => {
            if (!linkMap.has(id)) return false
            const arr = linkMap.get(id);
            return arr.length < 2 ?
                false :
                arr.filter(d => d.source === id).length > 1
        }
        const isMerge = id => {
            if (!linkMap.has(id)) return false
            const arr = linkMap.get(id);
            return arr.length < 2 ?
                false :
                arr.filter(d => d.target === id).length > 1
        }
        const isVisible = id => {
            if (!linkMap.has(id)) return false
            const arr = linkMap.get(id);
            return arr.some(l => linksVisible.has(l.id))
        }
        switch (props.highlightMode) {
            default:
                rl.attr("opacity", 1)
                rr.attr("opacity", 1)
                break;
            case "links":
                rl.attr("opacity", d => isVisible(d.id) ? 1 : 0.25)
                rr.attr("opacity", d => isVisible(d.id) ? 1 : 0.25)
                break;
            case "nolinks":
                rl.attr("opacity", d => !isVisible(d.id) ? 1 : 0.25)
                rr.attr("opacity", d => !isVisible(d.id) ? 1 : 0.25)
                break;
            case "split":
                rl.attr("opacity", d => isSplit(d.id) ? 1 : 0.25)
                rr.attr("opacity", d => isSplit(d.id) ? 1 : 0.25)
                break;
            case "merge":
                rl.attr("opacity", d => isMerge(d.id) ? 1 : 0.25)
                rr.attr("opacity", d => isMerge(d.id) ? 1 : 0.25)
                break;
        }
    }

    function showSelected() {
        const col = settings.lightMode ? "black" : "#dedede"

        if (props.codeLeft) {
            const tags = DM.getSelectedIds("tags_old")
            // draw dots
            if (tags.size === 0) {
                dots.selectAll(".dot-left").remove()
            } else {
                const r = Math.max(xl.bandwidth() / 2, 2)
                dots.selectAll(".dot-left")
                    .data(props.dataLeft.filter(d => tags.has(d.id)))
                    .join("circle")
                    .classed("dot-left", true)
                    .attr("cx", d => xl(name(d)) + r)
                    .attr("cy", props.textSize - xl.bandwidth())
                    .attr("r", r)
                    .attr("fill", col)
            }
        }
        if (props.codeRight) {
            const tags = DM.getSelectedIds("tags")
            // draw dots
            if (tags.size === 0) {
                dots.selectAll(".dot-right").remove()
            } else {
                const r = Math.max(xr.bandwidth() / 2, 2)
                dots.selectAll(".dot-right")
                    .data(props.dataRight.filter(d => tags.has(d.id)))
                    .join("circle")
                    .classed("dot-right", true)
                    .attr("cx", d => xr(name(d)) + r)
                    .attr("cy", props.height - props.textSize + xr.bandwidth())
                    .attr("r", r)
                    .attr("fill", col)
            }
        }
    }

    function flash() {
        if (settings.focusTag) {
            const col = settings.lightMode ? "black" : "#dedede"

            let onRight = true;
            let rect = rr.filter(d => d.id === settings.focusTag)
            if (rect.size() === 0) {
                onRight = false;
                rect = rl.filter(d => d.id === settings.focusTag)
            }

            if (rect.size() > 0) {
                const { y } =  (onRight ? d3.select(el.value) : rect).node().getBoundingClientRect()
                window.scrollTo({ top: Math.max(0, (y+window.scrollY)-100), behavior: "smooth"})

                let cycles = 0;

                rect.interrupt()
                rect
                    .transition()
                    .ease(d3.easeLinear)
                    .on("start", function repeat() {
                        if (cycles >= 3) return;
                        cycles++;
                        d3.active(this)
                            .duration(100)
                            .attr("fill", "red")
                        .transition()
                            .duration(100)
                            .delay(100)
                            .attr("fill", d => d.is_leaf === 1 ? colScale(color(d)) : col)
                        .transition()
                            .delay(200)
                            .on("start", repeat);
                    });
            }
        }
    }

    onMounted(draw)

    watch(() => settings.focusTime, flash)
    watch(() => settings.lightMode, draw)
    watch(() => Math.max(times.f_tags, times.f_tags_old), showSelected)

    watch(() => props.highlightMode, highlight)

    watch(() => {
        const obj = Object.assign({}, props)
        delete obj.highlightMode
        return obj
    }, draw, { deep: true })
</script>