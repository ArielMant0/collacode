<template>
    <div style="width: min-content;" class="pa-2">
        <div>

            <div style="text-align: center;">
                <v-btn
                    color="primary"
                    class="mb-4"
                    :disabled="split.length === 0"
                    density="comfortable"
                    @click="submit">done</v-btn>
            </div>

            <div v-for="(obj, idx) in split" :key="obj.tag.id">
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
                    <div class="d-flex align-center">
                        <div class="mr-1">
                            <ItemTeaser v-for="exId in obj.examplesYes"
                                :id="exId"
                                :width="obj.width"
                                :height="obj.height"
                                prevent-click
                                prevent-context
                                class="mb-1"/>
                        </div>
                        <div class="d-flex flex-column align-center" :style="{ minWidth: '300px' }">
                            <v-btn
                                density="comfortable"
                                :color="idx === 0 || obj.hasTag ? GR_COLOR.GREEN : 'default'"
                                :disabled="idx > 0"
                                @click="choose(true)">yes</v-btn>
                            <SpiralBubble
                                :width="obj.size"
                                :height="obj.size"
                                :highlights="obj.examplesYes"
                                :highlights-color="theme.current.value.colors.secondary"
                                @hover="onHover"
                                :selected="target ? [target] : []"
                                :data="obj.with.map(idx => itemsToUse[idx])"/>
                        </div>
                    </div>

                    <div class="d-flex align-center">
                        <div class="d-flex flex-column align-center" :style="{ minWidth: '300px' }">
                            <v-btn
                                density="comfortable"
                                :color="idx === 0 || !obj.hasTag ? GR_COLOR.RED : 'default'"
                                :disabled="idx > 0"
                                @click="choose(false)">no</v-btn>
                            <SpiralBubble
                                :width="obj.size"
                                :height="obj.size"
                                :highlights="obj.examplesNo"
                                :highlights-color="theme.current.value.colors.secondary"
                                @hover="onHover"
                                :selected="target ? [target] : []"
                                :data="obj.without.map(idx => itemsToUse[idx])"/>
                        </div>
                        <div class="ml-1">
                            <ItemTeaser v-for="exId in obj.examplesNo"
                                :id="exId"
                                :width="obj.width"
                                :height="obj.height"
                                prevent-click
                                prevent-context
                                class="mb-1"/>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ref, onMounted } from 'vue';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { GR_COLOR } from '@/store/games';
    import { randomChoice } from '@/use/random';
    import { capitalize, mediaPath } from '@/use/utility';
    import { useTooltip } from '@/store/tooltip';
    import SpiralBubble from '../vis/SpiralBubble.vue';
    import ItemTeaser from './ItemTeaser.vue';
    import { useTheme } from 'vuetify';

    const app = useApp()
    const tt = useTooltip()
    const theme = useTheme()

    const props = defineProps({
        imageWidth: {
            type: Number,
            default: 120
        },
        imageHeight: {
            type: Number,
            default: 60
        },
        minItems: {
            type: Number,
            default: 10
        },
        maxItems:{
            type: Number,
            default: 30
        },
        nodeSize: {
            type: Number
        },
        target: {
            type: Number,
        },
        numExamples: {
            type: Number,
            default: 5
        }
    })

    const emit = defineEmits(["submit"])

    const inventory = ref([])
    const split = ref([])

    let log = []
    let itemsToUse, tagsToUse
    const itemsLeft = new Set()
    const tagsLeft = new Set()


    function getImageHeight(n, m) {
        const bs = getBubbleSize(n, m)
        return Math.max(50, Math.min(160, Math.round(bs / 40)))
    }

    function getBubbleSize(n, m) {
        const s = Math.max(n, m)
        return Math.max(100, Math.min(Math.round(Math.sqrt(s) * 20), 300))
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


    function submit() {
        const indices = itemsLeft.size <= props.maxItems ?
            Array.from(itemsLeft.values()) :
            randomChoice(Array.from(itemsLeft.values()), props.maxItems)

        emit("submit", indices.map(idx => itemsToUse[idx]), log)
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
            log.push({
                desc: "reroll",
                step: split.value.length,
                tag: splitTag,
                with: withTag.map(i => itemsToUse[i].id),
                without: without.map(i => itemsToUse[i].id),
            })
            last.hasTag = null
            last.tag = splitTag
            last.with = withTag
            last.without = without

            const numEx = Math.max(last.examplesYes.length, last.examplesNo.length)
            // get random examples
            const examplesYes = withTag.length > numEx ?
                randomChoice(withTag, numEx) :
                withTag

            const examplesNo = without.length > numEx ?
                randomChoice(without, numEx) :
                without

            last.examplesYes = examplesYes.map(idx => itemsToUse[idx].id)
            last.examplesNo = examplesNo.map(idx => itemsToUse[idx].id)
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

        if (itemsLeft.size / 2 <= props.minItems) {
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

        const numEx = Math.max(2, props.numExamples - split.value.length)
        // get random examples
        const examplesYes = withTag.length > numEx ?
            randomChoice(withTag, numEx) :
            withTag

        const examplesNo = without.length > numEx ?
            randomChoice(without, numEx) :
            without

        const h = getImageHeight(withTag.length, without.length)
        split.value.unshift({
            tag: splitTag,
            hasTag: null,
            with: withTag,
            without: without,
            examplesYes: examplesYes.map(idx => itemsToUse[idx].id),
            examplesNo: examplesNo.map(idx => itemsToUse[idx].id),
            size: getBubbleSize(withTag.length, without.length),
            width: h*2,
            height: h
        })
        log.push({
            desc: "split step",
            step: split.value.length,
            tag: splitTag.id,
            with: withTag.map(i => itemsToUse[i].id),
            without: without.map(i => itemsToUse[i].id),
        })
    }

    function choose(hasTag) {
        if (split.value.length === 0) return
        const last = split.value.at(0)
        last.hasTag = hasTag === true
        log.push({
            desc: "choose answer",
            answer: last.hasTag ? "yes" : "no",
            tag: last.tag.id,
            step: split.value.length-1
        })
        nextTag()
    }


    function read() {
        itemsToUse = DM.getDataBy("items", d => d.allTags.length > 0 && (!props.target || d.id !== props.target))
        const tags = DM.getData("tags", false)
        tagsToUse = tags
            .filter(d => d.is_leaf === 1)
            .map(d => {
                const obj = Object.assign({}, d)
                obj.freq = []
                return obj
            })
    }

    function reset(update=true) {
        log = []
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