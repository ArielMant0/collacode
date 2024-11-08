<template>
    <v-sheet class="pa-0">
    <v-layout>

        <MiniNavBar
            :user-color="app.activeUser ? app.activeUser.color : 'default'"
            :code-name="app.activeCode ? app.getCodeName(app.activeCode) : '?'"
            :time="myTime"/>

        <v-card v-if="expandNavDrawer"  class="pa-2" :min-width="300" position="fixed" style="z-index: 3999; height: 100vh">
            <v-btn @click="expandNavDrawer = !expandNavDrawer"
                icon="mdi-arrow-left"
                block
                class="mb-2"
                density="compact"
                rounded="sm"
                color="secondary"/>

            <TransitionWidget :initial="activeTransition" :codes="codes" :transitions="transitions"/>
        </v-card>

        <div ref="wrapper" style="width: 100%; margin-left: 80px;" class="pa-2">
            <div class="mt-4" style="text-align: center;">
                <div><i class="text-caption">which connections should be displayed</i></div>
                <v-btn-toggle v-model="linksBy" density="compact" mandatory>
                    <v-btn value="none">none</v-btn>
                    <v-btn value="ext_id">ext</v-btn>
                    <v-btn value="group_id">group</v-btn>
                </v-btn-toggle>
                <ParallelDots v-if="psets.data"
                    :time="myTime"
                    :data="psets.data"
                    :dimensions="psets.dims"
                    name-attr="dim"
                    value-attr="name"
                    @click-dot="selectExtById"
                    @click-rect="selectExtByCat"
                    @hover-dot="showExtTooltip"
                    @hover-rect="tt.hide"
                    :link-by="linksBy !== 'none' ? linksBy : ''"
                    :width="Math.max(500, wSize.width.value-50)"/>
            </div>

            <!-- <div class="mt-4" style="text-align: center;">
                <ParallelSets v-if="psets.data"
                    :data="psets.data"
                    :dimensions="psets.dims"
                    :width="Math.max(500, wSize.width.value-50)"/>
            </div>

            <div class="mt-4" style="text-align: center;">
                <ChordDiagram v-if="psets.data"
                    :data="psets.data"
                    :dimensions="psets.dims"
                    :width="Math.max(500, wSize.width.value-50)"/>
            </div> -->
            <div class="d-flex justify-center mt-4">
                <EmbeddingExplorer :time="myTime" :size="600"/>
            </div>

            <div class="mt-4">
                <ExternalizationsList :time="myTime" show-bar-codes/>
            </div>
        </div>
    </v-layout>
    </v-sheet>
</template>

<script setup>
    import { onMounted, reactive, ref, watch } from 'vue';
    import ParallelDots from '../vis/ParallelDots.vue';
    import MiniNavBar from '../MiniNavBar.vue';
    import TransitionWidget from '../TransitionWidget.vue';

    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import { useElementSize } from '@vueuse/core';

    import { group } from 'd3';
    import DM from '@/use/data-manager';
    import ExternalizationsList from '../externalization/ExternalizationsList.vue';
    import { useTooltip } from '@/store/tooltip';
    import EmbeddingExplorer from '../EmbeddingExplorer.vue';

    const app = useApp();
    const times = useTimes()
    const settings = useSettings();
    const tt = useTooltip()

    const props = defineProps({
        time: {
            type: Number,
            default: 0
        }
    });

    const wrapper = ref(null)
    const wSize = useElementSize(wrapper)

    const linksBy = ref("none")
    const myTime = ref(props.time);

    const psets = reactive({
        data: [],
        dims: [],
        cats: [],
        activeCats: new Set()
    });

    const { activeTransition, codes, transitions } = storeToRefs(app);
    const { expandNavDrawer } = storeToRefs(settings)

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

        psets.cats = extCats;
        const array = []
        exts.forEach(d => {
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
    }

    function showExtTooltip(event, id) {
        if (id) {
            const ext = DM.getDataItem("externalizations", id)
            const game = DM.getDataItem("games", ext.game_id)
            tt.show(`<div class='text-caption'>
                <div><b>${game.name}, ${ext.name}</b></div>
                <p>${ext.description}</p>
            </div>`, event.pageX+15, event.pageY)
        } else {
            tt.hide()
        }
    }

    function setGamesFilter() {
        if (DM.hasFilter("externalizations")) {
            DM.setFilter(
                "games",
                "id",
                DM.getData("externalizations", true).map(d => d.game_id)
            )
        } else {
            DM.removeFilter("games", "id")
        }
        myTime.value = Date.now()
    }

    function selectExtById(id) {
        DM.toggleFilter('externalizations', 'id', [id]);
        setGamesFilter()
    }

    function selectExtByCat(id) {
        if (psets.activeCats.has(id)) {
            psets.activeCats.delete(id)
        } else {
            psets.activeCats.add(id)
        }

        if (psets.activeCats.size === 0) {
            DM.removeFilter('externalizations', 'categories')
        } else {
            DM.setFilter('externalizations', 'categories', cats => {
                let num = 0;
                cats.forEach(d => {
                    if (psets.activeCats.has(d.cat_id)) {
                        num++;
                    }
                })
                return num === psets.activeCats.size
            }, psets.activeCats);
        }
        setGamesFilter()
    }

    onMounted(readExts)

    watch(() => props.time, () => myTime.value = Date.now())

    watch(() => times.externalizations, readExts)

</script>