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
                        <v-card size="small"
                            density="comfortable"
                            elevation="0"
                            rounded="circle"
                            class="pa-1 mr-4 d-flex"
                            :color="getUseColor(user.id, user.color)">
                            <v-icon color="white">mdi-account</v-icon>
                        </v-card>
                    </template>
                </v-list-item>
            </v-list>
        </aside>
        <IdentitySelector v-model="askUserIdentity" @select="app.setActiveUser"/>
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
    import IdentitySelector from '@/components/IdentitySelector.vue';

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { onMounted } from 'vue'
    import DM from '@/use/data-manager'

    const loader = useLoader()
    const app = useApp()
    const { ds, datasets, activeUserId, initialized } = storeToRefs(app);

    const askUserIdentity = ref(false);

    async function loadData() {
        return Promise.all([
            loader.get(`${ds.value}/data`).then(data => DM.setData("raw", data)),
            loader.get(`${ds.value}/codes`).then(data => DM.setData("codes", data)),
            loader.get(`${ds.value}/tags`).then(data => DM.setData("tags", data)),
            loader.get(`${ds.value}/data_tags`).then(data => DM.setData("data_tags", data)),
        ])
    }

    async function init() {
        if (!initialized.value) {
            await loader.get("datasets").then(list => app.setDatasets(list))
            loader.get(`${ds.value}/users`).then(list => {
                app.setUsers(list);
                askUserIdentity.value = true;
            });

            await loadData();
            initialized.value = true;
        }
    }

    function getUseColor(id, color) {
        return activeUserId.value !== null ?
            (activeUserId.value === id ? color : color + "66") :
            color
    }

    onMounted(init);

    watch(activeUserId, () => askUserIdentity.value = activeUserId.value === null)
</script>
