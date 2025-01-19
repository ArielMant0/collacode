<template>
    <MiniDialog v-model="model" submit-text="" @cancel="cancel" min-width="700" style="max-width: 80%;">
        <template v-slot:text>
            <div class="d-flex flex-column align-center">
                <div class="d-flex" style="width: 100%;">
                    <v-number-input v-model="isbn"
                        controlVariant="stacked"
                        label="ISBN"
                        :min="0"
                        :step="1"
                        style="width: 100%;"
                        density="compact"
                        hide-details
                        hide-spin-buttons
                    />
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
                        class="mr-1 pa-2 cursor-pointer item-selector"
                        :title="c.title+' ('+c.author+')'"
                        style="border: 1px solid lightgrey;"
                        >
                        <p class="text-caption">{{ c.author }}, {{ c.title }} - ({{ c.year }})</p>
                    </v-sheet>
                </v-sheet>
            </div>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { getBookFromAuthor, getBookFromTitle } from '@/use/utility';
    import { useToast } from 'vue-toastification';
    import MiniDialog from './MiniDialog.vue';

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
            data = null;
            candidates.value = []
            isbn.value = 0;
            title.value = ""
            author.value = ""
        } else {
            toast.error("missing data")
        }
    }
    function cancel() {
        emit("cancel")
        model.value = false;
        data = null;
        candidates.value = []
        isbn.value = 0;
        title.value = ""
        author.value = ""
    }
    function select(game) {
        data = game;
        submit();
    }

    async function loadFromISBN() {
        if ((""+isbn.value).length < 10) {
            return toast.error("invalid ISBN (too short)");
        }

        try {
            candidates.value = []
            const response = await getBookFromTitle(isbn.value)

            if (response.data.length > 1) {
                candidates.value = response.data
            } else if (response.data.length > 0) {
                data = response.data
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
            console.log(response)

            if (response.data.length > 1) {
                candidates.value = response.data
            } else if (response.data.length > 0) {
                data = response.data
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
                data = response.data
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