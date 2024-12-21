<template>
    <v-sheet class="pa-0">
        <div ref="el" style="width: 100%;" class="pa-2">
            <div v-if="!loading" class="mt-2 d-flex align-center flex-column">

                <GameHistogram
                    :attributes="gameAttrs"
                    :width="Math.max(600, Math.min(1000, width-10))"/>

                <TreeMap v-if="tags"
                    :data="tags"
                    :time="myTime"
                    :selected="selTags"
                    :width="Math.max(1000, width-10)"
                    :height="1000"
                    collapsible
                    valid-attr="valid"
                    @click="toggleTag"
                    @right-click="onRightClickTag"/>

            </div>
        </div>
    </v-sheet>
</template>

<script setup>

    import * as d3 from 'd3'
    import { onMounted, ref, watch } from 'vue';
    import GameHistogram from '../games/GameHistogram.vue';
    import TreeMap from '../vis/TreeMap.vue';
    import { useElementSize } from '@vueuse/core';

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
    })
    const el = ref(null)
    const { width } = useElementSize(el)
    const active = computed(() => settings.activeTab === "explore_tags")

    const myTime = ref(Date.now());
    const tags = ref([])

    let selTagsMap = new Set()
    const selTags = ref([])

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