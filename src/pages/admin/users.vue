<template>
    <div style="width: fit-content; max-width: 100%;">

        <div style="text-align: center;" class="mt-4 mb-4">
            <v-btn prepend-icon="mdi-plus" color="secondary" @click="prepareNewUser">add user</v-btn>
        </div>

        <MiniDialog v-model="newUserDialog"
            close-icon
            title="Add User"
            @submit="addNewUser"
            submit-text="add"
            min-width="400">
            <template #text>
                <UserWidget @update="setNewUserData" show-password/>
            </template>
        </MiniDialog>

        <v-data-table :items="allUsers" :headers="userHeaders" density="compact" multi-sort style="max-height: 80vh;">

            <template v-slot:item.actions="{ item }">
                <div>
                    <v-btn icon="mdi-content-save" :disabled="!item.changes" density="compact" variant="text" @click="saveChanges(item)"/>
                    <v-btn class="ml-1" icon="mdi-undo-variant" :disabled="!item.changes" density="compact" variant="text" @click="discardChanges(item)"/>
                    <v-btn class="ml-1" icon="mdi-delete" density="compact" variant="text" color="error" @click="askDeleteUser(item)"/>
                </div>
            </template>

            <template v-slot:item.name="{ item }">
                <input v-model="item.name" placeholder="username" @update:model-value="update(item)" class="editable-text">
            </template>

            <template v-slot:item.role="{ item }">
                <v-select v-model="item.role"
                    density="compact"
                    hide-details
                    hide-spin-buttons
                    :items="userRoles"
                    @update:model-value="update(item)"/>
            </template>

            <template v-slot:item.email="{ item }">
                <input v-model="item.email" placeholder="email address" @update:model-value="update(item)" class="editable-text">
            </template>

            <template v-slot:item.projects="{ item }">
                <div>
                    <v-chip v-for="p in item.projects"
                        closable
                        class="text-caption mr-1"
                        @click:close="deleteProjectUser(item, p)"
                        density="compact">
                        {{ app.getDatasetName(p) }}
                    </v-chip>

                    <div v-if="otherProjects(item).length > 0" class="d-flex align-center mt-2">
                        <v-select v-model="item._add"
                            multiple
                            density="compact"
                            clearable
                            class="text-caption"
                            hide-details
                            hide-spin-buttons
                            item-title="name"
                            item-value="id"
                            style="max-width: 300px;"
                            :items="otherProjects(item)"/>

                        <v-btn
                            class="ml-1"
                            color="primary"
                            icon="mdi-plus"
                            :disabled="!item._add || item._add.length === 0"
                            @click="addProjectUser(item)"
                            density="compact"/>
                    </div>
                </div>
            </template>

             <template v-slot:footer.prepend>
                <div class="mr-auto">
                    <v-btn
                        prepend-icon="mdi-content-save"
                        :color="anyChanges ? 'primary' : 'default'"
                        :disabled="!anyChanges"
                        density="comfortable"
                        @click="saveAllChanges">
                        save changes
                    </v-btn>

                        <v-btn
                        prepend-icon="mdi-undo-variant"
                        :color="anyChanges ? 'error' : 'default'"
                        :disabled="!anyChanges"
                        density="comfortable"
                        class="ml-1"
                        @click="discardAllChanges">
                        discard changes
                    </v-btn>
                </div>
            </template>
        </v-data-table>

        <MiniDialog v-model="dialog.show"
            @cancel="askDeleteUser(null)"
            @submit="confirmDeleteUser">
            <template v-slot:text>
                <div v-if="dialog.user" class="d-flex flex-column align-center">
                    <p class="mb-2">Delete user <b>{{ dialog.user.name }}</b>?</p>
                </div>
            </template>
        </MiniDialog>
    </div>
</template>

