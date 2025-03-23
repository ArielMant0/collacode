<template>
    <MiniDialog v-model="model" title="Add new externalization category" @cancel="cancel" submit-text="" min-width="40%" close-icon>
        <template v-slot:text>
            <MetaCategoryWidget v-if="extcat" :item="extcat" @update="submit"/>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { watch } from 'vue';
    import { useApp } from '@/store/app';
    import MiniDialog from '../dialogs/MiniDialog.vue';
    import MetaCategoryWidget from '../meta_items/MetaCategoryWidget.vue';

    const model = defineModel();
    const emit = defineEmits(["cancel", "submit"])

    const app = useApp()
    const extcat = ref(null)

    function cancel() {
        emit("cancel")
        model.value = false;
    }
    function submit() {
        emit("submit", extcat.value)
        model.value = false;
    }
    watch(model, function(newval) {
        if (newval) {
            extcat.value = {
                code_id: app.currentCode,
                dataset_id: app.ds,
                name: "",
                description: "",
                parent: app.addExtCatP ? app.addExtCatP : null,
            };
        } else {
            extcat.value = null
        }
    });
</script>