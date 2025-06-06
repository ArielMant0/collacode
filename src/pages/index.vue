<template>
    <section>
        <ActionContextMenu/>
        <GlobalShortcuts/>

        <nav v-if="initialized" class="topnav d-flex align-stretch justify-center">
            <NavLink to="coding" :active="activeTab" :text="settings.tabNames.coding" :icon="settings.tabIcons.coding"/>
            <NavLink to="objections" :active="activeTab" :text="settings.tabNames.objections" :icon="settings.tabIcons.objections"/>
            <NavLink to="agree" :active="activeTab" :text="settings.tabNames.agree" :icon="settings.tabIcons.agree"/>
            <NavLink to="transition" :active="activeTab" :text="settings.tabNames.transition" :icon="settings.tabIcons.transition"/>

            <v-divider vertical thickness="2" color="primary" opacity="1" class="ml-1 mr-1"></v-divider>

            <NavLink to="games" :active="activeTab" :text="settings.tabNames.games" :icon="settings.tabIcons.games"/>

            <v-divider vertical thickness="2" color="primary" class="ml-1 mr-1" opacity="1"></v-divider>

            <NavLink to="explore_tags" :active="activeTab" :text="settings.tabNames.explore_tags" :icon="settings.tabIcons.explore_tags"/>
            <NavLink to="explore_ev" :active="activeTab" :text="settings.tabNames.explore_ev" :icon="settings.tabIcons.explore_ev"/>
            <NavLink v-if="hasMetaItems" :active="activeTab" to="explore_meta" :text="settings.tabNames.explore_meta" :icon="settings.tabIcons.explore_meta"/>
        </nav>

        <div ref="el">

            <div v-if="initialized && !isLoading" class="mb-2 pa-2">

                <div style="text-align: center;">
                    <ItemBarCodes :hidden="!showBarCodes"/>
                </div>

                <router-view/>

                <div class="d-flex justify-center">
                    <EmbeddingExplorer :hidden="!showScatter" :width="Math.max(300,width*0.8)"/>
                </div>

                <v-sheet class="mt-2 pa-2">
                    <RawDataView
                        :hidden="!showTable"
                        selectable
                        :allow-add="allowEdit"
                        check-assigned/>
                </v-sheet>

                <div style="text-align: center;">
                    <ItemEvidenceTiles :hidden="!showEvidenceTiles" :code="currentCode"/>
                </div>

                <div style="text-align: center;">
                    <MetaItemsList :hidden="!showExtTiles" show-bar-codes/>
                </div>
            </div>
        </div>
    </section>
</template>

