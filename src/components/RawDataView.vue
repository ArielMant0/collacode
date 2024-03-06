<template>
    <v-autocomplete
        v-model="filter"
        :items="data"
        density="compact"
        clearable
        label="filter games .."
        prepend-icon="mdi-magnify"
        item-title="name"
        item-value="id"/>
    <v-data-table v-model="selectedRows" :items="data" :headers="headers" item-value="id" :show-select="selectable" @update:model-value="selectRows">
        <template v-slot:item="{ item }">
            <tr :class="item.edit ? 'bg-grey' : ''">
                <td v-if="selectable">
                    <v-checkbox
                        :model-value="selectedRows.includes(item.id)"
                        density="compact"
                        hide-details hide-spin-buttons/>
                </td>
                <td v-for="(h, i) in headers">

                    <v-icon v-if="i === 0" class="mr-2" density="compact" variant="text" @click="toggleEdit(item)">
                        {{ item.edit ? 'mdi-check' : 'mdi-pencil' }}
                    </v-icon>

                    <v-icon v-if="h.key === 'tags'" class="mr-2" @click="openTagDialog(item.id)">mdi-plus</v-icon>

                    <a v-if="!item.edit && h.type === 'url'" :href="item[h.key]" target="_blank">open in new tab</a>
                    <span v-else-if="!item.edit && h.key === 'tags'" class="text-caption text-ww" >
                        {{ tagsToString(item.tags) }}
                    </span>
                    <input v-else
                        v-model="item[h.key]"
                        style="width: 90%;"
                        @keyup="event => onKeyUp(event, item, h)"
                        @blur="parseType(item, h.key, h.type)"
                        :disabled="!item.edit"/>

                </td>
            </tr>
        </template>
    </v-data-table>
    <v-btn v-if="allowAdd" @click="emit('add-row')">add row</v-btn>

    <v-dialog v-model="addTagsDialog" min-width="400" width="auto">
        <v-card max-width="500" title="Add tags">
            <template v-slot:text>
                <v-list density="compact">
                    <v-list-item v-for="tag in tagging.item.tags"
                        :title="tag.name"
                        :subtitle="app.getUserName(tag.created_by)"
                        density="compact"
                        hide-details>

                        <template v-slot:append>
                            <v-tooltip v-if="tag.tag_id" :text="getTagDesc(tag.tag_id)" location="right">
                                <template v-slot:activator="{ props }">
                                    <v-icon v-bind="props">mdi-information-outline</v-icon>
                                </template>
                            </v-tooltip>
                            <v-tooltip v-else-if="tag.description" :text="description" location="right">
                                <template v-slot:activator="{ props }">
                                    <v-icon v-bind="props">mdi-information-outline</v-icon>
                                </template>
                            </v-tooltip>
                        </template>
                    </v-list-item>
                </v-list>

                <v-text-field v-model="tagging.newTag"
                    autofocus
                    style="min-width: 250px"
                    density="compact"
                    hide-details
                    hide-spin-buttons
                    append-icon="mdi-plus"
                    @click:append="addNewTag"
                    @keyup="onKeyUpTag"/>

                <v-text-field v-model="tagging.newTagDesc"
                    style="min-width: 250px"
                    density="compact"
                    hide-details
                    hide-spin-buttons
                    placeholder="add a description"/>
            </template>

            <v-btn rounded="0" color="success" @click="saveAndClose">save</v-btn>
        </v-card>
    </v-dialog>

</template>

<script setup>
    import { computed, reactive, ref } from 'vue'
    import { useApp } from '@/store/app'
    import { useLoader } from '@/use/loader';
    import DM from '@/use/data-manager';

    const app = useApp();
    const loader = useLoader();

    const filter = ref("")
    const tagging = reactive({
        item: null,
        newTag: "",
        newTagDesc: ""
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
        return props.data.filter(d => d.name.match(filter.value) !== null)
    })

    function onKeyUp(event, item, header) {
        if (item.edit && event.code === "Enter") {
            item[header.key] = event.target.value;
            parseType(item, header.key, header.type);
        }
    }
    function onKeyUpTag(event) {
        if (event.code === "Enter") {
            addNewTag();
        }
    }

    function toggleEdit(item) {
        if (item.edit) {
            props.headers.forEach(h => parseType(item, h.key, h.type));
            loader.post("update/game", { game: item }).then(app.needsReload)
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
                    if (typeof(d[key]) === "string") {
                        d[key] = JSON.parse(d[key]);
                    }
                    break;
            }
        } catch {
            console.error("could not convert field", key, "to", type)
        }
    }

    function selectRows() {
        app.selectByAttr("id", selectedRows.value);
    }

    function tagsToString(tags) {
        return tags.map(d => d.name + " (" + d.created_by + ")")
            .join(", ")
    }

    function getTagDesc(id) {
        const t = tags.value.find(d => d.id === id);
        return t ? t.description : "";
    }

    function openTagDialog(id) {
        tagging.item = props.data.find(d => d.id === id);
        addTagsDialog.value = true;
    }
    function addNewTag() {
        if (tagging.item && tagging.newTag.length > 0) {
            const tag = tags.value.find(d => d.name === tagging.newTag)
            if (tagging.item.tags) {
                tagging.item.tags.push({
                    name: tagging.newTag,
                    description: tagging.newTagDesc,
                    created_by: app.activeUserId,
                    tag_id: tag ? tag.id : null
                });
            }
            tagging.newTag = "";
            tagging.newTagDesc = "";
        }
    }
    function saveAndClose() {
        const body = {
            game_id: tagging.item.id,
            user_id: app.activeUserId,
            code_id: app.activeCode,
            created: Date.now(),
        };
        body.tags = tagging.item.tags.map(t => {
            if (t.tag_id !== null) {
                return  { tag_id: t.tag_id };
            }
            return { tag_name: t.name, description: t.description }
        })
        loader.post("update/game/datatags", body).then(app.needsReload)
        tagging.item = {};
        tagging.newTag = "";
        addTagsDialog.value = false;
    }

    defineExpose({ parseType, defaultValue })
</script>

<style scoped>
.text-ww {
    overflow: hidden;
    white-space: wrap;
}
</style>
