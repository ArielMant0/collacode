<template>
    <div class="d-flex justify-center">
        <div v-for="(d, i) in dims" :key="d">
            <StackedBarChart v-if="data[d]"
                :data="data[d]"
                :x-domain="domains[d]"
                :width="padding[d]+140"
                :height="400"
                :y-domain="[0,maxValue]"
                x-attr="x"
                vertical
                :title="d"
                :padding="padding[d]"
                :color-legend="i === dims.length-1"
                :color-scale="'schemeObservable10'"
                :y-attrs="['single', 'double', 'multiple']"/>
        </div>
    </div>
</template>

<script setup>
    import { useSettings } from '@/store/settings';
    import DM from '@/use/data-manager';
    import { group, max } from 'd3';
    import { onMounted, reactive } from 'vue';
    import StackedBarChart from '../vis/StackedBarChart.vue';
    import { useTimes } from '@/store/times';

    const settings = useSettings()
    const times = useTimes()

    const dims = ref([])
    const domains = reactive([])
    const padding = reactive({})
    const data = reactive({})
    const maxValue = ref(0)

    function read() {
        if (!DM.hasData("ext_categories") || !DM.hasData("externalizations")) return setTimeout(read, 150)
        const cats = DM.getData("ext_categories", false)
        const leaves = cats.filter(c => !cats.find(d => d.parent === c.id))
        const parents = new Map()
        leaves.forEach(d => parents.set(d.id, d.parent))

        const requiredIds = group(leaves, d => d.parent)
        const requiredCats = cats.filter(d => requiredIds.has(d.id))
        requiredCats.sort((a, b) => settings.extCatOrder.indexOf(a.name)-settings.extCatOrder.indexOf(b.name))

        const exts = DM.getData("externalizations", false)
        const counts = {}
        requiredCats.forEach(dim => counts[dim.id] = {})
        exts.forEach(e => {
            e.categories.forEach(d => {
                const c = leaves.find(dd => dd.id === d.cat_id)
                if (c) {
                    if (!counts[c.parent][c.id]) counts[c.parent][c.id] = { multiple: 0, double: 0, single: 0 }
                    const num = e.categories.filter(dd => parents.get(dd.cat_id) === c.parent).length
                    const which = num > 1 ? (num > 2 ? "multiple" : "double") : "single"
                    counts[c.parent][c.id][which]++
                }
            })
        });

        maxValue.value = 0;

        requiredCats.forEach(dim => {
            const keys = Object.keys(counts[dim.id])
            keys.sort((a, b) => {
                const an = cats.find(c => c.id == a).name
                const bn = cats.find(c => c.id == b).name
                return settings.getExtCatValueOrder(dim.name, an, bn)
            })

            domains[dim.name] = keys.map(k => cats.find(c => c.id == k).name)
            data[dim.name] = keys.map((k, i) => ({
                x: domains[dim.name][i],
                single: counts[dim.id][k].single,
                double: counts[dim.id][k].double,
                multiple: counts[dim.id][k].multiple
            }))
            padding[dim.name] = Math.max(25, max(domains[dim.name], d => (''+d).length*6))
            maxValue.value = Math.max(maxValue.value, max(data[dim.name], d => d.single+d.double+d.multiple))
        });


        dims.value = requiredCats.map(d => d.name)
    }

    onMounted(read)

    watch(() => Math.max(times.ext_categories, times.externalizations), read)
</script>