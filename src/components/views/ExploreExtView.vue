<template>
    <v-sheet class="pa-0">
    <v-layout>

        <MiniNavBar
            :code-name="transitionData ? app.getCodeName(transitionData.old_code) : '?'"
            :other-code-name="transitionData ? app.getCodeName(transitionData.new_code) : '?'"
            :num-games="stats.numGames"
            :num-tags="stats.numTags"
            :num-tags-sel="stats.numTagsSel"
            :num-d-t="stats.numDT"
            />

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
                    :data="psets.data"
                    :dimensions="psets.dims"
                    @click-dot="selectExtById"
                    @click-rect="selectExtByCat"
                    @hover-dot="showExtTooltip"
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

            <div class="mt-4">
                <ExternalizationsList :time="myTime" show-bar-codes/>
            </div>
        </div>
    </v-layout>
    </v-sheet>
</template>

<script setup>
    import { onMounted, reactive, ref, watch } from 'vue';
    import ParallelSets from '../vis/ParallelSets.vue';
    import ChordDiagram from '../vis/ChordDiagram.vue';
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
    const stats = reactive({
        numGames: 0, numGamesSel: 0,
        numTags: 0, numTagsSel: 0,
        numDT: 0
    })
    const psets = reactive({
        data: [],
        dims: [],
        cats: [],
        activeCats: new Set()
    });

    const { activeTransition, transitionData, codes, transitions } = storeToRefs(app);
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
        psets.data = exts.map(d => {
            const obj = { id: d.id, group_id: d.group_id }
            d.categories.forEach(c => {
                const node = extCats.find(dd => dd.id === c.cat_id)
                if (node) {
                    const pname = dimMap.get(node.parent)
                    if (!obj[pname]) obj[pname] = []
                    obj[pname].push(node.name)
                }
            })
            for (const key in obj) {
                if (key !== "id" && key !== "group_id") {
                    obj[key].sort()
                }
            }
            return obj
        });
    }

    function showExtTooltip(event, id) {
        if (id) {
            const ext = DM.getDataItem("externalizations", id)
            const game = DM.getDataItem("games", ext.game_id)
            tt.show(`<div class='text-caption'>
                <div><b>${game.name}, ${ext.name}</b></div>
                <p>${ext.description}</p>
            </div>`, event.pageX, event.pageY)
        } else {
            tt.hide()
        }
    }

    function selectExtById(id) {
        DM.toggleFilter('externalizations', 'id', [id]);
        myTime.value = Date.now()
    }

    function selectExtByCat(name) {
        if (psets.activeCats.has(name)) {
            psets.activeCats.delete(name)
        } else {
            psets.activeCats.add(name)
        }

        if (psets.activeCats.size === 0) {
            DM.removeFilter('externalizations', 'categories')
        } else {
            DM.setFilter('externalizations', 'categories', cats => {
                let all = true;
                psets.activeCats.forEach(name => {
                    if (!cats.find(d => psets.cats.find(c => c.id === d.cat_id).name === name)) {
                        all = false;
                    }
                })
                return all
            }, psets.activeCats);
        }
        myTime.value = Date.now()
    }

    onMounted(readExts)

    watch(async () => props.time, function() {
        stats.numGames = DM.getSize("games", false);
        stats.numGamesSel = DM.getSize("games", true);
        stats.numTags = DM.getSize("tags", false);
        stats.numTagsSel = DM.hasFilter("tags", "id") ? DM.getSize("tags", true) : 0;
        stats.numDT = DM.getSize("datatags", false);
        myTime.value = Date.now();
    })

    watch(() => times.externalizations, readExts)

</script>