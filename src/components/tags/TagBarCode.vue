<template>
    <div>
        <BarCode v-if="barData.length > 0"
            :data="barData"
            @click="toggleTag"
            @right-click="onRightClick"
            selectable
            id-attr="0"
            :value-attr="relative ? '4' : '1'"
            name-attr="2"
            abs-value-attr="3"
            :height="height"
            :color-scale="relative ? (settings.lightMode ? colorScaleDiffLight : colorScaleDiffDark) : colorScale"
            :min-value="relative ? -1 : 0"
            :max-value="1"/>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import BarCode from '../vis/BarCode.vue';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { onMounted, ref, watch } from 'vue';
    import { ALL_ADD_OPTIONS, CTXT_OPTIONS, useSettings } from '@/store/settings';

    const app = useApp()
    const times = useTimes()
    const settings = useSettings()

    const props = defineProps({
        filter: { type: Function },
        height: {
            type: Number,
            default: 25
        },
        colorScale: {
            type: String,
            default: "interpolatePlasma"
        },
        colorScaleDiffLight: {
            type: [String, Array],
            default: "interpolateRdYlBu"
        },
        colorScaleDiffDark: {
            type: [String, Array],
            default: "interpolateRdYlBu"
            // default: () => (["#b30036", "black", "#0855ad"])
        },
        relative: {
            type: Boolean,
            default: false
        },
        referenceValues: {
            type: Array,
            required: false
        }
    })
    const emit = defineEmits(["click", "update"])

    const barData = ref([])

    function lastNames(n) {
        const parts = n.split("/")
        if (parts.length === 1) return n
        return parts.map((d, i) => i == 0 || i >= parts.length-2 ? d : "..")
            .reverse()
            .join(" / ")
    }
    function makeData() {

        const tags = DM.getDataBy("tags", t => t.is_leaf === 1)
        tags.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return 0
        });

        const counts = new Map();
        tags.forEach(t => counts.set(t.id, [t.id, 0, lastNames(t.pathNames)]))

        const src = props.filter ? DM.getDataBy("items", props.filter) : DM.getDataBy("items", d => d.allTags.length > 0)
        src.forEach(g => {
            g.allTags.forEach(t => {
                counts.set(t.id, [t.id, counts.has(t.id) ? counts.get(t.id)[1]+1 : 1, lastNames(t.pathNames)])
            })
        })

        const rel = props.referenceValues !== undefined

        barData.value = Array.from(counts.values())
            .map((d, i) => ([
                d[0],
                src.length > 0 ? d[1]/src.length : 0,
                d[2],
                d[1],
                rel && src.length > 0 ? d[1]/src.length-props.referenceValues[i] : 0
            ]))
    }

    function toggleTag(tag) {
        app.toggleSelectByTag([tag[0]])
        emit("click", tag[0])
    }
    function onRightClick(tag, event) {
        event.preventDefault();
        if (tag) {
            settings.setRightClick(
                "tag", tag[0],
                event.pageX + 15,
                event.pageY,
                tag[2], null,
                CTXT_OPTIONS.tag.concat(ALL_ADD_OPTIONS)
            );
        } else {
            settings.setRightClick(null)
        }
    }

    function getValues() {
        return barData.value.map(d => d[1])
    }

    defineExpose({ getValues })

    onMounted(makeData)

    watch(() => props.filter, makeData)
    watch(() => props.relative, makeData)
    watch(() => props.referenceValues, function() {
        if (props.relative) makeData()
    })
    watch(() => Math.max(times.all, times.tags, times.items), function() {
        makeData()
        emit("update")
    })
    watch(() => times.f_items, function() {
        if (props.filter) {
            makeData();
        }
    })


</script>