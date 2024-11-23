<template>
    <div v-if="!hidden">
        <v-sheet v-for="([gid, groups]) in visibleExts" :key="gid" style="width: 100%;" class="pa-1 mt-2">
            <div class="d-flex align-center mb-2">
                <v-img
                    :src="'teaser/'+gameData.get(gid).teaser"
                    :lazy-src="imgUrlS"
                    class="ml-1"
                    cover
                    style="max-width: 80px; max-height: 40px;"
                    width="80"
                    height="40"/>
                <span class="ml-2 mr-2">{{ gameData.get(gid).name }}</span>
                <BarCode v-if="barCodePerGame.has(gid)"
                    :key="'bc_'+gid"
                    :data="barCodePerGame.get(gid)"
                    :domain="barCodeDomain"
                    @select="toggleTagHighlight"
                    :selected="selectedTags"
                    :width="3"
                    :height="15"/>
            </div>
            <ExternalizationGroupTile v-for="g in groups"
                :key="'group_'+g"
                :id="g"
                class="mb-2"
                :selected="selectedExts"
                allow-edit
                :item="gameData.get(gid)"/>
        </v-sheet>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import { useApp } from '@/store/app';
    import { group, InternMap } from 'd3';
    import ExternalizationGroupTile from './ExternalizationGroupTile.vue';
    import { computed, onMounted, reactive, watch } from 'vue';
    import BarCode from '../vis/BarCode.vue';

    import imgUrlS from '@/assets/__placeholder__s.png'

    const app = useApp()
    const times = useTimes();

    const props = defineProps({
        hidden: {
            type: Boolean,
            default: false
        }
    })

    const exts = ref(new Map())
    const gameData = reactive(new Map())

    const barCodeDomain = ref([])
    const barCodePerGame = reactive(new Map())

    const selectedTags = ref([])
    const selectedExts = ref([])
    const selectedGroups = ref(new Set())

    const visibleExts = computed(() => {
        // selection but no matches
        if (!selectedGroups.value) return []
        // no selection
        if (selectedGroups.value.size === 0) return exts.value

        const m = new InternMap()
        exts.value.forEach((array, game) => {
            const v = array.filter(d => selectedGroups.value.has(d))
            if (v.length > 0) {
                m.set(game, v)
            }
        })
        return m
    });

    function readExts() {
        gameData.clear()
        const data = DM.getData("externalizations", true)
        data.forEach(d => {
            if (!gameData.has(d.game_id)) {
                gameData.set(d.game_id, DM.getDataItem("games", d.game_id))
            }
        })
        const perGame = group(data, d => d.game_id)
        exts.value = new InternMap(Array.from(perGame.entries()).map(([gameid, d]) => ([gameid, Array.from(new Set(d.map(dd => dd.group_id)))])))
    }
    function updateExts() {
        const ses = DM.hasFilter("externalizations") ? DM.getData("externalizations") : []
        if (ses.length === 0 && DM.hasFilter("externalizations")) {
            selectedExts.value = []
            selectedGroups.value = null
        } else {
            selectedExts.value = ses.map(d => d.id)
            selectedGroups.value = new Set(ses.map(d => d.group_id))
        }
    }

    function lastNames(n) {
        const parts = n.split("/")
        if (parts.length === 1) return n
        return parts.map((d, i) => i == 0 || i >= parts.length-2 ? d : "..")
            .reverse()
            .join(" / ")
    }
    function readBarCodes() {
        barCodePerGame.clear()
        const tags = DM.getDataBy("tags", t => t.is_leaf === 1)
        tags.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return a.path.length-b.path.length
        });
        barCodeDomain.value = tags.map(t => t.id)
        updateBarCodes();
    }
    function updateBarCodes() {
        gameData.forEach(g => {
            if (!barCodePerGame.has(g.id)) {
                barCodePerGame.set(g.id, g.allTags.map(t => ([t.id, lastNames(t.pathNames)])))
            }
        })
    }

    function toggleTagHighlight(id) {
        app.toggleSelectByTag([id])
    }

    onMounted(function() {
        readExts()
        readBarCodes()
    })

    watch(() => Math.max(times.tagging, times.tags, times.games), readBarCodes)
    watch(() => Math.max(times.all, times.externalizations, times.ext_categories), function() {
        readExts();
        readBarCodes()
    })
    watch(() => times.f_externalizations, updateExts)
</script>