<template>
    <div class="d-flex">
        <h3 v-if="dims.length === 0" class="text-uppercase" style="text-align: center; width: 100%;">
            NO {{ app.schemeMetaItemName }} CATEGORIES AVAILABLE
        </h3>
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
                clickable
                :color-legend="i === dims.length-1"
                :color-scale="'schemeObservable10'"
                @click-label="n => selectExtByCat(d, n)"
                @click-bar="n => selectExtByCatCombi(d, n)"
                @right-click-label="(n, e) => contextExtCat(d, n, e)"
                :y-attrs="['single', 'double', 'multiple']"/>
        </div>
    </div>
</template>

<script setup>
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import DM from '@/use/data-manager';
    import { group, max, pointer } from 'd3';
    import { onMounted, reactive } from 'vue';
    import StackedBarChart from '../vis/StackedBarChart.vue';
    import { useTimes } from '@/store/times';
    import { useApp } from '@/store/app';

    const app = useApp()
    const settings = useSettings()
    const times = useTimes()

    const dims = ref([])
    const domains = reactive([])
    const padding = reactive({})
    const data = reactive({})
    const maxValue = ref(0)

    let readCounter = 0;

    function read() {
        if (!DM.hasData("meta_categories") || !DM.hasData("meta_items")) {
            readCounter++
            if (readCounter < 3) {
                setTimeout(read, 150)
            }
            return
        }

        readCounter = 0;
        const cats = DM.getData("meta_categories", false)
        const leaves = cats.filter(c => !cats.find(d => d.parent === c.id))
        const parents = new Map()
        leaves.forEach(d => parents.set(d.id, d.parent))

        const requiredIds = group(leaves, d => d.parent)
        const requiredCats = cats.filter(d => requiredIds.has(d.id))
        requiredCats.sort((a, b) => settings.extCatOrder.indexOf(a.name)-settings.extCatOrder.indexOf(b.name))

        const exts = DM.getData("meta_items", false)
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

    function selectExtByCat(dim, name) {
        const cats = DM.getData("meta_categories", false)
        const isParent = id => cats.some(d => d.parent === id)
        const parent = cats.find(d => isParent(d.id) && d.name === dim)
        if (parent) {
            const datum = DM.find("meta_categories", d => {
                const path = DM.getDerivedItem("meta_cats_path", d.id)
                return d.name === name && path && path.path.includes(parent.id)
            })
            if (datum) {
                app.toggleSelectByExtCategory([datum.id])
            }
        }
    }

    function selectExtByCatCombi(dim, names) {
        app.toggleSelectByExtCategory(ids)

        const cats = DM.getData("meta_categories", false)
        const isParent = id => cats.some(d => d.parent === id)
        const parent = cats.find(d => isParent(d.id) && d.name === dim)
        if (parent) {
            const nameSet = new Set(names)
            const data = DM.getDataBy("meta_categories", d => {
                const path = DM.getDerivedItem("meta_cats_path", d.id)
                return nameSet.has(d.name) && path && path.path.includes(parent.id)
            })
            if (data.length > 0) {
                app.toggleSelectByExtCategory(data.map(d => d.id))
            }
        }
    }

    function contextExtCat(dim, name, event) {
        if (!app.allowEdit) return;
        const [mx, my] = pointer(event, document.body)
        const cats = DM.getData("meta_categories", false)
        const isParent = id => cats.some(d => d.parent === id)
        const parent = DM.find("meta_categories", d => isParent(d.id) && d.name === dim)
        if (parent) {
            const datum = DM.find("meta_categories", d => {
                const path = DM.getDerivedItem("meta_cats_path", d.id)
                return d.name === name && path && path.path.includes(parent.id)
            })
            if (datum) {
                settings.setRightClick(
                    "ext_category", datum.id,
                    mx + 10,
                    my + 10,
                    null,
                    CTXT_OPTIONS.ext_category
                )
            }
        }
    }

    onMounted(read)

    watch(() => Math.max(times.meta_categories, times.meta_items), read)
</script>