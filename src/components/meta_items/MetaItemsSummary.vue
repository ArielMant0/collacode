<template>
    <div class="d-flex flex-wrap justify-center">
        <div v-for="(list, c) in data.clusters" style="text-align: center;" class="ml-1 mr-1">

            <div v-if="list.length > 0"
                class="text-caption text-dots"
                :style="{
                    maxWidth: '250px',
                    color: 'white',
                    backgroundColor: settings.getClusterColor(c)
                }">
                <b>{{ c }}</b>
            </div>
            <MiniBarCode v-if="list.length > 0"
                :dimensions="data.dims"
                :options="data.dimOptions"
                :data="list"
                value-attr="value"
                color-type="sequential"
                :color-scale="colScale"
                :color-domain="[0, 1]"
                @click="d => onClick(c, d)"
                :width="250"
                :height="150"/>
        </div>
        <ColorLegend
            :colors="colValues"
            :ticks="colTicks"
            :min-value="0"
            :max-value="1"
            :size="170"
            :every-tick="4"
            hide-domain
            vertical/>
    </div>
</template>

<script setup>
    import { useTimes } from '@/store/times'
    import DM from '@/use/data-manager'
    import { group, interpolateGreys, range, scaleSequential } from 'd3'
    import { onMounted, watch, reactive, computed } from 'vue'
    import MiniBarCode from '../vis/MiniBarCode.vue'
    import { useSettings } from '@/store/settings'
    import ColorLegend from '../vis/ColorLegend.vue'
    import { useApp } from '@/store/app'
import { storeToRefs } from 'pinia'

    const times = useTimes()
    const settings = useSettings()
    const app = useApp()

    const { lightMode } = storeToRefs(settings)

    const maxPerCluster = reactive(new Map())
    const data = reactive({
        dims: [],
        dimOptions: {},
        clusters: {}
    })

    const colScale = computed(() => {
        if (lightMode.value) {
            return interpolateGreys
        }
        return t => interpolateGreys(1-t)
    })
    const colTicks = computed(() => {
        return range(0, 1.05, 0.05).map(d => +d.toFixed(2))
    })
    const colValues = computed(() => {
        const scale = scaleSequential(colScale.value)
        return colTicks.value.map(scale)
    })

    function read() {
        const cats = DM.getData("meta_categories", false)

        const leaves = cats.filter(d => !cats.some(dd => dd.parent === d.id))
        const set = new Set(Array.from(group(leaves, d => d.parent).keys()))
        data.dims = cats.filter(d => set.has(d.id)).map(d => d.name)

        data.dimOptions = {};
        data.dims.forEach(dim => {
            const id = cats.find(d => d.name === dim).id
            data.dimOptions[dim] = cats.filter(d => d.parent === id).map(d => ({ id: d.id, name: d.name }))
        })

        readItems()
    }
    function readItems() {
        const obj = {}
        const mi = DM.getData("meta_items")

        settings.clusterOrder.forEach((subset, i) => {
            const set = new Set(subset)
            const name = settings.clusterNames[i]
            let maxval = 0;
            const counts = new Map()
            mi.forEach(d => {
                if (!set.has(d.cluster)) return
                d.categories.forEach(c => counts.set(c.cat_id, (counts.get(c.cat_id) || 0) + 1))
            })
            const values = []
            counts.forEach((value, key) => {
                values.push({ id: +key, cat_id: +key, value: value })
                maxval = Math.max(maxval, value)
            })

            if (maxval > 0) {
                values.forEach(d => d.value /= maxval)
            }

            maxPerCluster.set(name, maxval)
            obj[name] = values;
        })

        data.clusters = obj
    }

    function onClick(cluster, d) {
        const idx = settings.clusterNames.indexOf(cluster)
        app.selectByExtValue("cluster", "cluster", settings.clusterOrder[idx])
        app.selectByExtCategory([d.id])
    }

    onMounted(read)

    watch(() => Math.max(times.all, times.meta_categories), read)
    watch(() => times.meta_items, readItems)

</script>