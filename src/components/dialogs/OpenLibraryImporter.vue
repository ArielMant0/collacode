<template>
    <MiniDialog v-model="model" submit-text="" @cancel="cancel" min-width="700" style="max-width: 80%;">
        <template v-slot:text>
            <div class="d-flex flex-column align-center">
                <div class="d-flex" style="width: 100%;">
                    <v-text-field v-model="isbn"
                        label="ISBN"
                        style="width: 100%;"
                        density="compact"
                        hide-details
                        hide-spin-buttons/>
                    <v-btn class="ml-2" @click="loadFromISBN">load</v-btn>
                </div>
                <div class="mt-2 mb-2">OR</div>
                <div class="d-flex" style="width: 100%;">
                    <v-text-field v-model="title"
                        density="compact"
                        label="Title"
                        style="width: 100%;"
                        hide-details
                        hide-spin-buttons/>
                    <v-btn class="ml-2" @click="loadFromTitle">load</v-btn>
                </div>
                <div class="mt-2 mb-2">OR</div>
                <div class="d-flex" style="width: 100%;">
                    <v-text-field v-model="author"
                        density="compact"
                        label="Author"
                        style="width: 100%;"
                        hide-details
                        hide-spin-buttons/>
                    <v-btn class="ml-2" @click="loadFromAuthor">load</v-btn>
                </div>
                <v-divider></v-divider>

                <v-sheet v-if="candidates" class="d-flex flex-wrap mt-4" style="max-width: 100%;">
                    <v-sheet v-for="c in candidates" :key="c.id"
                        @click="select(c)"
                        rounded="sm"
                        class="ma-1 pa-1 cursor-pointer item-selector"
                        :title="c.title+' ('+c.author+')'"
                        style="border: 1px solid lightgrey; max-width: 200px;"
                        >
                        <p class="text-caption">{{ c.author }}, {{ c.title }} ({{ c.year }})</p>
                        <v-img v-if="c.img"
                            :src="c.img"
                            :lazy-src="imgUrlS"
                            class="mt-2"
                            alt="Teaser Image"
                            width="100"
                            height="100"/>
                    </v-sheet>
                </v-sheet>
            </div>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { getBookFromAuthor, getBookFromISBN, getBookFromTitle } from '@/use/utility';
    import { useToast } from 'vue-toastification';
    import MiniDialog from './MiniDialog.vue';
    import imgUrlS from '@/assets/__placeholder__s.png';

    const emit = defineEmits(["load", "cancel"])

    const model = defineModel();
    const isbn = ref(0)
    const title = ref("")
    const author = ref("")
    const candidates = ref([])

    const toast = useToast();

    let data;

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
        isbn.value = "";
        title.value = ""
        author.value = ""
    }

    async function loadFromISBN() {
        const clear = isbn.value.replaceAll(/\s\-/gi, "");
        if (clear.length < 10) {
            return toast.error("invalid ISBN (too short)");
        }

        try {
            candidates.value = []
            const response = await getBookFromISBN(clear)

            if (response.data.length > 1) {
                candidates.value = response.data
            } else if (response.data.length > 0) {
                data = response.data[0]
                submit();
            } else {
                toast.error("could not find data with ISBN " + isbn.value)
            }
        } catch {
            toast.error("could not load data for ISBN " + isbn.value)
        }
    }

    async function loadFromTitle() {
        if (!title.value) return toast.error("missing title");

        try {
            candidates.value = []
            const response = await getBookFromTitle(title.value)

            if (response.data.length > 1) {
                candidates.value = response.data
            } else if (response.data.length > 0) {
                data = response.data[0]
                submit();
            } else {
                toast.error("could not find data with title " + title.value)
            }
        } catch {
            toast.error("could not find data with title " + title.value)
        }
    }

    async function loadFromAuthor() {
        if (!author.value) return toast.error("missing author");

        try {
            candidates.value = []
            const response = await getBookFromAuthor(author.value)

            if (response.data.length > 1) {
                candidates.value = response.data
            } else if (response.data.length > 0) {
                data = response.data[0]
                submit();
            } else {
                toast.error("could not find data with author " + author.value)
            }
        } catch {
            toast.error("could not find data with author " + author.value)
        }
    }
</script>

<style scoped>
.item-selector p {
    text-wrap: wrap;
}
.item-selector:hover {
    background-color: #efefef;
}
</style>