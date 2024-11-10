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
        <BarChart v-if="data"
            :data="data"
            :x-domain="domain"
            :width="width"
            :height="height"
            :x-labels="labels"
            x-attr="0" y-attr="1"/>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTimes } from '@/store/times';
    import { onMounted, ref, watch } from 'vue';
    import BarChart from '../vis/BarChart.vue';
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
            const vals = DM.getDataBy("games", d => d.allTags.length > 0)
                .map(d => conf.value ? conf.value(d) : d[conf.key])

            const binned = d3.bin()(vals)
            domain.value = binned.map(d => ([d.x0, d.x1]))
            labels.value = null;
            data.value = binned.map(d => ([d.x0, d.length]))

        } else {
            const vals = DM.getDataBy("games", d => d.allTags.length > 0)
                .map(d => conf.value ? conf.value(d) : d[conf.key])
                .flat()

            const min = conf.min ? conf.min : d3.min(vals)
            const max = conf.max ? conf.max : d3.max(vals)
            domain.value = d3.range(min, max+1)
            labels.value = conf.labels ? conf.labels : null
            const grouped = d3.group(vals.map(d => ({ value: d })), d => d.value)
            const result = []
            grouped.forEach((array, key) => result.push([+key, array.length]))
            data.value = result
        }
    }

    onMounted(calcHistogram)

    watch(() => ([times.all, times.games]), calcHistogram)

</script>