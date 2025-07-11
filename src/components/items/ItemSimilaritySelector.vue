<template>
    <div style="width: min-content; max-width: 90%;" class="pa-2">

        <div style="text-align: center;">
            <v-btn color="primary" class="mt-2" density="comfortable" @click="submit">done</v-btn>
        </div>

        <!-- <v-checkbox-btn v-model="ALL_TAGS" @update:model-value="reroll" label="use parents"></v-checkbox-btn> -->
        <div v-if="DEBUG">
            <div v-for="(ci, idx) in clsOrder" class="mb-4">
                <BarCode :key="ci.cluster+'_'+idx+'_'+rollTime"
                    :data="getBarCodeData(clusters.tags[ci.cluster])"
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
            <div v-for="(obj, idx) in clsOrder" :key="idx">
                <v-divider v-if="idx > 0" class="mt-1 mb-1" style="width: 100%;"></v-divider>
                <ItemSimilarityRow
                    :threshold="threshold"
                    :items="ICLS[idx]"
                    :node-size="usedNodeSize"
                    :show-index="obj.show"
                    :choice="sims[idx]"
                    :targets="target ? [target] : []"
                    :highlights="[clusters.clusters[obj.cluster][obj.show].id]"
                    class="mb-1"
                    @change="s => choose(idx, s)"
                    @click-item="d => chooseItemSave(d, idx, obj.cluster)"/>
            </div>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ref, onMounted, computed } from 'vue';
    import BarCode from '../vis/BarCode.vue';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import DM from '@/use/data-manager';
    import { getItemClusters } from '@/use/clustering';
    import ItemSimilarityRow from './ItemSimilarityRow.vue';
    import ItemSummary from './ItemSummary.vue';
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
        maxItems:{
            type: Number,
            default: 30
        },
        nodeSize: {
            type: Number
        },
        target: {
            type: Number,
        }
    })

    const emit = defineEmits(["submit", "inventory"])

    let reroll = []
    const sims = ref([])
    const clsOrder = ref([])
    const inventory = ref([])
    const clsSim = computed(() => clsOrder.value.filter(d => sims.value[d.index] > 0.5))
    const clsDis = computed(() => clsOrder.value.filter(d => sims.value[d.index] < 0.5))

    const tagsDomain = ref([])

    const threshold = ref(0.05)
    const usedNodeSize = computed(() => props.nodeSize !== undefined ? props.nodeSize : barCodeNodeSize.value)

    const DEBUG = ref(false)
    let ICLS = []
    let itemsToUse
    let clusters = null, maxClsSize = 0
    const clusterLeft = new Set()

    const rollTime = ref(0)
    const ALL_TAGS = ref(true)
    const FREQ_WEIGHTS = ref(true)

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

    async function nextItem(replace=false) {

        // remove groups that can be ignored
        if (clusters && clsOrder.value.length > 0) {
            const j = clsOrder.value.at(0).cluster
            const ps = sims.value.at(0)

            // const before = clusterLeft.size
            const indices = Array.from(clusterLeft.values())

            // if it was a hard yes or a hard no
            if (ps > 0.75 || ps < 0.25) {
                const sim = ps > 0.75
                indices.forEach(i => {
                    if (i === j) return

                    if (sim && clusters.meanDistances[j][i] < clusters.mean + 3*clusters.std && clusters.minDistances[j][i] > 0.75) {
                        // if hard yes: remove those that are far away
                        clusterLeft.delete(i)
                        reroll[0].push(i)
                        // console.log("removing cluster", i)
                        // console.log(clusters.clusters[i].map(d => d.name))
                    } else if (!sim && clusters.meanDistances[j][i] < clusters.mean - 1.5*clusters.std && clusters.maxDistances[j][i] < 0.7) {
                        // if hard no: remove those that are very close
                        clusterLeft.delete(i)
                        reroll[0].push(i)
                        // console.log("removing cluster", i)
                        // console.log(clusters.clusters[i].map(d => d.name))
                    }
                })

                // console.log("removed", before-clusterLeft.size, ", left", clusterLeft.size)
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
            inventory.value = []
            reroll = []

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
            clsOrder.value = cf.map(i => ({
                index: i,
                show: 0
            }))
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
                                clusters.minDistances[i][d.cluster],
                                clusters.maxDistances[i][d.cluster],
                                clusters.size[i],
                                sims.value[d.index],
                            )
                        )
                        // calculate score for similar groups
                        value = d3.mean(scores)
                    } else  {
                        const scores = clsDis.value.map(d =>
                            matchValue(
                                clusters.minDistances[i][d.cluster],
                                clusters.maxDistances[i][d.cluster],
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
                // console.log("-------------------")
                // for (let i = 0; i < 10; ++i) {
                //     const idx = tmp[i].index
                //     console.log("score", tmp[i].value)
                //     console.log(clusters.clusters[idx].map(d => d.name))
                // }
                next = tmp[0].index
            } else {
                // just pick one of the first clusters
                next = cf[0];//randomChoice(cf.slice(0, 3), 1)
            }

            clusterLeft.delete(next)

            if (replace) {
                const idx = clsOrder.value.length-1
                ICLS[idx] = clusters.clusters[next]
                clsOrder.value[idx] = {
                    index: 0,
                    cluster: next,
                    show: 0,
                }
                sims.value[idx] = 0
                inventory.value = []
            } else {
                ICLS.unshift(clusters.clusters[next])
                clsOrder.value.unshift({
                    index: 0,
                    cluster: next,
                    show: 0,
                })
                sims.value.unshift(0)
                inventory.value.unshift(null)
                reroll.unshift([])
            }
            clsOrder.value.forEach((d, i) => d.index = i)
        }
    }

    function chooseItemSave(item, index, cluster) {
        clsOrder.value[index].show = clusters.clusters[cluster].findIndex(d => d.id === item.id)
        inventory.value[index] = item
        emit("inventory", inventory.value.filter(d => d !== null))
    }

    function choose(index, similarity) {
        if (index > 0) {
            for (let i = 0; i < index; ++i) {
                clusterLeft.add(clsOrder.value[i].cluster)
                reroll[i].forEach(ci => clusterLeft.add(ci))
            }
            clsOrder.value = clsOrder.value.slice(index)
            sims.value = sims.value.slice(index)
            reroll = reroll.slice(index)
            inventory.value = inventory.value.slice(index)
            clsOrder.value.forEach((d, i) => d.index = i)
            index = 0
        }
        sims.value[index] = similarity
        inventory.value[index] = ICLS[index][clsOrder.value[index].show]
        emit("inventory", inventory.value.filter(d => d !== null))
        nextItem()
    }

    function read() {
        const domain = DM.getDataBy("tags_tree", d => d.is_leaf === 1)
        tagsDomain.value = domain.map(d => d.id)
    }

    function submit() {
        const best = clsOrder.value.find(d => sims.value[d.index] > 0.75)
        const last = clsOrder.value.find(d => sims.value[d.index] > 0.5)

        const ininv = inventory.value
            .filter((d, i) => d !== null && sims.value[i] > 0.5)
            .slice(0, 4)

        let list = []
        const num = props.maxItems - ininv.length

        if (best && best.index !== last.index) {
            const tmpA = randomChoice(clusters.clusters[best.cluster], Math.floor(num * 0.5))
            const tmpB = randomChoice(clusters.clusters[last.cluster], Math.floor(num * 0.5))
            list = tmpA.concat(tmpB)
        } else {
            list = randomChoice(clusters.clusters[last.cluster], num)
        }

        emit("submit", list.concat(ininv.filter(d => !list.find(dd => dd.id === d.id))))
    }

    function reset(update=true) {
        ICLS = []
        sims.value = []
        clsOrder.value = []
        clusterLeft.clear()
        itemsToUse = DM.getDataBy("items", d => d.allTags.length > 0 && (!props.target || d.id !== props.target))
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