<template>
    <div>
        <div v-if="showBarCodes" class="d-flex flex-column align-center">
            <div class="d-flex">
                <BarCode v-if="barCodeData.length > 0" :data="barCodeData" value-attr="0" name-attr="1" :height="30" :max-value="gameData.size"/>
                <span style="width: 150px;" class="ml-2">all tag occurences</span>
            </div>
            <v-btn
                @click="showBarMat = !showBarMat"
                color="primary"
                class="mt-2 mb-2 text-caption"
                density="comfortable">
                {{ showBarMat ? 'hide' : 'show' }} details
            </v-btn>
            <div v-if="showBarMat">
                <div v-for="([gid, _]) in exts" class="d-flex mb-1">
                    <BarCode v-if="barCodePerGame.has(gid)"
                        :key="'abc_'+gid"
                        :data="barCodePerGame.get(gid)"
                        :domain="barCodeDomain"
                        value-attr="0"
                        name-attr="1"
                        :height="20"/>
                    <span style="width: 150px;" class="ml-2" :title="gameData.get(gid).name">{{ getName(gid) }}</span>
                </div>
            </div>
        </div>
        <v-sheet v-for="([gid, groups]) in exts" :key="gid" style="width: 100%;" class="pa-1 mt-2">
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
                    :time="time"
                    :data="barCodePerGame.get(gid)"
                    :domain="barCodeDomain"
                    value-attr="0"
                    name-attr="1"
                    :width="3"
                    :height="25"/>
            </div>
            <ExternalizationGroupTile v-for="g in groups"
                :key="g" :id="g" class="mb-2"
                :item="gameData.get(gid)"/>
        </v-sheet>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import { group, InternMap } from 'd3';
    import ExternalizationGroupTile from './ExternalizationGroupTile.vue';
    import BarCode from '../vis/BarCode.vue';
    import { onMounted, watch } from 'vue';

    import imgUrlS from '@/assets/__placeholder__s.png'

    const times = useTimes();

    const props = defineProps({
        time: {
            type: Number,
            required: true
        },
        showBarCodes: {
            type: Boolean,
            default: false
        }
    })

    const showBarMat = ref(false)
    const exts = ref(new Map())
    const gameData = reactive(new Map())
    const barCodeDomain = ref([])
    const barCodeData = ref([])
    const barCodePerGame = reactive(new Map())
    const barTime = ref(props.time)

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
        const tags = DM.getDataBy("tags", t => t.is_leaf === 1)
        tags.sort((a, b) => {
            const l = Math.min(a.path.length, b.path.length);
            for (let i = 0; i < l; ++i) {
                if (a.path[i] < b.path[i]) return -1;
                if (a.path[i] > b.path[i]) return 1;
            }
            return 0
        });
        barCodeDomain.value = tags.map(t => t.id)
        gameData.forEach(g => {
            barCodePerGame.set(g.id, g.allTags.map(t => ([t.id, lastNames(t.pathNames)])))
        })
        updateBarCodeData(tags)
    }
    function updateBarCodes() {
        gameData.forEach(g => {
            if (!barCodePerGame.has(g.id)) {
                barCodePerGame.set(g.id, g.allTags.map(t => ([t.id, lastNames(t.pathNames)])))
            }
        })
        updateBarCodeData();
    }
    function updateBarCodeData(tags) {
        if (!tags) {
            tags = DM.getDataBy("tags", t => t.is_leaf === 1)
            tags.sort((a, b) => {
                const l = Math.min(a.path.length, b.path.length);
                for (let i = 0; i < l; ++i) {
                    if (a.path[i] < b.path[i]) return -1;
                    if (a.path[i] > b.path[i]) return 1;
                }
                return 0
            });
        }
        const counts = new Map()
        tags.forEach(t => counts.set(t.id, [0, lastNames(t.pathNames)]))
        gameData.forEach(g => {
            g.allTags.forEach(t => counts.set(t.id, [counts.has(t.id) ? counts.get(t.id)[0]+1 : 1, lastNames(t.pathNames)]))
        })
        barCodeData.value = Array.from(counts.values())
        barTime.value = Date.now()
    }


    onMounted(function() {
        readExts()
        readBarCodes()
    })

    watch(showBarMat, updateBarCodes)
    watch(() => props.showBarCodes, updateBarCodes)
    watch(() => times.games, readBarCodes)
    watch(() => props.time, function() {
        readExts()
        updateBarCodeData()
    })
    watch(() => times.externalizations, function() {
        readExts();
        readBarCodes()
    })
</script>