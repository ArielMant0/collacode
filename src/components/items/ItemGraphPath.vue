<template>
    <div style="width: min-content" class="pa-2">
        <div style="text-align: center;">
            <v-btn
                :color="clsOrder.length > 1 ? 'primary' : 'default'"
                class="mb-4"
                density="comfortable"
                :disabled="clsOrder.length <= 1"
                @click="submit">
                done
            </v-btn>
        </div>

        <h4 style="text-align: center;" class="mt-2 mb-4">Find the most similar {{ app.itemName }}</h4>

        <div style="text-align: center;">
            <v-btn v-if="clsOrder.length > 0"
                color="primary"
                class="mb-2"
                density="comfortable"
                variant="outlined"
                prepend-icon="mdi-sync"
                @click="reroll">reroll</v-btn>
        </div>
        <div class="d-flex align-start">
            <div>
                <div v-for="(obj, idx) in clsOrder" style="text-align: center;">
                    <v-divider v-if="idx > 0" class="mt-4 mb-4"></v-divider>
                    <div class="d-flex align-start justify-center">
                        <ItemSimilarityRow v-for="(index, idx2) in obj.list"
                            :items="clusters.clusters[index]"
                            :show-index="obj.show[idx2]"
                            :targets="target ? [target] : []"
                            :image-width="imageWidth"
                            :image-height="imageHeight"
                            :highlights="highlights[idx][idx2]"
                            :selected="obj.selected === index"
                            class="mb-1 mr-3 ml-3"
                            hide-buttons
                            vertical
                            @click="d => chooseItemSave(d, idx, index, idx2, true)"
                            @click-item="d => chooseItemSave(d, idx, index, idx2)"/>
                    </div>
                </div>
            </div>

            <v-sheet class="pa-2 ml-8" rounded border style="min-width: 345px;">
                <div style="text-align: center;">suggested {{ app.itemName }}s</div>
                <div v-for="(list, cidx) in candidates">
                    <v-divider v-if="cidx > 0" class="mt-3 mb-2" opacity="0.5"></v-divider>
                    <div class="pl-2 text-caption"><b>step {{ candidates.length-cidx }}</b></div>
                    <div class="d-flex flex-wrap justify-center">
                        <ItemTeaser v-for="id in list"
                            class="mr-1 mb-1"
                            :id="id"
                            :border-color="id === getSelectedId(cidx+1) ? theme.current.value.colors.secondary : undefined"
                            :border-size="2"
                            prevent-click
                            prevent-context
                            :width="100"
                            :height="50"/>
                    </div>
                </div>
            </v-sheet>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ref, onMounted, reactive } from 'vue';
    import DM from '@/use/data-manager';
    import { getItemClusters, getMinMaxMeanDistBetweenClusters } from '@/use/clustering';
    import ItemSimilarityRow from './ItemSimilarityRow.vue';
    import { randomInteger } from '@/use/random';
    import { useApp } from '@/store/app';
    import ItemTeaser from './ItemTeaser.vue';
    import { useTheme } from 'vuetify';

    const app = useApp()
    const theme = useTheme()

    const props = defineProps({
        numClusters: {
            type: Number,
            default: 5
        },
        imageWidth: {
            type: Number,
            default: 180
        },
        imageHeight: {
            type: Number,
            default: 90
        },
        maxItems:{
            type: Number,
            default: 30
        },
        maxSelect:{
            type: Number,
            default: 3
        },
        target: {
            type: Number,
        }
    })

    const emit = defineEmits(["submit"])

    let clsReroll = []

    const selection = ref([])
    const clsOrder = reactive({
        list: [],
        selected: null,
        show: null
    })

    const candidates = ref([])

    let itemsToUse
    let log = []
    let candidateItems = []
    let clusters = null, maxClsSize = 0

    const clusterLeft = new Set()

    const ALL_TAGS = ref(true)
    const FREQ_WEIGHTS = ref(true)

    function getSelectedId(index) {
        if (index >= clsOrder.value.length) return null
        const d = clsOrder.value[index]
        const clsIdx = d.selected
        const selIdx = d.list.indexOf(clsIdx)
        const showIdx = d.show[selIdx]
        return clusters.clusters[clsIdx][showIdx].id
    }

    function getCandidates() {
        // general idea: for the last 3 items, get similar items
        const num = Math.min(clsOrder.value.length, 3)

        const counts = []
        switch(num) {
            case 1:
                counts.push(props.maxItems)
                break
            case 2: {
                const f = Math.ceil(props.maxItems*0.5)
                counts.push(f)
                counts.push(props.maxItems-f)
                break
            }
            default: {
                const f1 = Math.ceil(props.maxItems*0.5)
                const f2 = Math.ceil(props.maxItems*0.25)
                counts.push(f1)
                counts.push(props.maxItems-f1)
                counts.push(props.maxItems-f1-f2)
                break
            }
        }

        const final = []
        const idSet = new Set()

        for (let j = num-1; j >= 0; --j) {
            const cls = clsOrder.value.at(j)
            if (cls.selected === null) continue
            const idx = cls.list.indexOf(cls.selected)
            const it = clusters.clusters[cls.selected][cls.show[idx]]
            idSet.add(it.id)
        }

        for (let j = num-1; j >= 0; --j) {
            const cls = clsOrder.value.at(j)
            if (cls.selected === null) continue
            const idx = cls.list.indexOf(cls.selected)
            const it = clusters.clusters[cls.selected][cls.show[idx]]
            const itIdx = itemsToUse.findIndex(d => d.id === it.id)
            const cands = clusters.pwd[itIdx].map((v, i) => ({ index: i, value: v }))
            // const cands = clusters.clusters[idx].map(i => ({ index: i, value: clusters.pwd[itIdx][i] }))
            cands.sort((a, b) => a.value - b.value)
            const tmp = cands.slice(0, props.maxItems).map(d => itemsToUse[d.index])

            const added = []
            tmp.forEach((d, idx) => {
                if (added.length < counts[j] && (!idSet.has(d.id) || idx === 0)) {
                    added.push(d)
                    idSet.add(d.id)
                }
            })

            final.unshift(added)
        }

        return final
    }

    function submit() {
        log.push({
            desc: "suggested items",
            items: candidates.value
        })

        emit("submit", candidateItems, log)
    }

    function matchValue(mindist, maxdist, size, similar, pow=4) {
        // const v = similar > 0.5 ? 1-mindist : mindist
        return similar > 0.5 ?
            1-maxdist :
            mindist * (mindist ** pow) * size
    }

    function reroll() {
        if (clsOrder.value.length > 0) {
            clsReroll[0] = clsReroll[0].concat(clsOrder.value[0].list)
        }
        log.push({
            desc: "reroll",
            clusters: clsOrder.value[0].list
        })
        clsOrder.value.shift()
        sims.value.shift()
        inventory.value.shift()
        clsOrder.value.forEach((d, i) => d.index = i)

        nextItem()
    }

    async function nextItem() {

        if (!clusters) {
            if (itemsToUse.length === 0) {
                return console.debug("no items")
            }

            const metric = "euclidean"
            clusters = await getItemClusters(itemsToUse, metric, 2, ALL_TAGS.value, FREQ_WEIGHTS.value)
            clusterLeft.clear()
            clsOrder.value = []
            inventory.value = []
            clsReroll = []
            maxClsSize = 0

            clusters.clusters.forEach((_, i) => {
                clusterLeft.add(i)
                maxClsSize = Math.max(maxClsSize, clusters.size[i])
            })

            if (!clusters) {
                return console.debug("no clusters found")
            }
        }


        const k = clusters.clusters.length
        // get indices of remaining clusters
        const cf = [...Array(k).keys()].filter(i => clusterLeft.has(i))

        if (cf.length === 0) {
            console.debug("no more groups left")
            return
        }

        let next, tmp

        if (clsOrder.value.length < props.maxRounds) {
            if (clsOrder.value.length > 0) {
                // look at mean match score to previous groups
                const inInv = clsOrder.value
                    .filter(d => inventory.value[d.index] !== null)
                    .map(d => itemsToUse.findIndex(dd => dd.id === inventory.value[d.index].id))

                tmp = cf.map(i => {
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
            } else {
                // get clusters with the highest distances between each other
                const subset = cf.slice(0, props.numClusters*2)
                tmp = subset.map(i => {
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
            }
            // sort from high to low match value
            tmp.sort((a, b) => {
                if (b.value === a.value) {
                    return clusters.size[b.index] - clusters.size[a.index]
                }
                return b.value - a.value
            })
            next = tmp.slice(0, props.numClusters).map(d => d.index)

            next.forEach(i => clusterLeft.delete(i))

            const nextObj = {
                index: 0,
                list: next,
                selected: null,
                show: next.map(ci => randomInteger(0, clusters.clusters[ci].length-1))
            }

            // log which clusters are shown to the user
            log.push({
                desc: "cluster options",
                size:  clsOrder.value.length,
                clusters: next.map((ci, i) => ({
                    id: ci,
                    visible: clusters.clusters[ci][nextObj.show[i]].id,
                    items: clusters.clusters[ci].map(d => d.id)
                })),
            })

            clsOrder.value.unshift(nextObj)
            sims.value.unshift(0)
            inventory.value.unshift(null)
            clsReroll.unshift([])
            clsOrder.value.forEach((d, i) => d.index = i)
        }

        // update list of candidates
        const cand = getCandidates()
        candidateItems = cand.flat()
        candidates.value = cand.map(list => list.map(d => d.id))
    }

    function chooseItemSave(item, index, cluster, clusterIdx, goNext=false) {
        clsOrder.value[index].show[clusterIdx] = clusters.clusters[cluster].findIndex(d => d.id === item.id)
        inventory.value[index] = item
        log.push({
            desc: "click item in cluster",
            step: clsOrder.value.length-index,
            cluster: cluster,
            item: item.id
        })

        if (index > 0 || clsOrder.value.length === props.maxRounds || goNext) {
            chooseItem(index, cluster)
        }
    }

    function chooseItem(index, clusterIndex) {
        if (index > 0) {
            for (let i = 0; i < index; ++i) {
                clsOrder.value[i].list.forEach(ci => clusterLeft.add(ci))
                clsReroll[i].forEach(ci => clusterLeft.add(ci))
            }
            clsOrder.value = clsOrder.value.slice(index)
            sims.value = sims.value.slice(index)
            clsReroll = clsReroll.slice(index)
            inventory.value = inventory.value.slice(index)
            clsOrder.value.forEach((d, i) => d.index = i)
            index = 0
        }
        clsOrder.value[index].selected = clusterIndex
        sims.value[index] = 0.75
        log.push({
            desc: "click cluster",
            step: clsOrder.value.length-index,
            cluster: clusterIndex
        })
        nextItem()
    }

    function reset(update=true) {
        log = []
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
        reset(true)
    })

</script>