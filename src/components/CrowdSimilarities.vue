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
                use-data-manager
                weight-attr="value"
                value-attr="unique"
                :min-value="2"
                image-attr="teaser"
                @click="item => clickNode(item.id)"
                :radius="50"
                :target="clickedItem.id"/>

            <v-sheet rounded="sm" class="mt-2" style="width: 100%; max-height: 200px; overflow-y: auto;">
                <div class="d-flex flex-wrap justify-start">
                    <div v-for="item in clickedItem.connected" :key="'con_'+clickedItem.id" class="mr-1 mb-1">
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
    import { onMounted, reactive, ref, useTemplateRef, watch } from 'vue';
    import { useTooltip } from '@/store/tooltip';
    import NodeLink from './vis/NodeLink.vue';
    import ItemTeaser from './items/ItemTeaser.vue';
    import SidePanel from './dialogs/SidePanel.vue';
    import { sortObjByValue } from '@/use/sorting';
    import { max } from 'd3';
    import { useWindowSize } from '@vueuse/core';

    const times = useTimes()
    const tt = useTooltip()

    const model = defineModel()
    const props = defineProps({
        target: { type: Object, required: false },
    })

    const el = useTemplateRef("el")
    const graphWidth = ref(300)
    const graphHeight = ref(300)

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
        different: [],
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
        if (connected) {
            connected.sort(sortObjByValue("value", { ascending: false }))
            const maxValue = max(connected, d => d.value)
            clickedItem.connected = connected.map(d => ({
                id: d.item_id === id ? d.target_id : d.item_id,
                value: Math.round(d.value/maxValue*100)
            }))
            clickedItem.id = id
            if (id && nl.value) {
                nl.value.focus(id)
            }
        } else {
            clickedItem.connected = []
            clickedItem.id = []
        }

    }

    function onShow() {
        if (el.value) {
            const rect = el.value.getNodeRect()
            if (rect) {
                graphWidth.value = Math.max(250, Math.min(rect.width-10, rect.width * 0.985))
                graphHeight.value = Math.max(250, rect.height * 0.925-300)
            }
        }
    }

    async function read() {
        if (DM.hasGraph()) {
            const g = DM.getGraph()
            graph.nodes = g.nodes
            graph.links = g.links
            clickNode(props.target?.id)
        } else {
            times.needsReload("similarity")
        }
    }

    onMounted(read)

    watch(() => Math.max(times.all, times.similarity), read)
    watch(() => ([width, height]), onShow)

</script>
