<template>
    <div>
        <div class="mb-8 d-flex align-center flex-column">
            <h3>Dataset Information</h3>

            <v-checkbox-btn v-model="existing"
                label="add to existing dataset"
                density="compact"
                class="mb-2"/>

            <div v-if="existing">
                <v-select v-model="ds"
                    style="min-width: 200px;"
                    :items="datasets"
                    hide-details
                    hide-spin-buttons
                    label="Dataset"
                    item-title="name"
                    item-value="id"
                    class="mb-1"
                    density="compact"/>

                <v-select v-if="ds && codes.length > 0"
                    style="min-width: 200px;"
                    v-model="selCode"
                    :items="codes"
                    hide-details
                    hide-spin-buttons
                    label="Code"
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
            <b>Who are these user tags uploaded for?</b>
            <div v-if="existing">
                <v-checkbox-btn v-model="newUser"
                    label="add new user"
                    density="compact"
                    class="mb-2"/>

                <div v-if="newUser">
                    <v-text-field v-model="userName"
                        label="User name"
                        hide-details
                        hide-spin-buttons
                        class="mb-1"
                        density="compact"/>
                    <v-text-field v-model="userPw"
                        label="User password"
                        hide-details
                        hide-spin-buttons
                        type="password"
                        class="mb-1"
                        density="compact"/>
                    <v-text-field v-model="userEmail"
                        label="User e-mail"
                        type="email"
                        hide-details
                        hide-spin-buttons
                        density="compact"/>
                </div>
                <div v-else class="d-flex text-caption mb-4">
                    <v-chip v-for="(u, i) in app.users"
                        :class="i > 0 ? 'pa-2 mr-1' : 'pa-2 mr-1 ml-1'"
                        :color="selectedUser === u.id ? u.color : 'default'"
                        @click="selectedUser = u.id"
                        variant="flat"
                        size="small"
                        density="compact">
                        {{ u.name }}
                    </v-chip>
                </div>
            </div>
            <div v-else-if="dsObj && dsObj.users" class="d-flex text-caption mb-4">
                <v-chip v-for="(uid, i) in dsObj.users"
                    :class="i > 0 ? 'pa-2 mr-1' : 'pa-2 mr-1 ml-1'"
                    :color="selectedUser === uid ? getUserColor(uid) : 'default'"
                    @click="selectedUser = uid"
                    variant="flat"
                    size="small"
                    density="compact">
                    {{ getUserName(uid) }}
                </v-chip>
            </div>
            <UploadTable :headers="userTagHeaders" label="User Tags CSV File" @change="data => contents.datatags = data"/>
        </div>

        <v-btn block color="primary" :disabled="numData === 0" @click="submit">submit</v-btn>
    </div>
</template>

<script setup>
    import { useLoader } from '@/use/loader';
    import { computed, reactive, ref, watch } from 'vue'
    import UploadTable from './UploadTable.vue';
    import { useToast } from 'vue-toastification';
    import DatasetWidget from './DatasetWidget.vue';
    import { useRouter } from 'vue-router';
    import { capitalize } from '@/use/utility';
    import { useTimes } from '@/store/times';
    import { useSettings } from '@/store/settings';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';

    const app = useApp()
    const loader = useLoader();
    const toast = useToast();
    const router = useRouter()
    const times = useTimes()
    const settings = useSettings()

    const { ds, datasets, codes } = storeToRefs(app)

    const existing = ref(false)
    const selCode = ref(undefined)

    const newUser = ref(false)
    const selectedUser = ref(-1)
    const userName = ref("")
    const userPw = ref("")
    const userEmail = ref("")

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

    function setDataSet(obj) { dsObj.value = obj }

    function getUserName(id) {
        const u = app.globalUsers.find(d => d.id === id);
        return u ? u.name : null;
    }

    function getUserColor(id) {
        const u = app.globalUsers.find(d => d.id === id);
        return u ? u.color : "black";
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

        if (!existing.value && (!dsObj.value || !dw.value.isValid())) {
            return toast.error("missing or invalid dataset")
        }

        const payload = {};
        contents.items.forEach(d => d.tags = d.tags.map(v => typeof v === "string" ? Number.parseInt(v) : v))
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
            if (!newUser.value) {
                if (!selectedUser.value) {
                    return toast.error("please select a user")
                }
                payload.dt_user = app.globalUsers.find(d => d.id === selectedUser.value).name
            } else {
                if (!userName.value || !userPw.value) {
                    return toast.error("missing user name or password")
                }
                payload.users = [{
                    name: userName.value,
                    password: userPw.value,
                    email: userEmail.value
                }]
                payload.dt_user = userName.value
            }
        } else {
            payload.dataset = dsObj.value;
        }

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

    watch(existing, () => selectedUser.value = -1)
    watch(newUser, () => {
        userName.value = ""
        userPw.value = ""
        userEmail.value = ""
    })
    watch(ds, function() {
        selectedUser.value = -1
        times.needsReload("codes")
        times.needsReload("users")
    })

</script>