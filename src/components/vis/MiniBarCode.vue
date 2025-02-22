<template>
    <svg ref="el" :width="width" :height="height"></svg>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useSettings } from '@/store/settings';
    import { computed, onMounted } from 'vue';
    import { useTooltip } from '@/store/tooltip';

    const tt = useTooltip()
    const settings = useSettings()

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
        }
    })
    const emit = defineEmits(["click", "right-click"])

    const el = ref(null)

    const binYes = computed(() => settings.lightMode ? "#222" : "#eee")
    const binNo = computed(() => settings.lightMode ? "#eee" : "#222")

    const getV = d => props.valueAttr ? d[props.valueAttr] : 0

    function has(id) { return props.data.find(d => d.cat_id === id) }

    function draw() {
        const svg = d3.select(el.value)
        svg.selectAll("*").remove()

        const dims = props.dimensions.slice()
        dims.sort((a, b) => settings.extCatOrder.indexOf(a)-settings.extCatOrder.indexOf(b))

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
                .range([5, props.height-5])
                .paddingInner(props.height < 200 ? 0 : 0.1)
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

        let color;

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
                .attr("stroke", d => {
                    if (props.binary) {
                        return has(d.id) ? binYes.value : binNo.value
                    }
                    const c = d3.color(color(d.value))
                    return settings.lightMode ? c.darker(0.5) : c.brighter(1)
                })
                .on("pointermove", (event, d) => {
                    const [mx, my] = d3.pointer(event, document.body)
                    if (props.valueAttr) {
                        const num = getV(d).toFixed(Number.isInteger(getV(d)) ? 0 : 2)
                        tt.show(`${dim} → ${d.name} (${num})`, mx, my)
                    } else {
                        tt.show(`${dim} → ${d.name}`, mx, my)
                    }
                })
                .on("pointerleave", _ => tt.hide())
                .on("click", (event, d) => emit("click", d, event))
                .on("contextmenu", (event, d) => {
                    event.preventDefault()
                    emit("right-click", d, event)
                })
        })
    }

    onMounted(draw)

    watch(props, draw, { deep: true })
    watch(() => settings.lightMode, draw)
</script>
