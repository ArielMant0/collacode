<template>
    <MiniDialog v-model="model" title="Add new tag" @cancel="cancel" @submit="submit" min-width="1000" no-actions close-icon>
        <template v-slot:text>
            <TagWidget
                :data="newTag"
                parents="tags"
                name-label="New Tag Name"
                desc-label="New Tag Description"
                button-label="add"
                button-icon="mdi-plus"
                can-edit
                @update="submit"
                @cancel="cancel"/>
        </template>
    </MiniDialog>
</template>

<script setup>
    import TagWidget from '../tags/TagWidget.vue';
    import MiniDialog from './MiniDialog.vue';
    import { useApp } from '@/store/app';

    const model = defineModel()
    const emit = defineEmits(["cancel", "submit"])

    const app = useApp()

    const newTag = ref(null)

    function cancel() {
        emit("cancel")
        model.value = false;
    }
    function submit() {
        emit("submit", newTag.value)
        model.value = false;
    }
    watch(model, function(newval) {
        if (newval) {
            newTag.value = {
                code_id: app.currentCode,
                dataset: app.ds,
                name: "",
                description: "",
                parent: app.addTag !== null && app.addTag >= 0 ? app.addTag : null,
                name: "",
                created_by: app.activeUserId,
                is_leaf: true
            };
        } else {
            newTag.value = null
        }
    });
</script>