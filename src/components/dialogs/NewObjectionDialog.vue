<template>
    <MiniDialog v-model="model" title="Add new objection" no-actions @cancel="cancel" submit-text="" min-width="300px" close-icon>
        <template v-slot:text>
            <ObjectionWidget v-if="objection" :item="objection" @update="submit"/>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { watch } from 'vue';
    import { OBJECTION_STATUS, useApp } from '@/store/app';
    import MiniDialog from '../dialogs/MiniDialog.vue';
    import ObjectionWidget from '../objections/ObjectionWidget.vue';
    import { SOUND, useSounds } from '@/store/sounds';
    import DM from '@/use/data-manager';
    import { useToast } from 'vue-toastification';

    const model = defineModel();
    const emit = defineEmits(["cancel", "submit"])

    const app = useApp()
    const toast = useToast()
    const sounds = useSounds()

    const objection = ref(null)

    function cancel() {
        emit("cancel")
        model.value = false;
    }
    function submit() {
        emit("submit", objection.value)
        sounds.play(SOUND.OBJECTION)
        model.value = false;
    }
    watch(model, function(newval) {
        if (newval) {
            let ex = null

            if (app.addObjItem) {
                const all = DM.getDataItem("objections_items", app.addObjItem)
                ex = all.find(d => {
                    return d.resolved === null &&
                        (app.addObjTag === null && !d.tag_id || d.tag_id === app.addObjTag)
                })
            } else if (app.addEvTag) {
                const all = DM.getDataItem("objections_tags", app.addEvTag)
                ex = all.find(d => d.resolved === null && d.item_id === null)
            }

            if (ex) {
                toast.info("objection alread exists", { timeout: 2000 })
                app.setShowObjection(ex.id)
                objection.value = null
                cancel()
            } else {
                objection.value = {
                    code_id: app.currentCode,
                    user_id: app.activeUserId,
                    tag_id: app.addObjTag,
                    item_id: app.addObjItem,
                    status: OBJECTION_STATUS.OPEN,
                    explanation: "",
                    action: app.addObjType,
                    resolution: "",
                    resolved: null,
                    resolved_by: null
                }
            }
        } else {
            objection.value = null
        }
    });
</script>