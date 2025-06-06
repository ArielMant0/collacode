<template>
    <div class="text-caption" style="text-align: center;">
        <div><b>Which tags occurr together? {{ app.showAllUsers ? "(all users)" : "(only you)" }}</b></div>
        <div v-if="corr.length > 0" style="text-align:right;">
            <MiniTree :node-width="nodeSize"/>
            <HeatMatrix
                :data="corr"
                :domain-values="tags.map(t => t.id)"
                :labels="corrLabels"
                hide-x-labels
                @click="onClickCell"
                :cell-size="nodeSize"
                :size="1000"/>
        </div>
        <div v-else style="text-align: center; min-width: 50%; min-height: 100px;">
            NO DATA
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { onMounted, ref, watch } from 'vue';
    import HeatMatrix from '../vis/HeatMatrix.vue';
    import { useTimes } from '@/store/times';
    import { FILTER_TYPES } from '@/use/filters';
    import { useApp } from '@/store/app';
    import { useTooltip } from '@/store/tooltip';
    import MiniTree from '../vis/MiniTree.vue';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import { useWindowSize } from '@vueuse/core';

    const app = useApp()
    const times = useTimes()
    const tt = useTooltip()
    const settings = useSettings()

    const { barCodeNodeSize } = storeToRefs(settings)

    const wSize = useWindowSize()
    const nodeSize = computed(() => {
        if (tags.value.length === 0) {
            return barCodeNodeSize.value
        }
        return Math.max(2, Math.floor((wSize.width.value - 350) / tags.value.length))
    })

    const corr = ref([])
    const corrLabels = {}
    const tags = ref([]);


    function readTags() {
        tags.value = DM.getDataBy("tags_tree", d => d.is_leaf === 1)
        calcCorrelation()
    }
    function calcCorrelation() {
        const items = DM.getData("items", true)

        const values = {}
        const counts = {}

        tags.value.forEach(t => {
            counts[t.id] = 0
            values[t.id] = {}
            for (let j = 0; j < tags.value.length; ++j) {
                values[t.id][tags.value[j].id] = 0
            }
            corrLabels[t.id] = t.name
        })


        items.forEach(d => {
            if (app.showAllUsers) {
                for (let i = 0; i < d.allTags.length; ++i) {
                    const di = d.allTags[i].id
                    counts[di]++
                    for (let j = i+1; j < d.allTags.length; ++j) {
                        const dj = d.allTags[j].id
                        values[di][dj]++
                    }
                }
            } else {
                const f = d.tags.filter(dd => dd.created_by === app.activeUserId)
                for (let i = 0; i < f.length; ++i) {
                    const di = f[i].tag_id
                    counts[di]++
                    for (let j = i+1; j < f.length; ++j) {
                        const dj = f[j].tag_id
                        values[di][dj]++
                    }
                }
            }
        })

        const array = []
        for (let i = 0; i < tags.value.length; ++i) {
            const t = tags.value[i]
            for (let j = 0; j < tags.value.length; ++j) {
                const t2 = tags.value[j]
                if (values[t.id][t2.id] > 0) {
                    array.push({ source: t.id, target: t2.id, value: values[t.id][t2.id] / counts[t.id] })
                    array.push({ source: t2.id, target: t.id, value: values[t.id][t2.id] / counts[t2.id] })
                }
            }
        }

        corr.value = array;
    }

    function onClickCell(item) {
        if (item === null) {
            app.selectByTag(null)
        } else {
            app.selectByTag([item.source, item.target], FILTER_TYPES.SET_AND)
        }
        tt.hide()
    }


    onMounted(readTags)

    watch(() => Math.max(times.all, times.tagging, times.tags), readTags)
    watch(() => Math.max(times.datatags, times.f_items), calcCorrelation)
    watch(() => app.showAllUsers, calcCorrelation)

</script>