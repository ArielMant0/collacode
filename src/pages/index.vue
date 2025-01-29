<template>
    <main>
        <ActionContextMenu/>
        <GlobalShortcuts/>

        <v-tabs v-model="activeTab"
            class="main-tabs"
            color="secondary"
            bg-color="surface-variant"
            align-tabs="center"
            density="compact"
            @update:model-value="checkReload"
            >
            <v-tab value="coding">{{ settings.getTabName("coding") }}</v-tab>
            <v-tab value="agree">{{ settings.getTabName("agree") }}</v-tab>
            <v-tab value="transition">{{ settings.getTabName("transition") }}</v-tab>
            <v-divider vertical thickness="2" color="primary" class="ml-1 mr-1" opacity="1"></v-divider>
            <v-tab value="explore_tags">{{ settings.getTabName("explore_tags") }}</v-tab>
            <v-tab value="explore_ev">{{ settings.getTabName("explore_ev") }}</v-tab>
            <v-tab value="explore_meta">{{ settings.getTabName("explore_meta") }}</v-tab>
        </v-tabs>

        <div ref="el" style="width: 100%;">

            <MiniNavBar :hidden="expandNavDrawer"/>

            <div v-if="initialized && !isLoading" class="mb-2 pa-2" style="margin-left: 70px;">

                <div style="text-align: center;">
                    <ItemBarCodes :hidden="!showBarCodes"/>
                </div>

                <div class="d-flex justify-center">
                    <EmbeddingExplorer :hidden="!showScatter" :width="Math.max(400,width*0.85)"/>
                </div>

                <v-tabs-window v-model="activeTab">

                    <v-tabs-window-item value="transition">
                        <TransitionView v-if="activeUserId !== null" :loading="isLoading"/>
                    </v-tabs-window-item>

                    <v-tabs-window-item value="agree">
                        <AgreementView v-if="activeUserId !== null" :loading="isLoading"/>
                    </v-tabs-window-item>

                    <v-tabs-window-item value="explore_meta">
                        <ExploreExtView v-if="activeUserId !== null" :loading="isLoading"/>
                    </v-tabs-window-item>

                    <v-tabs-window-item value="explore_tags">
                        <ExploreTagsView v-if="activeUserId !== null" :loading="isLoading"/>
                    </v-tabs-window-item>

                    <v-tabs-window-item value="explore_ev">
                        <ExploreEvidenceView v-if="activeUserId !== null" :loading="isLoading"/>
                    </v-tabs-window-item>

                </v-tabs-window>

                <v-sheet class="mt-2 pa-2">
                    <RawDataView
                        :hidden="!showTable"
                        selectable
                        :allow-edit="allowEdit"
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
    </main>
</template>

<script setup>

    import { useApp } from '@/store/app'
    import TransitionView from '@/components/views/TransitionView.vue'
    import ExploreTagsView from '@/components/views/ExploreTagsView.vue';
    import { storeToRefs } from 'pinia'
    import { onMounted, ref, watch } from 'vue'
    import GlobalShortcuts from '@/components/GlobalShortcuts.vue';
    import ItemEvidenceTiles from '@/components/evidence/ItemEvidenceTiles.vue';
    import RawDataView from '@/components/RawDataView.vue';
    import MetaItemsList from '@/components/meta_items/MetaItemsList.vue';

    import { useSettings } from '@/store/settings';
    import MiniNavBar from '@/components/MiniNavBar.vue';
    import ItemBarCodes from '@/components/items/ItemBarCodes.vue';
    import EmbeddingExplorer from '@/components/EmbeddingExplorer.vue';
    import { useElementSize } from '@vueuse/core';
    import ExploreExtView from '@/components/views/ExploreExtView.vue';
    import ActionContextMenu from '@/components/dialogs/ActionContextMenu.vue';
    import AgreementView from '@/components/views/AgreementView.vue';
    import ExploreEvidenceView from '@/components/views/ExploreEvidenceView.vue';
    import Cookies from 'js-cookie';
    import { useTimes } from '@/store/times';
    import { loadCodesByDataset, loadCodeTransitionsByDataset } from '@/use/utility';
    import DM from '@/use/data-manager';

    const settings = useSettings();
    const app = useApp()
    const times = useTimes()

    const {
        ds,
        allowEdit,
        activeUserId,
        currentCode,
        initialized,
    } = storeToRefs(app);

    const {
        askUserIdentity,
        isLoading,
        expandNavDrawer,
        activeTab,
        showBarCodes,
        showScatter,
        showTable,
        showEvidenceTiles,
        showExtTiles
    } = storeToRefs(settings)

    const el = ref(null)
    const { width } = useElementSize(el)

    function checkReload() {
        window.scrollTo(0, 0)
        switch (activeTab.value) {
            case "coding":
                app.cancelCodeTransition();
                showBarCodes.value = false;
                showScatter.value = false;
                showEvidenceTiles.value = false;
                showTable.value = true;
                showExtTiles.value = false;
                break;
            case "transition":
                app.startCodeTransition();
                showBarCodes.value = false;
                showScatter.value = false;
                showEvidenceTiles.value = false;
                showTable.value = true;
                showExtTiles.value = false;
                loadOldTags();
                break;
            case "explore_tags":
                app.cancelCodeTransition();
                showBarCodes.value = false;
                showScatter.value = false;
                showTable.value = false;
                showEvidenceTiles.value = false;
                showExtTiles.value = false;
                break;
            case "explore_meta":
                app.cancelCodeTransition();
                showBarCodes.value = false;
                showScatter.value = true;
                showTable.value = false;
                showEvidenceTiles.value = false;
                showExtTiles.value = true;
                break;
            default:
                app.cancelCodeTransition();
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

    onMounted(() => {
        const startPage = Cookies.get("start-page")
        if (startPage) {
            settings.activeTab = startPage;
        }
        checkReload()
    })

    watch(ds, async function() {
        DM.clear()
        const prevDs = +Cookies.get("dataset_id")
        // load codes
        await loadCodes();
        const prevCode = +Cookies.get("code_id")
        // set code as previously stored or last one in the list
        if (prevDs && prevDs === ds.value && prevCode && app.codes.some(d => d.id === prevCode)) {
            app.setActiveCode(prevCode)
        } else {
            app.setActiveCode(app.codes.at(-1).id);
        }

        // load transitions
        await loadCodeTransitions()
        const prevTrans = +Cookies.get("trans_id")
        // set transition as previously stored or last one in the list
        if (app.transitions.length > 0) {
            if (prevDs === ds.value && prevTrans && app.transitions.some(d => d.id === prevTrans)) {
                app.setActiveTransition(prevTrans)
            } else {
                app.setActiveTransition(app.transitions.at(-1).id);
            }
        } else {
            app.setActiveTransition(null)
        }
        // overwrite cookies
        Cookies.set("dataset_id", ds.value, { expires: 365 })
        times.needsReload("all");
    });

    // only watch for reloads when data is not served statically
    if (!app.static) {
        watch(activeUserId, async (now, prev) => {
            askUserIdentity.value = now === null;
            console.log(now, prev, ds.value)
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


</script>

<style scoped>
.main-tabs {
    position: sticky;
    top: 0;
    left: 0;
    z-index: 1999;
    width: 100vw;
}
</style>