<template>
    <v-sheet class="pa-0">
    <v-layout>
        <v-sheet class="pa-2" :min-width="expandNavDrawer ? 300 : 60">

            <v-btn @click="expandNavDrawer = !expandNavDrawer"
                :icon="expandNavDrawer ? 'mdi-arrow-left' : 'mdi-arrow-right'"
                block
                density="compact"
                rounded="sm"
                color="secondary"/>

            <v-divider class="mb-2 mt-2"></v-divider>

            <div v-if="!expandNavDrawer" class="d-flex flex-column align-center text-caption">
                <span v-if="transitionData" class="text-caption d-flex flex-column align-center">
                    <b>{{ app.getCodeName(transitionData.old_code) }}</b>
                    to
                    <b>{{ app.getCodeName(transitionData.new_code) }}</b>
                </span>

                <span class="mt-3 mb-1" style="text-align: center;">Games:</span>
                <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numGames) }}</v-chip>

                <span class="mt-3 mb-1" style="text-align: center;">Tags:</span>
                <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numTags) }}</v-chip>
                <v-chip v-if="stats.numTagsSel > 0" density="compact" class="mt-1 text-caption" color="primary">{{ formatNumber(stats.numTagsSel) }}</v-chip>

                <span class="mt-3 mb-1" style="text-align: center;">User Tags:</span>
                <v-chip density="compact" class="text-caption">{{ formatNumber(stats.numDT) }}</v-chip>
            </div>
            <div v-else>
                <TransitionWidget :initial="activeTransition" :codes="codes" :transitions="transitions"/>
            </div>
        </v-sheet>

        <div style="width: 100%;" class="pa-2">
            <div class="mt-2">
                <RadialTree v-if="cooc.nodes.length > 0" :time="myTime" :data="cooc.nodes" :matrix="cooc.matrix" :sums="cooc.sums" :size="1000"/>
            </div>

            <div class="mt-2">
                <GameEvidenceTiles v-if="transitionData" :time="myTime" :code="transitionData.new_code"/>
            </div>
        </div>
    </v-layout>
    </v-sheet>
</template>

<script setup>

    import * as d3 from 'd3'
    import { reactive, ref, watch } from 'vue';
    import RadialTree from '../vis/RadialTree.vue';
    import GameEvidenceTiles from '@/components/evidence/GameEvidenceTiles.vue';

    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { useSettings } from '@/store/settings';
    import { formatNumber } from '@/use/utility';

    import DM from '@/use/data-manager';

    const app = useApp();
    const settings = useSettings();

    const props = defineProps({
        time: {
            type: Number,
            default: 0
        }
    });

    const myTime = ref(props.time);
    const stats = reactive({
        numGames: 0,
        numTags: 0, numTagsSel: 0,
        numDT: 0
    })
    const cooc = reactive({
        nodes: [],
        matrix: {},
        sums: {},
        labels: {}
    });

    const { activeTransition, transitionData, codes, transitions } = storeToRefs(app);
    const { expandNavDrawer } = storeToRefs(settings)

    function makeGraph() {
        cooc.matrix = {};

        const allTags = DM.getData("tags", false)
        const games = DM.getData("games", false)

        const linkVals = {}
        const sums = {};

        cooc.labels = {};
        allTags.forEach(d => {
            cooc.labels[d.id] = d.name
            sums[d.id] = 0;
        });

        games.forEach(d => {
            const ts = Array.from(d.allTags).map(d => d.id)
            for (let i = 0; i < ts.length; ++i) {
                for (let j = i+1; j < ts.length; ++j) {
                    if (i === j) continue;

                    const min = Math.min(ts[i], ts[j]);
                    const max = Math.max(ts[i], ts[j]);

                    if (!linkVals[min]) { linkVals[min] = {} }

                    if (linkVals[min][max]) {
                        linkVals[min][max]++
                    } else {
                        linkVals[min][max] = 1
                    }
                }
                sums[ts[i]]++
            }
        });

        cooc.matrix = linkVals;
        cooc.sums = sums;

        allTags.forEach(d => d.parent = d.parent === null ? -1 : d.parent)
        cooc.nodes = [{ id: -1, name: "root", parent: null, path: [] }].concat(allTags)
        console.assert(cooc.nodes.every(d => d.path !== undefined), "missing path")
    }

    watch(async () => props.time, function() {
        myTime.value = Date.now();
        stats.numGames = DM.getSize("games", false);
        stats.numTags = DM.getSize("tags", false);
        stats.numTagsSel = DM.hasFilter("tags", "id") ? DM.getSize("tags", true) : 0;
        stats.numDT = DM.getSize("datatags", false);
        makeGraph()
    })

</script>