<template>
    <div>
        <div class="d-flex align-center mb-2">
            <v-select v-model="showAttr"
                :items="attributes"
                item-title="title"
                item-value="key"
                label="attribute"
                density="compact"
                class="mr-1"
                hide-spin-buttons
                single-line
                hide-details
                @update:model-value="calcHistogram"/>
            <v-number-input v-model="numBins"
                label="approx. number of bins"
                density="compact"
                control-variant="split"
                class="ml-1"
                :min="3"
                :step="1"
                hide-details
                hide-spin-buttons
                @update:model-value="calcHistogram"/>
        </div>
        <StackedBarChart v-if="data"
            :data="data"
            :x-domain="domain"
            :width="width"
            :height="height"
            :x-labels="labels"
            x-attr="x"
            color-legend
            :color-scale="['#078766', '#0ad39f']"
            :y-attrs="['tagged', 'untagged']"/>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTimes } from '@/store/times';
    import { onMounted, ref, watch } from 'vue';
    import StackedBarChart from '../vis/StackedBarChart.vue';
    import DM from '@/use/data-manager';

    const times = useTimes()

    const props = defineProps({
        attributes: {
            type: Array,
            required: true
        },
        width: {
            type: Number,
            default: 1000
        },
        height: {
            type: Number,
            default: 300
        },
    })

    const showAttr = ref(props.attributes[0].key)
    const data = ref([])
    const domain = ref([])
    const labels = ref(null)

    const numBins = ref (25)

    function calcHistogram() {
        const conf = props.attributes.find(d => d.key === showAttr.value)

        if (conf.aggregate) {
            const sizeNo = DM.getDataBy("items", d => d.allTags.length === 0).length
            const valsYes = DM.getDataBy("items", d => d.allTags.length > 0)
                .map(d => conf.value ? conf.value(d) : d[conf.key])

            const binned = d3.bin().thresholds(numBins.value)(valsYes)
            domain.value = binned.map(d => ([d.x0, d.x1]))
            labels.value = null;
            data.value = binned.map(d => ({ x: d.x0, tagged: d.length, untagged: d.x0 === 0 ? sizeNo : 0 }))
        } else {
            const valsNo = DM.getDataBy("items", d => d.allTags.length === 0)
                .map(d => conf.value ? conf.value(d) : d[conf.key])
                .flat()
            const valsYes = DM.getDataBy("items", d => d.allTags.length > 0)
                .map(d => conf.value ? conf.value(d) : d[conf.key])
                .flat()

            const min = conf.min ? conf.min : Math.min(valsYes.length > 0 ? d3.min(valsYes) : Number.MAX_SAFE_INTEGER, valsNo.length > 0 ? d3.min(valsNo) : Number.MAX_SAFE_INTEGER)
            const max = conf.max ? conf.max : Math.max(valsYes.length > 0 ? d3.max(valsYes) : Number.MIN_SAFE_INTEGER, valsNo.length > 0 ? d3.max(valsNo) : Number.MIN_SAFE_INTEGER)
            domain.value = d3.range(min, max+1)
            labels.value = conf.labels ? conf.labels : null
            const result = []
            const groupedY = d3.group(valsYes.map(d => ({ value: d })), d => d.value)
            groupedY.forEach((array, key) => result.push({ x: +key, tagged: array.length, untagged: 0 }))
            const groupedN = d3.group(valsNo.map(d => ({ value: d })), d => d.value)
            groupedN.forEach((array, key) => {
                const it = result.find(d => d.x === +key)
                if (it) {
                    it.untagged = array.length
                } else {
                    result.push({ x: +key, tagged: 0, untagged: array.length })
                }
            })
            data.value = result
        }
    }

    onMounted(calcHistogram)

    watch(() => Math.max(times.all, times.items), calcHistogram)
    watch(props, calcHistogram, { deep: true })

</script>