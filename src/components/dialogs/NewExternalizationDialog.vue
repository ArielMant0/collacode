<template>
    <MiniDialog v-model="model" :title="completeTitle" @cancel="cancel" submit-text="" min-width="1400" close-icon>
        <template v-slot:text>
            <ExternalizationWidget v-if="ext" :item="ext" allow-edit @update="submit"/>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { computed, watch } from 'vue';
    import MiniDialog from '../dialogs/MiniDialog.vue';
    import { useApp } from '@/store/app';
    import ExternalizationWidget from '../externalization/ExternalizationWidget.vue';

    const model = defineModel();
    const props = defineProps({
        item: { type: Object, },
        title: {
            type: String,
            default: "Add new externalization"
        },
        tags: {
            type: Array,
            default: () => ([])
        }
    })

    const emit = defineEmits(["cancel", "submit"])

    const app = useApp()

    const ext = ref(null)

    function cancel() {
        emit("cancel")
        model.value = false;
    }
    function submit() {
        emit("submit", ext.value)
        model.value = false;
    }

    const completeTitle = computed(() => {
        return props.title + (props.item ? ' for '+props.item.name : '')
    })

    watch(() => props.item?.id, function() {
        if (props.item) {
            ext.value = {
                game_id: props.item.id,
                code_id: app.currentCode,
                name: "",
                description: "",
                categories: [],
                tags: app.addExtTag ? [{ tag_id: app.addExtTag }] : [],
            };
        }
    });
</script>