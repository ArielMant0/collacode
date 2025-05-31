<template>
    <template v-if="app.initialized">
        <MiniNav v-show="!expandNavDrawer"
            :stats="stats"
            :num-filters="numFilters"/>

        <v-expand-transition v-if="settings.showNavTop">
            <NormalNav v-show="expandNavDrawer" :stats="stats" :num-filters="numFilters"/>
        </v-expand-transition>

        <NormalNav v-else v-show="expandNavDrawer" :stats="stats" :num-filters="numFilters"/>
    </template>
</template>

<script setup>
    import { storeToRefs } from 'pinia'
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { onMounted, reactive, watch } from 'vue';
    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import { useTheme } from 'vuetify/lib/framework.mjs';
    import Cookies from 'js-cookie'
    import { useSounds } from '@/store/sounds';
    import { useGames } from '@/store/games';
    import MiniNav from './navigation/MiniNav.vue';
    import NormalNav from './navigation/NormalNav.vue';
    import { useDisplay } from 'vuetify';

    const settings = useSettings();
    const app = useApp();
    const times = useTimes()
    const sounds = useSounds()
    const games = useGames()

    const theme = useTheme()

    const { mdAndDown } = useDisplay()

    const props = defineProps({
        size: {
            type: Number,
            default: 60
        },
    })

    const numFilters = ref(0)

    const { lightMode, expandNavDrawer, showNavTop } = storeToRefs(settings);
    const { showAllUsers, activeUserId } = storeToRefs(app);

    const stats = reactive({
        numItems: 0, numItemTags: 0, numItemEv: 0, numItemMeta: 0,
        numTags: 0, numTagsUser: 0,
        numDT: 0, numDTUnique: 0, numDTUser: 0,
        numEv: 0, numEvUser: 0,
        numMeta: 0, numMetaUser: 0
    })

    function readStats() {
        readItemStats()
        readTagStats()
        readDatatagsStats();
        readEvidenceStats();
        readMetaItemsStats()
        readMetaItemsStats();
    }
    function readItemStats() {
        stats.numItems = DM.getSize("items", false);
        let wT = 0, wEv = 0, wEx = 0, dtU = 0;
        DM.getData("items", false).forEach(d => {
            if (d.allTags.length > 0) wT++
            if (d.numEvidence > 0) wEv++
            if (d.numMeta > 0) wEx++
            dtU += d.allTags.length
        })
        stats.numItemTags = wT
        stats.numItemEv = wEv
        stats.numItemMeta = wEx
        stats.numDTUnique = dtU
    }
    function readTagStats() {
        stats.numTags = DM.getSize("tags", false);
        stats.numTagsUser = showAllUsers.value ? 0 :
            DM.getSizeBy("tags", d => d.created_by === activeUserId.value);
    }
    function readDatatagsStats() {
        stats.numDT = DM.getSize("datatags", false);
        stats.numDTUser = showAllUsers.value ? 0 :
            DM.getSizeBy("datatags", d => d.created_by === activeUserId.value)
    }
    function readEvidenceStats() {
        stats.numEv = DM.getSize("evidence", false);
        stats.numEvUser = showAllUsers.value ? 0 :
            DM.getSizeBy("evidence", d => d.created_by === activeUserId.value)
    }
    function readMetaItemsStats() {
        stats.numMeta = DM.getSize("meta_items", false);
        stats.numMetaUser = showAllUsers.value ? 0 :
            DM.getSizeBy("meta_items", d => d.created_by === activeUserId.value)
    }

    onMounted(function() {
        showNavTop.value = mdAndDown.value
        const t = Cookies.get("theme")
        if (t) {
            lightMode.value = t === "light"
        } else {
            let preferDark;
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                preferDark = true
            }

            lightMode.value = preferDark !== undefined?
                !preferDark :
                !theme.global.current.value.dark
        }
        const initialVolume = Cookies.get("volume")
        if (initialVolume) {
            sounds.setVolume(Number.parseFloat(initialVolume), false)
        }
        readStats()
        numFilters.value = DM.filters.size
    })

    watch(() => times.f_any, function() {
        numFilters.value = DM.filters.size
    });

    watch(() => times.items, readItemStats)
    watch(() => times.tags, readTagStats)
    watch(() => times.datatags, readDatatagsStats)
    watch(() => times.evidence, readEvidenceStats)
    watch(() => times.meta_items, readMetaItemsStats)
    watch(activeUserId, readStats)

    watch(lightMode, function(light) {
        theme.global.name.value = light ? 'customLight' : 'customDark'
        Cookies.set("theme", light ? "light" : "dark", { expires: 365 })
        games.setThemeColors(theme.current.value.colors)
    })

    watch(mdAndDown, () => showNavTop.value = mdAndDown.value)

</script>

<style scoped>
.stat-num {
    display: inline-block;
    width: 60px;
    max-width: 60px;
    min-width: 60px;
    margin-right: 2px;
}
</style>