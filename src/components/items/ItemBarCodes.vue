

<template>
    <div v-if="!hidden && smAndUp" class="d-flex flex-column align-center">
        <div class="d-flex mb-1">
            <span style="width: 20px; text-align: left;" class="text-caption mr-2"></span>
            <MiniTree value-attr="from_id" :value-data="tags.treeValues" value-agg="mean" :node-width="barCodeNodeSize" :time="time"/>
            <span style="width: 80px;" class="ml-2"></span>
        </div>
        <div class="d-flex mb-1">
            <span style="width: 20px; text-align: left;" class="text-caption mr-2"></span>
            <BarCode v-if="tags.all.length > 0"
                :data="tags.all"
                :domain="tagDomain"
                @click="toggleTag"
                @right-click="onRightClick"
                selectable
                discrete
                id-attr="0"
                value-attr="1"
                name-attr="2"
                abs-value-attr="3"
                :width="barCodeNodeSize"
                :height="20"
                :no-value-color="lightMode ? '#f2f2f2' : '#333333'"
                color-scale="interpolatePlasma"
                :min-value="0"
                :max-value="1"/>
            <span style="min-width: 80px; max-width: 80px; text-align: left;" class="text-caption text-dots ml-2 pt-1">all {{ app.itemName }}s</span>
        </div>
        <div class="d-flex">
            <span style="width: 20px; text-align: left;" class="text-caption mr-2">
                <v-tooltip text="show difference" location="left" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props"
                            :icon="diffSelected ? 'mdi-minus-circle' : 'mdi-minus-circle-off'"
                            rounded="sm"
                            variant="plain"
                            density="compact"
                            @click="diffSelected = !diffSelected"/>
                    </template>
                </v-tooltip>
            </span>
            <div :style="{ minWidth: (tagDomain.length*barCodeNodeSize)+'px' }">
                <BarCode v-if="tags.selection.length > 0"
                    :data="tags.selection"
                    :domain="tagDomain"
                    @click="toggleTag"
                    @right-click="onRightClick"
                    selectable
                    discrete
                    id-attr="0"
                    :value-attr="diffSelected ? '4' : '1'"
                    name-attr="2"
                    abs-value-attr="3"
                    :width="barCodeNodeSize"
                    :height="20"
                    :no-value-color="lightMode ? '#f2f2f2' : '#333333'"
                    :color-scale="diffSelected ? 'interpolateRdYlBu' : 'interpolatePlasma'"
                    :min-value="diffSelected ? -1 : 0"
                    :max-value="1"/>
            </div>
            <span style="min-width: 80px; max-width: 80px; text-align: left;" class="text-caption text-dots ml-2 pt-1">selection</span>
        </div>
    </div>
</template>

<script setup>
    import { pointer } from 'd3';
    import { onMounted, reactive, watch } from 'vue';
    import MiniTree from '../vis/MiniTree.vue';
    import { useApp } from '@/store/app';
    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import { storeToRefs } from 'pinia';
    import { useDisplay } from 'vuetify';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import BarCode from '../vis/BarCode.vue';

    const app = useApp()
    const times = useTimes()
    const settings = useSettings()

    const { showAllUsers } = storeToRefs(app)
    const { barCodeNodeSize, lightMode } = storeToRefs(settings)

    const { smAndUp } = useDisplay()

    const props = defineProps({
        hidden: {
            type: Boolean,
            default: false
        }
    })

    const tagDomain = ref([])
    const tags = reactive({
        all: [],
        selection: [],
        diff: [],
        treeValues : {}
    })

    const time = ref(0)
    const diffSelected = ref(false)

    let loadOnShow = true;

    function toggleTag(tag) {
        app.toggleSelectByTag([tag[0]])
    }
    function onRightClick(tag, event) {
        event.preventDefault();
        if (tag) {
            const [mx, my] = pointer(event, document.body)
            settings.setRightClick(
                "tag", tag[0],
                mx, my,
                tag[2], null,
                CTXT_OPTIONS.tag
            );
        } else {
            settings.setRightClick(null)
        }
    }

    function countTags(items) {
        const counts = new Map()
        let itemCount = 0
        // count tag occurrences
        items.forEach(d => {
            if (showAllUsers.value) {
                d.allTags.forEach(t => counts.set(t.id, (counts.get(t.id) || 0) + 1))
                itemCount++
            } else {
                let some = false
                d.tags.forEach(dt => {
                    if (dt.created_by !== app.activeUserId) return
                    some = true
                    counts.set(dt.tag_id, (counts.get(dt.tag_id) || 0) + 1)
                })
                if (some) itemCount++
            }
        })

        const data = []
        tagDomain.value.forEach(tid => {
            const val = counts.get(tid)
            if (val !== undefined) {
                data.push([tid, val / itemCount, DM.getDataItem("tags_name", tid, val), val])
            }
        })
        return data
    }

    function readSelection() {
        if (!props.hidden) {
            loadOnShow = false
            const hasSelection = DM.hasFilter("items") || DM.hasFilter("tags")
            if (hasSelection) {
                const sel = countTags(DM.getData("items", true))
                tags.all.forEach(t => {
                    const it = sel.find(d => d[0] === t[0])
                    if (it) {
                        it.push(it[1]-t[1])
                    }
                })
                tags.selection = sel
            } else {
                tags.selection = []
            }
            time.value = Date.now()
        } else {
            loadOnShow = true
        }
    }
    function readData() {
        if (!props.hidden) {
            loadOnShow = false
            tags.all = countTags(DM.getDataBy("items", d => d.allTags.length > 0))
            const obj = {}
            tags.all.forEach(t => obj[t[0]] = t[1])
            tags.treeValues = obj
            readSelection()
        } else {
            loadOnShow = true
        }
    }
    function readTags() {
        tagDomain.value = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
    }
    function read() {
        readTags()
        readData()
    }

    onMounted(read)

    watch(() => props.hidden, function(hidden) {
        if (!hidden && loadOnShow) {
            read()
        }
    })
    watch(() => Math.max(times.all, times.tagging, times.tags), read)
    watch(showAllUsers, readData)
    watch(() => times.datatags, readData)
    watch(() => Math.max(times.f_items, times.f_tags), readSelection)
</script>