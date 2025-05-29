<template>
    <v-sheet class="pa-0">
        <div v-if="!loading" style="width: 100%;" class="pa-2 d-flex flex-column align-center">

            <div class="d-flex flex-column justify-start align-start">
                <MiniTree
                    :node-width="5"
                    value-attr="from_id"
                    :value-data="barData.counts"
                    value-agg="mean"/>

                <BarCode v-if="barData.data.length > 0"
                    :data="barData.data"
                    :domain="barData.domain"
                    selectable
                    id-attr="id"
                    name-attr="name"
                    value-attr="value"
                    abs-value-attr="absolute"
                    hide-highlight
                    @click="toggleTag"
                    @right-click="onRightClick"
                    :min-value="0"
                    :max-value="1"
                    :width="5"
                    :height="20"/>
            </div>


            <ObjectionTable class="mt-4" style="width: 100%;"/>
        </div>
    </v-sheet>
</template>

<script setup>
    import { pointer } from 'd3';
    import { onMounted, reactive } from 'vue';
    import ObjectionTable from '../objections/ObjectionTable.vue';
    import BarCode from '../vis/BarCode.vue';
    import MiniTree from '../vis/MiniTree.vue';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';

    const app = useApp()
    const times = useTimes()
    const settings = useSettings()

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const barData = reactive({
        counts: {},
        data: [],
        domain: []
    })

    function calcBarData() {
        const tags = DM.getDataBy("tags_tree", d => d.is_leaf === 1)

        const tmp = []
        const counts = {}
        tags.forEach(d => {
            const list = DM.getDataItem("objections_tags", d.id)
            const count = DM.getDataItem("tags_counts", d.id)
            if (list && list.length > 0) {
                tmp.push({
                    id: d.id,
                    name: d.name,
                    absolute: list.length,
                    value: list.length / count
                })
                counts[d.id] = list.length / count
            } else {
                counts[d.id] = 0
            }
        })
        barData.counts = counts
        barData.domain = tags.map(d => d.id)
        barData.data = tmp
    }

     function toggleTag(tag) {
        app.toggleSelectByTag([tag.id])
    }
    function onRightClick(tag, event) {
        event.preventDefault();
        if (tag) {
            const [mx, my] = pointer(event, document.body)
            settings.setRightClick(
                "tag", tag.id,
                mx, my,
                tag.name, null,
                CTXT_OPTIONS.tag
            );
        } else {
            settings.setRightClick(null)
        }
    }

    onMounted(calcBarData)

    watch(() => Math.max(times.all, times.objections, times.tags), calcBarData)

</script>