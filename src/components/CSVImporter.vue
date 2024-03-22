<template>
    <div v-if="datasets">
        <div class="d-flex mb-8 align-center">
            <v-switch v-model="addToExisting" label="add to existing dataset"
                color="primary" density="compact"
                class="mr-2"
                hide-details hide-spin-buttons/>
            <v-select v-if="addToExisting"
                :items="datasets"
                item-value="id" item-title="name"
                :model-value="app.ds"
                density="compact"
                class="mr-2"
                hide-details
                hide-no-data
                hide-spin-buttons
                hide-selected
                @update:model-value="app.setDataset"/>
            <div v-else class="d-flex" style="width: 90%;">
                <v-text-field v-model="newDSName"
                    label="Dataset Name"
                    density="compact"
                    class="mr-1"
                    hide-details
                    hide-spin-buttons/>
                <v-text-field v-model="newDSDesc"
                    label="Dataset Description"
                    density="compact"
                    class="mr-2"
                    hide-details
                    hide-spin-buttons/>
            </div>
            <v-btn :disabled="numSelected === 0" @click="submit" color="primary">add to database</v-btn>
        </div>

        <div>
            <v-checkbox v-model="upload.games" label="Upload Games" density="compact" class="mb-2" hide-details hide-spin-buttons/>
            <UploadTable :headers="headers" label="Data CSV File" @change="data => contents.games = data"/>
        </div>

        <div class="mb-4">
            <v-checkbox v-model="upload.users" label="Upload Users" density="compact" class="mb-2" hide-details hide-spin-buttons/>
            <UploadTable :headers="userHeaders" label="Users CSV File" @change="data => contents.users = data"/>
        </div>

        <div class="mb-4">
            <v-checkbox v-model="upload.codes" label="Upload Codes" density="compact" class="mb-2" hide-details hide-spin-buttons/>
            <UploadTable :headers="codeHeaders" label="Codes CSV File" @change="data => contents.codes = data"/>
        </div>

        <div class="mb-4">
            <v-checkbox v-model="upload.tags" label="Upload Tags" density="compact" class="mb-2" hide-details hide-spin-buttons/>
            <UploadTable :headers="tagHeaders" label="Tags CSV File" @change="data => contents.tags = data"/>
        </div>

        <div class="mb-4">
            <v-checkbox v-model="upload.datatags" label="Upload DataTags" density="compact" class="mb-2" hide-details hide-spin-buttons/>
            <UploadTable :headers="datatagHeaders" label="DataTags CSV File" @change="data => contents.datatags = data"/>
        </div>

        <div class="mb-4">
            <v-checkbox v-model="upload.evidence" label="Upload Evidence" density="compact" class="mb-2" hide-details hide-spin-buttons/>
            <UploadTable :headers="evidenceHeaders" label="Evidece CSV File" @change="data => contents.evidence = data"/>
        </div>

        <div class="mb-4">
            <v-checkbox v-model="upload.tagAssignments" label="Upload Tag Assignments" density="compact" class="mb-2" hide-details hide-spin-buttons/>
            <UploadTable :headers="tagAssigHeaders" label="Tag Assignments CSV File" @change="data => contents.tagAssignments = data"/>
        </div>

        <div class="mb-4">
            <v-checkbox v-model="upload.codeTransitions" label="Upload Code Transitions" density="compact" class="mb-2" hide-details hide-spin-buttons/>
            <UploadTable :headers="codeTransHeaders" label="Code Transitions CSV File" @change="data => contents.codeTransitions = data"/>
        </div>
    </div>
</template>

