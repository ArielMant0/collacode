<template>
    <SidePanel v-model="model" ref="el" title="Crowd Similarities" width="50vw" @close="close" @show="onShow">
        <template #text>
            <div class="d-flex align-center mb-1">
                <v-btn
                    icon="mdi-magnify-minus"
                    density="comfortable"
                    variant="text"
                    rounded="small"
                    @click="resetZoom"/>
                <v-btn
                    class="ml-1 mr-2"
                    icon="mdi-magnify-plus"
                    density="comfortable"
                    variant="text"
                    rounded="small"
                    @click="focusTarget"/>

                <v-text-field v-model="search"
                    label="Search by name (min. 3 characters)"
                    variant="outlined"
                    density="compact"
                    @keyup.prevent="onSearchKey"
                    hide-details
                    hide-spin-buttons
                    clearable>
                </v-text-field>
            </div>

            <div v-if="search && search.length" class="text-caption d-flex mb-1">
                <div style="min-width: 70px;"><b>{{ searchHits.length }} {{ searchHits.length === 1 ? 'hit' : 'hits' }}</b></div>
                <div style="width: 100%; max-height: 100px; overflow-y: auto;">
                    <div v-for="item in searchHits"
                        class="cursor-pointer hover-it"
                        @click="setSearchTarget(item)">
                        {{ item.name }}
                    </div>
                </div>
            </div>

            <NodeLink v-if="graph.nodes.length > 0 && graph.links.length > 0"
                ref="nl"
                :nodes="graph.nodes"
                :links="graph.links"
                :width="graphWidth"
                :height="graphHeight"
                :target-neighbor-color="neighCol"
                use-data-manager
                edge-color-attr="distNorm"
                weight-attr="value"
                :value-attr="nodeValueAttr"
                :min-value="minEdgeValue"
                image-attr="teaser"
                selectable
                @click="item => clickNode(item.id)"
                :radius="50"
                :target="clickedItem.id"
                />

            <v-sheet rounded="sm" class="mt-2 d-flex align-start text-caption" style="width: 100%;">
                <div style="width: 75%; max-height: 20vh; overflow-y: auto;" class="d-flex flex-wrap justify-start">
                    <div v-for="item in clickedItem.connected" :key="'con_'+item.id" class="mr-1 mb-2">
                        <v-progress-linear
                            v-model="item.value"
                            height="5"
                            color="#8f027a"
                            class="text-caption mb-1"
                            >
                        </v-progress-linear>
                        <v-progress-linear
                            height="5"
                            v-model="item.distNorm"
                            :color="neighCol(item.distNorm/100)"
                            class="text-caption mb-1"
                            >
                        </v-progress-linear>
                        <ItemTeaser
                            :id="item.id"
                            prevent-open
                            prevent-tooltip
                            @click="clickNode(item.id)"
                            @hover="(_i, event) => onNeighborHover(item.id, event)"
                            :width="100"
                            :height="50"/>
                    </div>
                </div>

                <div style="width: 25%; max-height: 20vh; overflow-y: auto;" class="pl-4">
                    <div v-for="tag in clickedItem.same" :key="tag.id">
                        <TagText :id="tag.id"/> ({{ tag.count }})
                    </div>
                </div>
            </v-sheet>
        </template>
    </SidePanel>
</template>

