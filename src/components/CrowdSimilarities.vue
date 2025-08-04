<template>
    <SidePanel v-model="model" ref="el" title="Crowd Similarities" @close="close" @show="onShow">
        <template #text>
            <div class="mb-2 d-flex align-center">
                <v-btn
                    icon="mdi-magnify-minus"
                    density="comfortable"
                    variant="text"
                    rounded="sm"
                    @click="resetZoom"/>
                <v-btn
                    class="ml-1"
                    icon="mdi-magnify-plus"
                    density="comfortable"
                    variant="text"
                    rounded="sm"
                    @click="focusTarget"/>
                <v-text-field v-model="searchTerm"
                    label="Search"
                    append-inner-icon="mdi-magnify"
                    @click:append-inner="focusSearch"
                    variant="outlined"
                    density="compact"
                    class="ml-1"
                    clearable
                    single-line
                    hide-details/>
            </div>
            <NodeLink v-if="target && simNodes.length > 0 && simLinks.length > 0"
                ref="nl"
                :nodes="simNodes"
                :links="simLinks"
                :width="graphWidth"
                :height="graphHeight"
                weight-attr="value"
                image-attr="teaser"
                @click="clickNode"
                :radius="50"
                :target="target.id"/>

            <v-sheet rounded="sm" class="d-flex mt-2" style="width: 100%; max-height: 300px; overflow-y: auto;">
                <div>
                    <ItemTeaser v-if="target" :id="target.id" :width="120" :height="60"/>
                    <ItemTeaser v-if="clickedItem.id" class="mt-2" :id="clickedItem.id" :width="120" :height="60"/>
                </div>
                <div style="width: 40%;" class="ml-2">
                    <h4>Shared tags ({{ clickedItem.numSame }})</h4>
                    <div v-for="t in clickedItem.same">{{ t.name }}</div>
                    <div v-if="clickedItem.numSame > clickedItem.limit" class="text-caption font-italic">and {{ clickedItem.numSame-clickedItem.limit  }} more ..</div>
                </div>
                <div style="width: 40%;" class="ml-2">
                    <h4>Different tags ({{ clickedItem.numDiff }})</h4>
                    <div v-for="t in clickedItem.different">{{ t.name }}</div>
                    <div v-if="clickedItem.numDiff > clickedItem.limit" class="text-caption font-italic">and {{ clickedItem.numDiff-clickedItem.limit  }} more ..</div>
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
    import { mediaPath } from '@/use/utility';
    import { useApp } from '@/store/app';
    import ItemTeaser from './items/ItemTeaser.vue';
    import SidePanel from './dialogs/SidePanel.vue';

    const app = useApp()
    const times = useTimes()
    const tt = useTooltip()

    const model = defineModel()
    const props = defineProps({
        target: { type: Object, required: false },
    })

    const el = useTemplateRef("el")
    const graphWidth = ref(300)
    const graphHeight = ref(300)

    const searchTerm = ref("")

    const nl = useTemplateRef("nl")
    const simNodes = ref([])
    const simLinks = ref([])
    const clickedItem = reactive({
        id: null,
        limit: 16,
        numSame: 0,
        numDiff: 0,
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
            nl.value.focus()
        }
    }
    function focusSearch() {
        if (nl.value && searchTerm.value && searchTerm.value.length > 0) {
            const regex = new RegExp(searchTerm.value, "gi")
            const item = simNodes.value.find(d => regex.test(d.name))
            if (item) {
                nl.value.focus(item.id)
            }
        }
    }

    function clickNode(item) {
        if (!props.target) return

        // get item ids for target and clicked item
        const tagIds = app.showAllUsers ?
            props.target.allTags.map(d => d.id) :
            props.target.tags.filter(d => d.created_by === app.activeUserId).map(d => d.tag_id)

        const itemObj = DM.getDataItem("items", item.id)
        const itemTagIds = app.showAllUsers ?
            itemObj.allTags.map(d => d.id) :
            itemObj.tags.filter(d => d.created_by === app.activeUserId).map(d => d.tag_id)

        const targetTags = new Set(tagIds)
        const itemTags = new Set(itemTagIds)

        const int = targetTags.intersection(itemTags)
        const diff1 = itemTags.difference(targetTags)
        const diff2 = targetTags.difference(itemTags)

        clickedItem.numSame = int.size
        clickedItem.numDiff = diff1.size + diff2.size

        const half = Math.floor(clickedItem.limit / 2)
        clickedItem.same = props.target.allTags.filter(t => int.has(t.id)).slice(0, clickedItem.limit)
        clickedItem.different = itemObj.allTags.filter(t => diff1.has(t.id)).slice(0, half)
            .concat(props.target.allTags.filter(t => diff2.has(t.id)).slice(0, half))
        clickedItem.id = item.id
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

        // get similarity data
        const data = DM.getData("similarity", false)

        const sn = [], sl = []
        const nodeSet = new Set()

        const items = DM.getData("items", false)

        // construct the graph
        data.forEach(d => {
            const id = Number(d.target_id)
            const oid = Number(d.item_id)

            // add the main node
            if (!nodeSet.has(id)) {
                const obj = { id: id, name: "unknown", teaser: null }
                const it = items.find(d => d.id === id)
                if (it) {
                    obj.name = it.name
                    obj.teaser = mediaPath("teaser", it.teaser)
                }
                sn.push(obj)
                nodeSet.add(id)
            }

            // add the connected node if not already present
            if (!nodeSet.has(oid)) {
                const obj = { id: oid, name: "unknown", teaser: null }
                const it = items.find(d => d.id === oid)
                if (it) {
                    obj.name = it.name
                    obj.teaser = mediaPath("teaser", it.teaser)
                }
                sn.push(obj)
                nodeSet.add(oid)
            }

            const ex = sl.find(d => d.source === id && d.target === oid || d.source === oid && d.target === id)
            if (ex) {
                // update existing link
                ex.value += d.value
            } else {
                // add new link
                sl.push({
                    id: sl.length+1,
                    source: id,
                    target: oid,
                    value: d.value
                })
            }
        })

        simNodes.value = sn
        simLinks.value = sl
    }

    onMounted(read)

    watch(() => times.all, read)

</script>
