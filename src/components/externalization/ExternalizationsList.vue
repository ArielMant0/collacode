<template>
    <div v-if="!hidden">
        <div v-if="showBarCodes" class="d-flex flex-column align-center">
            <div class="d-flex align-center">
                <MiniTree v-if="barCodeDataAll.length > 0" :selected="selectedTags" @click-node="toggleTagHighlight"/>
                <span style="width: 150px;" class="ml-2"></span>
            </div>
            <div v-if="barCodeDataAll.length > 0" class="d-flex align-center mb-1">
                <BarCode
                    :data="barCodeDataAll"
                    @select="toggleTagHighlight"
                    :selected="selectedTags"
                    id-attr="0"
                    value-attr="1"
                    name-attr="2"
                    :height="30"
                    :highlight="6"
                    :max-value="1"/>
                <span style="width: 150px;" class="text-caption ml-2">all games</span>
            </div>
            <div v-if="barCodeDataN.length > 0" class="d-flex align-center">
                <BarCode
                    :data="barCodeDataN"
                    @select="toggleTagHighlight"
                    :selected="selectedTags"
                    id-attr="0"
                    value-attr="1"
                    name-attr="2"
                    :height="30"
                    :highlight="6"
                    color-scale="interpolateRdBu"
                    :min-value="-maxDiff"
                    :max-value="maxDiff"/>
                <span style="width: 150px;" class="text-caption ml-2">games w/o externalizations</span>
            </div>
            <div v-if="barCodeDataY.length > 0" class="d-flex align-center">
                <BarCode
                    :data="barCodeDataY"
                    @select="toggleTagHighlight"
                    :selected="selectedTags"
                    id-attr="0"
                    value-attr="1"
                    name-attr="2"
                    :height="30"
                    :highlight="6"
                    color-scale="interpolateRdBu"
                    :min-value="-maxDiff"
                    :max-value="maxDiff"/>
                <span style="width: 150px;" class="text-caption ml-2">games w/ externalizations</span>
            </div>
            <div v-if="barCodeDataSel.length > 0" class="d-flex align-center">
                <BarCode
                    :data="barCodeDataSel"
                    @select="toggleTagHighlight"
                    :selected="selectedTags"
                    id-attr="0"
                    value-attr="1"
                    name-attr="2"
                    :height="30"
                    :highlight="6"
                    color-scale="interpolateRdBu"
                    :min-value="-maxDiff"
                    :max-value="maxDiff"/>
                <span style="width: 150px;" class="text-caption ml-2">selection</span>
            </div>
            <div class="mt-2 mb-2">
                <v-btn
                    @click="resetTagHighlight"
                    color="error"
                    class="mr-2 text-caption"
                    density="comfortable">
                    reset highlight
                </v-btn>
                <v-btn
                    @click="showBarMat = !showBarMat"
                    color="primary"
                    class="text-caption"
                    density="comfortable">
                    {{ showBarMat ? 'hide' : 'show' }} individual
                </v-btn>
            </div>
            <div v-if="showBarMat">
                <div v-for="([gid, _]) in visibleExts" class="d-flex align-center">
                    <BarCode v-if="barCodePerGame.has(gid)"
                        :key="'abc_'+gid"
                        :data="barCodePerGame.get(gid)"
                        :domain="barCodeDomain"
                        @select="toggleTagHighlight"
                        :selected="selectedTags"
                        id-attr="0"
                        value-attr="0"
                        name-attr="1"
                        :height="15"/>
                    <span style="width: 150px;" class="text-caption ml-2" :title="gameData.get(gid).name">{{ getName(gid) }}</span>
                </div>
            </div>
        </div>
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
                <BarCode v-if="showBarCodes && barCodePerGame.has(gid)"
                    :key="'bc_'+gid"
                    :data="barCodePerGame.get(gid)"
                    :domain="barCodeDomain"
                    @select="toggleTagHighlight"
                    :selected="selectedTags"
                    id-attr="0"
                    value-attr="0"
                    name-attr="1"
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
    import { group, InternMap } from 'd3';
    import ExternalizationGroupTile from './ExternalizationGroupTile.vue';
    import { computed, onMounted, reactive, watch } from 'vue';
    import BarCode from '../vis/BarCode.vue';
    import MiniTree from '../vis/MiniTree.vue';

    import imgUrlS from '@/assets/__placeholder__s.png'

    const times = useTimes();

    const props = defineProps({
        showBarCodes: {
            type: Boolean,
            default: false
        },
        hidden: {
            type: Boolean,
            default: false
        }
    })

    const showBarMat = ref(false)
    const exts = ref(new Map())
    const gameData = reactive(new Map())
    const maxDiff = ref(0)
    const maxDiffStatic = ref(0)

    const barCodeDomain = ref([])
    const barCodeDataY = ref([])
    const barCodeDataN = ref([])
    const barCodeDataAll = ref([])
    const barCodeDataSel = ref([])

    const barCodePerGame = reactive(new Map())

    const tags = ref([])
    const tagSet = new Set()
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

    function getName(id) {
        const name = gameData.get(id).name;
        return name.length <= 15 ? name : name.slice(0, 15)+".."
    }
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
        updateBarCodeSelection();
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
        if (!props.showBarCodes) return;
        tags.value = DM.getDataBy("tags", t => t.is_leaf === 1)
        tags.value.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return a.path.length-b.path.length
        });
        barCodeDomain.value = tags.value.map(t => t.id)
        updateBarCodeDataAll()
        updateBarCodes();
    }
    function updateBarCodes() {
        gameData.forEach(g => {
            if (!barCodePerGame.has(g.id)) {
                barCodePerGame.set(g.id, g.allTags.map(t => ([t.id, lastNames(t.pathNames)])))
            }
        })
    }
    function updateBarCodeDataAll() {
        if (!tags.value) {
            tags.value = DM.getDataBy("tags", t => t.is_leaf === 1)
            tags.value.sort((a, b) => {
                const l = Math.min(a.path.length, b.path.length);
                for (let i = 0; i < l; ++i) {
                    if (a.path[i] < b.path[i]) return -1;
                    if (a.path[i] > b.path[i]) return 1;
                }
                return 0
            });
        }

        const countsYes = new Map(), countsNo = new Map()
        tags.value.forEach(t => {
            countsYes.set(t.id, [t.id, 0, lastNames(t.pathNames)])
            countsNo.set(t.id, [t.id, 0, lastNames(t.pathNames)])
        })

        let games = 0;
        DM.getData("games", false).forEach(g => {
            if (g.allTags.length > 0) {
                games++
                g.allTags.forEach(t => {
                    const c = g.numExt > 0 ? countsYes : countsNo
                    c.set(t.id, [t.id, c.has(t.id) ? c.get(t.id)[1]+1 : 1, lastNames(t.pathNames)])
                })
            }
        })

        const arrY = Array.from(countsYes.values())
        const arrN = Array.from(countsNo.values())
        barCodeDataAll.value = arrY.map((d, i) => ([d[0], (d[1]+arrN[i][1])/games, d[2]]))

        maxDiff.value = 0
        barCodeDataY.value = arrY.map((d,i) => {
            const diff = d[1]/gameData.size - (d[1]+arrN[i][1]) / games
            maxDiff.value = Math.max(Math.abs(diff), maxDiff.value)
            return [d[0], diff, d[2]]
        })

        const numOther = games-gameData.size
        barCodeDataN.value = arrN.map((d,i) => {
            const diff = d[1]/numOther - (d[1]+arrY[i][1]) / games
            maxDiff.value = Math.max(Math.abs(diff), maxDiff.value)
            return [d[0], diff, d[2]]
        })

        maxDiffStatic.value = maxDiff.value;
    }
    function updateBarCodeSelection() {
        const counts = new Map();

        if (!tags.value) {
            tags.value = DM.getDataBy("tags", t => t.is_leaf === 1)
            tags.value.sort((a, b) => {
                const l = Math.min(a.path.length, b.path.length);
                for (let i = 0; i < l; ++i) {
                    if (a.path[i] < b.path[i]) return -1;
                    if (a.path[i] > b.path[i]) return 1;
                }
                return 0
            });
        }

        tags.value.forEach(t => counts.set(t.id, [t.id, 0, lastNames(t.pathNames)]))

        if (!DM.hasFilter("games")) {
            barCodeDataSel.value = [];
            maxDiff.value = maxDiffStatic.value;
            return;
        }

        let games = 0;
        DM.getData("games", true).forEach(g => {
            if (g.allTags.length > 0) {
                games++
                g.allTags.forEach(t => {
                    counts.set(t.id, [t.id, counts.has(t.id) ? counts.get(t.id)[1]+1 : 1, lastNames(t.pathNames)])
                })
            }
        })

        if (games === 0) {
            barCodeDataSel.value = [];
            maxDiff.value = maxDiffStatic.value;
            return;
        }

        barCodeDataSel.value = Array.from(counts.values()).map((d,i) => {
            const diff = d[1]/games - barCodeDataAll.value[i][1]
            maxDiff.value = Math.max(Math.abs(diff), maxDiff.value)
            return [d[0], diff, d[2]]
        })
    }

    function resetTagHighlight() {
        tagSet.clear()
        selectedTags.value = [];
    }
    function toggleTagHighlight(id) {
        if (tagSet.has(id)) {
            tagSet.delete(id)
        } else {
            tagSet.add(id)
        }
        selectedTags.value = Array.from(tagSet.values())
    }


    onMounted(function() {
        readExts()
        readBarCodes()
    })

    watch(showBarMat, updateBarCodes)

    watch(() => props.showBarCodes, readBarCodes)
    watch(() => Math.max(times.tagging, times.tags, times.games), readBarCodes)
    watch(() => Math.max(times.all, times.externalizations, times.ext_categories), function() {
        readExts();
        readBarCodes()
    })
    watch(() => times.f_externalizations, updateExts)
</script>