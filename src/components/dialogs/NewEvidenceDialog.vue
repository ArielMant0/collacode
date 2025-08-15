<template>
    <MiniDialog v-model="model" title="Add new evidence" min-width="400" @cancel="cancel" close-icon no-actions>
        <template v-slot:text>
            <EvidenceWidget v-if="evidence" :item="evidence" @update="submit"/>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { ref, watch } from 'vue';
    import { useApp } from '@/store/app';
    import MiniDialog from '../dialogs/MiniDialog.vue';

    import EvidenceWidget from '../evidence/EvidenceWidget.vue';

    const model = defineModel();
    const emit = defineEmits(["cancel", "submit"])

    const app = useApp();

    const evidence = ref(null)

    function cancel() {
        emit("cancel")
        model.value = false;
    }
    function submit() {
        emit("submit", evidence.value)
        model.value = false;
    }
    watch(model, function(newval) {
        if (newval) {
            evidence.value = {
                code_id: app.currentCode,
                created_by: app.activeUserId,
                created: Date.now(),
                tag_id: app.addEvTag,
                item_id: app.addEvObj,
                filepath: app.addEvImg,
                type: app.addEvType,
                description: "",
            };
        } else {
            evidence.value = null
        }
    });

</script>