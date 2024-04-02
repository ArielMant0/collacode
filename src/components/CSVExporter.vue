<template>
    <div>
        <v-card class="d-flex mb-2">
            <v-text-field v-model="filename" label="Filename" hide-details class="mr-1" hide-spin-buttons density="compact"/>
            <v-select v-model="delim" label="Delimiter" :items="[';',',']" class="mr-1" hide-details hide-spin-buttons density="compact"/>
            <v-btn @click="exportData" color="primary" class="float-right">export</v-btn>
        </v-card>

        <v-card>
            <h4 class="ml-4 mt-2">Users</h4>
            <v-data-table :items="data.users" density="compact"/>

            <h4 class="ml-4 mt-2">Games</h4>
            <v-data-table :items="data.games" :headers="headers" density="compact"/>

            <h4 class="ml-4 mt-2">Codes</h4>
            <v-data-table :items="data.codes" density="compact"/>

            <h4 class="ml-4 mt-2">Tags</h4>
            <v-data-table :items="data.tags" density="compact"/>

            <h4 class="ml-4 mt-2">DataTags</h4>
            <v-data-table :items="data.datatags" density="compact"/>

            <h4 class="ml-4 mt-2">Evidence</h4>
            <v-data-table :items="data.evidence" density="compact"/>

            <h4 class="ml-4 mt-2">Tag Assignments</h4>
            <v-data-table :items="data.tagAssigs" density="compact"/>

            <h4 class="ml-4 mt-2">Code Transitions</h4>
            <v-data-table :items="data.codeTrans" density="compact"/>
        </v-card>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { onMounted, reactive, ref } from 'vue'
    import { useApp } from '@/store/app';
    import { saveAs } from 'file-saver';
    import DM from '@/use/data-manager'
    import JSZip from 'jszip';
    import axios from "axios";

    const app = useApp();

    const delim = ref(";")
    const filename = ref("export")
    const data = reactive({
        users: [],
        games: [],
        codes: [],
        tags: [],
        datatags: [],
        evidence: [],
        tagAssigs: [],
        codeTrans: [],
    })

    const headers = [
        { title: "Id", key: "id", type: "id" },
        { title: "Name", key: "name", type: "string" },
        { title: "Year", key: "year", type: "integer" },
        { title: "Played", key: "played", type: "integer" },
        { title: "URL", key: "url", type: "url" },
    ];

    async function exportData() {
        const zip = new JSZip()
        const csv = d3.dsvFormat(delim.value);

        if (data.users.length > 0) {
            zip.file("users.csv", csv.format(data.users))
        }
        if (data.games.length > 0) {
            zip.file("games.csv", csv.format(data.games, ["id", "name", "year", "played", "url"]))
        }
        if (data.codes.length > 0) {
            zip.file("codes.csv", csv.format(data.codes))
        }
        if (data.tags.length > 0) {
            zip.file("tags.csv", csv.format(data.tags))
        }
        if (data.datatags.length > 0) {
            zip.file("datatags.csv", csv.format(data.datatags))
        }

        if (data.evidence.length > 0) {
            zip.file("evidence.csv", csv.format(data.evidence))
            const folder = zip.folder("evidence")
            const proms = data.evidence.map(e => {
                return axios.get("evidence/"+e.filepath, { responseType: "arraybuffer"})
                    .then(response => folder.file(e.filepath, response.data, { binary: true }))
            })
            await Promise.all(proms)
        }

        if (data.tagAssigs.length > 0) {
            zip.file("tag_assignments.csv", csv.format(data.tagAssigs))
        }
        if (data.codeTrans.length > 0) {
            zip.file("code_transitions.csv", csv.format(data.codeTrans))
        }

        zip.generateAsync({type:"blob"}).then(blob => saveAs(blob, filename.value+".zip"));
    }

    function readData() {
        data.users = app.users;
        data.games = DM.getData("games", false)
        data.codes = DM.getData("codes", false)
        data.tags = DM.getData("tags", false)
        data.datatags = DM.getData("datatags", false)
        data.evidence = DM.getData("evidence", false)
        data.tagAssigs = DM.getData("tag_assignments", false) || []
        data.codeTrans = DM.getData("code_transitions", false) || []
    }

    onMounted(readData)

</script>