<template>
    <div>
        <v-file-input v-model="file" accept="text/csv" label="CSV file" @update:model-value="readFile"/>
        <v-card>
            <RawDataView ref="table"
                :data="contents.data"
                :headers="headers"
                allow-add
                @add-row="addEmptyRow"/>
        </v-card>
        <v-btn :disabled="!contents.data" @click="submit" color="#078766" class="mt-2 float-right">add to database</v-btn>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { useLoader } from '@/use/loader';
    import { useApp } from '@/store/app';
    import { ref, reactive, computed } from 'vue'
    import RawDataView from './RawDataView.vue';


    const app = useApp();
    const loader = useLoader();

    const table = ref(null)

    const file = ref([])
    const contents = reactive({ data: [] })

    const headers = [
        // { title: "ID", key: "id", type: "id" },
        { title: "Title", key: "title", type: "string" },
        { title: "Year", key: "year", type: "integer" },
        { title: "Played", key: "played", type: "boolean" },
        { title: "URL", key: "url", type: "url" },
    ];

    function readFile() {
        if (file.value.length === 0) return;

        const reader = new FileReader();
        reader.addEventListener('load', event => {
            const csv = d3.dsvFormat(";");
            const data = csv.parse(event.target.result);
            const assigned = {}

            Object.keys(data[0]).forEach(d => {
                let h = headers.find(dd => dd.title.match(new RegExp(d, "i")) !== null);
                console.log(h, d)
                if (h) {
                    assigned[h.key] = {
                        key: d,
                        type: h.type
                    };
                }
            })

            console.log(assigned)
            contents.data = data.map(d => {
                const obj = {};
                headers.forEach(h => {
                    if (assigned[h.key]) {
                        obj[h.key] = d[assigned[h.key].key]
                    } else {
                        obj[h.key] = table.value.defaultValue(h.type);
                    }
                    table.value.parseType(obj, h.key, h.type)
                })
                return obj;
            });
        });
        reader.readAsText(file.value[0]);
    }

    function addEmptyRow() {
        contents.data.push({
            title: "Title",
            year: new Date().getFullYear(),
            played: false,
            url: new URL(),
            edit: true
        });
    }

    function submit() {
        if (!app.ds) {
            console.error("no dataset selected");
            return;
        }

        loader.post(`${app.ds}/data/add`, { rows: contents.data.map(d => {
            const obj = Object.assign({}, d);
            delete obj.edit;
            return obj;
        }) })
    }
</script>