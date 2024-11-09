<template>
    <div :style="{ 'max-width': size+'px' }">
        <div class="d-flex">
            <v-select v-model="method"
                :items="DR_METHODS"
                @update:model-value="calculateDR"
                density="compact"
                class="mb-1"
                hide-details
                hide-spin-buttons/>
            <v-checkbox :model-value="showImages"
                density="compact"
                label="images"
                hide-details
                hide-spin-buttons
                single-line
                @click="showImages = !showImages"
                />
        </div>
        <ScatterPlot v-if="points.length > 0"
            :data="points"
            :time="time"
            :selected="selected"
            x-attr="0"
            y-attr="1"
            id-attr="2"
            url-attr="3"
            fill-attr="4"
            :width="size"
            :height="size"
            :grid="showImages"
            canvas
            @hover="onHover"/>
    </div>
</template>

<script setup>
    import { onMounted, ref } from 'vue';
    import * as druid from '@saehrimnir/druidjs';
    import ScatterPlot from './vis/ScatterPlot.vue';
    import DM from '@/use/data-manager';
    import { useTooltip } from '@/store/tooltip';

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
    const showImages = ref(false)

    let matrix, data;
    const gameMap = new Map();


    function readData() {
        data = DM.getDataBy("games", d => d.allTags.length > 0)
        const tags = DM.getDataBy("tags", d => d.is_leaf === 1)
        tags.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return a.path.length-b.path.length
        });
        const idToIdx = new Map()
        tags.forEach((d, i) => idToIdx.set(d.id, i))

        gameMap.clear()
        const p = new Array(data.length)
        data.forEach((d, i) => {
            gameMap.set(d.id, i)
            const arr = new Array(tags.length)
            arr.fill(0)
            d.allTags.forEach(t => arr[idToIdx.get(t.id)] = 1)
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
            case "UMAP": return new DR(matrix, { metric: druid.cosine, n_neighbors: 10, local_connectivity: 2, _n_epochs: 500 })
            default: return new DR(matrix)
        }
    }


    function calculateDR() {
        readSelected()
        points.value = Array.from(getDR().transform()).map((d,i) => {
            const game = data[i]
            return [d[0], d[1], i, "teaser/"+game.teaser, game.numExt > 0 ? 1 : 0]
        })
    }
    function readSelected() {
        selected.value = DM.hasFilter("games") ? DM.getSelectedIds("games").map(d => gameMap.get(d)) : []
    }

    function onHover(array, event) {
        if (array.length > 0) {
            const res = array.reduce((str, d) =>  str + `<div>
                <div class="text-caption text-dots" style="max-width: 165px">${data[d[2]].name}</div>
                <image src="teaser/${data[d[2]].teaser}" width="160" height="80"/>
            </div>` , "")

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