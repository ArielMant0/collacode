<template>
    <div>
        <div class="d-flex align-end">

            <div class="d-flex flex-column align-center">
                <h3>Related {{ app.itemNameCaptial+'s' }}</h3>
                <div class="d-flex flex-wrap justify-center" :style="{ minWidth: ((imageWidth+10)*2)+'px', maxWidth: ((imageWidth+10)*2)+'px' }">
                    <ItemTeaser v-for="(item, idx) in items"
                        :item="item"
                        :style="{ opacity: itemSel.has(idx) || itemSel.size === 0 ? 1 : 0.33 }"
                        @click="toggleCandidate(idx)"
                        :border-color="itemSel.has(idx) ? theme.current.value.colors.primary : undefined"
                        :border-size="4"
                        :width="imageWidth"
                        :height="imageHeight"
                        prevent-open
                        prevent-context
                        class="mr-1 mb-1"/>
                </div>
            </div>

            <div>
                <div style="max-width: 99%;" class="d-flex align-center">
                    <ColorLegend v-if="colorScale"
                        style="width: 200px;"
                        :colors="colorScale.range()"
                        :ticks="colorScale.thresholds().map(v => Math.floor(v)).concat([maxTagCount])"
                        :label-size="25"
                        :rect-size="15"
                        :size="200"
                        hide-domain/>
                    <v-slider v-model="threshold"
                        class="text-caption"
                        min="0"
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
</template>

<script setup>
    import * as d3 from 'd3'
    import { useApp } from '@/store/app'
    import DM from '@/use/data-manager'
    import { ref, reactive, onMounted, computed } from 'vue'
    import { useTheme } from 'vuetify/lib/composables/theme'
    import ColorLegend from '../vis/ColorLegend.vue'
    import ItemTeaser from './ItemTeaser.vue'
    import TreeMap from '../vis/TreeMap.vue'
    import { useWindowSize } from '@vueuse/core'
    import { useSettings } from '@/store/settings'
    import { storeToRefs } from 'pinia'

    const app = useApp()
    const theme = useTheme()
    const settings = useSettings()

    const ws = useWindowSize()
    const treeWidth = computed(() => Math.max(200, Math.floor(ws.width.value*0.7)))
    const treeHeight = computed(() => Math.max(200, Math.floor(ws.height.value*0.65)))

    const { lightMode } = storeToRefs(settings)

    const props = defineProps({
        items: {
            type: Array,
            required: true
        },
        imageWidth: {
            type: Number,
            default: 140
        },
        imageHeight: {
            type: Number,
            default: 70
        },
    })

    const emit = defineEmits(["update"])

    const treeData = ref([])
    const treeTime = ref(0)
    const maxTagCount = ref(1)
    const threshold = ref(1)
    const colorScale = ref(null)

    let tagCounts = new Map()
    const itemSel = reactive(new Set())
    const tagsSel = reactive(new Set())


    function treeMapColors(d3obj, h, light) {
        const n = Math.max(3,Math.min(9,h))
        const r = d3obj.range(1, n+1)
        return r.map(d3obj.scaleSequential([
            light ? "#fff" : "#000",
            light ? "#000" : "#fff"
        ]).domain([0, n]))
    }

    function toggleCandidate(index) {
        if (itemSel.has(index)) {
            itemSel.delete(index)
        } else {
            itemSel.add(index)
        }
        updateTags()
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
        itemSel.forEach(idx => items.push(props.items[idx]))

        const vals = new Map()
        items.forEach(d => d.allTags.forEach(t => vals.set(t.id, (vals.get(t.id) || 0) + 1)))

        let mtc = 0
        treeData.value.forEach(t => {
            if (t.is_leaf === 1) {
                const v = vals.get(t.id)
                if (items.length === 0) {
                    tagCounts.set(t.id, 0)
                } else if (v !== undefined) {
                    tagCounts.set(t.id, v)
                    mtc = Math.max(v, mtc)
                }
            }
        })

        const replace = threshold.value === maxTagCount.value
        maxTagCount.value = Math.max(1, mtc)
        if (replace) {
            threshold.value = maxTagCount.value
        }

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
        updateTags()
    }

    onMounted(read)
</script>