<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useSettings } from '@/store/settings';
    import { computed, onMounted } from 'vue';
    import { useTooltip } from '@/store/tooltip';
    import { storeToRefs } from 'pinia';

    const tt = useTooltip()
    const settings = useSettings()

    const { lightMode } = storeToRefs(settings)

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        dimensions: {
            type: Array,
            required: true
        },
        options: {
            type: Object,
            required: true
        },
        selected: {
            type: Array,
            default: () => ([])
        },
        selectedColor: {
            type: String,
            default: "red"
        },
        highlight: {
            type: Number,
            default: -1
        },
        highlightColor: {
            type: String,
            default: "#0ad39f"
        },
        valueAttr: {
            type: String,
            required: false
        },
        colorType: {
            type: String,
            default: "ordinal"
        },
        colorDomain: {
            type: Array,
        },
        colorScale: {
            type: [String, Function, Array],
            default: "schemeCategory10"
        },
        width: {
            type: Number,
            default: 300
        },
        height: {
            type: Number,
            default: 150
        },
        binary: {
            type: Boolean,
            default: false
        },
        showLabels: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["hover", "click", "right-click", "click-label", "right-click-label"])

    const el = ref(null)

    const binYes = computed(() => lightMode.value ? "#222" : "#eee")
    const binNo = computed(() => lightMode.value ? "#eee" : "#222")

    let color;

    const getV = d => props.valueAttr ? d[props.valueAttr] : 0

    function has(id) { return props.data.find(d => d.cat_id === id) }

    function getStroke(d, selection) {
        if (props.highlight === d.id) {
            return props.highlightColor
        }
        if (selection.has(d.id)) {
            return props.selectedColor
        }

        let tmp = color(d.value)
        if (props.binary) {
            tmp = has(d.id) ? binYes.value : binNo.value
        }

        const c = d3.color(tmp)
        return lightMode.value ? c.darker(0.5) : c.brighter(0.5)
    }

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove()

        const dims = props.dimensions.slice()
        dims.sort((a, b) => settings.extCatOrder.indexOf(a)-settings.extCatOrder.indexOf(b))

        const h = props.showLabels ? 100 : 5

        const options = {}
        for (const dim in props.options) {
            options[dim] = props.options[dim].map(d => Object.assign({}, d))
            options[dim].forEach(d => {
                const it = props.data.find(dd => dd.cat_id === d.id)
                d.value = it ? getV(it) : 0
            })
            options[dim].sort((a, b) => settings.getExtCatValueOrder(dim, a.name, b.name))
        }

        const x = d3.scaleBand()
            .domain(dims)
            .range([5, props.width-5])
            .paddingInner(props.width < 200 ? 0 : 0.1)

        const bands = {}
        dims.forEach(dim => {
            bands[dim] = d3.scaleBand()
                .domain(options[dim].map(d => d.name))
                .range([5, props.height-h])
                .paddingInner(props.height-h < 200 ? 0 : 0.1)
        })

        let colscale;
        switch (typeof props.colorScale) {
            case 'string':
                colscale = d3[props.colorScale]
                break;
            case 'object':
                if (Array.isArray(props.colorScale)) {
                    colscale = props.colorScale
                }
                break;
            case 'function':
                colscale = props.colorScale;
                break;
        }

        switch (props.colorType) {
            default:
            case "ordinal":
                color = d3.scaleOrdinal(colscale)
                    .domain(dims)
                    .unknown("#333")
                break;
            case "sequential":
                color = d3.scaleSequential(colscale)
                    .domain(props.colorDomain ? props.colorDomain : d3.extent(props.data, getV))
                break;
            case "diverging":
                color = d3.scaleDiverging(colscale)
                    .domain(props.colorDomain ?
                        props.colorDomain :
                        [d3.min(props.data, getV), 0, d3.max(props.data, getV)])
                break;

        }

        const sel = new Set(props.selected)

        dims.forEach(dim => {
            svg.append("g")
                .attr("transform", `translate(${x(dim)},0)`)
                .selectAll("rect")
                .data(options[dim])
                .join("rect")
                .style("cursor", "pointer")
                .attr("x", 1)
                .attr("y", d => bands[dim](d.name)+1)
                .attr("width", x.bandwidth()-2)
                .attr("height", bands[dim].bandwidth()-2)
                .attr("fill", d => props.binary ? (has(d.id) ? binYes.value : binNo.value) : color(d.value))
                .attr("stroke-width", d => props.highlight === d.id || sel.has(d.id) ? 2 : 1)
                .attr("stroke", d => getStroke(d, sel))
                .on("pointermove", function(event, d) {
                    // show tooltip
                    const [mx, my] = d3.pointer(event, document.body)
                    if (props.valueAttr) {
                        const num = getV(d).toFixed(Number.isInteger(getV(d)) ? 0 : 2)
                        tt.show(`${dim} → ${d.name} (${num})`, mx, my)
                    } else {
                        tt.show(`${dim} → ${d.name}`, mx, my)
                    }

                    // style rect
                    d3.select(this)
                        .attr("stroke", props.highlightColor)
                        .attr("stroke-width", 2)

                    // emit event to parent
                    emit("hover", d, event)
                })
                .on("pointerleave", function(event, d) {
                    // hide tooltip
                    tt.hide()

                    // style rect
                    d3.select(this)
                        .attr("stroke", getStroke(d, sel))
                        .attr("stroke-width", props.highlight === d.id || sel.has(d.id) ? 2 : 1)

                    // emit event to parent
                    emit("hover", null, event)
                })
                .on("click", (event, d) => emit("click", d, event))
                .on("contextmenu", (event, d) => {
                    event.preventDefault()
                    emit("right-click", d, event)
                })
        })

        if (props.showLabels) {
            svg.append("g")
                .attr("font-size", 10)
                .selectAll(".label")
                .data(dims)
                .join("text")
                .classed("label", true)
                .attr("text-anchor", "start")
                .attr("transform", d => `translate(${x(d) + x.bandwidth()*0.5 - 5},${props.height-h+8}) rotate(55)`)
                .text(d => d)
                .attr("fill", "currentColor")
                .on("pointerenter", function() { d3.select(this).style("font-weight", "bold") })
                .on("pointerleave", function() { d3.select(this).style("font-weight", null) })
                .style("cursor", "pointer")
                .on("click", (event, d) => emit("click-label", d, event))
                .on("contextmenu", (event, d) => {
                    event.preventDefault()
                    emit("right-click-label", d, event)
                })
        }

        svg.on("pointerleave", function(event) {
            // hide tooltip
            tt.hide()
            // emit event to parent
            emit("hover", null, event)
        })
    }

    function updateColors() {
        if (!color) return

        const svg = d3.select(el.value)
        const sel = new Set(props.selected)

        svg.selectAll("rect")
            .attr("fill", d => props.binary ? (has(d.id) ? binYes.value : binNo.value) : color(d.value))
            .attr("stroke-width", d => props.highlight === d.id || sel.has(d.id) ? 2 : 1)
            .attr("stroke", d => getStroke(d, sel))
    }

    onMounted(draw)

    watch(() => {
        const obj = Object.assign({}, props)
        delete obj.selected
        delete obj.selectedColor
        delete obj.highlight
        delete obj.highlightColor
        return obj
    }, draw, { deep: true })

    watch(() => ({
        selected: props.selected,
        selectedColor: props.selectedColor,
        highlight: props.highlight,
        highlightColor: props.highlightColor,
        lightMode: lightMode.value
    }), updateColors, { deep: true })

</script>
