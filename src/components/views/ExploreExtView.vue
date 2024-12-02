<template>
    <v-sheet class="pa-0">
        <div v-if="!loading" style="width: 100%;" class="pa-2">
            <div class="mt-4" style="text-align: center;">
                <!-- <div class="d-flex justify-center">
                    <div class="mb-1 mr-4" style="display: block; text-align: center;">
                        <div><i class="text-caption">which connections should be displayed</i></div>
                        <v-btn-toggle v-model="linksBy" density="compact" mandatory color="primary">
                            <v-btn density="compact" value="none">none</v-btn>
                            <v-btn density="compact" value="ext_id">ext</v-btn>
                            <v-btn density="compact" value="group_id">group</v-btn>
                        </v-btn-toggle>
                    </div>
                    <div class="mb-2 ml-4" style="display: block; text-align: center;">
                        <div><i class="text-caption">how to combine categories</i></div>
                        <v-btn-toggle v-model="selMode" density="compact" mandatory color="primary" @update:model-value="myTime = Date.now()">
                            <v-btn density="compact" :value="S_MODES.OR">OR</v-btn>
                            <v-btn density="compact" :value="S_MODES.AND">AND</v-btn>
                        </v-btn-toggle>
                    </div>
                </div> -->
                <!-- <ParallelDots v-if="psets.data"
                    :time="myTime"
                    :data="psets.data"
                    :dimensions="psets.dims"
                    name-attr="dim"
                    value-attr="name"
                    @click-dot="selectExtById"
                    @click-rect="selectExtByCat"
                    @right-click-dot="contextExt"
                    @right-click-rect="contextExtCat"
                    @right-click-dim="contextExtDim"
                    @hover-dot="showExtTooltip"
                    @hover-rect="tt.hide"
                    :link-by="linksBy !== 'none' ? linksBy : ''"
                    :width="Math.max(500, size-50)"/> -->

                <ParallelSets v-if="psets.sets"
                    :data="psets.sets"
                    :dimensions="psets.dims"
                    value-attr="categories"
                    :width="Math.max(500, size-50)"
                    :height="800"
                    class="mb-2"
                    />
            </div>

        </div>
    </v-sheet>
</template>

<script setup>
    import { pointer } from 'd3';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import ParallelDots from '../vis/ParallelDots.vue';

    import { useApp } from '@/store/app';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';

    import { group } from 'd3';
    import DM from '@/use/data-manager';
    import { useTooltip } from '@/store/tooltip';
    import ParallelSets from '../vis/ParallelSets.vue';

    const app = useApp();
    const times = useTimes()
    const settings = useSettings();
    const tt = useTooltip()

    const S_MODES = Object.freeze({
        OR: 0,
        AND: 1
    })

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
    const active = computed(() => settings.activeTab === "explore_exts")

    const linksBy = ref("none")
    const selMode = ref(S_MODES.OR)
    const myTime = ref(Date.now());
    const loaded = ref(false)

    const psets = reactive({
        data: [],
        sets: [],
        dims: [],
        cats: [],
        activeCats: new Set()
    });

    function getRequiredCategories(categories) {
        const leaves = categories.filter(d => !categories.some(dd => dd.parent === d.id))
        const set = new Set(Array.from(group(leaves, d => d.parent).keys()))
        return categories.filter(d => set.has(d.id))
    }

    function readExts() {
        const exts = DM.getData("externalizations", false)
        const extCats = DM.getData("ext_categories", false)
        const dimMap = new Map()
        psets.dims = getRequiredCategories(extCats).map(d => {
            dimMap.set(d.id, d.name);
            return d.name
        })
        psets.dims.sort((a, b) => settings.extCatOrder.indexOf(a)-settings.extCatOrder.indexOf(b))

        psets.cats = extCats;
        const array = [], array2 = [];

        const paths = DM.getDerived("ext_cats_path")
        exts.forEach(d => {
            const obj = {}
            dimMap.forEach((name, id) => {
                obj[name] = d.categories
                    .filter(c => {
                        const p = paths.find(dd => dd.id === c.cat_id)
                        return p ? p.path.includes(id) : false
                    })
                    .map(c => ({
                        cat_id: c.cat_id,
                        ext_id: c.ext_id,
                        group_id: d.group_id,
                        dim: name,
                        name: extCats.find(dd => dd.id === c.cat_id).name
                    }))
            })
            array2.push({
                id: d.id,
                cluster: d.cluster,
                categories: obj
            })
            d.categories.forEach(c => {
                const node = extCats.find(dd => dd.id === c.cat_id)
                if (node) {
                    const pname = dimMap.get(node.parent)
                    array.push({
                        cat_id: node.id,
                        ext_id: d.id,
                        group_id: d.group_id,
                        dim: pname,
                        name: node.name
                    })
                }
            })
        });
        psets.data = array
        psets.sets = array2
        myTime.value = Date.now();
    }

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

    onMounted(function() {
        readExts()
        loaded.value = true;
    })

    watch(active, (now) => { if (now) myTime.value = Date.now() })
    watch(() => Math.max(times.f_externalizations, times.f_games), () => myTime.value = Date.now())
    watch(() => Math.max(times.all, times.tags, times.datatags, times.tagging, times.externalizations), readExts)

</script>