<script setup>
    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app';
    import { computed, onMounted, reactive, ref } from 'vue'
    import { storeToRefs } from 'pinia';
    import UploadTable from './UploadTable.vue';
    import { useToast } from 'vue-toastification';


    const app = useApp();
    const loader = useLoader();
    const toast = useToast();
    const { datasets } = storeToRefs(app)

    const addToExisting = ref(true);
    const newDSName = ref("");
    const newDSDesc= ref("");

    const contents = reactive({
        games: [],
        users: [],
        codes: [],
        tags: [],
        datatags: [],
        evidence: [],
        tagAssignments: [],
        codeTransitions: []
    });
    const upload = reactive({
        games: true,
        users: true,
        codes: true,
        tags: true,
        datatags: true,
        evidence: true,
        tagAssignments: true,
        codeTransitions: true,
    });

    const numSelected = computed(() => Object.values(upload).reduce((acc, d) => acc + (d ? 1 : 0), 0))

    const headers = [
        { title: "Id", key: "id", type: "integer" },
        { title: "Name", key: "name", type: "string" },
        { title: "Year", key: "year", type: "integer" },
        { title: "Played", key: "played", type: "integer" },
        { title: "URL", key: "url", type: "url" },
    ];
    const userHeaders = [
        { title: "Id", key: "id", type: "integer" },
        { title: "Name", key: "name", type: "string" },
        { title: "Role", key: "role", type: "string" },
        { title: "E-Mail", key: "email", type: "string" },
    ];
    const codeHeaders = [
        { title: "Id", key: "id", type: "integer" },
        { title: "Name", key: "name", type: "string" },
        { title: "Description", key: "description", type: "string" },
        { title: "Created", key: "created", type: "integer" },
        { title: "Created By", key: "created_by", type: "integer" },
        { title: "Dataset Id", key: "dataset_id", type: "integer" },
    ];
    const tagHeaders = [
        { title: "Id", key: "id", type: "integer" },
        { title: "Name", key: "name", type: "string" },
        { title: "Description", key: "description", type: "string" },
        { title: "Created", key: "created", type: "integer" },
        { title: "Created By", key: "created_by", type: "integer" },
        { title: "Code Id", key: "code_id", type: "integer" },
        { title: "Parent", key: "parent", type: "integer", default: null },
        { title: "Is Leaf", key: "is_leaf", type: "integer", default: null },
    ];
    const datatagHeaders = [
        { title: "Id", key: "id", type: "integer" },
        { title: "Game Id", key: "game_id", type: "integer" },
        { title: "Tag Id", key: "tag_id", type: "integer" },
        { title: "Code Id", key: "code_id", type: "integer" },
        { title: "Created", key: "created", type: "integer" },
        { title: "Created By", key: "created_by", type: "integer" },
    ];
    const evidenceHeaders = [
        { title: "Id", key: "id", type: "integer" },
        { title: "Game Id", key: "game_id", type: "integer" },
        { title: "Code Id", key: "code_id", type: "integer" },
        { title: "Filepath", key: "filepath", type: "string" },
        { title: "Description", key: "description", type: "string" },
        { title: "Created", key: "created", type: "integer" },
        { title: "Created By", key: "created_by", type: "integer" },
    ];
    const tagAssigHeaders = [
        { title: "Id", key: "id", type: "integer" },
        { title: "Old Code Id", key: "old_code", type: "integer" },
        { title: "New Code Id", key: "new_code", type: "integer" },
        { title: "Old Code Tag", key: "old_tag", type: "integer" },
        { title: "New Code Tag", key: "new_tag", type: "integer" },
        { title: "Created", key: "created", type: "integer" },
        { title: "Description", key: "description", type: "string" },
    ];
    const codeTransHeaders = [
        { title: "Id", key: "id", type: "integer" },
        { title: "Old Code Id", key: "old_code", type: "integer" },
        { title: "New Code Id", key: "new_code", type: "integer" },
        { title: "Created", key: "created", type: "integer" },
        { title: "Created By", key: "created_by", type: "integer" },
    ];

    async function submit() {
        if (numSelected.value === 0) {
            return;
        }

        const payload = {};
        if (contents.games.length > 0 && upload.games) {
            payload.games = contents.games;
        }
        if (contents.users.length > 0 && upload.users) {
            payload.users = contents.users;
        }
        if (contents.codes.length > 0 && upload.codes) {
            payload.codes = contents.codes;
        }
        if (contents.tags.length > 0 && upload.tags) {
            payload.tags = contents.tags;
        }
        if (contents.datatags.length > 0 && upload.datatags) {
            payload.datatags = contents.datatags;
        }
        if (contents.evidence.length > 0 && upload.evidence) {
            payload.evidence = contents.evidence;
        }
        if (contents.tagAssignments.length > 0 && upload.tagAssignments) {
            payload.tag_assignments = contents.tagAssignments;
        }
        if (contents.codeTransitions.length > 0 && upload.codeTransitions) {
            payload.code_transitions = contents.codeTransitions;
        }

        const size = Object.values(payload).reduce((acc, d) => acc + d.length, 0)
        if (size> 0) {
            if (!addToExisting.value && newDSName.value) {
                await loader.post("add/dataset", { name: newDSName.value, description: newDSDesc.value })
            }

            if ((addToExisting.value && app.ds) || newDSName.value) {
                payload.dataset = addToExisting.value ? app.getDatasetName(app.ds) : newDSName.value;
                loader.post("upload", payload)
                    .then(() => toast.success("uploaded data"))
            }
        }
    }

    function loadDatasets() {
        loader.get("datasets").then(list => app.setDatasets(list))
    }

    onMounted(loadDatasets)
</script>