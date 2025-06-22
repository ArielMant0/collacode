<template>
    <div style="width: min-content;" class="pa-2">
        <div v-if="step === 1">

            <div style="text-align: center;">
                <v-btn
                    color="primary"
                    class="mb-4"
                    :disabled="split.length === 0"
                    density="comfortable"
                    @click="submit">done</v-btn>
            </div>

            <div v-for="(obj, idx) in split" :key="idx+'_t'+obj.tag.id">
                <div style="text-align: center;">
                    <div v-if="idx === 0">
                        Does this tag apply to the {{ app.itemName }}?
                    </div>
                    <div class="mt-4 mb-2 d-flex align-center justify-center">
                        <h4>{{ obj.tag.name }}</h4>
                        <v-btn v-if="idx === 0" variant="outlined" class="ml-2" icon="mdi-sync" size="small" density="comfortable" @click="rerollTag"/>
                    </div>
                    <p>{{ obj.tag.description }}</p>
                </div>

                <div class="d-flex mt-8">
                    <div class="d-flex flex-column align-center" :style="{ minWidth: '300px' }">
                        <v-btn
                            density="comfortable"
                            :color="idx === 0 || obj.hasTag ? GR_COLOR.GREEN : 'default'"
                            :disabled="idx > 0"
                            @click="choose(true)">yes</v-btn>
                        <BigBubble
                            :size="getBubbleSize(idx)"
                            @hover="onHover"
                            :selected="target ? [target] : []"
                            :data="obj.with.map(idx => itemsToUse[idx])"/>
                    </div>
                    <div class="d-flex flex-column align-center" :style="{ minWidth: '300px' }">
                        <v-btn
                            density="comfortable"
                            :color="idx === 0 || !obj.hasTag ? GR_COLOR.RED : 'default'"
                            :disabled="idx > 0"
                            @click="choose(false)">no</v-btn>
                        <BigBubble
                            :size="getBubbleSize(idx)"
                            @hover="onHover"
                            :selected="target ? [target] : []"
                            :data="obj.without.map(idx => itemsToUse[idx])"/>
                    </div>
                </div>
            </div>
        </div>
        <div v-else>
            <div class="d-flex align-end">

                <div class="d-flex flex-column align-center">
                    <h3>Related {{ app.itemNameCaptial+'s' }}</h3>
                    <div class="d-flex flex-wrap justify-center" :style="{ minWidth: ((imageWidth+10)*2)+'px', maxWidth: ((imageWidth+10)*2)+'px' }">
                        <ItemTeaser v-for="(item, idx) in candidates"
                            :item="item"
                            :style="{ opacity: candSelect.has(idx) || candSelect.size === 0 ? 1 : 0.5 }"
                            @click="toggleCandidate(idx)"
                            :border-color="candSelect.has(idx) ? theme.current.value.colors.primary : undefined"
                            :border-size="4"
                            :width="imageWidth"
                            :height="imageHeight"
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
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ref, onMounted, computed, reactive } from 'vue';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import DM from '@/use/data-manager';
    import ItemTeaser from './ItemTeaser.vue';
    import { useTheme } from 'vuetify';
    import TreeMap from '../vis/TreeMap.vue';
    import { useWindowSize } from '@vueuse/core';
    import ColorLegend from '../vis/ColorLegend.vue';
    import { useApp } from '@/store/app';
    import BigBubble from '../vis/BigBubble.vue';
    import { GR_COLOR } from '@/store/games';
    import { randomChoice } from '@/use/random';
    import { capitalize, mediaPath } from '@/use/utility';
    import { useTooltip } from '@/store/tooltip';

    const app = useApp()
    const tt = useTooltip()
    const settings = useSettings()
    const theme = useTheme()

    const { lightMode } = storeToRefs(settings)

    const ws = useWindowSize()
    const treeWidth = computed(() => Math.max(200, Math.floor(ws.width.value*0.7)))
    const treeHeight = computed(() => Math.max(200, Math.floor(ws.height.value*0.65)))

    const props = defineProps({
        imageWidth: {
            type: Number,
            default: 160
        },
        imageHeight: {
            type: Number,
            default: 80
        },
        nodeSize: {
            type: Number
        },
        target: {
            type: Number,
        }
    })

    const emit = defineEmits(["update", "step"])

    const inventory = ref([])
    const split = ref([])

    let itemsToUse, tagsToUse
    const itemsLeft = new Set()
    const tagsLeft = new Set()

    let tagCounts = new Map()
    const candidates = ref([])
    const candSelect = reactive(new Set())
    const tagsSel = reactive(new Set())
    const threshold = ref(0)
    const maxTagCount = ref(1)

    const colorScale = ref(null)

    const step = ref(1)
    const treeTime = ref(0)
    const treeData = ref([])

    function treeMapColors(d3obj, h, light) {
        const n = Math.max(3,Math.min(9,h))
        const r = d3obj.range(1, n+1)
        return r.map(d3obj.scaleSequential([
            light ? "#fff" : "#000",
            light ? "#000" : "#fff"
        ]).domain([0, n]))
    }

    function getBubbleSize(index) {
        const s = Math.max(split.value[index].with.length, split.value[index].without.length)
        return Math.max(100,Math.min(Math.round(Math.sqrt(s)*20), 300))
    }

    function onHover(d, event) {
        if (d === null) {
            tt.hide()
        } else {
            const [mx, my] = d3.pointer(event, document.body)
            const extra = app.itemColumns.reduce((acc, c) => acc + `<div><b>${capitalize(c.name)}:</b> ${d[c.name]}</div>`, "")
            tt.show(
                `<div>
                    <img src="${mediaPath('teaser', d.teaser)}" style="max-height: 150px; object-fit: contain;"/>
                    <div class="mt-1 text-caption">
                        <div>${d.name}</div>
                        ${d.description ? '<div><b>Description:</b> '+d.description+'</div>' : ''}
                        ${extra}
                    </div>
                </div>`,
                mx, my
            )
        }
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
        candSelect.clear()
        tagsSel.clear()
        tagCounts.clear()
        split.value.forEach(d => {
            if (d.hasTag) {
                tagsSel.add(d.tag.id)
            }
        })
        const indices = itemsLeft.size <= 20 ?
            Array.from(itemsLeft.values()) :
            randomChoice(Array.from(itemsLeft.values()), 20)

        candidates.value =  indices.map(idx => itemsToUse[idx])
        updateTags()
    }

    function rerollTag() {
        let splitTag = null;
        for (let i = 0; i < tagsToUse.length && splitTag === null; ++i) {
            if (tagsLeft.has(tagsToUse[i].id)) {
                splitTag = tagsToUse[i]
            }
        }
        if (splitTag !== null) {
            tagsLeft.delete(splitTag.id)
            // divide items based on split tag
            const withTag = [], without = []
            itemsLeft.forEach(idx => {
                const has = itemsToUse[idx].allTags.find(t => t.id === splitTag.id)
                if (has) {
                    withTag.push(idx)
                } else {
                    without.push(idx)
                }
            })

            const last = split.value.at(0)
            last.hasTag = null
            last.tag = splitTag
            last.with = withTag
            last.without = without
        }
    }

    async function nextTag() {
        // remove
        if (split.value.length > 0) {
            const last = split.value.at(0)
            const choice = last.tag.id
            const indices = Array.from(itemsLeft.values())
            indices.forEach(idx => {
                const hasTag = itemsToUse[idx].allTags.find(t => t.id === choice) !== undefined
                if (hasTag !== last.hasTag) {
                    itemsLeft.delete(idx)
                }
            })
        }

        if (itemsLeft.size <= 8) {
            return submit()
        }

        // calculate tag frequencies
        const counts = new Map()
        itemsLeft.forEach(idx => {
            itemsToUse[idx].allTags.forEach(t => {
                if (!tagsLeft.has(t.id)) return
                counts.set(t.id, (counts.get(t.id) || 0) + 1)
            })
        })
        tagsToUse.forEach(t => {
            if (counts.has(t.id)) {
                t.freq.push(counts.get(t.id) / itemsLeft.size)
            } else {
                t.freq.push(0)
            }
        })

        // sort tags by difference to 50%
        tagsToUse.sort((a, b) => Math.abs(0.5 - a.freq.at(-1)) - Math.abs(0.5 - b.freq.at(-1)))

        // choose first tag as the one to split on (if there are enough items on both sides)
        const splitTag = tagsToUse[0]
        // if (Math.round(splitTag.freq.at(-1)) * itemsLeft.size < 3) {
        //     return console.warn("not enough items left")
        // }

        // divide items based on split tag
        const withTag = [], without = []
        itemsLeft.forEach(idx => {
            const has = itemsToUse[idx].allTags.find(t => t.id === splitTag.id)
            if (has) {
                withTag.push(idx)
            } else {
                without.push(idx)
            }
        })

        tagsLeft.delete(splitTag.id)
        split.value.unshift({
            tag: splitTag,
            hasTag: null,
            with: withTag,
            without: without
        })
    }

    function choose(hasTag) {
        if (split.value.length === 0) return
        const last = split.value.at(0)
        last.hasTag = hasTag === true
        nextTag()
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
        itemsToUse = DM.getDataBy("items", d => d.allTags.length > 0 && (!props.target || d.id !== props.target))
        const tags = DM.getData("tags", false)
        treeData.value = tags
            .map(d => {
                const obj = Object.assign({}, d)
                obj.value = 0
                obj._exclude = true
                return obj
            })
        treeTime.value = Date.now()
        tagsToUse = tags
            .filter(d => d.is_leaf === 1)
            .map(d => {
                const obj = Object.assign({}, d)
                obj.freq = []
                return obj
            })
    }

    function reset(update=true) {
        split.value = []
        inventory.value = []
        itemsLeft.clear()
        tagsLeft.clear()
        itemsToUse.forEach((_, idx) => itemsLeft.add(idx))
        tagsToUse.forEach(t => tagsLeft.add(t.id))
        if (update) {
            nextTag()
        }
    }

    defineExpose({ reset })

    onMounted(function() {
        read()
        reset(nextTag)
    })

</script>