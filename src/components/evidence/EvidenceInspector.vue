<template>
    <div class="mt-2 mb-2">
        <div class="d-flex align-start">
            <div class="d-flex flex-column mr-2" style="width: 350px;">
                <v-switch v-model="onlySelected"
                    label="only selected"
                    class="ml-3 mt-2"
                    hide-details
                    hide-spin-buttons
                    color="primary"
                    density="compact"
                    @update:model-value="readGames"/>
                <v-switch v-model="onlyWithEvidence"
                    label="only with evidence"
                    class="ml-3 mt-1"
                    hide-details
                    hide-spin-buttons
                    color="primary"
                    density="compact"
                    @update:model-value="readGames"/>
                <v-combobox v-model="filterGames"
                    :items="gameNames"
                    class="mt-2"
                    density="compact"
                    clearable
                    hide-details
                    hide-no-data
                    hide-spin-buttons
                    @update:model-value="readGames"
                    label="filter by name .."/>
                <v-text-field v-model="search"
                    class="mt-2"
                    density="compact"
                    clearable
                    hide-details
                    hide-no-data
                    hide-spin-buttons
                    append-icon="mdi-magnify"
                    @click:append="readGames"
                    @click:clear="readGames"
                    label="search evidence ..."
                    />

                <v-list v-model:selected="data.selected"
                    return-object
                    class="mr-2 mt-2"
                    style="width: 100%;"
                    max-height="500"
                    @update:selected="data.selectedEvidence = null"
                    density="compact">

                    <v-list-item v-for="item in data.games" :value="item">
                        <v-list-item-title>
                            <v-chip density="compact" color="primary" class="mb-1 mr-1 ">{{ item.numEvidence }}</v-chip>
                            {{ item.name }}
                        </v-list-item-title>
                    </v-list-item>
                </v-list>
            </div>
            <v-card v-if="data.selected.length > 0" class="pa-2"  style="flex-grow: 1; text-align: center; min-height: 200px;">

                <v-btn class="ms-auto ma-2 mb-4"
                    @click="addDialog = true"
                    color="secondary"
                    rounded="sm"
                    density="comfortable"
                    block>
                    add new evidence
                </v-btn>

                <v-row>
                    <v-col v-for="d in selectionEvidence" :key="d.id" class="d-flex child-flex ml-1" cols="1">
                        <v-img :src="d.filepath ? ('evidence/'+d.filepath) : imgUrlS"
                            class="bg-grey-lighten-2 cursor-pointer"
                            v-ripple.center cover
                            rounded="sm"
                            aspect-ratio="1"
                            @click="select(d)">
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
                        <div class="d-flex justify-space-between">
                            <span>code</span>
                            <span>{{ app.getCodeName(app.currentCode) }}</span>
                        </div>
                        <v-btn rounded="sm" density="comfortable" :icon="data.selectedEvidence.edit ? 'mdi-check' : 'mdi-pencil'" variant="text" @click="toggleEdit(data.selectedEvidence)"/>
                        <v-btn rounded="sm" density="comfortable" icon="mdi-delete" variant="text" color="error" @click="deleteEvidence(data.selectedEvidence.id)"/>
                    </div>

                    <div class="d-flex justify-space-between align-start">
                        <div style="width: 48%" class="mr-2">
                            <v-select v-model="data.selectedEvidence.tag_id"
                                :disabled="!data.selectedEvidence.edit"
                                @update:model-value="data.selectedEvidence.changes = true"
                                class="mb-2"
                                density="compact"
                                label="Associated tag"
                                :items="data.tags"
                                item-title="name"
                                item-value="id"
                                hide-details
                                hide-spin-buttons/>


                            <v-card title="Evidence Description" min-height="300">
                                <v-card-text>
                                    <v-textarea v-if="data.selectedEvidence.edit"
                                        v-model="data.selectedEvidence.description"
                                        @update:model-value="data.selectedEvidence.changes = true"
                                        density="compact"
                                        class="mr-4"
                                        hide-details
                                        hide-spin-buttons
                                        style="width: 100%;"/>
                                    <span v-else>{{ data.selectedEvidence.description }}</span>
                                </v-card-text>
                            </v-card>
                        </div>

                        <div style="width: 50%">
                        <v-file-input v-model="editFile"
                            accept="image/*"
                            label="Upload a new image"
                            density="compact"
                            class="mt-2"
                            style="width: 100%"
                            hide-details
                            hide-spin-buttons
                            :disabled="!data.selectedEvidence.edit"
                            @update:model-value="readEditFile"/>

                            <div v-if="!editImagePreview && data.selectedEvidence.filepath">
                                <v-hover>
                                    <template v-slot:default="{ isHovering, props }">
                                        <v-img v-bind="props"
                                            class="pa-1 cursor-pointer"
                                            :src="'evidence/'+data.selectedEvidence.filepath"
                                            @click="enlarge('evidence/'+data.selectedEvidence.filepath)"
                                            v-ripple.center
                                            min-width="50%"
                                            max-width="100%">
                                            <v-overlay :model-value="isHovering" contained class="d-flex align-center justify-center" opacity="0.4">
                                                <v-icon size="64" color="grey-lighten-1">mdi-magnify-plus-outline</v-icon>
                                            </v-overlay>
                                        </v-img>
                                    </template>
                                </v-hover>
                            </div>
                            <div v-else>
                                <v-img class="pa-1"
                                    :src="editImagePreview"
                                    :lazy-src="imgUrl"
                                    height="300"/>
                            </div>
                        </div>
                    </div>
                </div>
            </v-card>
        </div>

        <v-dialog v-model="addDialog" width="auto" min-width="1000">
            <v-card title="Add new evidence">
                <v-card-text class="d-flex">
                    <v-sheet min-width="400" class="mr-1 ml-1">
                        <v-text-field :model-value="data.selected[0].name"
                            readonly
                            disabled
                            density="compact"
                            label="Game title"
                            hide-details
                            hide-spin-buttons/>
                        <v-select v-model="tagId"
                            class="mt-2"
                            density="compact"
                            label="Associated tag"
                            :items="data.tags"
                            item-title="name"
                            item-value="id"
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
                    </v-sheet>
                    <v-img class="pa-1 ml-2"
                        :src="imagePreview"
                        cover
                        :lazy-src="imgUrl"
                        alt="Image Preview"
                        height="300"/>
                </v-card-text>
                <v-card-actions>
                    <v-btn class="ms-auto" @click="closeAddDialog">cancel</v-btn>
                    <v-btn class="ms-2" @click="saveEvidence">submit</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <v-overlay v-model="showEnlargedImage" opacity="0.8">
            <div style="width: 100vw; position: relative;">
                <v-btn icon="mdi-close"
                    variant="text" size="x-large"
                    rounded="sm" color="grey-lighten-1"
                    density="compact"
                    class="mr-1 mt-1"
                    style="position: absolute; right: 1em; top: 0.25em;"
                @click="closeEnlarge"/>
            </div>
            <div style="width: 100vw; text-align: center;">
                <img class="pa-3"
                :src="enlargeImage"
                style="max-width: 100%;"
                alt="Image Preview"/>
            </div>
        </v-overlay>
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

    import imgUrl from '@/assets/__placeholder__.png'
    import imgUrlS from '@/assets/__placeholder__s.png'

    const app = useApp()
    const loader = useLoader()
    const toast = useToast();

    const onlySelected = ref(false)
    const onlyWithEvidence = ref(false)
    const filterGames = ref("")
    const search = ref("")

    const editfile = ref(null)
    const editImagePreview = ref("")

    const file = ref(null)
    const newDesc = ref("")
    const imagePreview = ref("")
    const addDialog = ref(false);
    const tagId = ref(null)

    const showEnlargedImage = ref(false)
    const enlargeImage = ref("");

    const selectionEvidence = computed(() => {
        if (!data.selected || data.evidence.size === 0) {
            return null;
        }
        return data.evidence.get(data.selected[0].id)
    })
    const gameNames = computed(() => data.games.map(d => d.name));
    const data = reactive({
        games: [],
        tags: [],
        selected: [],
        selectedEvidence: null,
        evidence: new Map(),
    });

    function select(d) {
        data.selectedEvidence = d;
        editFile.value = null;
        editImagePreview.value = "";
    }
    function resetSelection() {
        data.selectedEvidence = null;
    }

    function readAll() {
        readGames();
        readTags();
        readEvidence();
    }

    function readGames() {
        const special = /(\(\)\{\}\-\_\.\:)/g
        const regex1 = filterGames.value ? new RegExp(filterGames.value.replaceAll(special, "\$1"), "i") : null;
        const regex2 = search.value ? new RegExp(search.value.replaceAll(special, "\$1"), "i") : null;

        const gameIds = new Set(DM.getFilter("games", "id"));
        const games = DM.getDataBy("games", d => {
            return (!onlySelected.value || gameIds.has(d.id)) &&
                (!onlyWithEvidence.value || d.numEvidence > 0) &&
                (!filterGames.value || d.name.match(regex1) !== null) &&
                (!search.value || (data.evidence.has(d.id) && data.evidence.get(d.id).some(e => {
                    const t = e.tag_id ? data.tags.find(t => t.id === e.tag_id) : null;
                    return e.description.match(regex2) !== null || t && t.name.match(regex2) !== null
                })))
        })
        data.games = games
    }

    function readEvidence() {
        const ev = DM.getDataBy("evidence", d => app.showAllUsers || d.created_by === app.activeUserId);
        data.evidence = d3.group(ev, d => d.game_id)
    }

    function readTags() {
        data.tags = DM.getData("tags", false);
    }

    function readEditFile() {
        if (!editFile.value) {
            editImagePreview.value = "";
            return;
        }

        const reader = new FileReader();
        reader.addEventListener('load', () => editImagePreview.value = reader.result);
        reader.readAsDataURL(editFile.value);
        data.selectedEvidence.changes = true;
    }
    function readFile() {
        if (!file.value) {
            imagePreview.value = "";
            return;
        }

        const reader = new FileReader();
        reader.addEventListener('load', () => imagePreview.value = reader.result);
        reader.readAsDataURL(file.value);
    }

    function closeAddDialog() {
        addDialog.value = false;
        file.value = null
        newDesc.value = "";
        imagePreview.value = "";
    }

    async function saveEvidence() {
        if (data.selected.length > 0 && newDesc.value.length > 0) {

            const name = uuidv4();
            if (file.value) {
                await loader.postImage(`image/evidence/${name}`, file.value);
            }

            await loader.post("add/evidence", { rows: [{
                game_id: data.selected[0].id,
                code_id: app.currentCode,
                tag_id: tagId.value ? tagId.value : null,
                description: newDesc.value,
                created: Date.now(),
                created_by: app.activeUserId,
                filename: imagePreview.value ? name : null,
            }] })
            tagId.value = null;
            toast.success("added new evidence")
            app.needsReload("evidence");
            closeAddDialog();
        } else {
            toast.error("need description to add new evidence")
        }
    }

    async function deleteEvidence(id) {
        loader.post("delete/evidence", { ids: [id] })
            .then(() => {
                data.selectedEvidence = null;
                app.needsReload("evidence");
                toast.success("deleted evidence");
            })
    }

    async function toggleEdit(d) {
        if (d.edit && d.changes) {
            d.changes = false;
            const obj = { id: d.id, description: d.description, filepath: d.filepath, tag_id: d.tag_id }

            if (editFile.value) {
                const filename = uuidv4();
                await loader.postImage(`image/evidence/${filename}`, editFile.value);
                obj.filename = filename
            }

            await loader.post("update/evidence", { rows: [obj] })
            app.needsReload("evidence")
            toast.success("updated evidence");
            editFile.value = null;
            editImagePreview.value = "";
        }
        d.edit = !d.edit;
    }

    function enlarge(img) {
        if (img) {
            enlargeImage.value = img;
            showEnlargedImage.value = true;
        }
    }
    function closeEnlarge() {
        showEnlargedImage.value = false;
        enlargeImage.value = "";
    }

    watch(() => app.selectionTime, readGames);
    watch(() => app.userTime, function() {
        resetSelection();
        readGames();
        readTags();
        readEvidence();
    });
    watch(() => ([app.dataLoading.tags, app.dataLoading.games, app.dataLoading.evidence]), function(now) {
        if (now.some(d => d === false)) { readAll(); }
    }, { deep: true });

    onMounted(readAll)
</script>