<template>
    <div class="d-flex flex-wrap justify-center">
        <div v-for="(list, c) in data.clusters" style="text-align: center;" class="ml-1 mr-1">

            <div v-if="list.length > 0">
                <div class="d-flex mb-1">
                    <div v-if="smAndDown || c === data.allClusters[0]" style="width: 100px"></div>
                    <div
                        class="text-caption text-dots hover-sat"
                        @click="selectByCluster(c)"
                        :style="{
                            maxWidth: '300px',
                            width: '100%',
                            color: 'white',
                            right: '0px',
                            backgroundColor: settings.getClusterColor(c),
                            border: '2px solid ' + getHighlightColor(c)
                        }">
                        <b>{{ c }}</b>
                    </div>
                </div>
                <MiniBarCode
                    :dimensions="data.dims"
                    :options="data.dimOptions"
                    :selected="!selectedCluster || selectedCluster === c ? selectedCats : []"
                    :highlight="highlightCat"
                    :highlight-color="lightMode ? '#078766' : '#0ad39f'"
                    :data="list"
                    value-attr="value"
                    color-type="sequential"
                    :color-scale="colScale"
                    :color-domain="[0, 1]"
                    @hover="d => highlightCat = d === null ? d : d.id"
                    @click="d => onClick(c, d)"
                    @right-click="rightClickLeafCategory"
                    @right-click-label="rightClickCategory"
                    @pointerleave="tt.hide()"
                    :show-labels="smAndDown || c === data.allClusters[0]"
                    :width="smAndDown || c === data.allClusters[0] ? 400 : 300"
                    :height="200"/>
            </div>

        </div>
        <ColorLegend
            :colors="colValues"
            :ticks="colTicks"
            :tick-format="t => t+'%'"
            :size="230"
            :every-tick="4"
            hide-domain
            :vertical="!smAndDown"/>
    </div>
</template>

<script setup>
    import { useTimes } from '@/store/times'
    import DM from '@/use/data-manager'
    import { color, group, interpolateRgb, pointer, range, scaleSequential } from 'd3'
    import { onMounted, watch, reactive, computed } from 'vue'
    import MiniBarCode from '../vis/MiniBarCode.vue'
    import { CTXT_OPTIONS, useSettings } from '@/store/settings'
    import ColorLegend from '../vis/ColorLegend.vue'
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { useTooltip } from '@/store/tooltip'
    import { useDisplay } from 'vuetify'

    const times = useTimes()
    const settings = useSettings()
    const app = useApp()
    const tt = useTooltip()

    const { lightMode } = storeToRefs(settings)
    const { smAndDown } = useDisplay()

    const maxPerCluster = reactive(new Map())
    const data = reactive({
        dims: [],
        dimOptions: {},
        clusters: {},
        allClusters: []
    })

    const selectedCluster = ref("")
    const selectedCats = ref([])
    const highlightCat = ref(null)

    const colScale = computed(() => {
        if (lightMode.value) {
            return interpolateRgb("#efefef", "#000")// interpolateGreys
        }
        return interpolateRgb("#101010", "#fff")
    })
    const colTicks = computed(() => {
        return range(0, 105, 5)
    })
    const colValues = computed(() => {
        const scale = scaleSequential(colScale.value).domain([0, 100])
        return colTicks.value.map(scale)
    })

    function readSelectedCluster() {
        let match = "";
        const fd = DM.getFilterData("meta_items", "cluster")
        if (fd) {
            for (let idx = 0; idx < settings.clusterNames.length && match.length === 0; idx++) {
                const cs = settings.clusterOrder[idx]
                if (cs.length === fd.size && fd.union(new Set(cs)).size === cs.length) {
                    match = settings.clusterNames[idx];
                }
            }
        }
        selectedCluster.value = match
        selectedCats.value = DM.getSelectedIdsArray("meta_categories")
    }

    function getHighlightColor(cluster) {
        if (cluster === selectedCluster.value) {
            const col = settings.getClusterColor(cluster)
            return settings.lightMode ? color(col).darker() : color(col).brighter()
        }
        return settings.getClusterColor(cluster)
    }

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
        const mi = DM.getData("meta_items", false)

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

        data.allClusters = Object.keys(obj)
        data.clusters = obj
    }

    function onClick(cluster, d) {
        if (selectedCluster.value === cluster) {
            app.toggleSelectByExtCategory([d.id])
        } else {
            app.selectByExtCategory([d.id])
        }

        const fs = DM.getFilterData("meta_categories", "id")
        if (fs && fs.size > 0 && selectedCluster.value !== cluster) {
            const idx = settings.clusterNames.indexOf(cluster)
            app.selectByExtValue("cluster", "cluster", settings.clusterOrder[idx])
        } else {
            app.selectByExtValue("cluster", "cluster")
        }
    }

    function selectByCluster(cluster) {
        if (selectedCluster.value === cluster) {
            app.selectByExtValue("cluster", "cluster")
        } else {
            const idx = settings.clusterNames.indexOf(cluster)
            app.selectByExtValue("cluster", "cluster", settings.clusterOrder[idx])
        }
    }

    function rightClickCategory(name, event) {
        const cat = DM.find("meta_categories", d => d.name === name)
        if (cat) {
            const [mx, my] = pointer(event, document.body)
            settings.setRightClick(
                "meta_category",
                cat.id,
                mx, my,
                name,
                null,
                CTXT_OPTIONS.meta_category
            )
        }
    }

    function rightClickLeafCategory(datum, event) {
        if (datum && datum.id) {
            const [mx, my] = pointer(event, document.body)
            settings.setRightClick(
                "meta_category",
                datum.id,
                mx, my,
                datum.name,
                null,
                CTXT_OPTIONS.meta_category
            )
        }
    }

    onMounted(function() {
        read()
        readSelectedCluster()
    })

    watch(() => Math.max(times.all, times.meta_categories), read)
    watch(() => times.meta_items, readItems)
    watch(() => Math.max(times.f_meta_items, times.f_meta_categories), readSelectedCluster)

</script>

<style scoped>
.hover-sat {
    cursor: pointer;
}
.hover-sat:hover {
    filter: saturate(2);
}
</style>