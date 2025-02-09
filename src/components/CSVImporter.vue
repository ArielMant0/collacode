<template>
    <div>
        <div class="mb-8 d-flex align-center flex-column">
            <h3>Dataset Information</h3>
            <DatasetWidget ref="dw" @update="setDataSet" style="min-width: 800px;"/>
        </div>

        <div>
            <UploadTable :headers="itemHeaders" label="Item CSV File" @change="data => contents.items = data"/>
        </div>

        <div class="mb-4">
            <UploadTable :headers="tagHeaders" label="Tags CSV File" @change="data => contents.tags = data"/>
        </div>

        <v-btn block color="primary" :disabled="numData === 0" @click="submit">submit</v-btn>
    </div>
</template>

<script setup>
    import { useLoader } from '@/use/loader';
    import { computed, reactive, ref } from 'vue'
    import UploadTable from './UploadTable.vue';
    import { useToast } from 'vue-toastification';
    import DatasetWidget from './DatasetWidget.vue';
    import { useRouter } from 'vue-router';
    import { capitalize } from '@/use/utility';
    import { useTimes } from '@/store/times';
    import { useSettings } from '@/store/settings';

    const loader = useLoader();
    const toast = useToast();
    const router = useRouter()
    const times = useTimes()
    const settings = useSettings()

    const dw = ref(null)
    const ds = ref({})

    const contents = reactive({
        items: [],
        tags: []
    });

    let toastId;

    const numData = computed(() => Object.values(contents).reduce((acc, d) => acc + (d ? d.length : 0), 0))

    const itemBaseHeaders = [
        { title: "ID", key: "id", type: "integer" },
        { title: "Name", key: "name", type: "string" },
        { title: "Description", key: "description", type: "string" },
        { title: "Teaser", key: "teaser", type: "image" },
        { title: "URL", key: "url", type: "url" },
        { title: "Tags", key: "tags", type: "array" },
    ];
    const itemHeaders = computed(() => {
        if (ds.value.schema && ds.value.schema.columns.length > 0) {
            return itemBaseHeaders.slice(0, 3)
                .concat(ds.value.schema.columns
                    .map(d => ({ title: capitalize(d.name), key: d.name, type: d.type }))
                    .filter(d => d.key.length > 0)
                )
                .concat(itemBaseHeaders.slice(3))
        }
        return itemBaseHeaders
    })
    const tagHeaders = [
        { title: "ID", key: "id", type: "integer" },
        { title: "Name", key: "name", type: "string" },
        { title: "Description", key: "description", type: "string" },
        { title: "Parent", key: "parent", type: "integer", default: null },
    ];

    function setDataSet(obj) { ds.value = obj }

    async function submit() {

        if (contents.items.length === 0) {
            return toast.warning("missing data")
        }
        if (contents.tags.length === 0) {
            return toast.warning("missing tags")
        }
        if (!ds.value || !dw.value.isValid()) {
            return toast.warning("missing or invalid dataset information")
        }

        const payload = {};
        contents.items.forEach(d => d.tags = d.tags.map(v => typeof v === "string" ? Number.parseInt(v) : v))
        payload.items = contents.items
        payload.tags = contents.tags;
        payload.dataset = ds.value

        try {
            settings.isLoading = true
            toastId = toast("importing data, this may take a while...", { timeout: false })
            await loader.post("import", payload)
            settings.isLoading = false
            toast.dismiss(toastId)
            toast.success("imported data - redirecting ..")
            times.addAction("datasets", () => router.replace(`/?dsname=${ds.value.name}`))
            times.needsReload("datasets")
        } catch(e) {
            console.error(e.toString())
            toast.error("error importing data")
        }
    }

</script>