<script setup>
    import MiniDialog from '@/components/dialogs/MiniDialog.vue'
    import UserWidget from '@/components/UserWidget.vue'
    import { useApp } from '@/store/app'
    import { useTimes } from '@/store/times'
    import { addUsers, deleteUsers, updateUsers } from '@/use/data-api'
    import { isValidUserName } from '@/use/utility'
    import { storeToRefs } from 'pinia'
    import { computed, onMounted, reactive, watch } from 'vue'
    import { useToast } from 'vue-toastification'

    const times = useTimes()
    const toast = useToast()
    const app = useApp()
    const { globalUsers } = storeToRefs(app)

    const userRoles = ["collaborator", "admin"]
    const userHeaders = [
        { key: "actions", title: "Actions", width: 150 },
        { key: "id", title: "Id", width: 100 },
        { key: "name", title: "Name" },
        { key: "email", title: "E-Mail" },
        { key: "role", title: "Role", width: 300 },
        { key: "projects", title: "Projects", width: 350 },
    ]

    const allUsers = ref([])
    const dialog = reactive({
        show: false,
        user: null
    })

    const newUserDialog = ref(false)
    const newUserData = ref({})

    const anyChanges = computed(() => allUsers.value.some(d => d.changes))

    function read() {
        allUsers.value = globalUsers.value.map(d => {
            const obj = {
                _orig: Object.assign({}, d),
                _add: [],
                changes: false
            }
            Object.assign(obj, d)
            obj.projects = d.projects.slice()
            return obj
        })
    }
    function update(user) {
        const basic = user.name !== user._orig.name ||
            user.email !== user._orig.email ||
            user.role !== user._orig.role

        if (basic) {
            user.changes = true
            return
        }

        const setA = new Set(user.projects)
        const setB = new Set(user._orig.projects)
        const int = setA.intersection(setB)
        user.changes = int.size !== setA.size || int.size !== setB.size
    }

    function otherProjects(user) {
        return app.datasets.filter(d => !user.projects.includes(d.id))
    }

    function discardChanges(user) {
        if (!user.changes) return
        user.name = user._orig.name
        user.email = user._orig.email
        user.role = user._orig.role
        user.projects = user._orig.projects.slice()
        user.changes = false
    }
    function discardAllChanges() {
        allUsers.value.forEach(user => discardChanges(user))
    }

    async function saveChanges(user) {

        if (!user.name || user.name.length === 0 || !isValidUserName(user.name)) {
            return toast.error("invalid user name")
        }

        if (!user.role || !userRoles.includes(user.role)) {
            return toast.error("invalid user role")
        }

        try {
            await updateUsers([{
                id: user.id,
                name: user.name,
                role: user.role,
                email: user.email,
                projects: user.projects
            }])
            toast.success(`updated user ${user.name}`)
            user.changes = false
            times.needsReload("users")
        } catch (e) {
            toast.error(`error updating user ${user.name}`)
        }
    }

    async function saveAllChanges() {

        const users = []
        allUsers.value.forEach(user => {

            if (!user.changes) return

            if (!user.name || user.name.length === 0 || !isValidUserName(user.name)) {
                return toast.error("invalid user name for " + user.name)
            }

            if (!user.role || !userRoles.includes(user.role)) {
                return toast.error("invalid user role for " + user.name)
            }

            users.push({
                id: user.id,
                name: user.name,
                role: user.role,
                email: user.email,
                projects: user.projects
            })
        })

        if (users.length > 0) {
            try {
                await updateUsers(users)
                toast.success(`updated ${users.length} user`)
                allUsers.value.forEach(u => u.changes = false)
                times.needsReload("users")
            } catch (e) {
                toast.error("error updating user")
            }
        }

    }

    function askDeleteUser(user=null) {
        dialog.user = user
        dialog.show = user !== null
    }
    async function confirmDeleteUser() {
        if (!dialog.user) return

        try {
            await deleteUsers([dialog.user.id])
            toast.success(`deleted user ${dialog.user.name}`)
            dialog.show = false
            dialog.user = null
            times.needsReload("users")
        } catch (e) {
            toast.error(`error deleting user ${dialog.user.name}`)
        }
    }

    function addProjectUser(user) {
        if (!user._add || user._add.length === 0) return
        user.projects = user.projects.concat(user._add)
        user._add = []
        update(user)
    }
    function deleteProjectUser(user, id) {
        user.projects = user.projects.filter(d => d !== id)
        update(user)
    }

    function prepareNewUser() {
        newUserDialog.value = true
    }
    function setNewUserData(user) {
        newUserData.value = user
    }
    async function addNewUser() {
        if (!newUserData.value) return

        const name = newUserData.value.name
        if (!name || name.length === 0 || !isValidUserName(name)) {
            return toast.error("invalid user name")
        }

        const pw = newUserData.value.password
        if (!name || name.length === 0 || !isValidUserName(name)) {
            return toast.error("invalid user name")
        }

        const role = newUserData.value.role
        if (!role || !userRoles.includes(role)) {
            return toast.error("invalid user role")
        }

        try {
            await addUsers([newUserData.value])
            toast.success(`added user ${newUserData.value.name}`)
            dialog.show = false
            dialog.user = null
            times.needsReload("users")
        } catch (e) {
            toast.error(`error deleting user ${newUserData.value.name}`)
        }
        if (newUserData.value && isValidUserName(newUserData.value.name)) {
            users.push(newUserData.value)
            newUserData.value = {}
            update()
        }
    }

    onMounted(read)

    watch(globalUsers, read)
    watch(() => Math.max(times.all, times.users), read)

</script>

<style scoped>
.editable-text {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding-left: 4px;
    padding-right: 4px;
}
</style>