<template>
    <MiniDialog v-model="model" @cancel="cancel" @submit="submit" title="Add New Game" min-width="800">
        <template v-slot:text>
            <div class="d-flex flex-column align-center">
                <v-btn
                    @click="openSteamImporter"
                    density="compact"
                    class="mb-4"
                >
                    import from steam
                </v-btn>
                <v-text-field v-model="name"
                    density="compact"
                    label="Game Title"
                    style="width: 100%;"
                    hide-details
                    hide-spin-buttons/>
                <v-number-input v-model="year"
                    controlVariant="split"
                    label="Release Year"
                    :min="1950"
                    :max="2100"
                    :step="1"
                    class="mt-2"
                    style="width: 100%;"
                    density="compact"
                    hide-details
                    hide-spin-buttons
                    />
                <v-text-field v-model="url"
                    density="compact"
                    style="width: 100%;"
                    label="URL"
                    class="mt-2"
                    hide-details
                    hide-spin-buttons/>
                <v-file-input v-model="file"
                    accept="image/*"
                    label="Upload a game teaser"
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
</template>

<script setup>
    import { useApp } from '@/store/app';
    import MiniDialog from './MiniDialog.vue';
    import SteamImporter from './SteamImporter.vue';
    import { v4 as uuidv4 } from 'uuid';
    import { useToast } from 'vue-toastification';

    import imgUrlS from '@/assets/__placeholder__s.png';
    import { addItems, addItemTeaser } from '@/use/utility';
    import { useTimes } from '@/store/times';

    const app = useApp();
    const times = useTimes()
    const toast = useToast()

    const model = defineModel();
    const name = ref("Name")
    const year = ref(new Date().getFullYear())
    const url = ref("https://store.steampowered.com/")

    const file = ref(null)
    const image = ref("")
    const imageUrl = ref("")
    const teaser = ref("")

    const steamImport = ref(false)

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
        name.value = "Name"
        year.value = new Date().getFullYear()
        url.value = "https://store.steampowered.com/";
        file.value = null
        image.value = ""
        imageUrl.value = ""
        teaser.value = ""
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
        if (!year.value) {
            return toast.error("missing release year")
        }

        try {
            if (imageUrl.value) {
                await addItems([{
                    name: name.value,
                    year: year.value,
                    played: 0,
                    url: url.value,
                    teaserUrl: imageUrl.value
                }], app.ds)
             } else {
                await uploadTeaser();
                await addItems([{
                    name: name.value,
                    year: year.value,
                    played: 0,
                    url: url.value,
                    teaserName: teaser.value
                }], app.ds)
            }
            toast.success("added game: " + name.value)
            cancel();
            app.addAction("table", "last-page");
            times.needsReload("items")
        } catch {
            toast.error("could not add game")
        }
    }

    function openSteamImporter() {
        steamImport.value = true;
    }
    function loadFromSteam(game) {
        if (game) {
            name.value = game.name;
            year.value = game.year;
            url.value = game.url;
            image.value = game.img;
            imageUrl.value = game.img;
            toast.success("loaded data from steam")
        } else {
            imageUrl.value = "";
            toast.warning("received no steam data")
        }
    }
</script>