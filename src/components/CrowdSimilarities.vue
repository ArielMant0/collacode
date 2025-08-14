<template>
    <SidePanel v-model="model" ref="el" title="Crowd Similarities" width="45%" @close="close" @show="onShow">
        <template #text>
            <div class="d-flex align-center">
                <v-btn
                    icon="mdi-magnify-minus"
                    density="comfortable"
                    variant="text"
                    rounded="small"
                    @click="resetZoom"/>
                <v-btn
                    class="ml-1"
                    icon="mdi-magnify-plus"
                    density="comfortable"
                    variant="text"
                    rounded="small"
                    @click="focusTarget"/>

                <v-text-field v-model="search"
                    label="Search by name (min. 3 characters)"
                    variant="outlined"
                    density="compact"
                    class="mb-2 mt-4"
                    style="width: 75%;"
                    @keyup.prevent="onSearchKey"
                    hide-details
                    hide-spin-buttons
                    clearable>
                </v-text-field>

                <div v-if="search" class="text-caption d-flex">
                    <div style="min-width: 70px;"><b>{{ searchHits.length }} {{ searchHits.length === 1 ? 'hit' : 'hits' }}</b></div>
                    <div style="width: 100%; max-height: 100px; overflow-y: auto;">
                        <div v-for="item in searchHits"
                            class="cursor-pointer hover-it"
                            @click="setSearchTarget(item)">
                            {{ item.name }}
                        </div>
                    </div>
                </div>

            </div>
            <NodeLink v-if="simNodes.length > 0 && simLinks.length > 0"
                ref="nl"
                :nodes="simNodes"
                :links="simLinks"
                :width="graphWidth"
                :height="graphHeight"
                use-data-manager
                weight-attr="value"
                value-attr="unique"
                :min-value="2"
                image-attr="teaser"
                @click="item => clickNode(item.id)"
                :radius="50"
                :target="clickedItem.id"/>

            <v-sheet rounded="sm" class="mt-2" style="width: 100%; max-height: 250px; overflow-y: auto;">
                <div class="d-flex flex-wrap justify-start">
                    <div v-for="item in clickedItem.connected" class="mr-1 mb-1">
                        <v-progress-linear color="primary" v-model="item.value">
                            {{ item.value }}
                        </v-progress-linear>
                        <ItemTeaser
                            :id="item.id"
                            prevent-open
                            @click="clickNode(item.id)"
                            :width="100"
                            :height="50"/>
                    </div>
                </div>
            </v-sheet>
        </template>
    </SidePanel>
</template>

<script setup>
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { onMounted, reactive, useTemplateRef, watch } from 'vue';
    import { useTooltip } from '@/store/tooltip';
    import NodeLink from './vis/NodeLink.vue';
    import ItemTeaser from './items/ItemTeaser.vue';
    import SidePanel from './dialogs/SidePanel.vue';
    import { sortObjByValue } from '@/use/sorting';
    import { max } from 'd3';

    const times = useTimes()
    const tt = useTooltip()

    const model = defineModel()
    const props = defineProps({
        target: { type: Object, required: false },
    })

    const el = useTemplateRef("el")
    const graphWidth = ref(300)
    const graphHeight = ref(300)

    const search = ref("")
    const searchHits = computed(() => {
        if (search.value && search.value.length > 2) {
            const reg = new RegExp(search.value, "gi")
            return graphData.nodes.filter(d => reg.test(d.name, d.id))
        }
        return []
    })

    const nl = useTemplateRef("nl")
    const simNodes = ref([])
    const simLinks = ref([])
    const clickedItem = reactive({
        id: null,
        limit: 16,
        numSame: 0,
        numDiff: 0,
        connected: [],
        same: [],
        different: []
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
            nl.value.focus(props.target?.id)
        }
    }
    function setSearchTarget(item) {
        search.value = ""
        if (item) {
            nl.value.focus(item.id)
        }
    }
    function onSearchKey(event) {
        if (search.value && search.value.length > 0) {
            if (event.code === "Escape") {
                search.value = []
            } else if (event.code === "Enter") {
                if (searchHits.value.length > 0) {
                    setSearchTarget(searchHits.value[0])
                }
            }
        }
    }

    function clickNode(id=null) {

        id = id && id !== clickedItem.id ? id : props.target.id
        const connected = id ? DM.getDataItem("similarity_item", id) : []
        connected.sort(sortObjByValue("value", { ascending: false }))
        const maxValue = max(connected, d => d.count)
        clickedItem.connected = connected.map(d => ({ id: d.item_id === id ? d.target_id : d.item_id, value: Math.round(d.count/maxValue*100) }))
        clickedItem.id = id
        if (id && nl.value) {
            nl.value.focus(id)
        }

        // if (!props.target) return

        // get item ids for target and clicked item
        // const tagIds = app.showAllUsers ?
        //     props.target.allTags.map(d => d.id) :
        //     props.target.tags.filter(d => d.created_by === app.activeUserId).map(d => d.tag_id)

        // const itemObj = DM.getDataItem("items", item.id)
        // const itemTagIds = app.showAllUsers ?
        //     itemObj.allTags.map(d => d.id) :
        //     itemObj.tags.filter(d => d.created_by === app.activeUserId).map(d => d.tag_id)

        // const targetTags = new Set(tagIds)
        // const itemTags = new Set(itemTagIds)

        // const int = targetTags.intersection(itemTags)
        // const diff1 = itemTags.difference(targetTags)
        // const diff2 = targetTags.difference(itemTags)

        // clickedItem.numSame = int.size
        // clickedItem.numDiff = diff1.size + diff2.size

        // const half = Math.floor(clickedItem.limit / 2)
        // clickedItem.same = props.target.allTags.filter(t => int.has(t.id)).slice(0, clickedItem.limit)
        // clickedItem.different = itemObj.allTags.filter(t => diff1.has(t.id)).slice(0, half)
        //     .concat(props.target.allTags.filter(t => diff2.has(t.id)).slice(0, half))
        // clickedItem.id = item.id
    }

    // function onItemHover(item, event) {
    //     if (item) {
    //         const [mx, my] = pointer(event, document.body)
    //         tt.show(
    //             `<div>
    //                 <img src="${item.teaser}" style="max-height: 100px; object-fit: contain;"/>
    //                 <div class="mt-1 text-caption">
    //                     <div>${item.name}</div>
    //                 </div>
    //             </div>`,
    //             mx, my
    //         )
    //     } else {
    //         tt.hide()
    //     }
    // }

    function onShow() {
        if (el.value) {
            const rect = el.value.getNodeRect()
            if (rect) {
                graphWidth.value = Math.max(300, rect.width * 0.95)
                graphHeight.value = Math.max(300, rect.height * 0.925-350)
            }
        }
    }

    async function read() {
        const graph = DM.getGraph()
        simNodes.value = graph.nodes
        simLinks.value = graph.links
        clickNode(null)
    }

    onMounted(read)

    watch(() => times.all, read)

</script>
