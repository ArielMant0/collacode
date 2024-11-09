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
        </v-card>

        <div style="width: 100%; margin-left: 80px;" class="pa-2">
            <div class="mt-2 d-flex flex-column align-center">
                <ComplexRadialTree v-if="cooc.nodes.length > 0"
                    :time="myTime"
                    :data="cooc.nodes"
                    :matrix="cooc.matrix"
                    :sums="cooc.sums"
                    @click="toggleTag"
                    :size="1000"/>
            </div>

            <div class="mt-2">
                <GameEvidenceTiles v-if="currentCode" :time="myTime" :code="currentCode"/>
            </div>
        </div>
    </v-layout>
    </v-sheet>
</template>

<script setup>

    import { onMounted, reactive, ref, watch } from 'vue';
    import ComplexRadialTree from '../vis/ComplexRadialTree.vue';
    import GameEvidenceTiles from '@/components/evidence/GameEvidenceTiles.vue';
    import MiniNavBar from '../MiniNavBar.vue';

    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { useSettings } from '@/store/settings';

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

    const selTags = reactive(new Set())
    const cooc = reactive({
        nodes: [],
        matrix: {},
        sums: {},
        labels: {}
    });

    const { currentCode } = storeToRefs(app);
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

    function toggleTag(tag) {
        if (selTags.has(tag.id)) {
            selTags.delete(tag.id)
        } else {
            selTags.add(tag.id)
        }
        app.selectByTag(Array.from(selTags.values()))
    }

    onMounted(function() {
        makeGraph()
        myTime.value = Date.now();
    })

    watch(async () => props.time, function() {
        makeGraph()
        myTime.value = Date.now();
    })

</script>