<script setup>
    import * as d3 from 'd3'
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { onMounted, reactive, ref, useTemplateRef, watch } from 'vue';
    import { useTooltip } from '@/store/tooltip';
    import NodeLink from './vis/NodeLink.vue';
    import ItemTeaser from './items/ItemTeaser.vue';
    import SidePanel from './dialogs/SidePanel.vue';
    import { sortObjByValue } from '@/use/sorting';
    import { max } from 'd3';
    import { useWindowSize } from '@vueuse/core';
    import TagText from './tags/TagText.vue';
    import { getItemDistances } from '@/use/clustering';

    const times = useTimes()
    const tt = useTooltip()

    const model = defineModel()
    const props = defineProps({
        target: { type: Object, required: false },
    })

    const el = useTemplateRef("el")
    const graphWidth = ref(300)
    const graphHeight = ref(300)

    let neighCol, normDist
    let pwd, idToIndex

    const minEdgeValue = 2
    const nodeValueAttr = "unique"

    const { width, height } = useWindowSize()

    const search = ref("")
    const searchHits = computed(() => {
        if (search.value && search.value.length > 2) {
            const reg = new RegExp(search.value, "gi")
            return graph.nodes.filter(d => reg.test(d.name, d.id))
        }
        return []
    })

    const nl = useTemplateRef("nl")
    const clickedItem = reactive({
        id: null,
        limit: 16,
        numSame: 0,
        numDiff: 0,
        connected: [],
        same: [],
        different: {},
    })
    const graph = reactive({
        nodes: [],
        links: []
    })

    function close() {
        tt.hide()
    }
    function resetZoom() {
        if (nl.value) {
            nl.value.resetZoom()
        }
    }
    function focusTarget() {
        if (nl.value) {
            clickNode(props.target?.id)
        }
    }
    function setSearchTarget(item) {
        search.value = ""
        if (item) {
            clickNode(item.id)
        }
    }
    function onSearchKey(event) {
        if (event.code === "Escape") {
            search.value = []
        } else if (search.value && search.value.length > 2) {
            if (event.code === "Enter" && searchHits.value.length > 0) {
                setSearchTarget(searchHits.value[0])
            }
        }
    }

    function clickNode(id=null) {

        id = id && id !== clickedItem.id ? id : props.target?.id

        const connected = DM.getDataItem("similarity_item", id)
            .filter(d => d.unique_clients >= minEdgeValue)

        if (connected) {
            connected.sort(sortObjByValue("value", { ascending: false }))
            const maxValue = max(connected, d => d.value)
            clickedItem.connected = connected.map(d => {
                const other = d.item_id === id ? d.target_id : d.item_id
                const dist = pwd[idToIndex.get(id)][idToIndex.get(other)]
                return  {
                    id: other,
                    value: Math.round(d.value/maxValue*100),
                    distNorm: Number.isFinite(dist) ?
                        Math.round(normDist(dist) * 100) :
                        0
                }
            })

            const tagCounts = new Map()
            const ids = new Set(connected.map(d => d.item_id === id ? d.target_id : d.item_id))

            const targetTags = new Set(DM.getDataItem("items", id).allTags.map(t => t.id))
            const neighborDiffs = {}

            DM.getDataBy("items", d => ids.has(d.id)).forEach(d => {
                
                const diff = { plus: [], minus: [] }

                d.allTags.forEach(t => {
                    if (!targetTags.has(t.id)) {
                        diff.plus.push(t.name)
                    }
                    // increase tag count
                    if (tagCounts.has(t.id)) {
                        tagCounts.get(t.id).count++
                    } else {
                        tagCounts.set(t.id, { id: t.id, name: t.name, count: 1 })
                    }
                })

                targetTags.forEach(tid => {
                    if (!d.allTags.find(t => t.id === tid)) {
                        diff.minus.push(DM.getDataItem("tags_name", tid))
                    }
                })

                neighborDiffs[d.id] = diff
            })
            // get most common tags for all neighbors
            const mostCommon = Array.from(tagCounts.values())
            mostCommon.sort((a, b) => b.count - a.count)
            clickedItem.same = mostCommon.slice(0, 15)

            clickedItem.different = neighborDiffs

            clickedItem.id = id
            if (id && nl.value) {
                nl.value.focus(id)
            }
        } else {
            clickedItem.same = []
            clickedItem.different = {}
            clickedItem.connected = []
            clickedItem.id = null
        }

    }

    function onNeighborHover(itemId, event) {
        if (itemId) {
            const [mx, my] = d3.pointer(event, document.body)
            const maxTags = 10

            const plus = clickedItem.different[itemId].plus
                .slice(0, maxTags)
                .reduce((acc, name) => acc + `<div>+ ${name}</div>`, "")
            const plusExtra = clickedItem.different[itemId].plus.length-maxTags > 0 ?
                `<div><it>and ${clickedItem.different[itemId].plus.length-maxTags} more..</it></div>` :
                ""

            const minus = clickedItem.different[itemId].minus
                .slice(0, maxTags)
                .reduce((acc, name) => acc + `<div>- ${name}</div>`, "")
            const minusExtra = clickedItem.different[itemId].minus.length-maxTags > 0 ?
                `<div><it>and ${clickedItem.different[itemId].minus.length-maxTags} more..</it></div>` :
                ""

            tt.show(
                `<div class="d-flex align-start text-caption">
                    <div class="mr-1">
                        ${plus}
                        ${plusExtra}
                    </div>
                    <div class="ml-1">
                        ${minus}
                        ${minusExtra}
                    </div>
                </div>`,
                mx, my
            )
        } else {
            tt.hide()
        }
    }

    function onShow() {
        if (el.value) {
            const rect = el.value.getNodeRect()
            if (rect) {
                graphWidth.value = Math.max(250, Math.round(rect.width+25))
                graphHeight.value = Math.max(250, Math.round(rect.height*0.985)-250)
            }
        }
    }

    async function read() {
        if (DM.hasGraph()) {
            const items = DM.getData("items", false)
            idToIndex = new Map(items.map((d,i) => ([d.id, i])))
            // get pairwise distances between items
            pwd = getItemDistances(items)

            const g = DM.getGraph()
            // normalize distances to [0, 1] range
            normDist = d3.scaleLinear()
                .domain([0, d3.max(pwd.flat().filter(d => Number.isFinite(d)))])
                .range([1, 0])

            g.links.forEach(d => d.distNorm = normDist(
                pwd[idToIndex.get(d.source)][idToIndex.get(d.target)]
            ))

            neighCol = d3.scaleSequential(d3.interpolateCool).domain([0, 1])

            graph.nodes = g.nodes
            graph.links = g.links
            clickNode(props.target?.id)
        } else {
            times.needsReload("similarity")
        }
    }

    onMounted(read)

    watch(() => Math.max(times.all, times.similarity, times.tagging), read)
    watch(() => ([width, height]), onShow)

</script>
