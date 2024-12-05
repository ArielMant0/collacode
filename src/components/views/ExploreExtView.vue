<template>
    <v-sheet class="pa-0">
        <div v-if="!loading" style="width: 100%;" class="pa-2">
            <div class="mt-4" style="text-align: center;">
                <ExtDimsBars/>
            </div>

        </div>
    </v-sheet>
</template>

<script setup>
    import { pointer } from 'd3';

    import { useApp } from '@/store/app';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';

    import DM from '@/use/data-manager';
    import { useTooltip } from '@/store/tooltip';
    import ExtDimsBars from '../externalization/ExtDimsBars.vue';

    const app = useApp();
    const settings = useSettings();
    const tt = useTooltip()

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
        size: {
            type: Number,
            default: 1000
        }
    })

    function showExtTooltip(id, event) {
        if (id) {
            const ext = DM.getDataItem("externalizations", id)
            const game = DM.getDataItem("games", ext.game_id)
            const wN = ext.name.length > 15 ? 415 : Math.min(415, ext.name.length * 15 + 15)
            const wD = ext.description.length > 100 ? 415 : Math.min(415, ext.description.length * 6 + 15)
            tt.show(`<div class='text-caption'>
                <div><b>${game.name}, ${ext.name}</b></div>
                <p>${ext.description}</p>
            </div>`, event.pageX-Math.max(wN, wD), event.pageY)
        } else {
            tt.hide()
        }
    }

    function selectExtById(id) {
        app.toggleSelectByExternalization([id])
        myTime.value = Date.now();
    }

    function selectExtByCat(id) {
        app.toggleSelectByExtCategory([id])
        myTime.value = Date.now();
    }

    function contextExt(id, event) {
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "externalization", id,
            mx + 10,
            my + 10,
            null,
            CTXT_OPTIONS.externalization
        )
    }
    function contextExtCat(id, event) {
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "ext_category", id,
            mx + 10,
            my + 10,
            { parent: id },
            CTXT_OPTIONS.ext_category
        )
    }
    function contextExtDim(name, event) {
        const item = psets.cats.find(d => d.name === name)
        if(!item) return;
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "ext_category", item.id,
            mx + 10,
            my + 10,
            { parent: item.id },
            CTXT_OPTIONS.ext_category
        )
    }

</script>