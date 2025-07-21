<template>
    <v-sheet class="d-flex align-center" :class="{ 'flex-column': vertical }">
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
        <BigBubble
            :style="{ opacity: disabled ? 0.5 : 1 }"
            :selected="targets"
            :highlights="highlights"
            :data="items"
            selected-color="red"
            :highlights-color="theme.current.value.colors.secondary"
            :size="120"
            :radius="5"
            :class="[vertical ? 'mt-1 mb-1' : 'ml-1 mr-1']"
            @hover="onHover"
            @click="d => emit('click-item', d)"/>
        <MostCommonTags v-if="tags.length > 0"
            :style="{ opacity: disabled ? 0.5 : 1 }"
            :tags="tags"
            value-attr="rel"
            :limit="numTags"
            :time="time"/>
    </v-sheet>
</template>

<script setup>
    import { pointer } from 'd3';
    import { onMounted, onUpdated } from 'vue';
    import BigBubble from '../vis/BigBubble.vue';
    import ItemTeaser from './ItemTeaser.vue';
    import DM from '@/use/data-manager';
    import { useTooltip } from '@/store/tooltip';
    import { useApp } from '@/store/app';
    import { capitalize, mediaPath } from '@/use/utility';
    import { useTheme } from 'vuetify';
    import MostCommonTags from './MostCommonTags.vue';

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
        numTags: {
            type: Number,
            default: 8
        }
    })

    const emit = defineEmits(["change", "click", "click-item"])

    const domain = ref([])
    const tags = ref([])
    const time = ref(0)

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

    function read() {
        const tmp = DM.getDataBy("tags_tree", d => d.is_leaf === 1)
        domain.value = tmp.map(d => d.id)

        const counts = new Map()
        // counts tags
        props.items.forEach(d => d.allTags.forEach(t => counts.set(t.id, (counts.get(t.id) || 0) + 1)))

        tags.value = tmp
            .filter(d => counts.has(d.id))
            .map(d => {
                const obj = Object.assign({}, d)
                const abs = counts.get(d.id)
                obj.abs = abs ? abs : 0
                obj.rel = abs ? abs / props.items.length : 0
                return obj
            })

        time.value = Date.now()
    }

    onMounted(read)
    onUpdated(read)

</script>