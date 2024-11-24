<template>
    <v-list v-if="app.users">
        <v-list-item v-for="user in app.users"
            :key="user.id"
            :title="user.name"
            :subtitle="user.id + ' - ' + user.role"
            density="compact"
            hide-details
            @click="tryChangeUser(user)">

            <template v-slot:prepend>
                <v-card size="small"
                    density="comfortable"
                    elevation="0"
                    rounded="circle"
                    class="pa-1 mr-4 d-flex"
                    :color="getUseColor(user.id, user.color)">
                    <v-icon color="white">mdi-account</v-icon>
                </v-card>
            </template>
        </v-list-item>

        <v-list-item key="guest"
            title="guest"
            :value="-1"
            density="compact"
            hide-details>

            <template v-slot:prepend>
                <v-card size="small"
                    density="comfortable"
                    elevation="0"
                    rounded="circle"
                    class="pa-1 mr-4 d-flex"
                    :color="getUseColor(-1, '#000000')">
                    <v-icon color="white">mdi-account</v-icon>
                </v-card>
            </template>
        </v-list-item>
    </v-list>

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
                    <v-btn color="warning" @click="cancelLogin">cancel</v-btn>
                    <v-btn color="primary" @click="tryLogin">login</v-btn>
                </div>
            </v-card-text>
        </v-card>
    </v-dialog>
</template>

<script setup>
    import { useApp } from '@/store/app'
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const loader = useLoader()
    const toast = useToast()

    const userObj = {}
    const askPw = ref(false)
    const pw = ref("")

    function getUseColor(id, color) {
        return app.activeUserId !== null ?
            (app.activeUserId === id ? color : color + "66") :
            color
    }

    function tryChangeUser(user) {
        userObj.name = user.name;
        userObj.id = user.id;
        pw.value = ""
        askPw.value = true;
    }
    function cancelLogin() {
        askPw.value = false;
        pw.value = ""
    }

    function makeBasicAuth(name, pw) { return btoa(name+":"+pw) }
    async function tryLogin() {
        if (!userObj.name) { return toast.error("missing user name") }
        if (!pw.value) { return toast.error("missing password") }

        try {
            await loader.post("/login", null, null, { "Authorization": "Basic "+makeBasicAuth(userObj.name, pw.value)})
            toast.success("logged in succesfully")
            askPw.value = false;
            pw.value = ""
            app.setActiveUser(userObj.id)
        } catch (e) {
            toast.error("error with login")
            userObj.id = null;
            userObj.name = "";
        }
    }

</script>