<template>
    <MiniDialog v-model="model" submit-text="" @cancel="cancel" min-width="700" style="max-width: 80%;">
        <template v-slot:text>
            <div class="d-flex flex-column align-center">
                <div class="d-flex" style="width: 100%;">
                    <v-number-input v-model="steamId"
                        controlVariant="stacked"
                        label="Steam ID"
                        :min="0"
                        :step="1"
                        style="width: 100%;"
                        density="compact"
                        hide-details
                        hide-spin-buttons
                    />
                    <v-btn class="ml-2" @click="loadFromId">load</v-btn>
                </div>
                <div class="mt-2 mb-2">OR</div>
                <div class="d-flex" style="width: 100%;">
                    <v-text-field v-model="steamName"
                        density="compact"
                        label="Game Title"
                        style="width: 100%;"
                        hide-details
                        hide-spin-buttons/>
                    <v-btn class="ml-2" @click="loadFromName">load</v-btn>
                </div>
                <v-divider></v-divider>
                <v-sheet v-if="candidates" class="d-flex flex-wrap mt-4" style="max-width: 100%;">
                    <div v-for="c in candidates" :key="c.id" @click="select(c)" class="mr-1 pa-1 cursor-pointer game-selector" :title="c.name+' ('+c.year+')'">
                        <p class="text-caption" style="max-width: 160px;">{{ c.name }} ({{ c.year }})</p>
                        <v-img
                            :src="c.img"
                            :lazy-src="imgUrlS"
                            class="mt-2"
                            alt="Teaser Image"
                            width="160"
                            height="80"/>
                    </div>
                </v-sheet>
            </div>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { getSteamFromId, getSteamFromName } from '@/use/utility';
    import { useToast } from 'vue-toastification';
    import MiniDialog from './MiniDialog.vue';
    import imgUrlS from '@/assets/__placeholder__s.png';

    const emit = defineEmits(["load", "cancel"])

    const model = defineModel();
    const steamId = ref(0)
    const steamName = ref("")
    const candidates = ref([])

    const toast = useToast();

    let data;
    let toastId = null;

    function submit() {
        if (data) {
            emit("load", data)
            model.value = false;
            reset()
        } else {
            toast.error("missing data")
        }
    }
    function cancel() {
        emit("cancel")
        model.value = false;
        reset()
    }
    function select(game) {
        data = game;
        submit();
    }
    function reset() {
        data = null;
        candidates.value = []
        steamId.value = 0;
        steamName.value = ""
    }

    async function loadFromId() {
        if (steamId.value < 1) {
            return;
        }

        try {
            candidates.value = []
            toastId = toast("fetching steam data, this may take a while...", { timeout: false})
            const response = await getSteamFromId(steamId.value)

            toast.update(toastId, { content: "done!"})
            toast.dismiss(toastId)
            setTimeout(() => {
                toast.dismiss(toastId)
                toastId = null
            }, 250)

            if (response.data.length > 0) {
                response.year = new Date(response.release_date).getFullYear()
                data = response[0];
                submit();
            } else {
                toast.error("could not find data for id " + steamId.value)
            }
        } catch {
            toast.error("could not find data for id " + steamId.value)
        }
    }

    async function loadFromName() {
        if (!steamName.value) {
            return;
        }

        try {
            candidates.value = []
            toastId = toast("fetching steam data, this may take a while...", { timeout: false})
            const response = await getSteamFromName(steamName.value)

            toast.update(toastId, { content: "done!"})
            setTimeout(() => {
                toast.dismiss(toastId)
                toastId = null
            }, 250)

            if (response.data.length > 1) {
                response.data.forEach(d => d.year = new Date(d.release_date).getFullYear())
                candidates.value = response.data
            } else if (response.data.length > 0) {
                response.year = new Date(response.release_date).getFullYear()
                data = response.data[0];
                submit();
            } else {
                toast.error("could not find data with name " + steamName.value)
            }
        } catch {
            toast.error("could not find data with name " + steamName.value)
        }
    }
</script>

<style scoped>
.game-selector p {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}
.game-selector:hover {
    background-color: #efefef;
}
</style>