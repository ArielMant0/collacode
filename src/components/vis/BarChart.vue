<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>

    import * as d3 from 'd3'
    import { ref, watch, onMounted } from 'vue'
    import DM from '@/use/data-manager';

    const el = ref(null);

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        xDomain: {
            type: Array,
        },
        xLabels: {
            type: Object,
        },
        width: {
            type: Number,
            default: 300
        },
        height: {
            type: Number,
            default: 120
        },
        xAttr: {
            type: String,
            default: "x"
        },
        yAttr: {
            type: String,
            default: "y"
        },
        color: {
            type: String,
            default: "#078766"
        },
        altColor: {
            type: String,
            default: "#0ad39f"
        },
        clickable: {
            type: Boolean,
            default: false
        },
        sort: {
            type: Boolean,
            default: false
        },
        rotateLabels: {
            type: Boolean,
            default: false
        },
    });

    const emit = defineEmits(["click-bar", "click-label"])

    let ticks, rects, domain;

    function draw() {
        const svg = d3.select(el.value);
        svg.selectAll("*").remove();

        if (props.data.length === 0) return;

        let agg = false;
        if (props.xDomain) {
            if (Array.isArray(props.xDomain[0])) {
                domain = props.xDomain.map(d => d[0])
                agg = true;
            } else {
                domain = props.xDomain
            }
        } else {
            domain = d3.extent(props.data, d => d[props.xAttr])
        }

        const x = d3.scaleBand()
            .domain(domain)
            .range([25, props.width-5])
            .padding(0.1)

        const y = d3.scaleLinear()
            .domain([0, d3.max(props.data, d => d[props.yAttr])])
            .range([props.height-75, 5])

        rects = svg.append("g")
            .selectAll("rect")
            .data(props.data)
            .join("rect")
            .attr("fill", props.color)
            .attr("x", d => x(d[props.xAttr]))
            .attr("y", d => y(d[props.yAttr]))
            .attr("width", x.bandwidth())
            .attr("height", d => y(0) - y(d[props.yAttr]))

        rects.append("title")
            .text(d => getLabel(d[props.xAttr]) + ": " + d[props.yAttr])

        if (props.clickable) {
            rects
                .style("cursor", "pointer")
                .on("click", (_, d) => emit("click-bar", d[props.xAttr]))
                .on("pointerenter", function() { d3.select(this).attr("fill", props.altColor) })
                .on("pointerleave", function() { d3.select(this).attr("fill", props.color) })
        }

        ticks = svg.append("g")
            .attr("transform", `translate(0,${props.height-75})`)
            .call(d3.axisBottom(x).tickFormat(d => getLabel(d)))
            .selectAll(".tick text")

        if (props.rotateLabels || agg) {
            ticks
                .attr("text-anchor", "start")
                .attr("transform", "rotate(45)")
        }

        if (props.clickable) {
            ticks
                .style("cursor", "pointer")
                .attr("text-anchor", "start")
                .on("click", (_, d) => emit("click-label", d))
                .on("pointerenter", function() { d3.select(this).attr("font-weight", "bold") })
                .on("pointerleave", function(_, d) {
                    const tags = new Set(DM.getFilter("tags", "id"));
                    if (!tags.has(+d)) {
                        d3.select(this).attr("font-weight", null)
                    }
                })
        }

        svg.append("g")
            .attr("transform", `translate(25,0)`)
            .call(d3.axisLeft(y).ticks(Math.max(3, Math.round(props.height / 30))))

        function getLabel(d, maxLength=-1) {
            if (agg) {
                const match = props.xDomain.find(dd => dd[0] == d)
                return props.xLabels ?
                    `${props.xLabels[d]} - ${props.xLabels[match[1]]}` :
                    `${d} - ${match[1]}`
            }
            return props.xLabels ? props.xLabels[d] : ""+d
            // if (props.xDomain !== undefined) {
            //     return maxLength > 0 && d > maxLength ? d.slice(0, maxLength) + ".." : d
            // }
            // return x.tickFormat(d);
        }
    }


    onMounted(draw);

    watch(props, draw, { deep: true });

</script>
