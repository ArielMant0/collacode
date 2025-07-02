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
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { ref, onMounted } from 'vue';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import BigBubble from '../vis/BigBubble.vue';
    import { GR_COLOR } from '@/store/games';
    import { randomChoice } from '@/use/random';
    import { capitalize, mediaPath } from '@/use/utility';
    import { useTooltip } from '@/store/tooltip';

    const app = useApp()
    const tt = useTooltip()

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

    const emit = defineEmits(["submit"])

    const inventory = ref([])
    const split = ref([])

    let itemsToUse, tagsToUse
    const itemsLeft = new Set()
    const tagsLeft = new Set()


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


    function submit() {
        const indices = itemsLeft.size <= 20 ?
            Array.from(itemsLeft.values()) :
            randomChoice(Array.from(itemsLeft.values()), 20)

        emit("submit", indices.map(idx => itemsToUse[idx]))
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