<template>
    <MiniDialog v-model="model" :title="title" min-width="900" close-icon>
        <template v-slot:text>
            <DatasetWidget @update="setObj"/>
        </template>

        <template v-slot:actions>
            <v-btn color="warning" @click="cancel">cancel</v-btn>
            <v-btn class="ml-2" color="primary" @click="submit">create</v-btn>
        </template>
    </MiniDialog>
</template>

<script setup>
    import MiniDialog from './MiniDialog.vue';
    import { useToast } from 'vue-toastification';
    import { useTimes } from '@/store/times';
    import { addDatasets } from '@/use/data-api';
    import DatasetWidget from '../DatasetWidget.vue';

    const toast = useToast()
    const times = useTimes()

    const model = defineModel()
    const props = defineProps({
        title: {
            type: String,
            default: "Create new project"
        },
    })

    const emit = defineEmits(["cancel", "submit"])

    let dsObj = null;

    function setObj(obj) {
        dsObj = obj
    }

    function cancel() {
        emit("cancel")
        model.value = false;
    }
    async function submit() {
        try {
            if (!dsObj) {
                return toast.error("missing data")
            }

            if (!dsObj.name || dsObj.name.length === 0) {
                return toast.error("missing project name")
            }
            if (!dsObj.description || dsObj.description.length === 0) {
                return toast.error("missing project description")
            }
            if (!dsObj.item_name || dsObj.item_name.length === 0) {
                return toast.error("missing item name")
            }

            if (!dsObj.code_name || dsObj.code_name.length === 0) {
                return toast.error("missing code name")
            }
            if (!dsObj.code_desc || dsObj.code_desc.length === 0) {
                return toast.error("missing code description")
            }

            if (!dsObj.users || dsObj.users.length === 0) {
                return toast.error("select at least 1 user for this project")
            }

            await addDatasets([dsObj])
            toast.success("created project " + dsObj.name)
            emit("submit", dsObj)
            model.value = false;
            times.needsReload("datasets")
        } catch {
            toast.error("error creating project " + dsObj.name)
        }
    }

</script>