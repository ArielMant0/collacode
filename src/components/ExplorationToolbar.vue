<template>
    <v-sheet class="d-flex justify-center align-center mb-2">
        <v-btn-toggle v-model="treeLayout" color="primary" density="comfortable" rounded="sm" border divided mandatory variant="text" class="mr-4">
            <v-tooltip text="history bar codes" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" :disabled="!hasTransition" class="pl-4 pr-4" value="history" icon="mdi-barcode"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="cluster node-link layout with leaves on the same level" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="cluster" icon="mdi-family-tree"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="compact node-link layout" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="tidy" icon="mdi-file-tree"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="radial node-link layout" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="radial" icon="mdi-radar"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="compact treemap layout" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="treemap" icon="mdi-chart-tree"></v-btn>
                </template>
            </v-tooltip>
        </v-btn-toggle>

        <v-tooltip text="reset selection" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-4" icon="mdi-select" color="secondary" @click="resetSelection"></v-btn>
            </template>
        </v-tooltip>

        <v-tooltip text="show tag assignments" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props"
                    rounded="sm" density="comfortable"
                    :disabled="!hasTransition || (treeLayout != 'tidy' && treeLayout != 'cluster')"
                    :icon="tagAssign ? 'mdi-eye' : 'mdi-eye-off'"
                    :color="treeLayout != 'tidy' && treeLayout != 'cluster' ? 'default' : 'secondary'"
                    @click="tagAssign = !tagAssign"></v-btn>
            </template>
        </v-tooltip>
    </v-sheet>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import DM from '@/use/data-manager';
    import Cookies from 'js-cookie';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted } from 'vue';

    const app = useApp()
    const settings = useSettings()
    const { tagAssign, treeLayout } = storeToRefs(settings)

    const hasTransition = computed(() => app.transitionData !== null)

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    onMounted(function() {
        const tl = Cookies.get("tree-layout")
        if (tl) {
            if (app.transitions.length === 0 && tl === "history") {
                treeLayout.value = "cluster"
            } else {
                treeLayout.value = tl;
            }
        }
    })

    watch(treeLayout, function() {
        Cookies.set("tree-layout", treeLayout.value, { expires: 365 })
    })
    watch(() => app.transitions, function() {
        if (app.transitions.length === 0 && treeLayout.value === "history") {
            treeLayout.value = "cluster"
        }
    })

</script>