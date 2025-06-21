<template>
    <div style="width: min-content" class="pa-2">

        <div v-if="step === 1">
            <v-checkbox-btn v-model="ALL_TAGS" @update:model-value="reset(true)" label="use parents"></v-checkbox-btn>
            <div>
                <div v-for="(obj, idx) in clsOrder" :key="'clsi_'+idx" style="text-align: center;">
                    <v-btn v-if="idx === clsOrder.length-1" color="primary" class="mb-2" density="comfortable" variant="outlined" @click="reroll">reroll</v-btn>
                    <div class="d-flex align-center justify-center">
                        <ItemSimilarityRow v-for="(index, idx2) in obj.list"
                            :key="'c'+idx+'_isr_'+idx2"
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

            <div style="text-align: center;">
                <v-btn color="primary" class="mt-2" density="comfortable" @click="submit">done</v-btn>
            </div>
        </div>
        <div v-else>
            <div class="d-flex align-end">

                <div class="d-flex flex-column align-center">
                    <h3>Related {{ app.itemNameCaptial+'s' }}</h3>
                    <div class="d-flex flex-wrap justify-center" :style="{ minWidth: (170*2)+'px', maxWidth: (170*2)+'px' }">
                        <ItemTeaser v-for="(item, idx) in candidates"
                            :item="item"
                            :style="{ opacity: candSelect.has(idx) || candSelect.size === 0 ? 1 : 0.5 }"
                            @click="toggleCandidate(idx)"
                            :border-color="candSelect.has(idx) ? theme.current.value.colors.primary : undefined"
                            :border-size="4"
                            :width="160"
                            :height="80"
                            prevent-open
                            prevent-context
                            class="mr-1 mb-1"/>
                    </div>
                </div>

                <div>
                    <div style="text-align: center; max-width: 99%;" class="mt-4">
                        <ColorLegend v-if="colorScale"
                            :colors="colorScale.range()"
                            :ticks="colorScale.thresholds().map(v => Math.floor(v)).concat([maxTagCount])"
                            :size="treeWidth-15"
                            :label-size="25"
                            :rect-size="15"
                            hide-domain/>
                        <v-slider v-model="threshold"
                            class="text-caption"
                            min="1"
                            :max="maxTagCount"
                            :step="1"
                            :ticks="d3.range(1, maxTagCount+1)"
                            show-ticks="always"
                            hide-spin-buttons
                            @update:model-value="updateTags"/>
                    </div>

                    <TreeMap
                        :data="treeData"
                        :time="treeTime"
                        color-attr="color"
                        valid-attr="_exclude"
                        color-invalid="red"
                        :color-map="treeMapColors"
                        @click="toggleTag"
                        :width="treeWidth"
                        :height="treeHeight"/>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ref, onMounted, computed, reactive } from 'vue';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import DM from '@/use/data-manager';
    import { getItemClusters, getMinMaxMeanDistBetweenClusters } from '@/use/clustering';
    import ItemSimilarityRow from './ItemSimilarityRow.vue';
    import ItemTeaser from './ItemTeaser.vue';
    import { useTheme } from 'vuetify';
    import TreeMap from '../vis/TreeMap.vue';
    import { useWindowSize } from '@vueuse/core';
    import ColorLegend from '../vis/ColorLegend.vue';
    import { useApp } from '@/store/app';

    const app = useApp()
    const settings = useSettings()
    const theme = useTheme()

    const { lightMode, barCodeNodeSize } = storeToRefs(settings)

    const ws = useWindowSize()
    const treeWidth = computed(() => Math.max(200, Math.floor(ws.width.value*0.7)))
    const treeHeight = computed(() => Math.max(200, Math.floor(ws.height.value*0.65)))

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

    const emit = defineEmits(["update", "step"])

    let clsReroll = []
    const inventory = ref([])
    const sims = ref([])
    const clsOrder = ref([])

    let tagCounts = new Map()
    const candidates = ref([])
    const candSelect = reactive(new Set())
    const tagsSel = reactive(new Set())
    const threshold = ref(1)
    const maxTagCount = ref(1)

    const colorScale = ref(null)

    const step = ref(1)
    const treeTime = ref(0)
    const treeData = ref([])
    const usedNodeSize = computed(() => props.nodeSize !== undefined ? props.nodeSize : barCodeNodeSize.value)

    let itemsToUse
    let clusters = null, maxClsSize = 0
    const clusterLeft = new Set()

    const ALL_TAGS = ref(true)
    const FREQ_WEIGHTS = ref(true)

    function treeMapColors(d3obj, h, light) {
        const n = Math.max(3,Math.min(9,h))
        const r = d3obj.range(1, n+1)
        return r.map(d3obj.scaleSequential([
            light ? "#fff" : "#000",
            light ? "#000" : "#fff"
        ]).domain([0, n]))
    }

    function toggleCandidate(index) {
        if (candSelect.has(index)) {
            candSelect.delete(index)
        } else {
            candSelect.add(index)
        }
        updateTags()
    }
    function submit() {
        step.value = 2
        emit("step", 2)
        const last = clsOrder.value.at(-2)
        const idx = last.list.indexOf(last.selected)
        const it = clusters.clusters[last.selected][last.show[idx]]
        const itIdx = itemsToUse.findIndex(d => d.id === it.id)
        const cands = clusters.pwd[itIdx].map((v, i) => ({ index: i, value: v }))
        cands.sort((a, b) => a.value - b.value)
        candSelect.clear()
        tagsSel.clear()
        tagCounts.clear()
        candidates.value = cands.slice(0, 20).map(d => itemsToUse[d.index])
        updateTags()
    }

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

    function toggleTag(tag) {
        if (tagsSel.has(tag.id)) {
            tagsSel.delete(tag.id)
        } else {
            tagsSel.add(tag.id)
        }
        updateTreemap()
    }

    function updateTags() {
        const items = []
        candSelect.forEach(idx => items.push(candidates.value[idx]))

        const vals = new Map()
        items.forEach(d => d.allTags.forEach(t => vals.set(t.id, (vals.get(t.id) || 0) + 1)))

        let mtc = 0
        treeData.value.forEach(t => {
            if (t.is_leaf === 1) {
                const v = vals.get(t.id)
                if (v !== undefined) {
                    tagCounts.set(t.id, v)
                    mtc = Math.max(v, mtc)
                }
            }
        })

        maxTagCount.value = Math.max(1, mtc)

        colorScale.value = d3.scaleQuantize()
            .domain([1, maxTagCount.value])
            .range(d3.schemePuBuGn[Math.max(3, Math.min(maxTagCount.value, 9))])

        treeData.value.forEach(t => {
            const v = tagCounts.get(t.id)
            t.value = v !== undefined ? v : 0
            if (v !== undefined) {
                t.color = v > 0 ? colorScale.value(v) : (lightMode.value ? "white" : "black")
                if (v >= threshold.value) {
                    tagsSel.add(t.id)
                } else {
                    tagsSel.delete(t.id)
                }
            } else {
                delete t.color
            }
        })

        updateTreemap()
    }

    function updateTreemap() {
        const data = []
        treeData.value.forEach(t => {
            t._exclude = !tagsSel.has(t.id)
            if (!t._exclude) {
                data.push(t)
            }
        })
        emit("update", data)
        treeTime.value = Date.now()
    }

    function read() {
        treeData.value = DM.getData("tags", false)
            .map(d => {
                const obj = Object.assign({}, d)
                obj.value = 0
                obj._exclude = true
                return obj
            })
        treeTime.value = Date.now()
    }

    function reset(update=true) {
        sims.value = []
        clsOrder.value = []
        inventory.value = []
        clsReroll = []
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