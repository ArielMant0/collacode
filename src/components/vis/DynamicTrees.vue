<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTooltip } from '@/store/tooltip';
    import { computed, onMounted, ref, watch } from 'vue';
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
            default: "interpolatePlasma"
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
        drawLeft: {
            type: Number,
            default: -1
        },
        drawRight: {
            type: Number,
            default: -1
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
        },
        clickableCenter: {
            type: Boolean,
            default: false
        }
    })

    const emit = defineEmits(["click", "right-click", "click-link", "right-click-link"])

    const el = ref(null)

    const value = d => d[props.valueAttr]
    const name = d => d[props.nameAttr]
    const color = d => d[props.colorAttr]

    const linkMap = new Map()
    const linksVisible = new Set()

    let rl, rr, xl, xr, y, dots;
    let links, tmpLinks, colScale;

    const shouldDrawLink = computed(() => props.drawLeft >= 0 || props.drawRight >= 0)

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
            .attr("stroke-width", 2)
            .attr("d", d => path([
                [xl(d.source) + xl.bandwidth()*0.5, props.textSize + y(d.sourceValue)],
                [xr(d.target) + xr.bandwidth()*0.5, props.height - props.textSize - y(d.targetValue)],
            ]))
            .on("click", function(_, d) {
                if (props.clickableCenter) {
                    emit("click-link", { id: d.id, old_tag: d.s, new_tag: d.t })
                }
            })
            .style("cursor", props.clickableCenter ? "pointer" : "default")
            .on("pointerenter", function(event, d) {
                // d3.select(this).raise()
                const l = props.dataLeft.filter(dd => dd.id === d.s)
                const r = props.dataRight.filter(dd => dd.id === d.t)
                const strC = d.changes ? d.changes + "</br>" : ""
                const strL = l
                    .map(dd => `${name(dd)} (${color(dd)})`)
                    .join("</br>")
                const strR = r
                    .map(dd => `-> ${name(dd)} (${color(dd)})`)
                    .join("</br>")
                tt.show(`${strC}${strL}</br>${strR}`, event.pageX+10, event.pageY)
                hover(l[0].id, r[0].id)
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
                    const cs = linkMap.get(d.id).filter(l => l.source === d.id)
                    let changes = cs.map(l => l.changes).filter(d => d && d.length > 0)
                    if (changes.length > 0) {
                        const counts =  new Map();
                        changes.forEach(c => counts.set(c, (counts.get(c) || 0)+1))
                        changes = ""
                        counts.forEach((v, k) => changes += `${k} (x${v})`)
                        changes += "</br><hr class='mt-1 mb-1'>"
                    }
                    const str = cs
                        .map(l => `-> ${name(getRight(l.target))} (${color(getRight(l.target))})`)
                        .join("</br>")

                    tt.show(`${changes}${name(d)} (${color(d)})</br>${str}`, event.pageX+10, event.pageY)
                } else {
                    tt.show(`${name(d)} (${color(d)})`, event.pageX+10, event.pageY)
                }
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
                    const cs = linkMap.get(d.id).filter(l => l.target === d.id)
                    let changes = cs.map(l => l.changes).filter(d => d && d.length > 0)
                    if (changes.length > 0) {
                        const counts =  new Map();
                        changes.forEach(c => counts.set(c, (counts.get(c) || 0)+1))
                        changes = ""
                        counts.forEach((v, k) => changes += `${k} (x${v})`)
                        changes += "</br><hr class='mt-1 mb-1'>"
                    }
                    const str = cs
                        .map(l => `${name(getLeft(l.source))} (${color(getLeft(l.source))})`)
                        .join("</br>")

                    tt.show(`${changes}${str}</br>-> ${name(d)} (${color(d)})`, event.pageX+10, event.pageY)
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
        drawTmpLink()
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
            .attr("stroke-width", 3)
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
                visible = d.changes.length > 0;
                break;
            case "same":
                visible = d.changes.length === 0;
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
        const col = settings.lightMode ? "black" : "#dedede"
        const tags1 = DM.getSelectedIds("tags_old")
        const tags2 = DM.getSelectedIds("tags")

        const selected = d => tags1 && tags1.has(d.s) || tags2 && tags2.has(d.t)

        switch (props.highlightMode) {
            case "":
                rl.attr("opacity", 1)
                rr.attr("opacity", 1)
                links.attr("opacity", d => selected(d) ? 1 : 0.25).attr("stroke", col)
                break;
            case "changes":
                rl.attr("opacity", d => d.changes.length > 0 ? 1 : 0.25)
                rr.attr("opacity", d => d.changes.length > 0 ? 1 : 0.25)
                links
                    .attr("opacity", d => d.changes.length > 0 || selected(d) ? 1 : 0.1)
                    .attr("stroke", d => d.changes.length > 0 ? "red" : col)
                break;
            case "same":
                rl.attr("opacity", d => d.changes.length > 0 ? 0.25 : 1)
                rr.attr("opacity", d => d.changes.length > 0 ? 0.25 : 1)
                links
                    .attr("opacity", d => d.changes.length === 0 || selected(d) ? 1 : 0.1)
                    .attr("stroke", d => d.changes.length === 0 ? "red" : col)
                break;
            case "new":
                rl.attr("opacity", 0.25)
                rr.attr("opacity", d => d.changes !== "new" ? 0.25 : 1)
                links.attr("opacity", 0.1).attr("stroke", col)
                break;
            case "deleted":
                rl.attr("opacity", d => d.changes !== "deleted" ? 0.25 : 1)
                rr.attr("opacity", 0.25)
                links.attr("opacity", 0.1).attr("stroke", col)
                break;
            default:
                rl.attr("opacity", d => d.changes === props.highlightMode ? 1 : 0.25)
                rr.attr("opacity", d => d.changes === props.highlightMode ? 1 : 0.25)
                links
                    .attr("opacity", d => d.changes === props.highlightMode || selected(d) ? 1 : 0.1)
                    .attr("stroke", d => d.changes === props.highlightMode ? "red" : col)
                break;
        }
    }

    function showSelected() {
        const col = settings.lightMode ? "black" : "#dedede"

        let tags1, tags2;

        if (props.codeLeft) {
            tags1 = DM.getSelectedIds("tags_old")
            // draw dots
            if (tags1.size === 0) {
                dots.selectAll(".dot-left").remove()
            } else {
                const r = Math.max(xl.bandwidth() / 2, 2)
                dots.selectAll(".dot-left")
                    .data(props.dataLeft.filter(d => tags1.has(d.id)))
                    .join("circle")
                    .classed("dot-left", true)
                    .attr("cx", d => xl(name(d)) + r)
                    .attr("cy", props.textSize - xl.bandwidth())
                    .attr("r", r)
                    .attr("fill", col)
            }
        }

        if (props.codeRight) {
            tags2 = DM.getSelectedIds("tags")
            // draw dots
            if (tags2.size === 0) {
                dots.selectAll(".dot-right").remove()
            } else {
                const r = Math.max(xr.bandwidth() / 2, 2)
                dots.selectAll(".dot-right")
                    .data(props.dataRight.filter(d => tags2.has(d.id)))
                    .join("circle")
                    .classed("dot-right", true)
                    .attr("cx", d => xr(name(d)) + r)
                    .attr("cy", props.height - props.textSize + xr.bandwidth())
                    .attr("r", r)
                    .attr("fill", col)
            }
        }

        if (!tags1 && !tags2) {
            links.attr("opacity", 0.25)
        } else {
            links.attr("opacity", d => tags1 && tags1.has(d.s) || tags2 && tags2.has(d.t) ? 1 : 0.1)
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

    function drawTmpLink() {
        const svg = d3.select(el.value)
        svg.selectAll(".tmp-link").remove()
        if (!shouldDrawLink.value) return


        if (props.drawLeft >= 0 && props.drawRight < 0) {
            const from = props.dataLeft.find(d => d.id === props.drawLeft)
            if (!from) return console.error("could not find tag on left", props.drawLeft)
            svg.append("line")
                .classed("tmp-link", true)
                .attr("stroke-width", 3)
                .attr("stroke", "black")
                .attr("stroke-dasharray", "4 1")
                .attr("fill", "none")
                .attr("x1", xl(name(from)) + xl.bandwidth()*0.5)
                .attr("x2", xl(name(from)) + xl.bandwidth()*0.5)
                .attr("y1", props.textSize + y(value(from)))
                .attr("y2", props.textSize + y(value(from)) + 25)

        } else if (props.drawLeft < 0 && props.drawRight >= 0) {
            const to = props.dataRight.find(d => d.id === props.drawRight)
            if (!to) return console.error("could not find tag on right", props.drawRight)
            svg.append("line")
                .classed("tmp-link", true)
                .attr("stroke-width", 3)
                .attr("stroke", "black")
                .attr("stroke-dasharray", "4 1")
                .attr("fill", "none")
                .attr("x1", xr(name(to)) + xr.bandwidth()*0.5)
                .attr("x2", xr(name(to)) + xr.bandwidth()*0.5)
                .attr("y1", props.height - props.textSize - y(value(to)))
                .attr("y2", props.height - props.textSize - y(value(to)) - 25)
        } else {
            const path = d3.line().curve(d3.curveBumpY)
            const from = props.dataLeft.find(d => d.id === props.drawLeft)
            const to = props.dataRight.find(d => d.id === props.drawRight)
            if (!from) return console.error("could not find tag on left", props.drawLeft)
            if (!to) return console.error("could not find tag on right", props.drawRight)

            svg.append("path")
                .classed("tmp-link", true)
                .attr("stroke-width", 3)
                .attr("stroke", "black")
                .attr("stroke-dasharray", "4 1")
                .attr("fill", "none")
                .attr("d", path([
                    [xl(name(from)) + xl.bandwidth()*0.5, props.textSize + y(value(from))],
                    [xr(name(to)) + xr.bandwidth()*0.5, props.height - props.textSize - y(value(to))],
                ]))
        }

    }

    onMounted(draw)

    watch(() => settings.focusTime, flash)
    watch(() => settings.lightMode, draw)
    watch(() => Math.max(times.f_tags, times.f_tags_old), showSelected)
    watch(() => ([props.drawLeft, props.drawRight]), drawTmpLink, { deep: true })

    watch(() => props.highlightMode, highlight)

    watch(() => {
        const obj = Object.assign({}, props)
        delete obj.highlightMode
        delete obj.drawLeft
        delete obj.drawRight
        return obj
    }, draw, { deep: true })
</script>