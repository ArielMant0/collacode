<template>
    <v-sheet class="pa-0">
        <div v-if="!loading" style="width: 100%;" class="pa-2">

            <div style="text-align: center;" class="mb-2">
                <v-btn
                    icon="mdi-land-plots"
                    class="mr-1"
                    variant="tonal"
                    density="compact"
                    rounded="sm"
                    @click="showSummary = !showSummary"
                    :color="showSummary ? 'primary' : 'default'">
                </v-btn>
                <v-btn
                    icon="mdi-chart-bar-stacked"
                    class="ml-1"
                    variant="tonal"
                    density="compact"
                    rounded="sm"
                    @click="showBars = !showBars"
                    :color="showBars ? 'primary' : 'default'">
                </v-btn>
            </div>

            <MetaItemsSummary/>

            <div v-if="showBars" class="mt-4">
                <MetaItemsDimsBars/>
            </div>
        </div>
    </v-sheet>
</template>

<script setup>
    import MetaItemsDimsBars from '../meta_items/MetaItemDimsBars.vue';
    import MetaItemsSummary from '../meta_items/MetaItemsSummary.vue';

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const showSummary = ref(true)
    const showBars = ref(false)

</script>