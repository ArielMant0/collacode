<template>
    <v-sheet class="d-flex align-center" :class="{ 'flex-column': vertical, 'align-center': vertical }">

        <div class="text-caption mt-1 mb-1">
            <div v-for="t in tags">
                <TagText :tag="t"/>
            </div>
        </div>

        <div :style="{ opacity: disabled ? 0.5 : 1 }">
            <ItemTeaser v-if="items.length > 0"
                :item="items[showIndex]"
                @click="emit('click', items[showIndex])"
                :width="imageWidth"
                :height="imageHeight"
                :border-size="3"
                :border-color="selected ? theme.current.value.colors.secondary : undefined"
                prevent-open
                prevent-context/>
            <div v-if="!hideButtons" class="d-flex justify-space-between mt-1">
                <v-btn
                    style="width: 49%;"
                    class="text-caption"
                    :disabled="disabled"
                    @click="setSim(0)"
                    :color="disabled && choice !== 0  ? 'default' : 'error'"
                    density="compact">
                    hard no
                </v-btn>
                <v-btn
                    style="width: 49%;"
                    class="text-caption"
                    :disabled="disabled"
                    @click="setSim(0.25)"
                    :color="disabled && choice !== 0.25  ? 'default' : '#fc3d23'"
                    density="compact">
                    no
                </v-btn>
            </div>
            <div v-if="!hideButtons" class="d-flex justify-space-between mt-1">
                <v-btn
                    style="width: 49%;"
                    class="text-caption"
                    :disabled="disabled"
                    @click="setSim(1)"
                    :color="disabled && choice !== 1 ? 'default' : 'primary'"
                    density="compact">
                    hard yes
                </v-btn>
                <v-btn
                    style="width: 49%;"
                    class="text-caption"
                    :disabled="disabled"
                    @click="setSim(0.75)"
                    :color="disabled && choice !== 0.75  ? 'default' : 'secondary'"
                    density="compact">
                    yes
                </v-btn>
            </div>
        </div>
        <div class="d-flex flex-wrap justify-space-between align-start mt-2"
            :style="{
                minWidth: imageWidth+'px',
                maxWidth: imageWidth+'px',
                minHeight: imageHeight+'px',
            }">
            <ItemTeaser v-for="ex in examples"
                class="mb-1"
                :item="ex"
                @click="emit('click-item', ex)"
                :width="miniImageWidth"
                :height="miniImageHeight"
                prevent-open
                prevent-context/>
        </div>

        <RectBubble v-if="otherItems.length > 0"
            :style="{ opacity: disabled ? 0.5 : 1 }"
            :data="otherItems"
            :width="imageWidth"
            :rect-size="30"
            :class="[vertical ? 'mt-1 mb-1' : 'ml-1 mr-1']"
            @hover="onHover"
            @click="d => emit('click-item', d)"/>

    </v-sheet>
</template>

<script setup>
    import { pointer, range } from 'd3';
    import { computed, onMounted, watch } from 'vue';
    import ItemTeaser from './ItemTeaser.vue';
    import { useTooltip } from '@/store/tooltip';
    import { useApp } from '@/store/app';
    import { capitalize, mediaPath } from '@/use/utility';
    import { useTheme } from 'vuetify';
    import { randomChoice } from '@/use/random';
    import DM from '@/use/data-manager';
    import TagText from '../tags/TagText.vue';
    import { sortObjByValue } from '@/use/sorting';
    import RectBubble from '../vis/RectBubble.vue';

    const app = useApp()
    const tt = useTooltip()
    const theme = useTheme()

    const props = defineProps({
        items: {
            type: Array,
            required: true
        },
        imageWidth: {
            type: Number,
            default: 160
        },
        imageHeight: {
            type: Number,
            default: 80
        },
        choice: {
            type: Number,
            default: -1
        },
        showIndex: {
            type: Number,
            default: 0
        },
        targets: {
            type: Array,
            default: () => ([])
        },
        highlights: {
            type: Array,
            default: () => ([])
        },
        selected: {
            type: Boolean,
            default: false
        },
        disabled: {
            type: Boolean,
            default: false
        },
        vertical: {
            type: Boolean,
            default: false
        },
        hideButtons: {
            type: Boolean,
            default: false
        },
        numExamples: {
            type: Number,
            default: 4
        },
        numTags: {
            type: Number,
            default: 2
        }
    })

    const emit = defineEmits(["change", "click", "click-item"])

    const tags = ref([])
    const examples = ref([])
    const otherItems = computed(() => props.items.filter(d => props.items[props.showIndex].id !== d.id && !examples.value.find(e => e.id === d.id)))
    const miniImageWidth = computed(() => (props.imageWidth-5) * (examples.value.length === 1 ? 1 : 0.5))
    const miniImageHeight = computed(() => (props.imageHeight-5) * (examples.value.length === 1 ? 1 : 0.5))

    function setSim(value) {
        emit("change", value)
    }

    function onHover(d, event) {
        if (d === null) {
            tt.hide()
        } else {
            const [mx, my] = pointer(event, document.body)
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

    function readExamples() {
        const cands = range(props.items.length).filter(i => i !== props.showIndex)
        examples.value =  cands.length > props.numExamples ?
            randomChoice(cands, props.numExamples).map(i => props.items[i]) :
            cands.map(i => props.items[i])
    }

    function read() {
        const dom = DM.getDataBy("tags", d => d.is_leaf === 1)
        const tagCounts = DM.getData("tags_counts", false)

        const freq = new Map()
        const globalSize = DM.getSizeBy("items", d => d.allTags.length > 0)
        // calculate global tag frequencies
        dom.forEach(d => freq.set(d.id, tagCounts.get(d.id) / globalSize))

        const counts = new Map()
        // counts tags
        props.items.forEach(d => d.allTags.forEach(t => counts.set(t.id, (counts.get(t.id) || 0) + 1)))

        const tmp = dom
            .filter(d => counts.has(d.id))
            .map(d => {
                const obj = { id: d.id, name: d.name, description: d.description}
                const abs = counts.get(d.id)
                obj.abs = abs ? abs : 0
                obj.rel = abs ? abs / props.items.length : 0
                obj.diff = obj.rel - freq.get(d.id)
                return obj
            })

        tmp.sort(sortObjByValue("diff", { ascending: false }))
        tags.value = tmp.slice(0, props.numTags)

        readExamples()
    }

    onMounted(read)

    watch(() => props.showIndex, readExamples)
    watch(() => props.items, read)

</script>