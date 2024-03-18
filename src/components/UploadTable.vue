<template>
    <div>
        <div class="d-flex">
            <v-file-input accept="text/csv"
                :label="label"
                hide-details hide-spin-buttons
                density="compact"
                class="mr-2"
                @update:model-value="f => readFromFile(f[0])"/>

            <v-select v-model="delim" label="Delimiter"
                :items="[';',',']"
                hide-details hide-spin-buttons
                density="compact"/>
        </div>
        <div class="d-flex mt-2 mb-4" v-if="data.assignment">
            <v-select v-for="(h, i) in headers" :key="h.key"
                v-model="data.assignment[h.key]"
                hide-details hide-spin-buttons
                density="compact"
                :class="i > 0 ? 'ml-1' : ''"
                :items="data.dataHeaders"
                item-title="title"
                :label="`Assign to '${h.title}'`"
                @update:model-value="setAssignment"/>
        </div>
        <v-data-table :items="data.parsed" :headers="headers" density="compact" :key="'dt_'+time"/>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { reactive, ref } from 'vue'

    const props = defineProps({
        headers: {
            type: Array,
            required: true
        },
        label: {
            type: String,
            default: "File Upload"
        }
    })
    const emit = defineEmits(["change"])

    const time = ref(0);
    const delim = ref(";")
    const data = reactive({
        parsed: [],
        dataHeaders: [],
        assignment: {},
    })

    function readFromFile(file) {

        if (!file || file.length === 0) {
            data.raw = [];
            data.parsed = [];
            data.dataHeaders = [];
            data.assignment = {};
            emit("change", [])
            return;
        };

        const reader = new FileReader();
        reader.addEventListener('load', event => {
            data.raw = d3.dsvFormat(delim.value).parse(event.target.result);
            data.parsed = guessAssignemnt(data.raw, data.raw.columns)
            time.value = Date.now()
            emit("change", data.parsed)
        });
        reader.readAsText(file);
    }

    function defaultValue(type) {
        switch (type) {
            case "string": return "";
            case "url": return new URL("https://store.steampowered.com/");
            case "integer": return 0;
            case "float": return 0.0;
            case "boolean": return false;
            case "datetime": return new Date();
            case "array": return [];
            case "object": return {};
        }
        return null;
    }
    function parseType(d, key, type) {
        if (!d[key]) return;
        try {
            switch (type) {
                case "string": d[key] = ""+d[key]; break;
                case "url": d[key] = new URL(d[key]); break;
                case "integer": d[key] = typeof(d[key]) === "number" ? d[key] : Number.parseInt(d[key]); break;
                case "float": d[key] = typeof(d[key]) === "number" ? d[key] : Number.parseFloat(d[key]); break;
                case "boolean": d[key] = typeof(d[key]) === "boolean" ? d[key] : (d[key] === true || d[key] === 1 || d[key].match(/true|yes/i) !== null); break;
                case "datetime": d[key] = typeof(d[key]) === "object" ? d[key] :  Date.parse(d[key]); break;
                case "array":
                case "object":
                    if (typeof(d[key]) === "string") {
                        d[key] = JSON.parse(d[key]);
                    }
                    break;
            }
        } catch {
            console.error("could not convert field", key, "to", type)
        }
    }

    function guessAssignemnt(array, headers=null) {
        const assigned = {}
        data.dataHeaders = headers ? headers : Object.keys(array[0]);
        data.dataHeaders.forEach(d => {
            let hTitle = props.headers.find(dd => dd.title.match(new RegExp(d, "i")) !== null);
            let hKey = props.headers.find(dd => dd.key.match(new RegExp(d, "i")) !== null);
            if (hTitle) { assigned[hTitle.key] = d; }
            if (hKey) { assigned[hKey.key] = d; }
        })

        data.assignment = assigned;
        return parseAssignment(array)
    }

    function parseAssignment(array) {
        return array.map(d => {
            const obj = {};
            props.headers.forEach(h => {
                if (data.assignment[h.key]) {
                    obj[h.key] = d[data.assignment[h.key]]
                } else {
                    obj[h.key] = defaultValue(h.type);
                }
                parseType(obj, h.key, h.type)
            })
            return obj;
        });
    }

    function setAssignment() {
        data.parsed = parseAssignment(data.raw)
        time.value = Date.now()
        emit("change", data.parsed)
    }
</script>