<template>
    <v-autocomplete
        v-model="filter"
        :items="data"
        density="compact"
        clearable
        label="filter titles .."
        prepend-icon="mdi-magnify"
        item-title="title"
        item-value="id"/>
    <v-data-table v-model="selectedRows" :items="data" :headers="headers" item-value="id" :show-select="selectable" @update:model-value="selectRows">
        <template v-slot:item="{ item }">
            <tr>
                <td v-if="selectable">
                    <v-checkbox
                        :model-value="selectedRows.includes(item.id)"
                        density="compact"
                        hide-details hide-spin-buttons/>
                </td>
                <td v-for="(h, i) in headers">
                    <v-icon v-if="i === 0" class="mr-2" density="compact" variant="text" @click="toggleEdit(item)">
                        mdi-pencil
                    </v-icon>
                    <a v-if="!item.edit && h.type === 'url'" :href="item[h.key]" target="_blank">{{ item[h.key] }}</a>
                    <input v-else
                        v-model="item[h.key]"
                        style="width: 90%;"
                        @keyup="event => onKeyUp(event, item, h)"
                        @blur="parseType(item, h.key, h.type)"
                        :disabled="!item.edit" autofocus/>

                    <v-icon v-if="h.key === 'tags'" @click="openTagDialog(item.id)">mdi-plus</v-icon>
                </td>
            </tr>
        </template>
    </v-data-table>
    <v-btn v-if="allowAdd" @click="emit('add-row')">add row</v-btn>

    <v-dialog v-model="addTagsDialog" width="auto" @update:model-value="onClose">
        <v-card max-width="500" title="Add tags">
            <template v-slot:text>
                <v-list :items="tagging.item.tags"></v-list>

                <v-text-field v-model="tagging.newTag"
                    autofocus
                    style="min-width: 250px"
                    density="compact"
                    hide-details
                    hide-spin-buttons
                    append-icon="mdi-plus"
                    @click:append="addNewTag"/>
            </template>
        </v-card>
    </v-dialog>

</template>

<script setup>
    import { computed, reactive, ref } from 'vue'
    import { useApp } from '@/store/app'
    import { useLoader } from '@/use/loader';

    const app = useApp();
    const loader = useLoader();

    const filter = ref("")
    const tagging = reactive({
        item: null,
        newTag: "",
    })
    const addTagsDialog = ref(false)
    const selectedRows = ref([])

    const tags = computed(() => DM.getData("tags"))

    const props = defineProps({
        data: {
            type: Array,
            required: true
        },
        headers: {
            type: Array,
            required: true
        },
        allowAdd: {
            type: Boolean,
            default: false
        },
        selectable: {
            type: Boolean,
            default: false
        }
    });
    const emit = defineEmits(["add-row"])

    const data = computed(() => {
        if (!filter.value) {
            return props.data
        }
        return props.data.filter(d => d.title.match(filter.value) !== null)
    })

    function onKeyUp(event, item, header) {
        if (item.edit && event.keyCode === "Enter") {
            item[header.key] = event.target.value;
            parseType(item, header.key, header.type);
        }
    }

    function toggleEdit(item) {
        if (item.edit) {
            props.headers.forEach(h => parseType(item, h.key, h.type));
        }
        item.edit = !item.edit;
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
                case "integer": d[key] = Number.parseInt(d[key]); break;
                case "float": d[key] = Number.parseFloat(d[key]); break;
                case "boolean": d[key] = (d[key] === true || d[key] === 1 || d[key].match(/true|yes/i) !== null); break;
                case "datetime": d[key] = Date.parse(d[key]); break;
                case "array":
                case "object":
                    d[key] = JSON.parse(d[key]);
                    break;
            }
        } catch {
            console.error("could not convert field", key, "to", type)
        }
    }

    function selectRows() {
        app.selectByAttr("id", selectedRows.value);
    }

    function openTagDialog(id) {
        tagging.item = props.data.find(d => d.id === id);
        addTagsDialog.value = true;
    }
    function addNewTag() {
        if (tagging.item && tagging.newTag.length > 0) {
            tagging.item.tags.push(tagging.newTag);
            tagging.newTag = "";
        }
    }
    function onClose() {
        if (!addTagsDialog.value) {
            const body = {
                game_id: tagging.item.id,
                user_id: app.activeUserId,
                code_id: app.activeCode,
                created: Date.now(),
            };
            body.tags = tagging.item.tags.map(t => {
                return {
                    tag_id: tags.value.find(d => d.name === t),
                    name: t,
                };
            })
            loader.post("data_tags/update", body)
            tagging.item = {};
            tagging.newTag = "";
        }
    }

    defineExpose({ parseType, defaultValue })
</script>
