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
            :width="nodeWidth"
            :height="height"
            :color-scale="relative ? (settings.lightMode ? colorScaleDiffLight : colorScaleDiffDark) : colorScale"
            :min-value="relative ? -1 : 0"
            :max-value="1"/>
    </div>
</template>

<script setup>
    import { pointer } from 'd3';
    import { useApp } from '@/store/app';
    import BarCode from '../vis/BarCode.vue';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { onMounted, ref, watch } from 'vue';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';

    const app = useApp()
    const times = useTimes()
    const settings = useSettings()

    const { showAllUsers } = storeToRefs(app)

    const props = defineProps({
        filter: {
            type: Boolean,
            default: false
        },
        height: {
            type: Number,
            default: 25
        },
        nodeWidth: {
            type: Number,
            default: 5
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

    function makeData() {

        const tags = DM.getDataBy("tags_tree", d => d.is_leaf === 1)
        const counts = new Map();
        tags.forEach(t => counts.set(t.id, [t.id, 0, t.name]))

        const selSize = DM.getSelectedIds("items").size
        let src = props.filter ?
            (selSize > 0 ? DM.getData("items", true).filter(d => d.allTags.length > 0)  : []) :
            DM.getDataBy("items", d => d.allTags.length > 0)

        if (!props.filter || selSize > 0) {
            src.forEach(g => {
                if (showAllUsers.value) {
                    g.allTags.forEach(t => {
                        counts.set(t.id, [t.id, counts.has(t.id) ? counts.get(t.id)[1]+1 : 1, t.name])
                    })
                } else {
                    g.tags.forEach(dt => {
                        if (dt.created_by === app.activeUserId) {
                            const t = tags.find(dd => dd.id === dt.tag_id)
                            counts.set(t.id, [t.id, counts.has(t.id) ? counts.get(t.id)[1]+1 : 1, t.name])
                        }
                    })
                }
            })
            const rel = props.referenceValues !== undefined

            barData.value = Array.from(counts.values())
                .map((d, i) => ([
                    d[0],
                    src.length > 0 ? d[1]/src.length : 0,
                    d[2],
                    d[1],
                    rel && src.length > 0 ? d[1]/src.length - props.referenceValues[i] : 0
                ]))
        } else {
            barData.value = []
        }
    }

    function toggleTag(tag) {
        app.toggleSelectByTag([tag[0]])
        emit("click", tag[0])
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

    function getValues() {
        return barData.value.map(d => d[1])
    }

    defineExpose({ getValues, makeData })

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
    watch(() => Math.max(times.f_any, times.f_items), function() {
        if (props.filter) {
            makeData();
        }
    })

    watch(showAllUsers, function() {
        makeData()
        emit("update")
    })

</script>