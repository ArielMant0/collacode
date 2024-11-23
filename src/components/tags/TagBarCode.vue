<template>
    <div>
        <BarCode v-if="barData.length > 0"
            :data="barData"
            @select="toggleTag"
            :selected="selected"
            id-attr="0"
            value-attr="1"
            name-attr="2"
            abs-value-attr="3"
            :height="height"
            :highlight="highlightSize"
            :color-scale="relative ? colorScaleDiff : colorScale"
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

    const app = useApp()
    const times = useTimes()

    const props = defineProps({
        filter: { type: Function },
        height: {
            type: Number,
            default: 25
        },
        highlightSize: {
            type: Number,
            default: 3
        },
        colorScale: {
            type: String,
            default: "interpolateCool"
        },
        colorScaleDiff: {
            type: String,
            default: "interpolateRdBu"
        },
        relative: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["click"])

    const barData = ref([])
    const selected = ref([])

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

        const src = props.filter ? DM.getDataBy("games", props.filter) : DM.getDataBy("games", d => d.allTags.length > 0)
        src.forEach(g => {
            g.allTags.forEach(t => {
                counts.set(t.id, [t.id, counts.has(t.id) ? counts.get(t.id)[1]+1 : 1, lastNames(t.pathNames)])
            })
        })

        barData.value = Array.from(counts.values())
            .map(d => ([d[0], src.length > 0 ? d[1]/src.length : 0, d[2], d[1]]))
    }
    function readSelected(update=true) {
        selected.value = DM.getSelectedIdsArray("tags")
        if (update && props.filter) {
            makeData();
        }
    }
    function toggleTag(id) {
        app.toggleSelectByTag([id])
        emit("click", id)
    }

    onMounted(function() {
        readSelected(false)
        makeData()
    })

    watch(() => props.filter, makeData)
    watch(() => Math.max(times.all, times.tags, times.games), makeData)
    watch(() => times.f_games, readSelected.bind(null, true))


</script>