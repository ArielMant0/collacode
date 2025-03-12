<template>
    <MiniDialog v-model="model" title="Add new objection" no-actions @cancel="cancel" submit-text="" min-width="300px" close-icon>
        <template v-slot:text>
            <ObjectionWidget v-if="objection" :item="objection" @update="submit"/>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { watch } from 'vue';
    import { OBJECTION_ACTIONS, useApp } from '@/store/app';
    import MiniDialog from '../dialogs/MiniDialog.vue';
    import ObjectionWidget from '../objections/ObjectionWidget.vue';

    const model = defineModel();
    const emit = defineEmits(["cancel", "submit"])

    const app = useApp()
    const objection = ref(null)

    function cancel() {
        emit("cancel")
        model.value = false;
    }
    function submit() {
        emit("submit", objection.value)
        model.value = false;
    }
    watch(model, function(newval) {
        if (newval) {
            objection.value = {
                code_id: app.currentCode,
                user_id: app.activeUserId,
                tag_id: app.addObjTag,
                item_id: app.addObjItem,
                explanation: "",
                action: OBJECTION_ACTIONS.DISCUSS
            };
        } else {
            objection.value = null
        }
    });
</script>