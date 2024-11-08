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
            x-attr="0" y-attr="1"
            fill-attr="3"
            stroke-attr="4"
            :width="size"
            :height="size"
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

    const DR_METHODS = ["PCA", "UMAP", "TSNE", "ISOMAP"]
    const method = ref("UMAP")
    const points = ref([])

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

    function calculateDR() {
        const sel = new Set(DM.hasFilter("games") ? DM.getSelectedIds("games") : [])
        const DR = druid[method.value]
        const params = method.value !== "PCA" ? { metric: druid.cosine } : {}
        points.value = Array.from(new DR(matrix, params).transform()).map((d,i) => {
            const game = data[i]
            return [
                d[0], d[1], i,
                game.numExt > 0 ? 1 : 0,
                sel.size > 0 && sel.has(game.id) ? 1 : 0
            ]
        })
    }
    function readSelected() {
        const sel = new Set(DM.hasFilter("games") ? DM.getSelectedIds("games") : [])
        points.value.forEach((d, i) => {
            const game = data[i]
            d[4] = sel.size > 0 && sel.has(game.id) ? 1 : 0
        })
    }

    function onHover(d, event) {
        if (d !== null) {
            tt.show(`<div>
                <div>${data[d[2]].name}</div>
                <image src="teaser/${data[d[2]].teaser}" width="160" height="80"/>
                </div>`, event.pageX+10, event.pageY)
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