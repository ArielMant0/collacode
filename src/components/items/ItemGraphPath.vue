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
        </div>

        <v-checkbox-btn v-model="ALL_TAGS" @update:model-value="reset(true)" label="use parents"></v-checkbox-btn>
        <div>
            <div v-for="(obj, idx) in clsOrder" :key="'clsi_'+idx" style="text-align: center;">
                <v-btn v-if="idx === clsOrder.length-1" color="primary" class="mb-2" density="comfortable" variant="outlined" @click="reroll">reroll</v-btn>
                <div class="d-flex align-center justify-center">
                    <ItemSimilarityRow v-for="(index, idx2) in obj.list"
                        :key="'isr_'+idx2"
                        :items="clusters.clusters[index]"
                        :show-index="obj.show[idx2]"
                        :node-size="usedNodeSize"
                        :disabled="clsOrder.length > idx+1"
                        :targets="target ? [target] : []"
                        :highlights="[clusters.clusters[index][obj.show[idx2]].id]"
                        class="mb-1 mr-1 ml-1"
                        :selected="obj.selected === index"
                        hide-barcode
                        hide-buttons
                        vertical
                        @click="chooseItem(idx, index)"
                        @click-item="d => chooseItemSave(d, idx, index, idx2)"/>
                </div>
            </div>
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
    import { getItemClusters, getMinMaxMeanDistBetweenClusters } from '@/use/clustering';
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
        },
        target: {
            type: Number,
        }
    })

    const emit = defineEmits(["update"])

    let tagProbs = []
    let clsReroll = []
    const inventory = ref([])
    const sims = ref([])
    const clsOrder = ref([])
    // const choices = ref([])
    const excluded = reactive(new Set())
    const once = new Set()

    const tagsDomain = ref([])

    const threshold = ref(0.05)
    const barCode = ref([])
    const usedNodeSize = computed(() => props.nodeSize !== undefined ? props.nodeSize : barCodeNodeSize.value)

    let itemsToUse
    let clusters = null, maxClsSize = 0
    const clusterLeft = new Set()

    const ALL_TAGS = ref(true)
    const FREQ_WEIGHTS = ref(true)

    function matchValue(mindist, maxdist, size, similar, pow=4) {
        // const v = similar > 0.5 ? 1-mindist : mindist
        return similar > 0.5 ? 1-maxdist : mindist * (mindist ** pow) * size
    }

    function reroll() {
        if (clsOrder.value.length > 1) {
            const idx = clsOrder.value.length-1
            clsReroll[idx] = clsReroll[idx].concat(clsOrder.value[idx].list)
        }
        inventory.value.pop()
        clsOrder.value.pop()
        sims.value.pop()
        nextItem()
    }

    async function nextItem() {

        // remove groups that can be ignored
        if (clusters && clsOrder.value.length > 0) {
            const j = clsOrder.value.at(-1).selected
            const ps = sims.value.at(-1)

            const before = clusterLeft.size
            const indices = Array.from(clusterLeft.values())

            // if it was a hard yes or a hard no
            if (ps > 0.75 || ps < 0.25) {
                const sim = ps > 0.75
                indices.forEach(i => {
                    if (i === j) return

                    if (sim && clusters.meanDistances[j][i] < clusters.mean + 3*clusters.std && clusters.minDistances[j][i] > 0.75) {
                        // if hard yes: remove those that are far away
                        clusterLeft.delete(i)
                    } else if (!sim && clusters.meanDistances[j][i] < clusters.mean - 1.5*clusters.std && clusters.maxDistances[j][i] < 0.7) {
                        // if hard no: remove those that are very close
                        clusterLeft.delete(i)
                    }
                })

                console.log("removed", before-clusterLeft.size, ", left", clusterLeft.size)
            }
        }

        if (!clusters) {
            if (itemsToUse.length === 0) {
                return console.log("no items")
            }

            const metric = "euclidean"
            clusters = await getItemClusters(itemsToUse, metric, 2, ALL_TAGS.value, FREQ_WEIGHTS.value)
            clusterLeft.clear()
            maxClsSize = 0
            clsOrder.value = []
            inventory.value = []
            clsReroll = []

            clusters.clusters.forEach((_, i) => {
                clusterLeft.add(i)
                maxClsSize = Math.max(maxClsSize, clusters.size[i])
            })

            if (!clusters) {
                return console.log("no clusters found")
            }
        }


        const k = clusters.clusters.length
        // get indices of remaining clusters
        const cf = [...Array(k).keys()].filter(i => clusterLeft.has(i))

        if (cf.length === 0) {
            console.log("no more groups left")
            return
        }

        let next;
        if (clsOrder.value.length > 0) {
            // look at mean match score to previous groups
            const inInv = clsOrder.value
                .filter(d => inventory.value[d.index] !== null)
                .map(d => itemsToUse.findIndex(dd => dd.id === inventory.value[d.index].id))

            let tmp = cf.map(i => {
                let value = 0
                let scores = clsOrder.value.map((d, j) => {
                    return matchValue(
                        clusters.minDistances[d.selected][i],
                        clusters.maxDistances[d.selected][i],
                        clusters.size[i],
                        1,
                    )
                })
                scores = scores.concat(inInv.map(d => {
                    const [dmin, dmax, _] = getMinMaxMeanDistBetweenClusters(
                        clusters.indices[i],
                        [d],
                        clusters.pwd
                    )
                    return matchValue(
                        dmin / clusters.min,
                        dmax / clusters.max,
                        clusters.size[i],
                        1,
                    )
                }))

                // calculate score for similar groups
                value = d3.max(scores)

                return {
                    index: i,
                    value: value,
                }
            })
            // sort from high to low match value
            tmp.sort((a, b) => {
                if (b.value === a.value) {
                    return clusters.size[b.index] - clusters.size[a.index]
                }
                return b.value - a.value
            })
            // console.log("-------------------")
            // for (let i = 0; i < 10; ++i) {
            //     const idx = tmp[i].index
            //     console.log("score", tmp[i].value)
            //     console.log(clusters.clusters[idx].map(d => d.name))
            // }
            next = tmp.slice(0, 5).map(d => d.index)
        } else {
            // from the first ten clusters, get the five with the highest distances between each other
            const subset = cf.slice(0, 10)
            let tmp = subset.map(i => {
                const scores = subset.map((d, j) => {
                    if (i === j) return 0
                    return matchValue(
                        clusters.minDistances[d][i],
                        clusters.maxDistances[d][i],
                        clusters.size[i],
                        0, // should be different to the others
                    )
                })

                return {
                    index: i,
                    value: d3.mean(scores),
                }
            })
            // sort from high to low match value
            tmp.sort((a, b) => {
                if (b.value === a.value) {
                    return clusters.size[b.index] - clusters.size[a.index]
                }
                return b.value - a.value
            })
            next = tmp.slice(0, 5).map(d => d.index)
        }

        next.forEach(i => clusterLeft.delete(i))

        clsOrder.value.push({
            index: 0,
            list: next,
            selected: null,
            show: next.map(() => 0)
        })
        sims.value.push(0)
        inventory.value.push(null)
        clsReroll.push([])

        updateBarCode()
    }

    function chooseItemSave(item, index, cluster, clusterIdx) {
        clsOrder.value[index].show[clusterIdx] = clusters.clusters[cluster].findIndex(d => d.id === item.id)
        inventory.value[index] = item
        chooseItem(index, cluster)
    }

    function chooseItem(index, clusterIndex) {
        if (index < clsOrder.value.length-1) {
            for (let i = index+1; i < clsOrder.value.length; ++i) {
                clsOrder.value[i].list.forEach(ci => clusterLeft.add(ci))
                clsReroll[i].forEach(ci => clusterLeft.add(ci))
            }
            clsOrder.value = clsOrder.value.slice(0, index+1)
            sims.value = sims.value.slice(0, index+1)
            clsReroll = clsReroll.slice(0, index+1)
            inventory.value = inventory.value.slice(0, index+1)
        }
        clsOrder.value[index].selected = clusterIndex
        sims.value[index] = 0.75
        nextItem()
    }

    function updateBarCode(index=-1, tags=null, similarity=0) {
        let goNext = false
        if (index >= 0 && tags !== null) {
            sims.value[index] = similarity
            tagProbs[index] = tags
            goNext = true
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

        if (goNext) {
            nextItem()
        }
    }

    function read() {
        const domain = DM.getDataBy("tags_tree", d => d.is_leaf === 1)
        tagsDomain.value = domain.map(d => d.id)
        barCode.value = domain.map(d => {
            const obj = Object.assign({}, d)
            obj.value = 0
            return obj
        })
    }

    function reset(update=true) {
        sims.value = []
        clsOrder.value = []
        inventory.value = []
        clsReroll = []
        once.clear()
        excluded.clear()
        clusterLeft.clear()
        itemsToUse = DM.getDataBy("items", d => d.allTags.length > 0)
        clusters = null
        if (update) {
            nextItem()
        }
    }

    defineExpose({ reset })

    onMounted(function() {
        read()
        reset(nextItem)
    })

</script>