<script setup>

    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { onMounted, ref, watch } from 'vue'
    import GlobalShortcuts from '@/components/GlobalShortcuts.vue';
    import ItemEvidenceTiles from '@/components/evidence/ItemEvidenceTiles.vue';
    import RawDataView from '@/components/RawDataView.vue';
    import MetaItemsList from '@/components/meta_items/MetaItemsList.vue';

    import { useSettings } from '@/store/settings';
    import ItemBarCodes from '@/components/items/ItemBarCodes.vue';
    import EmbeddingExplorer from '@/components/EmbeddingExplorer.vue';
    import { useElementSize, useWindowSize } from '@vueuse/core';
    import ActionContextMenu from '@/components/dialogs/ActionContextMenu.vue';
    import Cookies from 'js-cookie';
    import { useTimes } from '@/store/times';
    import { loadCodesByDataset, loadCodeTransitionsByDataset } from '@/use/data-api';
    import DM from '@/use/data-manager';
    import { useRoute, useRouter } from 'vue-router';
    import { useTooltip } from '@/store/tooltip';
    import NavLink from '@/components/navigation/NavLink.vue';

    const settings = useSettings();
    const app = useApp()
    const times = useTimes()
    const route = useRoute()
    const tt = useTooltip()

    const {
        ds,
        hasMetaItems,
        allowEdit,
        activeUserId,
        currentCode,
        initialized,
    } = storeToRefs(app);

    const {
        askUserIdentity,
        isLoading,
        activeTab,
        showNavTop,
        showBarCodes,
        showScatter,
        showTable,
        showEvidenceTiles,
        showExtTiles,
        barCodeNodeSize
    } = storeToRefs(settings)

    const el = ref(null)
    const { width } = useElementSize(el)
    const wSize = useWindowSize()

    const router = useRouter()

    const numLeafTags = ref(0)
    const nodeSize = computed(() => {
        if (numLeafTags.value === 0) {
            return 3
        }

        const pref = Math.min(25, wSize.width.value * 0.75 / numLeafTags.value)
        if (pref >= 5) return pref

        if (wSize.width.value < 1000) {
            return 3
        } else if (wSize.width.value < 1250) {
            return 4
        } else if (wSize.width.value < 1750) {
            return 5
        } else {
            return 6
        }
    })

    function checkReload() {
        window.scrollTo(0, 0)
        tt.hide()
        switch (activeTab.value) {
            case "coding":
                showBarCodes.value = true;
                showScatter.value = false;
                showEvidenceTiles.value = false;
                showTable.value = true;
                showExtTiles.value = false;
                break;
            case "transition":
                showBarCodes.value = false;
                showScatter.value = false;
                showEvidenceTiles.value = false;
                showTable.value = true;
                showExtTiles.value = false;
                break;
            case "explore_tags":
                showBarCodes.value = false;
                showScatter.value = false;
                showTable.value = false;
                showEvidenceTiles.value = false;
                showExtTiles.value = false;
                break;
            case "explore_meta":
                if (ds.value && !hasMetaItems.value) {
                    return router.push("/coding")
                }
                showBarCodes.value = false;
                showScatter.value = true;
                showTable.value = false;
                showEvidenceTiles.value = false;
                showExtTiles.value = true;
                break;
            default:
                showBarCodes.value = false;
                showScatter.value = false;
                showEvidenceTiles.value = false;
                showTable.value = false;
                showExtTiles.value = false;
                break;
        }
    }

    async function loadCodes() {
        if (!ds.value) return;
        try {
            const data = await loadCodesByDataset(ds.value)
            DM.setData("codes", data);
            app.setCodes(data)
        } catch {
            toast.error("error loading codes for dataset")
        }
    }
    async function loadCodeTransitions() {
        if (!ds.value) return;
        try {
            const result = await loadCodeTransitionsByDataset(ds.value);
            result.forEach(d => d.name = `${app.getCodeName(d.old_code)} to ${app.getCodeName(d.new_code)}`)
            result.sort((a, b) => a.id - b.id)
            DM.setData("code_transitions", result);
            app.setTransitions(result);

        } catch {
            toast.error("error loading code transitions")
        }
    }

    function readQuery() {
        if (route.query.dsid) {
            const id = Number.parseInt(route.query.dsid)
            const dataset = app.datasets.find(d => d.id === id)
            if (dataset) {
                app.setDataset(id)
            }
        } else if (route.query.dsname) {
            const n = route.query.dsname
            const dataset = app.datasets.find(d => d.name === n)
            if (dataset) {
                app.setDataset(dataset.id)
            }
        }

        if (route.query.codeid) {
            const id = Number.parseInt(route.query.codeid)
            const code = app.codes.find(d => d.id === id)
            if (code) {
                app.setActiveCode(id)
            }
        } else if (route.query.codename) {
            const n = route.query.codename
            const code = app.codes.find(d => d.name === n)
            if (code) {
                app.setActiveCode(code.id)
            }
        }
    }

    function checkDataset() {
        if (!askUserIdentity.value && app.datasets.length > 0) {
            readQuery()
            if (ds.value === null) {
                const dataset = +Cookies.get("dataset_id")
                if (dataset && app.datasets.find(d => d.id == dataset)) {
                    app.setDataset(dataset)
                } else {
                    app.setDataset(app.datasets[0].id)
                }
            }
        }
    }

    onMounted(() => {
        if (route.path.length <= 1) {
            if (route.query.tab && settings.tabNames[route.query.tab]) {
                router.push(route.query.tab)
            } else {
                const startPage = Cookies.get("start-page")
                if (startPage) {
                    router.push(startPage)
                }
            }
        } else {
            activeTab.value = route.path.slice(1)
        }
        checkDataset()
        checkReload()
        barCodeNodeSize.value = nodeSize.value
    })

    watch(ds, async function() {
        DM.clear()

        // load codes
        await loadCodes();
        const prevCode = +Cookies.get("code_id")
        // set code as previously stored or last one in the list
        if (prevCode && app.codes.some(d => d.id === prevCode)) {
            app.setActiveCode(prevCode)
        } else {
            app.setActiveCode(app.codes.at(-1).id);
        }

        // load transitions
        await loadCodeTransitions()
        const prevTrans = +Cookies.get("trans_id")
        // set transition as previously stored or last one in the list
        if (app.transitions.length > 0) {
            if (prevTrans && app.transitions.some(d => d.id === prevTrans)) {
                app.setActiveTransition(prevTrans)
            } else {
                app.setActiveTransition(app.transitions.at(-1).id);
            }
        } else {
            app.setActiveTransition(null)
        }
        checkReload()
        // overwrite cookies
        Cookies.set("dataset_id", ds.value, { expires: 365 })
        times.needsReload("all");
    });

    watch(() => times.datasets, checkDataset)

    // only watch for reloads when data is not served statically
    if (!app.static) {
        watch(activeUserId, async (now, prev) => {
            askUserIdentity.value = now === null;
            if (prev === null && now !== null) {
                if (ds.value === null || app.currentCode === null) {
                    times.needsReload("datasets")
                } else {
                    times.needsReload("all")
                }
            } else {
                app.updateItems()
            }
        });
    }

    watch(() => times.tags, () => {
        numLeafTags.value = DM.getSizeBy("tags", d => d.is_leaf === 1)
    })
    watch(nodeSize, () => barCodeNodeSize.value = nodeSize.value)

    watch(() => route.path, function() {
        const tab = route.path.slice(1)
        if (tab) {
            activeTab.value = tab
            checkReload()
        }
    })


</script>