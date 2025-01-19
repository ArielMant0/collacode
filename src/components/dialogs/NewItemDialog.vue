<template>
    <MiniDialog v-model="model" @cancel="cancel" @submit="submit" title="Add New Item" min-width="900">
        <template v-slot:text>
            <div class="d-flex flex-column align-center">
                <v-btn
                    @click="importer = !importer"
                    density="comfortable">
                    {{ importer ? 'hide' : 'show' }} importer
                </v-btn>

                <div v-if="importer" class="mt-4 d-flex">
                    <v-card class="d-flex align-center flex-column pa-2 mr-2">
                        Steam
                        <v-img
                            density="compact"
                            width="50"
                            height="50"
                            class="cursor-pointer"
                            src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/480px-Steam_icon_logo.svg.png"
                            @click.stop="steamImport = true"/>
                    </v-card>
                    <v-card class="d-flex align-center flex-column pa-2">
                        OpenLibrary
                        <v-img
                            density="compact"
                            width="50"
                            height="50"
                            class="cursor-pointer"
                            src="https://openlibrary.org/static/images/openlibrary-logo-tighter.svg"
                            @click.stop="openLibImport = true"/>
                    </v-card>
                </div>

                <v-divider style="width: 100%;" class="mt-4 mb-4"></v-divider>

                <v-text-field v-model="name"
                    density="compact"
                    :label="app.schemeItemName + ' name'"
                    style="width: 100%;"
                    hide-details
                    hide-spin-buttons
                    class="mb-1"/>

                <v-textarea v-model="desc"
                    hide-details
                    hide-spin-buttons
                    density="compact"
                    style="width: 100%;"
                    :label="app.schemeItemName + ' description'"
                    class="mb-1"/>

                <v-text-field v-model="url"
                    density="compact"
                    style="width: 100%;"
                    label="URL"
                    class="mb-1"
                    hide-details
                    hide-spin-buttons/>

                <div v-for="([key, obj]) in otherValues" :key="key" class="mb-1" style="width: 100%;">
                    <v-text-field v-if="obj.type === 'string'"
                        v-model="obj.value"
                        density="compact"
                        style="width: 100%;"
                        :label="obj.label"
                        hide-details
                        hide-spin-buttons/>
                    <v-number-input v-if="obj.type === 'integer'"
                        v-model="obj.value"
                        controlVariant="split"
                        :label="obj.label"
                        :step="1"
                        style="width: 100%;"
                        density="compact"
                        hide-details
                        hide-spin-buttons/>
                    <v-number-input v-if="obj.type === 'float'"
                        v-model="obj.value"
                        controlVariant="split"
                        :label="obj.label"
                        style="width: 100%;"
                        density="compact"
                        hide-details
                        hide-spin-buttons/>
                    <v-date-input v-if="obj.type === 'date'"
                        v-model="obj.value"
                        :label="obj.label"
                        style="width: 100%;"
                        density="compact"
                        clearable
                        hide-details
                        hide-spin-buttons/>
                </div>

                <v-file-input v-model="file"
                    accept="image/*"
                    label="Upload a teaser"
                    style="width: 100%;"
                    density="compact"
                    class="mt-2"
                    hide-details
                    hide-spin-buttons
                    @update:model-value="readFile"/>
                <v-img
                    :src="image"
                    :lazy-src="imgUrlS"
                    class="mt-2"
                    alt="Teaser Image"
                    width="160"
                    height="80"/>
            </div>
        </template>
    </MiniDialog>

    <SteamImporter v-model="steamImport" @load="loadFromSteam"/>
    <OpenLibraryImporter v-model="openLibImport" @load="loadFromOpenLibrary"/>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import MiniDialog from './MiniDialog.vue';
    import SteamImporter from './SteamImporter.vue';
    import OpenLibraryImporter from './OpenLibraryImporter.vue';
    import { v4 as uuidv4 } from 'uuid';
    import { useToast } from 'vue-toastification';

    import imgUrlS from '@/assets/__placeholder__s.png';
    import { addItems, addItemTeaser } from '@/use/utility';
    import { useTimes } from '@/store/times';
    import { reactive, watch } from 'vue';

    const app = useApp();
    const times = useTimes()
    const toast = useToast()

    const model = defineModel();
    const name = ref("")
    const desc = ref("")
    const url = ref("")

    const file = ref(null)
    const image = ref("")
    const imageUrl = ref("")
    const teaser = ref("")

    const otherValues = reactive(new Map())

    const importer = ref(false)
    const steamImport = ref(false)
    const openLibImport = ref(false)

    function readFile() {
        if (!file.value) {
            image.value = "";
            return;
        }

        const reader = new FileReader();
        reader.addEventListener('load', () => {
            image.value = reader.result
            imageUrl.value = ""
        });
        reader.readAsDataURL(file.value);
    }

    function cancel() {
        model.value = false;
        name.value = ""
        url.value = "";
        file.value = null
        image.value = ""
        imageUrl.value = ""
        teaser.value = ""
        otherValues.clear()
    }

    async function uploadTeaser() {
        if (!file.value) {
            return toast.error("missing teaser image")
        }

        try {
            const filename = uuidv4();
            await addItemTeaser(filename, file.value)
            teaser.value = filename;
        } catch (e) {
            toast.error("could not upload teaser image")
            throw e;
        }
    }

    async function submit() {
        if (!name.value) {
            return toast.error("missing name")
        }

        try {
            if (imageUrl.value) {
                await addItems([{
                    name: name.value,
                    url: url.value,
                    teaserUrl: imageUrl.value
                }], app.ds)
             } else {
                await uploadTeaser();
                await addItems([{
                    name: name.value,
                    url: url.value,
                    teaserName: teaser.value
                }], app.ds)
            }
            toast.success("added item: " + name.value)
            cancel();
            app.addAction("table", "last-page");
            times.needsReload("items")
        } catch {
            toast.error("could not add item")
        }
    }

    function loadFromSteam(game) {
        if (game) {
            for (const key in game) {
                switch (key) {
                    case "name":
                        name.value = game[key];
                        break;
                    case "desc":
                    case "description":
                        desc.value = game[key];
                        break;
                    case "url":
                        url.value = game[key];
                        break;
                    case "img":
                        image.value = game[key];
                        imageUrl.value = game[key];
                        break;
                    default:
                        if (otherValues.has(key)) {
                            otherValues.get(key).value = game[key]
                        }
                }
            }
            toast.success("loaded data from Steam")
        } else {
            imageUrl.value = "";
            toast.warning("received no Steam data")
        }
    }
    function loadFromOpenLibrary(item) {
        if (item) {
            for (const key in item) {
                switch (key) {
                    case "name":
                    case "title":
                        name.value = item[key];
                        break;
                    case "desc":
                    case "description":
                        desc.value = item[key];
                        break;
                    case "url":
                        url.value = item[key];
                        break;
                    case "img":
                        image.value = item[key];
                        imageUrl.value = item[key];
                        break;
                    default:
                        if (otherValues.has(key)) {
                            otherValues.get(key).value = item[key]
                        }
                }
            }
            toast.success("loaded data from OpenLibrary")
        } else {
            imageUrl.value = "";
            toast.warning("received no OpenLibrary data")
        }
    }

    function getDefaultValue(column) {
        if (column.default_value) {
            switch(column.type) {
                case "date": return new Date(column.default_value)
                case "float": return Number.parseFloat(column.default_value)
                case "integer": return Number.parseInt(column.default_value)
                default: return ""+column.default_value
            }
        }
        switch(column.type) {
            case "date": return new Date()
            case "float":
            case "integer": return 1;
            default: return ""
        }
    }

    watch(model, function() {
        if (model.value) {
            otherValues.clear()
            if (app.scheme && app.scheme.columns) {
                app.scheme.columns.forEach(d => {
                    otherValues.set(d.name, {
                        type: d.type,
                        value: getDefaultValue(d),
                        label: d.description
                    })
                })
            }
        }
    })
</script>