<template>
    <div class="d-flex pa-2">
        <aside style="max-width: 300px;">
            <v-select v-model="ds"
                density="compact"
                hide-details
                :items="datasets" item-title="name" item-value="id"/>

            <v-list v-if="ds">
                <v-list-item v-for="user in app.users"
                    :key="user.id"
                    :title="user.name"
                    :subtitle="user.role"
                    density="compact"
                    hide-details>

                    <template v-slot:prepend>
                        <v-icon :color="user.color">mdi-circle</v-icon>
                    </template>
                </v-list-item>
            </v-list>
        </aside>
        <div v-if="initialized" class="d-flex flex-column pa-2">
            <TaxonomyOverview/>
            <FilterPanel/>
            <CodesView/>
        </div>
    </div>
</template>

<script setup>
    import FilterPanel from '@/components/FilterPanel.vue';
    import TaxonomyOverview from '@/components/TaxonomyOverview.vue';
    import CodesView from '@/components/CodesView.vue';

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { onMounted } from 'vue'
    import DM from '@/use/data-manager'

    const loader = useLoader()
    const app = useApp()
    const { ds, datasets } = storeToRefs(app);

    const initialized = ref(false);

    async function loadData() {
        return Promise.all([
            loader.get(`${ds.value}/data`).then(data => DM.setData("raw", data)),
            loader.get(`${ds.value}/codes`).then(data => DM.setData("codes", data)),
            loader.get(`${ds.value}/tags`).then(data => DM.setData("tags", data)),
            loader.get(`${ds.value}/data_tags`).then(data => DM.setData("data_tags", data)),
        ])
    }

    async function init() {
        initialized.value = false;

        await loader.get("datasets").then(list => app.setDatasets(list))
        loader.get(`${ds.value}/users`).then(list => app.setUsers(list))

        await loadData();

        initialized.value = true;
    }

    onMounted(init);
</script>
