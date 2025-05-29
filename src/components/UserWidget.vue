<template>
    <v-form>
        <v-text-field v-model="name"
            hide-spin-buttons
            :rules="[
                v => v.length >= 5 || 'name must be at least 5 characters',
                v => isValidUserName(v) || 'name contains invalid characters',
                v => !app.hasUserName(v) || 'name already taken'
            ]"
            @update:model-value="update"
            density="compact">

            <template #label>
                <span class="text-red"><b>*</b></span>Name
            </template>
        </v-text-field>
        <v-text-field  v-if="showPassword"
            v-model="pw"
            hide-spin-buttons
            @update:model-value="update"
            :rules="[
                v => v.length >= 5 || 'password must be at least 5 characters',
                v => isValidUserPassword(v) || 'password contains invalid characters'
            ]"
            :append-inner-icon="showPw ? 'mdi-eye' : 'mdi-eye-off'"
            @click:append-inner="showPw = !showPw"
            :type="showPw ? 'text' : 'password'"
            density="compact">

            <template #label>
                <span class="text-red"><b>*</b></span>Password
            </template>
        </v-text-field>
        <v-select v-model="role"
            density="compact"
            hide-spin-buttons
            hide-details
            class="mb-2"
            :items="USER_ROLES"
            @update:model-value="update">
            <template #label>
                <span class="text-red"><b>*</b></span>Role
            </template>
        </v-select>
        <v-text-field v-model="email"
            label="E-mail"
            type="email"
            @update:model-value="update"
            hide-spin-buttons
            hide-details
            density="compact"/>
    </v-form>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { isValidUserName, isValidUserPassword } from '@/use/utility';
    import { ref, watch } from 'vue';

    const app = useApp()

    const props = defineProps({
        user: {
            type: Object,
            default: () => ({
                name: "",
                password: "",
                email: "",
                role: "collaborator"
            })
        },
        showPassword: {
            type: Boolean,
            default: false
        }
    })

    const USER_ROLES = ["guest", "collaborator", "admin"]

    const name = ref("")
    const email = ref("")
    const role = ref(USER_ROLES[1])
    const pw = ref("")

    const showPw = ref(false)

    const emit = defineEmits(["update", "remove"])

    function makeUser() {
        const u = Object.assign({}, props.user)
        u.name = name.value
        u.email = email.value
        u.role = role.value
        if (props.showPassword) {
            u.password = pw.value;
        }
        return u
    }
    function update() {
        emit("update", makeUser())
    }

    function read() {
        name.value = props.user.name ? props.user.name : ""
        email.value = props.user.email ? props.user.email : ""
        role.value = props.user.role ? props.user.role : USER_ROLES[1]
        pw.value = ""
    }

    watch(props, read)
</script>