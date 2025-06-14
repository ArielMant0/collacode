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
            <ItemSimilarityRow v-for="(_, idx) in clsOrder"
                :key="idx"
                :threshold="threshold"
                :items="ICLS[idx]"
                :node-size="usedNodeSize"
                :disabled="clsOrder.length > idx+1"
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
    import { randomChoice } from '@/use/random';

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

    let ICLS = []
    let itemsToUse, clusters, clsPwd

    let simMean, simStdDev

    function toggleExcludeTag(tid) {
        if (excluded.has(tid)) {
            excluded.delete(tid)
        } else {
            excluded.add(tid)
        }
        updateBarCode()
    }

    function matchValue(value, target) {
        return Math.abs(target - value)
        // return (1 + (5 * (target - 0.5)**2)) * Math.abs(target - value)
    }

    function nextItem(replace=false) {

        // remove items that we can ignore this round
        // based on the rating for the previous round
        if (clsOrder.value.length > 0) {
            // - if 0.5 similarity: remove all that have 0.5 similarity
            const j = clsOrder.value.at(-1)
            const ps = sims.value.at(-1)
            const k = clusters.clusters.length

            const ids = new Set()

            for (let i = 0; i < k; ++i) {
                if (i === j) continue

                if (ps < 0.2) {
                    // if low similarity: remove all that have high similarity
                    if (clsPwd[j][i] > simMean + 4*simStdDev) {
                        clusters.clusters[i].forEach(d => ids.add(d.id))
                    }
                } else if (ps > 0.8) {
                    // if high similarity: remove all that have low similarity
                    if (clsPwd[j][i] < simMean - 2*simStdDev) {
                        clusters.clusters[i].forEach(d => ids.add(d.id))
                    }
                } else if (clsPwd[j][i] <= simMean - 2*simStdDev && clsPwd[j][i] >= simMean + 2*simStdDev) {
                    // if medium similarity: remove all that have very high or very low similarity
                    clusters.clusters[i].forEach(d => ids.add(d.id))
                }
            }

            // const dsize = DM.getSize("items", false)
            // const ignoreTags = new Set()
            // counts.forEach((num, tid) => {
            //     const v = num / ids.size
            //     const f = DM.getDataItem("tags_counts", tid) / dsize
            //     // "relatively" infrequent tags
            //     if (f < 0.1 && v >= 0.5) {
            //         ignoreTags.add(tid)
            //     }
            // })
            // console.log("ignoring tags:", Array.from(ignoreTags.values()).map(tid => DM.getDataItem("tags_name", tid)))

            console.log("removing items: ", itemsToUse.filter(d => ids.has(d.id)).map(d => d.name))

            const before = itemsToUse.length
            itemsToUse = itemsToUse.filter(d => !ids.has(d.id))
            console.log("removed", before-itemsToUse.length, ", left", itemsToUse.length)
        }

        if (itemsToUse.length === 0) {
            return console.log("no items left")
        }

        clusters = getItemClusters(itemsToUse)

        if (!clusters) {
            return console.log("no clusters found")
        }

        const k = clusters.clusters.length
        const simvals = []
        clsPwd = new Array(k)
        for (let i = 0; i < k; ++i) {
            clsPwd[i] = new Array(k)
            clsPwd[i][i] = 1
        }

        for (let i = 0; i < k; ++i) {
            for (let j = i+1; j < k; ++j) {
                clsPwd[i][j] = getSimilarity(clusters.tags[i], clusters.tags[j])
                simvals.push(clsPwd[i][j])
                clsPwd[j][i] = clsPwd[i][j]
            }
        }

        simMean = d3.mean(simvals)
        simStdDev = d3.deviation(simvals)

        console.log("mean similarity", simMean)
        console.log("std dev similarity", simStdDev)

        // get indices of remaining clusters
        const cf = [...Array(clusters.clusters.length).keys()]

        let next;

        if (clsOrder.value.length > 0) {
            // based on similarity for previous item, look for high, low, or medium similarity
            let tmp = cf.map(i => ({
                index: i,
                value: clsOrder.value.reduce((acc, j, jidx) => acc + matchValue(clsPwd[i][j], sims.value[jidx]), 0) / clsOrder.value.length
            }))
            // sort from high to low match value
            tmp.sort((a, b) => {
                if (b.value === a.value) {
                    return clusters.size[a.index] - clusters.size[b.index]
                }
                return a.value - b.value
            })
            tmp = tmp.slice(0, 5)
            next = randomChoice(tmp, 1).index
        } else {
            // just pick the first cluster
            next = randomChoice(cf.slice(0, 5), 1)
        }

        const ids = new Set(clusters.clusters[next].map(d => d.id))
        itemsToUse = itemsToUse.filter(d => !ids.has(d.id))

        if (replace) {
            ICLS[IP.length-1] = clusters.clusters[next]
            clsOrder.value[clsOrder.value.length-1] = next
            sims.value[sims.value.length-1] = 0
        } else {
            ICLS.push(clusters.clusters[next])
            clsOrder.value.push(next)
            sims.value.push(0)
        }

        updateBarCode()
    }

    function easeInSine(x) {
        return 1 - Math.cos((x * Math.PI) / 2);
    }

    function updateBarCode(index=-1, tags=null, similarity=0) {
        if (index >= 0 && tags !== null) {
            sims.value[index] = similarity
            tagProbs[index] = tags
        }

        const vals = new Map()
        const counts = new Map()
        tagProbs.forEach(list => {
            const occured = new Set()
            list.forEach(t => {
                vals.set(t.id, (vals.get(t.id) || 0) + t.value)
                occured.add(t.id)
            })
            occured.forEach(tid => counts.set(tid, (counts.get(tid) || 0) + 1))
        })

        const data = []
        barCode.value.forEach(t => {
            const v = vals.has(t.id) ? vals.get(t.id) / counts.get(t.id) : 0
            t.value = v > threshold.value ? v : 0
            if (v > threshold.value && !excluded.has(t.id)) {
                data.push(t)
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
        ICLS = []
        once.clear()
        excluded.clear()
        itemsToUse = DM.getDataBy("items", d => d.allTags.length > 0)
        if (update) {
            nextItem()
        }
    }

    defineExpose({ reset })

    onMounted(function() {
        read()
        reset()
    })

</script>