<template>
    <div style="width: min-content; max-width: 90%;" class="pa-2">

        <v-checkbox-btn v-model="ALL_TAGS" @update:model-value="reroll" label="use parents"></v-checkbox-btn>
        <div v-if="DEBUG">
            <div v-for="(ci, idx) in clsOrder" class="mb-4">
                <BarCode :key="ci+'_'+idx+'_'+rollTime"
                    :data="getBarCodeData(clusters.tags[ci])"
                    :domain="tagsDomain"
                    hide-highlight
                    id-attr="id"
                    name-attr="name"
                    value-attr="value"
                    :min-value="0"
                    :max-value="1"
                    :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                    :width="usedNodeSize"
                    :height="15"/>
                <v-divider></v-divider>
                <ItemSummary v-for="(item, j) in ICLS[idx]" :key="item.id+'_'+j+'_'+rollTime" :id="item.id" hide-teaser :node-size="usedNodeSize" show-all-users/>
            </div>
        </div>

        <div v-else>
            <div v-for="(_, idx) in clsOrder" :key="idx">
                <v-divider v-if="idx > 0" class="mt-1 mb-1" style="width: 100%;"></v-divider>
                <ItemSimilarityRow
                    :threshold="threshold"
                    :items="ICLS[idx]"
                    :node-size="usedNodeSize"
                    :disabled="clsOrder.length > idx+1"
                    :targets="target ? [target] : []"
                    class="mb-1"
                    @change="(tags, s) => updateBarCode(idx, tags, s)"/>
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
    import { getItemClusters } from '@/use/clustering';
    import ItemSimilarityRow from './ItemSimilarityRow.vue';
    import ItemSummary from './ItemSummary.vue';

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
    const sims = ref([])
    const clsOrder = ref([])
    const clsSim = computed(() => clsOrder.value.map((d,i) => ({ value: d, index: i })).filter(d => sims.value[d.index] > 0.5))
    const clsDis = computed(() => clsOrder.value.map((d,i) => ({ value: d, index: i })).filter(d => sims.value[d.index] < 0.5))
    // const choices = ref([])
    const excluded = reactive(new Set())
    const once = new Set()

    const tagsDomain = ref([])

    const threshold = ref(0.05)
    const barCode = ref([])
    const barCodeFiltered = computed(() => barCode.value.filter(d => d.value > 0))
    const usedNodeSize = computed(() => props.nodeSize !== undefined ? props.nodeSize : barCodeNodeSize.value)

    const colScale = d3.scaleSequential(d3.interpolatePlasma).domain([0, 1])

    const DEBUG = ref(false)
    let ICLS = []
    let itemsToUse
    let clusters = null, maxClsSize = 0
    const clusterLeft = new Set()

    const rollTime = ref(0)
    const ALL_TAGS = ref(true)
    const FREQ_WEIGHTS = ref(true)

    function toggleExcludeTag(tid) {
        if (excluded.has(tid)) {
            excluded.delete(tid)
        } else {
            excluded.add(tid)
        }
        updateBarCode()
    }

    function getBarCodeData(data) {
        const tags = DM.getDataBy("tags_tree", d => ALL_TAGS.value || d.is_leaf === 1)
        return tags.map((d, i) => {
            const obj = Object.assign({}, d)
            obj.value = data[i]
            return obj
        })
    }

    function matchValue(mindist, maxdist, size, similar, pow=4) {
        // const v = similar > 0.5 ? 1-mindist : mindist
        return similar > 0.5 ?
            1-maxdist :
            mindist * (mindist ** pow) * size

        // similar items are worth more because they are more informative
        // ((1-distance) * (100 + clsOrder.value.length))
        // return target < 0.5 ? value*size : -value/size
        // return (1 + (5 * (target - 0.5)**2)) * Math.abs(target - value)
    }

    function reroll() {
        reset()
        rollTime.value = Date.now()
    }

    async function nextItem(replace=false) {

        // remove groups that can be ignored
        if (clusters && clsOrder.value.length > 0) {
            const j = clsOrder.value.at(-1)
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
                        console.log("removing cluster", i)
                        console.log(clusters.clusters[i].map(d => d.name))
                    } else if (!sim && clusters.meanDistances[j][i] < clusters.mean - 1.5*clusters.std && clusters.maxDistances[j][i] < 0.7) {
                        // if hard no: remove those that are very close
                        clusterLeft.delete(i)
                        console.log("removing cluster", i)
                        console.log(clusters.clusters[i].map(d => d.name))
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

        if (DEBUG.value) {
            ICLS = clusters.clusters
            sims.value = cf.map(() => 0)
            clsOrder.value = cf
        } else {

            if (cf.length === 0) {
                console.log("no more groups left")
                return
            }

            let next;
            if (clsOrder.value.length > 0) {
                // look at mean match score to previous groups
                let tmp = cf.map(i => {
                    let value = 0
                    if (clsSim.value.length > 0) {
                        const scores = clsSim.value.map(d  =>
                            matchValue(
                                clusters.minDistances[i][d.value],
                                clusters.maxDistances[i][d.value],
                                clusters.size[i],
                                sims.value[d.index],
                            )
                        )
                        // calculate score for similar groups
                        value = d3.max(scores)
                    } else  {
                        const scores = clsDis.value.map(d =>
                            matchValue(
                                clusters.minDistances[i][d.value],
                                clusters.maxDistances[i][d.value],
                                clusters.size[i],
                                sims.value[d.index],
                            )
                        )
                        // calculate score for dissimilar groups
                        value = d3.min(scores)
                    }

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
                console.log("-------------------")
                for (let i = 0; i < 10; ++i) {
                    const idx = tmp[i].index
                    console.log("score", tmp[i].value)
                    console.log(clusters.clusters[idx].map(d => d.name))
                }
                next = tmp[0].index
            } else {
                // just pick one of the first clusters
                next = cf[0];//randomChoice(cf.slice(0, 3), 1)
            }

            clusterLeft.delete(next)
            // const ids = new Set(clusters.clusters[next].map(d => d.id))
            // itemsToUse = itemsToUse.filter(d => !ids.has(d.id))

            if (replace) {
                ICLS[IP.length-1] = clusters.clusters[next]
                clsOrder.value[clsOrder.value.length-1] = next
                sims.value[sims.value.length-1] = 0
            } else {
                ICLS.push(clusters.clusters[next])
                clsOrder.value.push(next)
                sims.value.push(0)
            }
        }

        updateBarCode()
    }

    function easeInSine(x) {
        return 1 - Math.cos((x * Math.PI) / 2);
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
        ICLS = []
        sims.value = []
        clsOrder.value = []
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