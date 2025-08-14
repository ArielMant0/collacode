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
    import { defaultValue, parseType } from '@/use/utility';

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