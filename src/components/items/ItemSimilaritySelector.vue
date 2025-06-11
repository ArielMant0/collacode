<template>
    <div style="width: min-content" class="pa-2">
        <div class="d-flex">
            <div>
                <h3>Current Result</h3>
                <BarCode
                    :data="barCode"
                    selectable
                    id-attr="id"
                    name-attr="name"
                    value-attr="value"
                    abs-value-attr="value"
                    show-absolute
                    :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                    :min-value="0"
                    :max-value="1"
                    :width="usedNodeSize"
                    :height="15"/>
            </div>

            <v-slider v-model="threshold"
                hide-details
                hide-spin-buttons
                thumb-size="15"
                class="mt-2"
                min="0"
                max="1">
            </v-slider>
        </div>

        <!-- <div class="d-flex flex-wrap" style="width: 100%; max-width: 100%;">
            <v-chip v-for="t in barCodeFiltered"
                :key="t.id"
                :color="colScale(t.value)"
                rounded
                density="compact"
                :variant="excluded.has(t.id) ? 'outlined' : 'flat'"
                @click="toggleExcludeTag(t.id)"
                class="mr-1 mb-1 text-caption">
                {{ t.name }}
            </v-chip>
        </div> -->

        <div>
            <ItemSimilarityRow v-for="(i, idx) in clsOrder"
                :key="i"
                :threshold="threshold"
                :items="clusters.clusters[i]"
                :node-size="usedNodeSize"
                @change="(tags, s) => updateBarCode(idx, tags, s)"/>

            <v-btn density="compact" @click="nextItem()" variant="tonal">next</v-btn>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ref, onMounted, computed, reactive } from 'vue';
    import BarCode from '../vis/BarCode.vue';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import DM from '@/use/data-manager';
    import { getItemClusters, getSimilarity } from '@/use/clustering';
    import ItemSimilarityRow from './ItemSimilarityRow.vue';

    const settings = useSettings()

    const { barCodeNodeSize } = storeToRefs(settings)

    const props = defineProps({
        imageWidth: {
            type: Number,
            default: 100
        },
        imageHeight: {
            type: Number,
            default: 50
        },
        nodeSize: {
            type: Number
        }
    })

    const emit = defineEmits(["update"])

    let tagProbs = []
    const sims = ref([])
    const clsOrder = ref([])
    // const choices = ref([])
    const excluded = reactive(new Set())
    const once = new Set()

    const threshold = ref(0.05)
    const barCode = ref([])
    const barCodeFiltered = computed(() => barCode.value.filter(d => d.value > 0))
    const usedNodeSize = computed(() => props.nodeSize !== undefined ? props.nodeSize : barCodeNodeSize.value)

    const colScale = d3.scaleSequential(d3.interpolatePlasma).domain([0, 1])

    let clusters, clsPwd
    const clustersTaken = new Set()

    function toggleExcludeTag(tid) {
        if (excluded.has(tid)) {
            excluded.delete(tid)
        } else {
            excluded.add(tid)
        }
        updateBarCode()
    }

    function nextItem(replace=false) {
        // get indices of remaining clusters
        const ck = [...Array(clusters.clusters.length).keys()]
        const big = ck.filter(i => !clustersTaken.has(i) && clusters.size[i] > 5)
        const cf = big.length > 0 ? big : ck.filter(i => !clustersTaken.has(i))

        let next;
        if (clsOrder.value.length > 0) {
            // based on similarity for previous item, look for high, low, or medium similarity
            const tmp = cf.map(i => ({ index: i, value: clsOrder.value.reduce((acc, j, jidx) => acc + Math.abs(sims.value[jidx] - clsPwd[i][j]), 0) / clsOrder.value.length}))
            // sort from high to low match value
            tmp.sort((a, b) => {
                if (b.value === a.value) {
                    return clusters.size[a.index] - clusters.size[b.index]
                }
                return a.value - b.value
            })
            next = tmp[0].index
        } else {
            // just pick the first cluster
            next = cf[0]
        }


        if (replace) {
            clsOrder.value[clsOrder.value.length-1] = next
            sims.value[sims.value.length-1] = 0
        } else {
            clsOrder.value.push(next)
            sims.value.push(0)
        }

        clustersTaken.add(next)
        updateBarCode()
    }

    function updateBarCode(index=-1, tags=null, similarity=0) {
        if (index >= 0 && tags !== null) {
            sims.value[index] = similarity
            tagProbs[index] = tags
        }

        const vals = new Map()
        const counts = new Map()
        tagProbs.forEach(list => {
            list.forEach(t => {
                vals.set(t.id, (vals.get(t.id) || 0) + t.value)
                counts.set(t.id, (counts.get(t.id) || 0) + 1)
            })
        })

        const data = []
        barCode.value.forEach(t => {
            const v = vals.has(t.id) ? vals.get(t.id) / counts.get(t.id) : 0
            t.value = v > threshold.value ? v : 0
            if (v > threshold.value && !excluded.has(t.id)) {
                data.push(t.id)
            }
        })

        emit("update", data)
    }

    function read() {
        const domain = DM.getDataBy("tags_tree", d => d.is_leaf === 1)
        barCode.value = domain.map(d => {
            const obj = Object.assign({}, d)
            obj.value = 0
            return obj
        })
    }

    function reset(update=true) {
        sims.value = []
        clsOrder.value = []
        clustersTaken.clear()
        once.clear()
        excluded.clear()
        if (update) {
            nextItem()
        }
    }

    defineExpose({ reset })

    onMounted(function() {
        read()
        reset(false)

        clusters = getItemClusters()
        const k = clusters.clusters.length
        clsPwd = new Array(k)
        for (let i = 0; i < k; ++i) {
            clsPwd[i] = new Array(k)
            clsPwd[i][i] = 1
        }

        for (let i = 0; i < k; ++i) {
            for (let j = i+1; j < k; ++j) {
                clsPwd[i][j] = getSimilarity(clusters.tags[i], clusters.tags[j])
                clsPwd[j][i] = clsPwd[i][j]
            }
        }
        nextItem()
    })

</script>