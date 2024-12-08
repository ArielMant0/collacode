<template>
    <v-sheet class="pa-0">
        <div style="width: 100%;" class="pa-2">
            <div v-if="!loading" class="mt-2 d-flex align-center flex-column">

                <GameHistogram
                    :attributes="gameAttrs"
                    :width="Math.max(600, Math.min(1000, size-10))"/>

                <TreeMap v-if="tags"
                    :data="tags"
                    :time="myTime"
                    :selected="selTags"
                    :width="Math.max(1000, size-10)"
                    :height="1000"
                    collapsible
                    valid-attr="valid"
                    @click="toggleTag"
                    @right-click="onRightClickTag"/>

                <!-- <ComplexRadialTree v-if="cooc.nodes.length > 0"
                    :time="myTime"
                    :data="cooc.nodes"
                    :matrix="cooc.matrix"
                    :sums="cooc.sums"
                    :selected="selTags"
                    @click="toggleTag"
                    :size="1000"/> -->
            </div>
        </div>
    </v-sheet>
</template>

<script setup>

    import * as d3 from 'd3'
    import { onMounted, reactive, ref, watch } from 'vue';
    import ComplexRadialTree from '../vis/ComplexRadialTree.vue';
    import GameHistogram from '../games/GameHistogram.vue';
    import TreeMap from '../vis/TreeMap.vue';

    import { useApp } from '@/store/app';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';

    import DM from '@/use/data-manager';

    const app = useApp();
    const settings = useSettings();
    const times = useTimes()

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

    const myTime = ref(Date.now());
    const tags = ref([])

    let selTagsMap = new Set()
    const selTags = ref([])
    const cooc = reactive({
        nodes: [],
        matrix: {},
        sums: {},
        labels: {}
    });

    const gameAttrs = [
        { title: "release year", key: "year" },
        { title: "expertise rating", key: "expertise", value: d => getExpValue(d), min: 0, max: 3, labels: { 0: "none", 1: "basic", 2: "knowledgeable", 3: "expert" } },
        { title: "tags per game", key: "numTags", aggregate: true },
        { title: "evidence per game", key: "numEvidence", aggregate: true },
    ]

    function getExpValue(game) {
        if (app.showAllUsers) {
            return d3.max(app.users.map(u => {
                const r = game.expertise.find(d => d.user_id === u.id)
                return r ? r.value : 0
            }))
        }
        const r = game.expertise.find(d => d.user_id === app.activeUserId)
        return r ? r.value : 0
    }

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

        myTime.value = Date.now();
    }

    function toggleTag(tag) {
        app.toggleSelectByTag([tag.id])
    }
    function onRightClickTag(tag, event) {
        const [mx, my] = d3.pointer(event, document.body)
        settings.setRightClick(
            "tag", tag.id,
            mx + 10,
            my + 10,
            null,
            CTXT_OPTIONS.tag,
        )
    }

    function readSelectedTags() {
        const sels = DM.getSelectedIdsArray("tags")
        selTagsMap = new Set(sels)
        selTags.value = sels
        myTime.value = Date.now()
    }

    function readTags() {
        tags.value = DM.getData("tags", false)
    }

    onMounted(function() {
        readTags()
        readSelectedTags()
        // makeGraph()
    })

    watch(() => Math.max(times.tags, times.datatags, times.tagging), readTags)
    watch(active, (now) => { if (now) myTime.value = Date.now() })
    watch(() => times.f_tags, readSelectedTags)

</script>