<template>
    <div>
        <v-sheet v-for="([gid, data]) in exts" :key="gid" style="width: 100%;" class="pa-1 mt-2">
            <div class="d-flex align-center mb-2">
                <v-img
                    :src="'teaser/'+gameData.get(gid).teaser"
                    :lazy-src="imgUrlS"
                    class="ml-1"
                    cover
                    style="max-width: 80px; max-height: 40px;"
                    width="80"
                    height="40"/>
                <span class="ml-2">{{ gameData.get(gid).name }}</span>
            </div>
            <ExternalizationTile v-for="e in data" :key="e.id" :item="e" show-bars/>
        </v-sheet>
    </div>
</template>

<script setup>
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { onMounted } from 'vue';
    import ExternalizationTile from './ExternalizationTile.vue';
    import { group } from 'd3';
    import imgUrlS from '@/assets/__placeholder__s.png'

    const times = useTimes();

    const props = defineProps({
        time: {
            type: Number,
            required: true
        }
    })
    const exts = ref(new Map())
    const gameData = reactive(new Map())

    function readExts() {
        gameData.clear()
        const data = DM.getData("externalizations", true)
        data.forEach(d => gameData.set(d.game_id, DM.getDataItem("games", d.game_id)))
        exts.value = group(data, d => d.game_id)
    }

    onMounted(readExts)

    watch(() => [props.time, times.externalizations], readExts, { deep: true })
</script>