<template>
    <div class="text-caption" style="text-align: center;">
        <div v-if="corr.length > 0">
            <div class="d-flex">
                <span style="width: 150px"></span>
                <div>
                    <div><b>Which tags occurr together? {{ app.showAllUsers ? "(all users)" : "(only you)" }}</b></div>
                    <MiniTree :node-width="5"/>
                </div>
            </div>
            <HeatMatrix
                :data="corr"
                :domain-values="tags.map(t => t.id)"
                :labels="corrLabels"
                hide-x-labels
                @click="onClickCell"
                :cell-size="tags.length > 100 ? 5 : undefined"
                :size="1000"/>
        </div>
        <div v-else style="text-align: center; min-width: 1000px; min-height: 100px;">
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

    const app = useApp()
    const times = useTimes()
    const tt = useTooltip()

    const corr = ref([])
    const corrLabels = {}

    let tags = [];


    function readTags() {
        tags = DM.getDataBy("tags_tree", d => d.is_leaf === 1)
        calcCorrelation()
    }
    function calcCorrelation() {
        const items = DM.getData("items", true)

        const values = {}
        const counts = {}

        tags.forEach(t => {
            counts[t.id] = 0
            values[t.id] = {}
            for (let j = 0; j < tags.length; ++j) {
                values[t.id][tags[j].id] = 0
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
        for (let i = 0; i < tags.length; ++i) {
            const t = tags[i]
            for (let j = 0; j < tags.length; ++j) {
                const t2 = tags[j]
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