<template>
    <div class="d-flex pa-2">
        <aside style="max-width: 300px;">
            <v-select v-model="ds"
                class="mb-2"
                density="compact"
                hide-details
                :items="datasets"
                item-title="name" item-value="id"/>


            <v-card v-if="code" class="pa-3 mb-2 text-caption">
                <v-select v-model="activeCode"
                    class="mb-2"
                    density="compact"
                    hide-details
                    :items="codes"
                    item-title="name" item-value="id"/>
                {{ code.description }}

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
            </v-card>

        </aside>
        <IdentitySelector v-model="askUserIdentity" @select="app.setActiveUser"/>
        <div v-if="initialized" class="d-flex flex-column pa-2">
            <RawDataView :data="allData" :headers="headers" selectable/>
            <TagOverview/>
        </div>
    </div>
</template>

<script setup>
    import FilterPanel from '@/components/FilterPanel.vue';
    import TagOverview from '@/components/TagOverview.vue';
    import CodesView from '@/components/CodesView.vue';
    import IdentitySelector from '@/components/IdentitySelector.vue';
    import RawDataView from '@/components/RawDataView.vue';
    import SteamView from '@/components/SteamView.vue';

    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { computed, onMounted } from 'vue'
    import DM from '@/use/data-manager'

    const loader = useLoader()
    const app = useApp()
    const { ds, datasets, activeUserId, activeCode, code, codes, initialized } = storeToRefs(app);

    const askUserIdentity = ref(false);
    const allData = computed(() => {
        const tmp = DM.getData("raw", false);
        const t = DM.getData("tags");
        DM.getData("data_tags").forEach(d => {
            const g = tmp.find(dd => dd.id === d.game_id);
            if (g) {
                const tag = t.find(tt => tt.id === d.tag_id).name
                if (g.tags) {
                    g.tags.push(tag);
                } else {
                    g.tags = [tag];
                }
            }
        })
        return tmp;
    })

    const headers = [
        // { title: "ID", key: "id", type: "id" },
        { title: "Title", key: "title", type: "string" },
        { title: "Year", key: "year", type: "integer" },
        { title: "Played", key: "played", type: "boolean" },
        { title: "Tags", key: "tags", type: "array" },
        { title: "URL", key: "url", type: "url" },
    ];

    async function loadData() {
        return Promise.all([
            loader.get(`${ds.value}/data`).then(data => DM.setData("raw", data)),
            loader.get(`${ds.value}/tags`).then(data => DM.setData("tags", data)),
            loader.get(`${ds.value}/data_tags`).then(data => DM.setData("data_tags", data)),
        ]).then(async () => {
            return loader.get(`${ds.value}/codes`).then(data => {
                DM.setData("codes", data);
                app.setActiveCode(data[0].id);
            })
        });
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
