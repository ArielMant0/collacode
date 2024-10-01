<template>
    <MiniDialog v-model="model" @cancel="cancel" @submit="create" submit-text="create" title="Create new externalization category">
        <template v-slot:text>
            <div>
                <v-text-field
                    v-model="name"
                    density="compact"
                    label="Name"
                    class="mb-1"
                    hide-details
                    hide-spin-buttons/>
                <v-select
                    v-model="parent"
                    :items="cats"
                    label="Parent Category"
                    item-title="name"
                    item-value="id"
                    density="compact"
                    hide-details
                    hide-spin-buttons
                    class="mb-1"
                    />
                <v-textarea
                    v-model="desc"
                    density="compact"
                    label="Description"
                    hide-details
                    hide-spin-buttons/>
            </div>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { createExtCategory } from '@/use/utility';
    import MiniDialog from './MiniDialog.vue';
    import { useToast } from 'vue-toastification';
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';

    const model = defineModel();
    const name = ref("")
    const desc = ref("")
    const parent = ref(null)

    const emit = defineEmits(["cancel", "create"])

    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    function cancel() {
        emit("cancel")
        model.value = false;
    }
    async function create() {
        try {
            await createExtCategory(
                app.ds,
                app.currentCode,
                {
                    name: name.value,
                    description: desc.value,
                    parent: parent.value ? parent.value : null,
                    created: Date.now(),
                    created_by: app.activeUserId
                }
            )
            toast.success("created new externalization category")
            emit("create")
            model.value = false;
            times.needsReload("ext_categories")
        } catch {
            toast.error("error creating new category")
        }
    }
</script>