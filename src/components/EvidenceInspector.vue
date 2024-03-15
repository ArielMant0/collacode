<template>
    <div class="mt-4 mb-2">
        <h4>Evidence Inspector</h4>
        <div class="d-flex align-start">
            <div class="d-flex flex-column mr-2" style="width: 350px;">
                <v-switch v-model="onlySelected"
                    label="show selected games"
                    class="ml-3 mt-2"
                    hide-details
                    hide-spin-buttons
                    color="#078766"
                    density="compact"
                    @update:model-value="readEvidence"/>
                <v-switch v-model="onlyWithEvidence"
                    label="show games with evidence"
                    class="ml-3 mt-2"
                    hide-details
                    hide-spin-buttons
                    color="#078766"
                    density="compact"
                    @update:model-value="readEvidence"/>
                <v-list v-model:selected="data.selected"
                    return-object
                    class="mr-2"
                    style="width: 100%;"
                    @update:selected="data.selectedEvidence = null"
                    density="compact">

                    <v-list-item v-for="item in data.games" :value="item">
                        <v-list-item-title>
                            <v-chip density="compact" color="#078766" class="mb-1 mr-1 ">{{ item.numEvidence }}</v-chip>
                            {{ item.name }}
                        </v-list-item-title>
                    </v-list-item>
                </v-list>
            </div>
            <v-card v-if="data.selected.length > 0" class="pa-2"  style="flex-grow: 1; text-align: center; min-height: 200px;">

                <v-btn class="ms-auto ma-1 mb-4"
                    @click="addDialog = true"
                    color="success"
                    icon="mdi-plus"
                    rounded="sm"
                    density="comfortable"
                    block/>

                <v-row>
                    <v-col v-for="d in selectionEvidence" :key="d.id" class="d-flex child-flex" cols="1">
                        <v-img :src="'/image_evidence/'+d.filepath"
                            class="bg-grey-lighten-2 cursor-pointer"
                            v-ripple.center cover
                            aspect-ratio="1"
                            @click="data.selectedEvidence = d">
                            <template v-slot:placeholder>
                                <v-row align="center" class="fill-height ma-0" justify="center">
                                    <v-progress-circular color="grey-lighten-5" indeterminate></v-progress-circular>
                                </v-row>
                            </template>
                        </v-img>
                    </v-col>
                </v-row>

                <div v-if="data.selectedEvidence" class="pa-3">

                    <div style="width: 100%" class="mb-2">
                        <div class="d-flex justify-space-between">
                            <span>created by</span>
                            <span>{{ app.getUserName(data.selectedEvidence.created_by) }}</span>
                        </div>
                        <div class="d-flex justify-space-between">
                            <span>created on</span>
                            <span>{{ new Date(data.selectedEvidence.created).toLocaleDateString('de-DE') }}</span>
                        </div>
                        <v-btn rounded="sm" :icon="data.selectedEvidence.edit ? 'mdi-check' : 'mdi-pencil'" variant="text" @click="toggleEdit(data.selectedEvidence)"/>
                        <v-btn rounded="sm" icon="mdi-delete" variant="text" color="error" @click="deleteEvidence(data.selectedEvidence.id)"/>
                    </div>

                    <div class="d-flex">
                        <v-textarea v-model="data.selectedEvidence.description"
                            :readonly="!data.selectedEvidence.edit"
                            @update:model-value="data.selectedEvidence.changes = true"
                            density="compact"
                            class="mr-2"
                            label="Evidence description"
                            hide-details
                            hide-spin-buttons
                            auto-grow
                            style="width: 100%;"/>

                        <v-img class="pa-1" :src="'/image_evidence/'+data.selectedEvidence.filepath" min-width="50%" max-width="100%"/>
                    </div>

                </div>
            </v-card>
        </div>

        <v-dialog v-model="addDialog" width="auto" min-width="800">
            <v-card title="Add new evidence">
                <v-card-text class="d-flex">
                    <div style="width: 50%;" class="mr-1 ml-1">
                        <v-text-field :model-value="data.selected[0].name"
                            readonly
                            disabled
                            density="compact"
                            label="Game title"
                            hide-details
                            hide-spin-buttons/>
                        <v-textarea v-model="newDesc"
                            class="mt-2"
                            density="compact"
                            label="Evidence description"
                            hide-details
                            hide-spin-buttons/>
                        <v-file-input v-model="file"
                            accept="image/*"
                            label="Upload a matching image"
                            density="compact"
                            class="mt-2"
                            hide-details
                            hide-spin-buttons
                            @update:model-value="readFile"/>
                    </div>
                    <div style="width: 50%; text-align: center;" class="mr-1 ml-1">
                        <img class="pa-1" :src="imagePreview" width="300px" alt="Image Preview"/>
                    </div>
                </v-card-text>
                <v-card-actions>
                    <v-btn class="ms-auto" @click="closeAddDialog">cancel</v-btn>
                    <v-btn class="ms-2" @click="saveEvidence">submit</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup>
    import * as d3 from 'd3'
    import { computed, onMounted, reactive, ref, watch } from 'vue'
    import { useApp } from '@/store/app'
    import { useLoader } from '@/use/loader';
    import { useToast } from "vue-toastification";
    import { v4 as uuidv4 } from 'uuid';
    import DM from '@/use/data-manager'

    const app = useApp()
    const loader = useLoader()
    const toast = useToast();

    const onlySelected = ref(true)
    const onlyWithEvidence = ref(false)
    const file = ref([])
    const newDesc = ref("")
    const imagePreview = ref("")
    const addDialog = ref(false);

    const selectionEvidence = computed(() => {
        console.log(data.selected)
        if (!data.selected || data.evidence.size === 0) {
            return null;
        }
        return data.evidence.get(data.selected[0].id)
    })
    const data = reactive({
        games: [],
        selected: [],
        selectedEvidence: null,
        evidence: new Map(),
    });

    function readEvidence() {
        const gameIds = new Set(DM.getFilter("games", "id"));
        const games = DM.getDataBy("games", d => {
            return (!onlySelected.value || gameIds.has(d.id)) &&
                (!onlyWithEvidence.value || d.numEvidence > 0)
        })
        const ev = DM.getDataBy("evidence", d => app.showAllUsers || d.created_by === app.activeUserId);
        data.evidence = d3.group(ev, d => d.game_id)
        data.games = games
    }

    function readFile() {
        if (file.value.length === 0) {
            imagePreview.value = "";
            return;
        }

        const reader = new FileReader();
        reader.addEventListener('load', () => imagePreview.value = reader.result);
        reader.readAsDataURL(file.value[0]);
    }

    function closeAddDialog() {
        addDialog.value = false;
        file.value = []
        newDesc.value = "";
        imagePreview.value = "";
    }

    async function saveEvidence() {
        if (data.selected.length > 0 && newDesc.value.length > 0 && imagePreview.value) {

            const name = uuidv4();
            await loader.postImage(`image/image_evidence/${name}`, file.value[0]);

            loader.post("add/game/image_evidence", {
                game_id: data.selected[0].id,
                user_id: app.activeUserId,
                created: Date.now(),
                description: newDesc.value,
                name: name,
            }).then(() => app.needsReload())
            closeAddDialog();
        }
    }

    async function deleteEvidence(id) {
        loader.post("delete/image_evidence", { ids: [id] })
            .then(() => {
                data.selectedEvidence = null;
                app.needsReload();
                toast.success("deleted evidence");
            })
    }

    function toggleEdit(d) {
        if (d.edit && d.changes) {
            d.changes = false;
            loader.post("update/image_evidence", { rows: [{ id: d.id, description: d.description }] })
                .then(() => {
                    app.needsReload()
                    toast.success("updated evidence");
                })
        }
        d.edit = !d.edit;
    }

    watch(() => app.selectionTime, readEvidence);
    watch(() => app.userTime, readEvidence);
    watch(() => app.dataReloaded, readEvidence);

    onMounted(readEvidence)
</script>