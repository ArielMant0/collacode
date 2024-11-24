<template>
    <div>
        <v-dialog v-model="model" width="auto" persistent>
            <v-card max-width="500" title="Who are you?" class="text-center">
                <template v-slot:text>
                    <v-list select-strategy="single-leaf" v-model:selected="selected" @update:selected="selectUser">
                        <v-list-item v-for="user in users"
                            :key="user.id"
                            :title="user.name"
                            :subtitle="user.role"
                            :value="user.id"
                            density="compact"
                            class="pr-2 pl-2 pt-1 pb-1"
                            hide-details>

                            <template v-slot:prepend>
                                <v-card size="small"
                                    density="comfortable"
                                    elevation="0"
                                    rounded="circle"
                                    class="pa-1 mr-4 d-flex"
                                    :color="user.color">
                                    <v-icon color="white">mdi-account</v-icon>
                                </v-card>
                            </template>
                        </v-list-item>

                        <v-list-item key="guest"
                            title="guest"
                            subtitle="proceed as guest"
                            :value="-1"
                            class="pr-2 pl-2 pt-1 pb-1"
                            density="compact"
                            hide-details>

                            <template v-slot:prepend>
                                <v-card size="small"
                                    density="comfortable"
                                    elevation="0"
                                    rounded="circle"
                                    class="pa-1 mr-4 d-flex"
                                    color="black">
                                    <v-icon color="white">mdi-account</v-icon>
                                </v-card>
                            </template>
                        </v-list-item>
                    </v-list>
                </template>
            </v-card>
        </v-dialog>

        <v-dialog v-model="askPw" width="auto" min-width="400">
            <v-card title="Login">
                <v-card-text>
                    <v-text-field :model-value="userObj.name"
                        label="user name"
                        readonly
                        density="compact"/>
                    <v-text-field v-model="pw"
                        label="enter your password"
                        type="password"
                        density="compact"/>

                    <div class="d-flex justify-space-between">
                        <v-btn color="warning" @click="cancel">cancel</v-btn>
                        <v-btn color="primary" @click="submit">login</v-btn>
                    </div>
                </v-card-text>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup>
    import { computed, onMounted, ref } from 'vue';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';

    const app = useApp();
    const loader = useLoader()
    const toast = useToast()

    const model = defineModel({ type: Boolean, required: true })

    const selected = ref([]);
    const askPw = ref(false);
    const pw = ref("");

    const { users } = storeToRefs(app);

    const userObj = computed(() => {
        if (selected.value.length === 0) return null
        if (selected.value[0] < 0) return { name: "guest" }
        return app.users.find(d => d.id === selected.value[0])
    })

    function selectUser() {
        if (selected.value && selected.value[0] >= 0) {
            askPw.value = true;
        } else {
            app.setActiveUser(-1)
        }
    }
    function cancel() { askPw.value = false; }

    function makeBasicAuth(name, pw) { return btoa(name+":"+pw) }
    async function submit() {
        try {
            await loader.post("/login", null, null, { "Authorization": "Basic "+makeBasicAuth(userObj.value.name, pw.value)})
            toast.success("logged in succesfully")
            askPw.value = false;
            pw.value = ""
            app.setActiveUser(selected.value[0])
        } catch {
            toast.error("error with login")
            selected.value = [];
        }
    }

    async function tryLoginRemember() {
        try {
            const uid = await loader.get("/user_login")
            app.setActiveUser(uid.id)
        } catch {
            console.debug("could not authenticate")
        }
    }

    onMounted(tryLoginRemember)
</script>