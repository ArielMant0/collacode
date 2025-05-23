<template>
    <div style="width: fit-content; max-width: 100%;">

        <div style="text-align: center;" class="mt-4 mb-4">
            <v-btn prepend-icon="mdi-plus" color="secondary" @click="prepareNewProject">add project</v-btn>
        </div>

        <NewDatasetDialog v-model="newPrjDialog"/>

        <v-data-table :items="allProjects" :headers="projectHeaders" density="compact" multi-sort style="max-height: 80vh;">

            <template v-slot:item.actions="{ item }">
                <div>
                    <v-btn icon="mdi-content-save" :disabled="!item.changes" density="compact" variant="text" @click="saveChanges(item)"/>
                    <v-btn class="ml-1" icon="mdi-undo-variant" :disabled="!item.changes" density="compact" variant="text" @click="discardChanges(item)"/>
                    <v-btn class="ml-1" icon="mdi-delete" density="compact" variant="text" color="error" @click="askDeleteProject(item)"/>
                </div>
            </template>

            <template v-slot:item.name="{ item }">
                <input v-model="item.name" placeholder="project name" @update:model-value="update(item)" class="editable-text">
            </template>

            <template v-slot:item.description="{ item }">
                <textarea v-model="item.description"
                    style="width: 100%;"
                    placeholder="project description"
                    @update:model-value="update(item)"
                    class="editable-text"></textarea>
            </template>

            <template v-slot:item.users="{ item }">
                <div class="mt-1 mb-1">
                    <v-chip v-for="u in item.users"
                        closable
                        class="text-caption mr-1"
                        :color="app.getUserColor(u)"
                        @click:close="deleteProjectUser(item, u)"
                        density="compact">
                        {{ app.getUserName(u) }}
                    </v-chip>

                    <div v-if="otherUsers(item).length > 0" class="d-flex align-center mt-2">
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
                            :items="otherUsers(item)"/>

                        <v-btn
                            class="ml-1"
                            color="primary"
                            icon="mdi-plus"
                            :disabled="!item._add || item._add.length === 0"
                            @click="addProjectUsers(item)"
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
            @cancel="askDeleteProject(null)"
            @submit="confirmDeleteProject">
            <template v-slot:text>
                <div v-if="dialog.project" class="d-flex flex-column align-center">
                    <p class="mb-2">Delete project <b>{{ dialog.project.name }}</b>?</p>
                </div>
            </template>
        </MiniDialog>
    </div>
</template>

<script setup>
    import MiniDialog from '@/components/dialogs/MiniDialog.vue'
    import NewDatasetDialog from '@/components/dialogs/NewDatasetDialog.vue'
    import { useApp } from '@/store/app'
    import { useTimes } from '@/store/times'
    import { deleteDatasets, updateDatasets } from '@/use/data-api'
    import { storeToRefs } from 'pinia'
    import { computed, onMounted, reactive, watch } from 'vue'
    import { useToast } from 'vue-toastification'

    const times = useTimes()
    const toast = useToast()
    const app = useApp()
    const { datasets } = storeToRefs(app)

    const projectHeaders = [
        { key: "actions", title: "Actions", width: 150 },
        { key: "id", title: "Id", width: 100 },
        { key: "name", title: "Name" },
        { key: "description", title: "Description", width: 300  },
        { key: "users", title: "Users" },
    ]

    const allProjects = ref([])
    const dialog = reactive({
        show: false,
        project: null
    })

    const newPrjDialog = ref(false)

    const anyChanges = computed(() => allProjects.value.some(d => d.changes))

    function read() {
        allProjects.value = datasets.value.map(d => {
            const obj = {
                _orig: Object.assign({}, d),
                _add: [],
                changes: false
            }
            Object.assign(obj, d)
            obj.users = d.users.slice()
            return obj
        })
    }
    function update(project) {
        const basic = project.name !== project._orig.name ||
            project.description !== project._orig.description

        if (basic) {
            project.changes = true
            return
        }

        const setA = new Set(project.users)
        const setB = new Set(project._orig.users)
        const int = setA.intersection(setB)
        project.changes = int.size !== setA.size || int.size !== setB.size
    }

    function discardChanges(project) {
        if (!project.changes) return
        project.name = project._orig.name
        project.description = project._orig.description
        project.users = project._orig.users.slice()
        project.changes = false
    }
    function discardAllChanges() {
        allUsers.value.forEach(user => discardChanges(user))
    }

    async function saveChanges(project) {

        if (!project.name || project.name.length === 0) {
            return toast.error("invalid project name")
        }

        if (!project.description || project.description.length === 0) {
            return toast.error("invalid project description")
        }

        try {
            await updateDatasets([{
                id: project.id,
                name: project.name,
                description: project.description,
                users: project.users
            }])
            toast.success(`updated project ${project.name}`)
            project.changes = false
            times.needsReload("datasets")
        } catch (e) {
            toast.error(`error project user ${project.name}`)
        }
    }

    async function saveAllChanges() {

        const projects = []
        allProjects.value.forEach(project => {

            if (!project.changes) return

             if (!project.name || project.name.length === 0) {
                return toast.error("invalid project name")
            }

            if (!project.description || project.description.length === 0) {
                return toast.error("invalid project description")
            }

            projects.push({
                id: project.id,
                name: project.name,
                description: project.description,
                users: project.users
            })
        })

        if (projects.length > 0) {
            try {
                await updateDatasets(projects)
                toast.success(`updated ${projects.length} projects`)
                allProjects.value.forEach(u => u.changes = false)
                times.needsReload("datasets")
            } catch (e) {
                toast.error("error updating projects")
            }
        }

    }

    function askDeleteProject(project=null) {
        dialog.project = project
        dialog.show = project !== null
    }
    async function confirmDeleteProject() {
        if (!dialog.project) return

        try {
            await deleteDatasets([dialog.project.id])
            toast.success(`deleted project ${dialog.project.name}`)
            dialog.show = false
            dialog.project = null
            times.needsReload("datasets")
        } catch (e) {
            toast.error(`error deleting project ${dialog.project.name}`)
        }
    }

    function otherUsers(project) {
        return app.globalUsers.filter(d => !project.users.includes(d.id))
    }

    function addProjectUsers(project) {
        if (!project._add || project._add.length === 0) return
        project.users = project.users.concat(project._add)
        project._add = []
        update(project)
    }
    function deleteProjectUser(project, id) {
        project.users = project.users.filter(d => d !== id)
        update(project)
    }

    function prepareNewProject() {
        newPrjDialog.value = true
    }

    onMounted(read)

    watch(datasets, read)
    watch(() => Math.max(times.all, times.datasets), read)

</script>

<style scoped>
.editable-text {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding-left: 4px;
    padding-right: 4px;
}
</style>