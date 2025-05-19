<template>
    <div>
        <div class="mb-8 d-flex align-center flex-column">
            <h3>Dataset Information</h3>

            <v-checkbox-btn v-model="existing"
                label="add to existing dataset"
                density="compact"
                class="mb-2"/>

            <div v-if="existing" class="d-flex mb-2">
                <v-select v-model="dsId"
                    style="min-width: 200px;"
                    :items="datasets"
                    hide-details
                    hide-spin-buttons
                    label="Dataset"
                    item-title="name"
                    item-value="id"
                    class="mr-1"
                    @update:model-value="app.setDataset(dsId)"
                    density="compact"/>

                <v-select v-if="ds && codes.length > 0"
                    style="min-width: 200px;"
                    v-model="selCode"
                    :items="codes"
                    hide-details
                    hide-spin-buttons
                    label="Code"
                    class="ml-1"
                    item-title="name"
                    item-value="id"
                    density="compact"/>
            </div>

            <DatasetWidget v-else ref="dw" @update="setDataSet" style="min-width: 800px;"/>
        </div>

        <div>
            <UploadTable :headers="itemHeaders" label="Item CSV File" @change="data => contents.items = data"/>
        </div>

        <div>
            <UploadTable :headers="tagHeaders" label="Tags CSV File" @change="data => contents.tags = data"/>
        </div>

        <div class="mb-4">
            <div class="mb-2">
                <b>Who are these user tags uploaded for?</b>
                <v-btn density="compact" class="ml-2" @click="openNewUserDialog" color="secondary" prepend-icon="mdi-plus">
                    add new user
                </v-btn>
            </div>
            <div class="d-flex text-caption mb-4">
                <v-chip v-for="(u, i) in users"
                    :class="i > 0 ? 'mr-1' : 'mr-1 ml-1'"
                    :color="selectedUser === u.name ? 'primary' : 'default'"
                    @click="selectedUser = u.name"
                    variant="flat"
                    size="small">
                    {{ u.name }}
                </v-chip>
            </div>
            <UploadTable :headers="userTagHeaders" label="User Tags CSV File" @change="data => contents.datatags = data"/>
        </div>

        <v-btn block color="primary" :disabled="numData === 0" @click="submit">submit</v-btn>

        <MiniDialog v-model="newUserDialog"
            close-icon
            @submit="addNewUser"
            submit-text="add"
            min-width="400">
            <template #text>
                <UserWidget @update="setNewUserData" show-password/>
            </template>
        </MiniDialog>
    </div>
</template>

<script setup>
    import { useLoader } from '@/use/loader';
    import { computed, reactive, ref, toRaw, watch } from 'vue'
    import UploadTable from './UploadTable.vue';
    import { useToast } from 'vue-toastification';
    import DatasetWidget from './DatasetWidget.vue';
    import { useRouter } from 'vue-router';
    import { capitalize } from '@/use/utility';
    import { useTimes } from '@/store/times';
    import { useSettings } from '@/store/settings';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import MiniDialog from './dialogs/MiniDialog.vue';

    const app = useApp()
    const loader = useLoader();
    const toast = useToast();
    const router = useRouter()
    const times = useTimes()
    const settings = useSettings()

    const { ds, datasets, codes } = storeToRefs(app)

    const dsId = ref(ds.value)
    const existing = ref(false)
    const selCode = ref(undefined)

    const newUserDialog = ref(false)
    const newUserData = ref({})
    const selectedUser = ref(-1)
    const users = ref([])

    const dw = ref(null)
    const dsObj = ref({})

    const contents = reactive({
        items: [],
        tags: [],
        datatags: [],
        users: [],
    });

    let toastId;

    const numData = computed(() => Object.values(contents).reduce((acc, d) => acc + (d ? d.length : 0), 0))

    const itemBaseHeaders = [
        { title: "ID", key: "id", type: "integer" },
        { title: "Name", key: "name", type: "string" },
        { title: "Description", key: "description", type: "string" },
        { title: "Teaser", key: "teaser", type: "image" },
        { title: "URL", key: "url", type: "url" },
    ];
    const itemHeaders = computed(() => {
        if (dsObj.value.schema && dsObj.value.schema.columns.length > 0) {
            return itemBaseHeaders.slice(0, 3)
                .concat(dsObj.value.schema.columns
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
    const userTagHeaders = [
        { title: "Item ID", key: "item_id", type: "integer" },
        { title: "Tag ID", key: "tag_id", type: "integer" }
    ];

    function setDataSet(obj) {
        dsObj.value = obj
        users.value = obj.users
    }

    function openNewUserDialog() {
        newUserData.value = {}
        newUserDialog.value = true;
    }
    function setNewUserData(user) {
        newUserData.value = user
    }
    function addNewUser() {
        if (!users.value.find(d => d.name === newUserData.value.name)) {
            users.value.push(newUserData.value)
            selectedUser.value = newUserData.value.name
        } else {
            toast.error("username " + newUserData.value.name + " already exists")
        }
    }

    async function submit() {

        if (numData === 0) {
            return toast.error("please upload data")
        }

        if ((existing.value && !ds.value)) {
            return toast.error("please select a dataset")
        }
        if ((existing.value && !selCode.value)) {
            return toast.error("please select a code")
        }
        if (users.length === 0 || !selectedUser.value) {
            return toast.error("please select at least 1 user")
        }

        if (!existing.value && (!dsObj.value || !dw.value.isValid())) {
            return toast.error("missing or invalid dataset")
        }

        const payload = {};
        if (contents.items.length > 0) {
            payload.items = contents.items
        }
        if (contents.tags.length > 0) {
            payload.tags = contents.tags;
        }
        if (contents.datatags.length > 0) {
            payload.datatags = contents.datatags;
        }

        if (existing.value) {
            payload.dataset_id = ds.value
            payload.code_id = selCode.value
        } else {
            payload.dataset = dsObj.value;
        }

        payload.users = users.value
        payload.dt_user = selectedUser.value

        try {
            settings.isLoading = true
            toastId = toast("importing data, this may take a while...", { timeout: false })
            await loader.post("import", payload)
            settings.isLoading = false
            toast.dismiss(toastId)
            toast.success("imported data - redirecting ..")
            if (existing.value && ds.value) {
                times.addAction("datasets", () => router.replace(`/?dsname=${app.dataset.name}`))
            } else {
                times.addAction("datasets", () => router.replace(`/?dsname=${payload.dataset.name}`))
            }
            times.addAction("datasets", () => times.needsReload("all"))
            times.needsReload("datasets")
        } catch(e) {
            console.error(e.toString())
            toast.error("error importing data")
        }
    }

    watch(existing, () => {
        selectedUser.value = ""
        if (existing.value) {
            users.value = app.users
        } else {
            users.value = []
        }
    })

    watch(ds, function() {
        selectedUser.value = ""
        if (existing.value) {
            users.value = app.users
        } else {
            users.value = []
        }
        times.needsReload("codes")
        times.needsReload("users")
        dsObj.value = toRaw(app.dataset)
    })

    watch(() => times.users, function() {
        if (existing.value) {
            users.value = app.users
        }
    })

</script>