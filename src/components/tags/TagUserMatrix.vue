<template>
    <div class="text-caption" style="text-align: center;">
        <b>Who tags together?</b>
        <HeatMatrix v-if="data.length > 0"
            :data="data"
            :labels="labels"
            :max-value="1"
            @click="onClickCell"
            :size="size"/>
        <div v-else :style="{ width: size+'px'}">
            NO DATA
        </div>
    </div>
</template>

<script setup>
    import { group } from 'd3';
    import { onMounted, watch } from 'vue';
    import HeatMatrix from '../vis/HeatMatrix.vue';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { FILTER_TYPES } from '@/use/filters';

    const app = useApp()
    const times = useTimes()

    const props = defineProps({
        size: {
            type: Number,
            default: 300
        },
    })

    const data = ref([])
    const labels = ref({})

    function isSelectedTag(id, sel) {
        if (sel.has(id)) return true
        const p = DM.getDerivedItem("tags_path", id)
        return p && p.path.some(d => sel.has(d))
    }
    function readData() {
        const sel = DM.getSelectedIds("tags")
        const datatags = DM.getData("datatags")

        const values = {}
        const counts = {}
        const names = {}

        app.users.forEach(d => {
            values[d.id] = {}
            counts[d.id] = 0
            names[d.id] = d.short
            app.users.forEach(u => values[d.id][u.id] = 0)
        })

        const filter = DM.getSelectedIds("items")

        const grouped = group(datatags, d => d.item_id)
        grouped.forEach((vals, itemid) => {
            if (filter.size > 0 && !filter.has(itemid)) return

            const perTag = group(vals, d => d.tag_id)
            perTag.forEach((array, tagId) => {

                if (sel.size > 0 && !isSelectedTag(tagId, sel)) return

                for (let i = 0; i < array.length; ++i) {
                    const u1 = array[i].created_by
                    counts[u1]++
                    for (let j = i+1; j < array.length; ++j) {
                        const u2 = array[j].created_by
                        values[u1][u2]++
                        values[u2][u1]++
                    }
                }
            })
        })

        const list = []
        app.users.forEach((u1, i) => {
            for (let j = i+1; j < app.users.length; ++j) {
                const u2 = app.users[j]
                if (values[u1.id][u2.id] > 0) {
                    list.push({ source: u1.id, target: u2.id, value: values[u1.id][u2.id] / counts[u1.id] })
                    list.push({ source: u2.id, target: u1.id, value: values[u1.id][u2.id] / counts[u2.id] })
                }
            }
        })

        labels.value = names
        data.value = list
    }

    function onClickCell(item) {
        if (item === null) {
            app.selectByItemValue("coders", "coders", [])
        } else {
            app.selectByItemValue("coders", "coders", [item.source, item.target], FILTER_TYPES.SET_AND)
        }
    }

    onMounted(readData)

    watch(props, readData, { deep: true })
    watch(() => Math.max(times.all, times.users, times.f_tags, times.f_items, times.tags, times.tagging, times.datatags), readData)

</script>