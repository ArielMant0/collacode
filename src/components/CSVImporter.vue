<template>
    <div>
        <v-file-input v-model="file" accept="text/csv" label="CSV file" @update:model-value="readFile"/>
        <v-card>
            <div class="d-flex">
                <div v-for="h in contents.headers" style="min-width: 150px;" class="mr-2">
                    <v-select v-model="h.match"
                        :label="'match - ' + h.title + ' - to'"
                        :items="headers"
                        item-value="title"
                        item-key="key"
                        return-object
                        density="compact"
                        hide-details
                        hide-no-data
                        @update:model-value="setMatch(h, h.match)"/>
                </div>
            </div>
            <v-data-table :items="contents.data" :headers="contents.headers">
                <template v-slot:item="{ item }">
                    <tr>
                        <td v-for="h in contents.headers">
                            {{ formatColumn(item[h.key], h.type) }}
                        </td>
                    </tr>
                </template>
            </v-data-table>
        </v-card>
        <v-btn :disabled="!allMatched" @click="submit" color="#078766">add to database</v-btn>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app';
    import { ref, reactive, computed } from 'vue'

    const app = useApp();
    const loader = useLoader();
    const file = ref([])
    const contents = reactive({
        data: [],
        headers: []
    })
    const allMatched = computed(() => {
        if (!contents.headers) return false;
        return !headers.some(d => contents.headers.find(h => h.match.key === d.key) === undefined)
    })

    const headers = [
        // { title: "ID", key: "id", type: "id" },
        { title: "Title", key: "title", type: "string" },
        { title: "Year", key: "year", type: "integer" },
        { title: "Played", key: "played", type: "boolean" },
        { title: "Notes", key: "notes", type: "string" },
    ];

    function readFile() {
        if (file.value.length === 0) return;

        const reader = new FileReader();
        reader.addEventListener('load', event => {
            const csv = d3.dsvFormat(";");
            const data = csv.parse(event.target.result);
            const assigned = {}
            contents.headers = Object.keys(data[0]).map(d => {
                let h = headers.find(dd => dd.title.match(new RegExp(d, "i")) !== null);
                if (!h) {
                    h = headers.find(dd => assigned[dd.key] === undefined)
                }
                assigned[h.key] = d.key;
                return {
                    title: d,
                    key: d,
                    type: h.type,
                    match: h
                }
            })

            contents.data = data.map(d => {
                contents.headers.forEach(h => parseType(d, h.key, h.type));
                return d;
            });
        });
        reader.readAsText(file.value[0]);
    }

    function setMatch(header, match) {
        const item = headers.find(d => d.key === match);
        if (item) {
            header.type = item.type;
            parseTypeForAll(header.key, header.type)
        }
    }

    function parseTypeForAll(key, type) {
        if (!contents.data) return;
        contents.data.forEach(d => parseType(d, key, type))
    }

    function parseType(d, key, type) {
        if (!d[key]) return;
        try {
            switch (type) {
                case "string": d[key] = ""+d[key]; break;
                case "integer": d[key] = Number.parseInt(d[key]); break;
                case "float": d[key] = Number.parseFloat(d[key]); break;
                case "boolean": d[key] = (d[key] === true || d[key] === 1 || d[key].match(/true|yes/i) !== null); break;
                case "datetime": d[key] = Date.parse(d[key]); break;
                case "array":
                case "object": d[key] = JSON.parse(d[key]); break;
            }
        } catch {
            console.error("could not convert field", key, "to", type)
        }
    }

    function formatColumn(value, type) {
        if (value === "" || value === null || value === undefined) return "";
        switch (type) {
            case "string": return value;
            case "integer": return value.toFixed(0);
            case "float": return value.toFixed(2);
            case "boolean": return ""+value
            case "datetime": return value.toLocaleString()
            case "array":
            case "object": return JSON.stringify(value);
        }
    }

    function submit() {
        if (!allMatched.value) {
            console.error("not all columns were matched");
            return;
        }
        if (!app.ds) {
            console.error("no dataset selected");
            return;
        }

        const data = contents.data.map(d => {
            const obj = {};
            contents.headers.forEach(h => obj[h.match.key] = d[h.key])
            return obj
        })
        loader.post(`${app.ds}/data`, { rows: data })
    }
</script>