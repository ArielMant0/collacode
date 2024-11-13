<template>
    <div>
        <v-select v-model="showAttr"
            :items="attributes"
            item-title="title"
            item-value="key"
            label="attribute"
            density="compact"
            class="mb-2"
            hide-spin-buttons
            single-line
            hide-details
            @update:model-value="calcHistogram"/>
        <StackedBarChart v-if="data"
            :data="data"
            :x-domain="domain"
            :width="width"
            :height="height"
            :x-labels="labels"
            x-attr="x"
            :y-attrs="['untagged', 'tagged']"/>
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

    function calcHistogram() {
        const conf = props.attributes.find(d => d.key === showAttr.value)

        if (conf.aggregate) {
            const sizeNo = DM.getDataBy("games", d => d.allTags.length === 0).length
            const valsYes = DM.getDataBy("games", d => d.allTags.length > 0)
                .map(d => conf.value ? conf.value(d) : d[conf.key])

            const binned = d3.bin()(valsYes)
            domain.value = binned.map(d => ([d.x0, d.x1]))
            labels.value = null;
            data.value = binned.map(d => ({ x: d.x0, tagged: d.length, untagged: d.x0 === 0 ? sizeNo : 0 }))
        } else {
            const valsNo = DM.getDataBy("games", d => d.allTags.length === 0)
                .map(d => conf.value ? conf.value(d) : d[conf.key])
                .flat()
            const valsYes = DM.getDataBy("games", d => d.allTags.length > 0)
                .map(d => conf.value ? conf.value(d) : d[conf.key])
                .flat()

            const min = conf.min ? conf.min : Math.min(d3.min(valsYes), d3.min(valsNo))
            const max = conf.max ? conf.max : Math.max(d3.max(valsYes), d3.max(valsNo))
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

    watch(() => ([times.all, times.games]), calcHistogram)

</script>