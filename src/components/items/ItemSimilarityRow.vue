<template>
    <v-sheet class="d-flex align-center" :class="{ 'flex-column': vertical }">
        <div>
            <ItemTeaser v-if="items.length > 0"
                :item="items[0]"
                @click="emit('click-item', items[0])"
                :border-size="3"
                :border-color="selected ? 'red' : undefined"
                prevent-open
                prevent-context/>
            <div v-if="!hideButtons" class="d-flex justify-space-between mt-1">
                <v-btn
                    style="width: 49%;"
                    class="text-caption"
                    :disabled="disabled"
                    @click="setSim(0)"
                    :color="disabled && sim !== 0  ? 'default' : 'error'"
                    density="compact">
                    no
                </v-btn>
                <v-btn
                    style="width: 49%;"
                    class="text-caption"
                    :disabled="disabled"
                    @click="setSim(0.25)"
                    :color="disabled && sim !== 0.25  ? 'default' : 'orange'"
                    density="compact">
                    soft no
                </v-btn>
            </div>
            <div v-if="!hideButtons" class="d-flex justify-space-between mt-1">
                <v-btn
                    style="width: 49%;"
                    class="text-caption"
                    :disabled="disabled"
                    @click="setSim(1)"
                    :color="disabled && sim !== 1 ? 'default' : 'primary'"
                    density="compact">
                    yes
                </v-btn>
                <v-btn
                    style="width: 49%;"
                    class="text-caption"
                    :disabled="disabled"
                    @click="setSim(0.75)"
                    :color="disabled && sim !== 0.75  ? 'default' : 'secondary'"
                    density="compact">
                    soft yes
                </v-btn>
            </div>
        </div>
        <BigBubble
            :selected="targets"
            :data="items"
            :size="120"
            :radius="5"
            :class="[vertical ? 'mt-1 mb-1' : 'ml-1 mr-1']"
            @hover="onHover"
            @click="d => emit('click-item', d)"/>
        <BarCode v-if="!hideBarcode"
            :data="tags"
            :domain="domain"
            selectable
            id-attr="id"
            name-attr="name"
            value-attr="rel"
            abs-value-attr="abs"
            :min-value="0"
            :max-value="1"
            :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
            :width="usedNodeSize"
            :height="15"/>
    </v-sheet>
</template>

<script setup>
    import { pointer } from 'd3';
    import { onMounted } from 'vue';
    import BarCode from '../vis/BarCode.vue';
    import BigBubble from '../vis/BigBubble.vue';
    import ItemTeaser from './ItemTeaser.vue';
    import DM from '@/use/data-manager';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import { useTooltip } from '@/store/tooltip';
    import { useApp } from '@/store/app';
    import { capitalize, mediaPath } from '@/use/utility';

    const app = useApp()
    const tt = useTooltip()
    const settings = useSettings()

    const { barCodeNodeSize } = storeToRefs(settings)

    const props = defineProps({
        items: {
            type: Array,
            required: true
        },
        targets: {
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
        hideBarcode: {
            type: Boolean,
            default: false
        },
        hideButtons: {
            type: Boolean,
            default: false
        },
        nodeSize: {
            type: Number,
        },
    })

    const emit = defineEmits(["change", "click-item"])

    const sim = ref(0)
    const domain = ref([])
    const tags = ref([])
    const chosen = ref(false)

    const usedNodeSize = computed(() => props.nodeSize !== undefined ? props.nodeSize : barCodeNodeSize.value)

    function setSim(value) {
        sim.value = value
        onChange()
        chosen.value = true
    }

    function onChange() {
        emit("change", tags.value.map(d => ({ id: d.id, value: d.rel*sim.value })), sim.value)
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
    }

    onMounted(read)

</script>