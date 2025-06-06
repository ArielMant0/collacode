<template>
    <v-sheet class="pa-0">
        <div v-if="!loading" style="width: 100%;" class="pa-2 d-flex flex-column align-center">
            <div v-if="smAndUp" class="d-flex align-end">
                <span style="width: 50px;"></span>
                <MiniTree
                    :node-width="barCodeNodeSize"
                    value-attr="from_id"
                    :value-data="barData.counts"
                    value-agg="mean"/>
            </div>

            <div v-if="smAndUp" class="d-flex align-center text-caption">
                <span style="width: 50px;">open</span>
                <BarCode v-if="barData.open.length > 0"
                    :data="barData.open"
                    :domain="barData.domain"
                    selectable
                    id-attr="id"
                    name-attr="name"
                    value-attr="value"
                    :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                    abs-value-attr="absolute"
                    hide-highlight
                    @click="toggleTag"
                    @right-click="onRightClick"
                    :min-value="0"
                    :max-value="1"
                    :width="barCodeNodeSize"
                    :height="20"/>
            </div>

            <div v-if="smAndUp" class="d-flex align-center mb-4 text-caption">
                <span style="width: 50px;">closed</span>
                <BarCode v-if="barData.closed.length > 0"
                    :data="barData.closed"
                    :domain="barData.domain"
                    selectable
                    id-attr="id"
                    name-attr="name"
                    value-attr="value"
                    abs-value-attr="absolute"
                    :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
                    hide-highlight
                    @click="toggleTag"
                    @right-click="onRightClick"
                    :min-value="0"
                    :max-value="1"
                    :width="barCodeNodeSize"
                    :height="20"/>
            </div>

            <ObjectionTable style="width: 100%;"/>
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
    import { OBJECTION_STATUS, useApp } from '@/store/app';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useDisplay } from 'vuetify';
    import { storeToRefs } from 'pinia';

    const app = useApp()
    const times = useTimes()
    const settings = useSettings()

    const { smAndUp } = useDisplay()
    const { barCodeNodeSize } = storeToRefs(settings)

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const barData = reactive({
        counts: {},
        open: [],
        closed: [],
        domain: []
    })

    function calcBarData() {
        const tags = DM.getDataBy("tags_tree", d => d.is_leaf === 1)

        const tmpOpen = [], tmpClosed = []
        const counts = {}
        tags.forEach(d => {
            const list = DM.getDataItem("objections_tags", d.id)
            const open = list ? list.filter(dd => dd.status === OBJECTION_STATUS.OPEN) : null
            const count = DM.getDataItem("tags_counts", d.id)
            if (list && list.length > 0) {
                tmpOpen.push({
                    id: d.id,
                    name: d.name,
                    absolute: open.length,
                    value: open.length / count
                })
                tmpClosed.push({
                    id: d.id,
                    name: d.name,
                    absolute: (list.length - open.length),
                    value: (list.length - open.length) / count
                })
                counts[d.id] = list.length / count
            } else {
                counts[d.id] = 0
            }
        })
        barData.counts = counts
        barData.domain = tags.map(d => d.id)
        barData.open = tmpOpen
        barData.closed = tmpClosed
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