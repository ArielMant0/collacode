<template>
    <div>
        <v-dialog v-model="model" width="auto" persistent>
            <v-card max-width="500" title="Who are you?" class="text-center">
                <v-card-text>
                    <v-btn color="default" block class="mb-2" @click="tryGuest">enter as guest</v-btn>
                    <v-btn color="primary" block @click="tryLogin">login</v-btn>
                </v-card-text>
            </v-card>
        </v-dialog>

        <v-dialog v-model="askPw" width="auto" min-width="400">
            <v-card title="Login">
                <v-card-text>
                    <v-form>

                        <v-text-field v-model="name"
                            label="user name"
                            autocomplete="username"
                            hide-spin-buttons
                            density="compact"/>
                        <v-text-field v-model="pw"
                            label="password"
                            type="password"
                            autocomplete="password"
                            hide-spin-buttons
                            @keydown="pwKeyDown"
                            density="compact"/>

                        <div class="d-flex justify-space-between">
                            <v-btn color="warning" @click="cancel">cancel</v-btn>
                            <v-btn color="primary" @click="submit">login</v-btn>
                        </div>
                    </v-form>
                </v-card-text>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup>
    import { onMounted, ref } from 'vue';
    import { useApp } from '@/store/app';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';
    import Cookies from 'js-cookie';

    const app = useApp();
    const loader = useLoader()
    const toast = useToast()

    const model = defineModel({ type: Boolean, required: true })

    const askPw = ref(false);

    const pw = ref("");
    const name = ref("")

    function tryGuest() {
        app.setActiveUser(-1)
        Cookies.set("isGuest", true, { expires: 365 })
    }
    function tryLogin() {
        name.value = ""
        pw.value = ""
        askPw.value = true;
    }
    function cancel() {
        askPw.value = false;
        name.value = ""
        pw.value = ""
    }

    function pwKeyDown(event) {
        if (event.code === "Enter") {
            submit()
        }
    }

    function makeBasicAuth(name, pw) { return btoa(name+":"+pw) }
    async function submit() {
        if (name.value.length === 0) {
            return toast.error("missing user name")
        }
        if (pw.value.length === 0) {
            return toast.error("missing password")
        }

        try {
            const uid = await loader.post("/login", null, null, { "Authorization": "Basic "+makeBasicAuth(name.value, pw.value)})
            toast.success("logged in succesfully")
            askPw.value = false;
            app.setActiveUser(uid.id)
            Cookies.remove("isGuest")
        } catch {
            toast.error("error with login")
        }
        name.value = ""
        pw.value = ""
    }

    async function tryLoginRemember() {
        try {
            const uid = await loader.get("/user_login")
            app.setActiveUser(uid.id)
            Cookies.remove("isGuest")
        } catch {
            console.debug("could not authenticate")
            if (Cookies.get("isGuest")) {
                tryGuest()
            }
        }
    }

    onMounted(tryLoginRemember)
</script>