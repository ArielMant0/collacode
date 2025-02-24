<template>
    <div class="d-flex">
        <div style="text-align: center;">
            <div v-if="title"><b>{{ title }}</b></div>
            <svg ref="el" :width="width" :height="height"></svg>
        </div>
        <ColorLegend v-if="colorLegend" :style="{ 'margin-top': title ? '1.5em' : 0}"
            :colors="colorVals"
            :ticks="colorTicks"
            vertical
            hide-domain
            :size="colorVals.length*25"
            :rect-size="25"/>
    </div>
</template>

<script setup>

    import * as d3 from 'd3'
    import { ref, watch, onMounted, computed } from 'vue'
    import DM from '@/use/data-manager';
    import ColorLegend from './ColorLegend.vue';
    import { useSettings } from '@/store/settings';
    import { useTooltip } from '@/store/tooltip';

    const el = ref(null);
    const settings = useSettings()
    const tt = useTooltip()

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        xDomain: { type: Array },
        yDomain: { type: Array },
        selected: {
            type: Array,
            default: () => ([])
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
        yAttrs: {
            type: Array,
            required: true
        },
        colorScale: {
            type: [String, Array],
            default: "schemePaired"
        },
        title: {
            type: String,
        },
        clickable: {
            type: Boolean,
            default: false
        },
        rotateLabels: {
            type: Boolean,
            default: false
        },
        vertical: {
            type: Boolean,
            default: false
        },
        colorLegend: {
            type: Boolean,
            default: false
        },
        padding: {
            type: Number,
            default: 75
        }
    });

    const emit = defineEmits(["click-bar", "click-label", "right-click-label", "right-click-bar"])

    let ticks, rects, domain;

    const colorVals = ref([])
    const colorTicks = ref([])

    const xSize = computed(() => props.vertical ? props.height : props.width)
    const ySize = computed(() => props.vertical ? props.width : props.height)
    const altColor = computed(() => settings.lightMode ? "black" : "white")

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
            .range(props.vertical ? [5, xSize.value-25] : [25, xSize.value-5])
            .padding(0.1)

        const y =  d3.scaleLinear()
            .domain(props.yDomain ? props.yDomain : [0, d3.max(props.data, d => d3.sum(props.yAttrs, attr => d[attr]))])
            .range(props.vertical ? [props.padding, ySize.value-10] : [ySize.value-props.padding, 5])

        const color = d3.scaleOrdinal(typeof props.colorScale === "string" ? d3[props.colorScale] : props.colorScale)
            .domain(props.yAttrs)

        colorTicks.value = color.domain()
        colorVals.value = colorTicks.value.map(color)

        rects = svg.append("g")
            .selectAll("g")
            .data(props.data)
            .join("g")
            .attr("transform", d => props.vertical ?
                `translate(0,${x(d[props.xAttr])})` :
                `translate(${x(d[props.xAttr])},0)`
            )
            .selectAll("rect")
            .data(d => {
                let sum = 0;
                return props.yAttrs.map(attr => {
                    const hasRange = Array.isArray(props.xDomain[0])
                    const obj = {
                        x: d[props.xAttr],
                        key: attr,
                        value: d[attr],
                        before: sum,
                        range: [
                            d[props.xAttr],
                            hasRange ?
                                props.xDomain.find(dd => dd[0] == d[props.xAttr])[1] :
                                d[props.xAttr]
                        ]
                    }
                    sum += d[attr]
                    return obj
                })
            })
            .join("rect")
            .attr("fill", d => color(d.key))
            .attr("x", d => props.vertical ? y(d.before) : 0)
            .attr("y", d => props.vertical ? 0 : y(d.before+d.value))
            .attr("width", d => props.vertical ? Math.abs(y(d.value+d.before)-y(d.before)) : x.bandwidth())
            .attr("height", d => props.vertical ? x.bandwidth() : Math.abs(y(d.before) - y(d.value+d.before)))
            .on("pointermove", function(event, d) {
                if (props.clickable) {
                    d3.select(this).attr("fill", altColor.value)
                }
                const [mx, my] = d3.pointer(event, document.body)
                const num = Number.isInteger(d.value) ? d.value : d.value.toFixed(2)
                tt.show(`${d[props.xAttr]} → ${d.key}: ${num}`, mx, my)
            })
            .on("pointerleave", function(_, d) {
                if (props.clickable) {
                    d3.select(this).attr("fill", color(d.key))
                }
                tt.hide()
            })

        if (props.clickable) {
            rects
                .style("cursor", "pointer")
                .on("click", (_, d) => emit("click-bar", d))
                .on("contextmenu", (event, d) => {
                    event.preventDefault();
                    emit("right-click-bar", d, event)
                })
        }

        if (props.vertical) {
            ticks = svg.append("g")
                .attr("transform", `translate(${props.padding},0)`)
                .call(d3.axisLeft(x).tickFormat(d => getLabel(d)))
                .selectAll(".tick text")
        } else {
            ticks = svg.append("g")
                .attr("transform", `translate(0,${props.height-props.padding})`)
                .call(d3.axisBottom(x).tickFormat(d => getLabel(d)))
                .selectAll(".tick text")
        }

        if (props.selected.length > 0) {
            ticks.style("font-weight", d => props.selected.includes(d) ? "bold" : null)
        }

        if (props.rotateLabels || agg) {
            ticks
                .attr("text-anchor", "start")
                .attr("transform", "rotate(55)")
        }

        if (props.clickable) {
            ticks
                .style("cursor", "pointer")
                .on("click", (_, d) => emit("click-label", d))
                .on("contextmenu", (event, d) => {
                    event.preventDefault();
                    emit("right-click-label", d, event)
                })
                .on("pointerenter", function() { d3.select(this).attr("font-weight", "bold") })
                .on("pointerleave", function(_, d) {
                    const tags = DM.getSelectedIds("tags")
                    if (!tags.has(+d)) {
                        d3.select(this).attr("font-weight", null)
                    }
                })
        }

        if (props.vertical) {
            svg.append("g")
                .attr("transform", `translate(0,${props.height-25})`)
                .call(d3.axisBottom(y).ticks(Math.max(3, Math.round((props.width-props.padding) / 30))))
        } else {
            svg.append("g")
                .attr("transform", `translate(25,0)`)
                .call(d3.axisLeft(y).ticks(Math.max(3, Math.round((props.height-props.padding) / 30))))
        }

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
