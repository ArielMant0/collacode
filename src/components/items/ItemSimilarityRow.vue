<template>
    <div class="d-flex">
        <div>
            <ItemTeaser v-if="items.length > 0"
                :item="items[0]"
                prevent-click
                prevent-open
                prevent-context/>
            <v-slider v-model="sim"
                density="compact"
                min="0"
                max="1"
                :thumb-size="15"
                @update:model-value="onChange"
                style="width: 160px;"/>
        </div>
        <BigBubble
            :data="items"
            :size="120"
            :radius="5"
            @hover="onHover"
            class="ml-1 mr-1"/>
        <BarCode
            :data="tags"
            :domain="domain"
            selectable
            id-attr="id"
            name-attr="name"
            value-attr="value"
            abs-value-attr="value"
            show-absolute
            :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
            :min-value="0"
            :max-value="1"
            :width="usedNodeSize"
            :height="15"/>
    </div>
</template>

<script setup>
    import { pointer } from 'd3';
    import { onMounted, watch } from 'vue';
    import BarCode from '../vis/BarCode.vue';
    import BigBubble from '../vis/BigBubble.vue';
    import ItemTeaser from './ItemTeaser.vue';
    import DM from '@/use/data-manager';
    import { getGroupSet } from '@/use/clustering';
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
        threshold: {
            type: Number,
            default: 0
        },
        nodeSize: {
            type: Number,
        }
    })

    const emit = defineEmits(["change"])

    const sim = ref(0)
    const domain = ref([])
    const tags = ref([])

    const usedNodeSize = computed(() => props.nodeSize !== undefined ? props.nodeSize : barCodeNodeSize.value)

    function onChange() {
        const vals = new Map()
        props.items.forEach(d => {
            d.allTags.forEach(t => {
                vals.set(t.id, (vals.get(t.id) || 0) + sim.value)
            })
        })
        const keys = Array.from(vals.keys())
        keys.forEach(k => vals.set(k, vals.get(k) / props.items.length))
        tags.value.forEach(d => {
            const v = vals.get(d.id)
            d.value = v && v > props.threshold ? v : 0
        })
        emit("change", tags.value.filter(d => d.value > 0), sim.value)
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
        const set = getGroupSet(props.items)
        tags.value = tmp
            .filter(d => set.has(d.id))
            .map(d => {
                const obj = Object.assign({}, d)
                obj.value = 1 * sim.value
                return obj
            })
    }

    onMounted(read)

    watch(() => props.threshold, onChange)

</script>