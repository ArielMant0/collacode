<template>
    <div>
        <HeatMatrix v-if="corr.length > 0"
            :data="corr"
            :labels="corrLabels"
            hide-x-labels
            :size="1200"/>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { onMounted, ref, watch } from 'vue';
    import HeatMatrix from '../vis/HeatMatrix.vue';
    import { useTimes } from '@/store/times';

    const times = useTimes()

    const corr = ref([])
    const corrLabels = {}

    let tags;

    function readTags() {
        tags = DM.getDataBy("tags", d => d.is_leaf === 1)
        tags.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return 0
        });
        calcCorrelation()
    }
    function calcCorrelation() {
        const items = DM.getData("items", true)

        const values = {}
        const counts = {}

        tags.forEach(t => {
            counts[t.id] = 0
            values[t.id] = {}
            for (let j = 0; j < tags.length; ++j) {
                values[t.id][tags[j].id] = 0
            }
            corrLabels[t.id] = t.name
        })


        items.forEach(d => {
            for (let i = 0; i < d.allTags.length; ++i) {
                const di = d.allTags[i].id
                counts[di]++
                for (let j = i+1; j < d.allTags.length; ++j) {
                    const dj = d.allTags[j].id
                    values[di][dj]++
                }
            }
        })

        const array = []
        for (let i = 0; i < tags.length; ++i) {
            const t = tags[i]
            for (let j = 0; j < tags.length; ++j) {
                const t2 = tags[j]
                if (values[t.id][t2.id] > 0) {
                    array.push({ source: t.id, target: t2.id, value: values[t.id][t2.id] / counts[t.id] })
                    array.push({ source: t2.id, target: t.id, value: values[t.id][t2.id] / counts[t2.id] })
                }
            }
        }

        corr.value = array;
    }

    onMounted(readTags)

    watch(() => Math.max(times.all, times.tagging, times.tags), readTags)
    watch(() => Math.max(times.datatags, times.f_items), calcCorrelation)

</script>