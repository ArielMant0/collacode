<template>
    <div style="width: min-content" class="pa-2">
        <div style="text-align: center;">
            <v-btn
                :color="selectionItems.length > 0 ? 'primary' : 'default'"
                class="mb-4"
                density="comfortable"
                :disabled="selectionItems.length === 0"
                @click="submit">
                done
            </v-btn>
        </div>

        <h3 style="text-align: center;" class="mt-2 mb-4">Find up to {{ maxSelect }} similar seed {{ app.itemName }}s!</h3>

        <div class="d-flex justify-center align-center mb-2">
            <v-btn
                color="error"
                class="mr-2"
                density="comfortable"
                variant="outlined"
                prepend-icon="mdi-delete"
                @click="resetRerolls">
                reset rerolls
            </v-btn>
            <v-btn
                color="primary"
                class="ml-2"
                density="comfortable"
                variant="outlined"
                prepend-icon="mdi-sync"
                @click="reroll">
                reroll
            </v-btn>
        </div>
        <div>
            <div class="d-flex align-start justify-center">
                <ItemSimilarityRow v-for="(index, idx2) in clsOrder.list"
                    :items="clusters.clusters[index]"
                    :show-index="clsOrder.show[idx2]"
                    :targets="target ? [target] : []"
                    :image-width="imageWidth"
                    :image-height="imageHeight"
                    :highlights="selection.filter(d => d && d.cluster === index).map(d => d.id)"
                    class="mb-1 mr-3 ml-3"
                    hide-buttons
                    vertical
                    @dragstart-item="d => onStartDrag(d.id, 'cluster-drag')"
                    @click="d => toggleItem(d.id, 'cluster')"
                    @click-item="d => toggleItem(d.id, 'cluster')"/>
            </div>

            <div class="d-flex justify-space-around mt-4 mb-8 pa-2">
                <div v-for="(sel, i) in selection" class="mr-1 ml-1">
                    <div style="text-align: center;" class="text-caption">{{ app.itemNameCaptial }} {{ i+1 }}</div>
                    <ItemTeaser v-if="sel"
                        :id="sel.id"
                        prevent-open
                        prevent-context
                        rounded
                        @click="removeSelection(i, 'selection')"
                        @dragover.prevent
                        @drop="onDrop(i)"
                        @dragstart="onStartDrag(sel.id, 'selection-drag')"
                        draggable
                        :width="imageWidth"
                        :height="imageHeight"/>
                    <v-card v-else
                        :min-width="imageWidth"
                        :min-height="imageHeight"
                        :max-width="imageWidth"
                        :max-height="imageHeight"
                        @dragover.prevent
                        @drop="onDrop(i)"
                        color="surface-light"
                        class="d-flex pa-1 align-center justify-center prevent-select">
                        <v-icon size="large">mdi-image-area</v-icon>
                    </v-card>
                </div>
            </div>

            <div style="text-align: center;">suggested {{ app.itemName }}s</div>

            <v-sheet class="pa-2" rounded border :style="{ minHeight: ((miniImageHeight+5)*3)+'px' }">
                <div class="d-flex justify-start align-start">
                    <div v-for="(list, cidx) in candidates" :style="{ maxWidth: Math.floor(100/selectionItems.length)+'%' }">
                        <div class="d-flex flex-wrap justify-center">
                            <ItemTeaser v-for="id in list"
                                class="mr-1 mb-1"
                                :id="id"
                                :border-color="id === getSelectedId(cidx) ? theme.current.value.colors.secondary : undefined"
                                :border-size="3"
                                prevent-open
                                prevent-context
                                @click="toggleItem(id, 'suggestions')"
                                draggable
                                @dragstart="onStartDrag(id, 'suggestions-drag')"
                                :width="miniImageWidth"
                                :height="miniImageHeight"/>
                        </div>
                    </div>
                </div>
            </v-sheet>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ref, onMounted, reactive, computed } from 'vue';
    import DM from '@/use/data-manager';
    import { getItemClusters } from '@/use/clustering';
    import ItemSimilarityRow from './ItemSimilarityRow.vue';
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

    const selection = ref(new Array(props.maxSelect))
    const selectionItems = computed(() => selection.value.filter(d => d !== null && d !== undefined))
    const candidates = ref([])
    const clsOrder = reactive({
        list: [],
        selected: new Set(),
        show: []
    })

    const miniImageWidth = computed(() => Math.max(50, Math.round(props.imageWidth * 0.66)))
    const miniImageHeight = computed(() => Math.round(miniImageWidth.value * 0.5))

    let itemsToUse
    let log = []
    let candidateItems = []
    let clusters = null, maxClsSize = 0

    const clusterLeft = new Set()

    const ALL_TAGS = ref(true)
    const FREQ_WEIGHTS = ref(true)

    let dragId = null, dragSrc = null

    function onStartDrag(id, source="") {
        dragId = id
        dragSrc = source
    }

    function onDrop(target=0) {
        if (target < props.maxSelect) {
            toggleItem(dragId, dragSrc, target)
        }
        dragId = null
        dragSrc = null
    }

    function getFreeSelectionIndex() {
        for (let i = 0; i < props.maxSelect; ++i) {
            if (selection.value[i] === undefined || selection.value[i] === null) {
                return i
            }
        }
        return props.maxSelect-1
    }

    function getSelectedId(index) {
        return selection.value[index] ? selection.value[index].id : null
    }

    function getCandidates() {
        if (selectionItems.value.length === 0) return []

        // get candidates for all selected items
        const num = Math.min(selectionItems.value.length, props.maxSelect)

        const counts = []
        let rest = props.maxItems
        let step = Math.floor(props.maxItems / num)
        for (let i = 0; i < num; ++i) {
            counts.push(i === num-1 ? rest : step)
            rest -= step
        }

        const final = []
        const idSet = new Set()

        selectionItems.value.forEach(d => idSet.add(d.id))

        const k = clusters.clusters.length
        // get indices of remaining clusters
        const cf = [...Array(k).keys()]

        selectionItems.value.forEach((sel, i) => {
            const s1 = Math.ceil(counts[i] * 0.5)
            // for half the items, select the most similar items
            const cands1 = clusters.pwd[sel.index].map((v, j) => ({ index: j, value: v }))
            cands1.sort((a, b) => a.value - b.value)

            const added = []
            // add similar items
            for (let j = 0; j < cands1.length && added.length < s1; ++j) {
                const item = itemsToUse[cands1[j].index]
                if (added.length < s1 && (!idSet.has(item.id) || j === 0)) {
                    added.push(item)
                    idSet.add(item.id)
                }
            }

            // for the other half, select items from similar clusters
            const cands2 = cf.map(d => {
                let score
                if (sel.cluster === d) {
                    score = 1
                } else {
                    score = matchValue(
                        clusters.minDistances[d][sel.cluster],
                        clusters.maxDistances[d][sel.cluster],
                        clusters.size[d],
                        1, // should be similar to chosen cluster
                    )
                }

                return {
                    index: d,
                    value: score,
                }
            })
            // sort from high to low match value
            cands2.sort((a, b) => {
                if (b.value === a.value) {
                    return clusters.size[b.index] - clusters.size[a.index]
                }
                return b.value - a.value
            })

            // add items from similar clusters
            for (let j = 0; j < cands2.length && added.length < counts[i]; ++j) {
                const list = clusters.clusters[cands2[j].index]
                list.forEach(item => {
                    if (added.length < counts[i] && !idSet.has(item.id)) {
                        added.push(item)
                        idSet.add(item.id)
                    }
                })
            }

            final.push(added)
        })

        return final
    }

    function submit() {
        logAction({
            desc: "submit suggested items",
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

    function resetRerolls() {
        logAction({ desc: "reset rerolls" })
        for (let i = 0; i < clusters.clusters.length; ++i) {
            clusterLeft.add(i)
        }
        nextClusters()
    }
    function reroll() {
        logAction({
            desc: "reroll",
            clusters: clsOrder.list
        })
        nextClusters()
    }

    async function init() {
        if (!clusters) {
            if (itemsToUse.length === 0) {
                return console.debug("no items")
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
                return console.debug("no clusters found")
            }
        }

        nextClusters()
    }

    async function nextClusters() {

        const k = clusters.clusters.length
        // get indices of remaining clusters
        const cf = [...Array(k).keys()].filter(i => clusterLeft.has(i))

        if (cf.length === 0) {
            console.debug("no more clusters left")
            return
        }

        // get next clusters with the highest distances between each other
        const subset = cf.slice(0, props.numClusters*2)
        const tmp = subset.map(i => {
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
                value: d3.median(scores),
            }
        })
        // sort from high to low match value
        tmp.sort((a, b) => {
            if (b.value === a.value) {
                return clusters.size[b.index] - clusters.size[a.index]
            }
            return b.value - a.value
        })

        const fixed = clsOrder.list
            .map((d, i) => ({ cluster: d, index: i }))
            .filter(d => clsOrder.selected.has(d.cluster))

        const next = new Array()
        fixed.forEach(d => next[d.index] = d.cluster)

        for (let i = 0, j = 0; i < props.numClusters; ++i) {
            if (next[i] === undefined) {
                next[i] = tmp[j].index
                j++
                clusterLeft.delete(next[i])
            }
        }

        // log which clusters are shown to the user
        logAction({
            desc: "set cluster options",
            clusters: next.map((ci, i) => ({
                id: ci,
                items: clusters.clusters[ci].map(d => d.id)
            })),
        })

        clsOrder.list = next
        clsOrder.show = next.map(() => 0)
    }

    function updateCandidates() {
        // update list of candidates
        const cand = getCandidates()
        candidateItems = cand.flat()
        candidates.value = cand.map(list => list.map(d => d.id))
    }

    function toggleItem(id, source="", target=null) {
        const index = selection.value.findIndex(d => d && d.id === id)

        // get the new index
        const newIdx = target !== null ? target : getFreeSelectionIndex()
        if (newIdx < 0) return

        const add = index < 0 || selection.value[index].id !== id
        const move = index >= 0 && target !== null && newIdx !== index
        const replace = index < 0 && newIdx >= 0 && selection.value[newIdx]

        // move the item to another position
        if (move) {
            selection.value[newIdx] = selection.value[index]
            selection.value[index] = null
            updateCandidates()
        } else if (replace || add) {
            // get the necessary data
            const clsIndex = clusters.clusters.findIndex(list => list.find(d => d.id === id))
            const selObj = {
                id: id,
                cluster: clsIndex,
                index: itemsToUse.findIndex(d => d.id === id)
            }
            // perform replacement or adding
            if (replace) {
                replaceSelection(newIdx, selObj, source)
            } else {
                addSelection(newIdx, selObj, source)
            }
        } else {
            removeSelection(index, source)
        }
    }

    function addSelection(index, object, source="") {
        logAction({
            desc: "add item",
            source: source,
            item: object.id
        })
        // add the cluster to the list of selected clusters
        clsOrder.selected.add(object.cluster)
        // set the selected item
        selection.value[index] = object
        updateCandidates()
    }

    function removeSelection(index, source="") {
        if (selection.value[index]) {
            logAction({
                desc: "remove item",
                source: source,
                item: selection.value[index].id
            })

            const c = selection.value[index].cluster
            const numCls = selectionItems.value.reduce((acc, d) => acc + (d.cluster === c ? 1 : 0), 0)
            // remove cluster highlight (if this was the only related item)
            if (numCls === 1) {
                clsOrder.selected.delete(selection.value[index].cluster)
            }
            selection.value[index] = null
            // update candidates for suggestion
            updateCandidates()
        }
    }

    function replaceSelection(index, replacement, source="") {
        if (selection.value[index]) {
            logAction({
                desc: "replace item",
                source: source,
                item: replacement.id,
                previous: selection.value[index].id
            })
            const c = selection.value[index].cluster
            const numCls = selectionItems.value.reduce((acc, d) => acc + (d.cluster === c ? 1 : 0), 0)
            // remove cluster highlight (if this was the only related item)
            if (numCls === 1) {
                clsOrder.selected.delete(selection.value[index].cluster)
            }
            selection.value[index] = replacement
            clsOrder.selected.add(replacement.cluster)
            // update candidates for suggestion
            updateCandidates()
        }
    }

    function reset(update=true) {
        log = []
        clusterLeft.clear()
        itemsToUse = DM.getDataBy("items", d => d.allTags.length > 0 && (!props.target || d.id !== props.target))
        clusters = null
        clsOrder.list = []
        clsOrder.selected.clear()
        clsOrder.show = []
        selection.value = new Array(props.maxSelect)
        candidates.value = []
        candidateItems = []
        if (update) {
            init()
        }
    }

    function logAction(obj) {
        log.push(obj)
        // console.log("log", obj)
    }

    defineExpose({ reset })

    onMounted(function() {
        reset(false)
        init()
    })

</script>