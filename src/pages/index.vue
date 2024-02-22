<template>
    <div class="d-flex pa-2">
        <aside style="max-width: 300px;">
            <v-select v-model="ds"
                density="compact"
                hide-details
                :items="datasets" item-title="name" item-value="id"/>

            <v-list v-if="ds">
                <v-list-item v-for="user in app.users"
                    :key="user.name"
                    :title="user.name"
                    density="compact"
                    hide-details>

                    <template v-slot:prepend>
                        <v-icon :color="user.color">mdi-circle</v-icon>
                    </template>
                </v-list-item>
            </v-list>
        </aside>
        <div class="d-flex flex-column pa-2">
            <TaxonomyOverview/>
            <FilterPanel/>
        </div>
    </div>
</template>

<script setup>
    import FilterPanel from '@/components/FilterPanel.vue';
    import TaxonomyOverview from '@/components/TaxonomyOverview.vue';
    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia';
    import { onMounted } from 'vue'

    const loader = useLoader()
    const app = useApp()
    const { ds, datasets } = storeToRefs(app);

    function init() {
        loader.get("datasets").then(list => app.setDatasets(list))
    }

    onMounted(init);
</script>
