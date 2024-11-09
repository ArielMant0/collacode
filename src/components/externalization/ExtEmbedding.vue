<template>
    <div :style="{ 'max-width': size+'px' }">
        <v-select v-model="method"
            :items="DR_METHODS"
            @update:model-value="calculateDR"
            density="compact"
            class="mb-1"
            hide-details
            hide-spin-buttons/>
        <ScatterPlot v-if="points.length > 0"
            :data="points"
            :selected="selected"
            :time="time"
            x-attr="0"
            y-attr="1"
            id-attr="2"
            :width="size"
            :height="size"
            canvas
            @hover="onHover"/>
    </div>
</template>

<script setup>
    import { onMounted, ref } from 'vue';
    import * as druid from '@saehrimnir/druidjs';
    import DM from '@/use/data-manager';
    import { useTooltip } from '@/store/tooltip';
    import ScatterPlot from '../vis/ScatterPlot.vue';

    const tt = useTooltip();

    const props = defineProps({
        time: {
            type: Number,
            default: 0
        },
        size: {
            type: Number,
            default: 500
        }
    })

    const DR_METHODS = ["PCA", "UMAP", "TSNE", "MDS", "TopoMap"]
    const method = ref("UMAP")
    const points = ref([])
    const selected = ref([])

    let matrix, data;
    const extMap = new Map();

    function readData() {
        data = DM.getData("externalizations", false)
        const allCats = DM.getData("ext_categories", false)
        const cats = allCats.filter(d => !allCats.some(dd => dd.parent === d.id))
        cats.sort((a, b) => a.parent-b.parent);
        const idToIdx = new Map()
        cats.forEach((d, i) => idToIdx.set(d.id, i))

        extMap.clear()
        const p = new Array(data.length)
        data.forEach((d, i) => {
            extMap.set(d.id, i)
            const arr = new Array(cats.length)
            arr.fill(0)
            d.categories.forEach(t => arr[idToIdx.get(t.cat_id)] = 1)
            p[i] = arr;
        });
        matrix = druid.Matrix.from(p)
    }

    function getDR() {
        const DR = druid[method.value]
        switch (method.value) {
            // case "ISOMAP": return new DR(matrix, { metric: druid.cosine })
            case "TopoMap": return new DR(matrix, { metric: druid.cosine })
            case "MDS": return new DR(matrix, { metric: druid.cosine })
            case "TSNE": return new DR(matrix, { metric: druid.cosine, perplexity: 10 })
            case "UMAP": return new DR(matrix, { metric: druid.cosine, n_neighbors: 10, local_connectivity: 1, _n_epochs: 500 })
            default: return new DR(matrix)
        }
    }


    function calculateDR() {
        readSelected()
        points.value = Array.from(getDR().transform()).map((d,i) => {
            return [d[0], d[1], i]
        })
    }
    function readSelected() {
        selected.value = DM.hasFilter("externalizations") ? DM.getSelectedIds("externalizations").map(d => extMap.get(d)) : []
    }

    function onHover(array, event) {
        if (array.length > 0) {
            const res = array.reduce((str, d) => {
                const game = DM.getDataItem("games", data[d[2]].game_id)
                return str + `<div class="d-flex">
                    <div class="mr-2">
                        <div class="text-caption text-dots" style="max-width: 85px">${game.name}</div>
                        <image src="teaser/${game.teaser}" width="80" height="40"/>
                    </div>
                    <p class="text-caption" style="max-width: 250px"><b>${data[d[2]].name}</b></br>${data[d[2]].description}</p>
                </div>`
            }, "")

            tt.show(`<div class="d-flex flex-wrap">${res}</div>`, event.pageX+10, event.pageY)
        } else {
            tt.hide()
        }
    }

    onMounted(function() {
        readData()
        calculateDR();
    })

    watch(() => props.time, readSelected)
</script>