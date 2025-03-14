<template>
    <div style="max-width: 100%;">
        <div class="d-flex">
            <v-file-input accept="text/csv"
                :label="label"
                hide-details hide-spin-buttons
                density="compact"
                class="mr-2"
                @update:model-value="f => readFromFile(f)"/>

            <v-select v-model="delim" label="Delimiter"
                :items="[';',',']"
                hide-details hide-spin-buttons
                density="compact"/>
        </div>
        <div class="d-flex mt-2 mb-4" v-if="data.assignment">
            <v-select v-for="(h, i) in headers" :key="h.key"
                v-model="data.assignment[h.key]"
                hide-details hide-spin-buttons
                clearable
                density="compact"
                :class="i > 0 ? 'ml-1' : ''"
                :items="data.dataHeaders"
                item-title="title"
                :label="`Assign to '${h.title}'`"
                @update:model-value="setAssignment"/>
        </div>
        <v-data-table
            :items="data.parsed"
            :headers="headers"
            style="max-width: 100%;"
            density="compact"
            :key="'dt_'+time">

            <template v-slot:item="{ item }">
                <tr>
                    <td v-for="h in headers" class="text-ww">
                        <img v-if="h.type === 'image'" width="100" height="50"
                            :src="item[h.key]"
                            style="object-fit: contain;"
                            @pointermove="e => hoverImg(item[h.key], e)"
                            @pointerleave="hoverImg(null)"/>
                        <span v-else-if="h.type === 'array'">{{ item[h.key].join(', ') }}</span>
                        <span v-else>{{ item[h.key] }}</span>
                    </td>
                </tr>
            </template>
        </v-data-table>

        <ToolTip :x="hoverI.x" :y="hoverI.y" :data="hoverI.src">
            <template v-slot:default>
                <img :src="hoverI.src" style="max-height: 250px; object-fit: contain;"/>
            </template>
        </ToolTip>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { reactive, ref, watch } from 'vue'
    import ToolTip from './ToolTip.vue';

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
    const delim = ref(",")
    const data = reactive({
        raw: [],
        parsed: [],
        dataHeaders: [],
        assignment: {},
    })

    const hoverI = reactive({
        x: 0, y: 0,
        src: null
    })

    function readFromFile(file) {

        if (!file) {
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
            data.parsed = guessAssignemnt(data.raw, data.raw.columns, true)
            time.value = Date.now()
            emit("change", data.parsed)
        });
        reader.readAsText(file);
    }

    function defaultValue(type) {
        switch (type) {
            default:
            case "url": return "";
            case "string": return "";

            case "integer": return 0;
            case "float": return 0.0;
            case "boolean": return false;
            case "datetime": return new Date();
            case "array": return [];
            case "object": return {};
        }
    }
    function parseType(d, key, type) {
        if (!d[key]) return;
        try {
            switch (type) {
                case "image": d[key] = ""+d[key]; break;
                case "string": d[key] = ""+d[key]; break;
                case "url": d[key] = d[key]; break;
                case "integer":
                    switch(typeof(d[key])) {
                        case 'string': {
                            const l = d[key].toLowerCase()
                            if (l === "true" || l === "false") {
                                d[key] = l === "true" ? 1 : 0
                            } else {
                                d[key] = Number.parseInt(d[key])
                            }
                        } break;
                        case 'boolean':
                            d[key] = d[key] ? 1 : 0
                            break
                        case 'symbol':
                        case 'undefined':
                        case 'object':
                        case 'function':
                            d[key] = NaN
                            break
                    }
                    break;
                case "float": d[key] = typeof(d[key]) === "number" ? d[key] : Number.parseFloat(d[key]); break;
                case "boolean": d[key] = typeof(d[key]) === "boolean" ? d[key] : (d[key] === true || d[key] === 1 || d[key].match(/true|yes/i) !== null); break;
                case "datetime": d[key] = typeof(d[key]) === "object" ? d[key] :  Date.parse(d[key]); break;
                case "array":
                case "object":
                    if (typeof(d[key]) === "string") {
                        try {
                            d[key] = JSON.parse(d[key]);
                        } catch {
                            d[key] = d[key].split(",")
                        }
                    }
                    break;
            }
        } catch {
            console.error("could not convert field", key, "to", type)
            console.debug(d[key], typeof d[key])
        }
    }

    function guessAssignemnt(array, headers=null, reset=false) {
        const assigned = !reset && data.assignment ? data.assignment : {}
        data.dataHeaders = headers ? headers : Object.keys(array[0]);
        data.dataHeaders.forEach(d => {
            if (assigned[d.key]) return
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
                    obj[h.key] = h.default !== undefined ? h.default : defaultValue(h.type);
                }
                parseType(obj, h.key, h.type)
            })
            return obj;
        });
    }

    function hoverImg(src, e) {
        if (src) {
            const [mx, my] = d3.pointer(e, document.body)
            hoverI.x = mx + 15
            hoverI.y = my
            hoverI.src = src;
        } else {
            hoverI.src = null;
        }
    }

    function setAssignment() {
        data.parsed = parseAssignment(data.raw)
        time.value = Date.now()
        emit("change", data.parsed)
    }

    watch(() => props.headers, function() {
        if (data.raw.length > 0) {
            data.parsed = guessAssignemnt(data.raw, data.raw.columns)
            time.value = Date.now()
        }
    }, { deep: true })
</script>