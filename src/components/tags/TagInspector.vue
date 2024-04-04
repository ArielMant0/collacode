<template>
    <div class="d-flex flex-start align-start">
        <TagTiles :source="source" @click="onClick" :selected="data.selected" highlight-clicked :width="100" style="width: 70%">
            <template v-slot:actions="{ tag }">
                <div class="d-flex justify-space-between mt-1">
                    <v-btn v-if="canDelete" icon="mdi-delete" rounded="sm" variant="text" size="sm" color="error" @click.stop="onDelete(tag)"/>
                    <v-tooltip :text="tag.description" location="right" open-delay="200">
                        <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" class="cursor-help" icon="mdi-information-outline"/>
                        </template>
                    </v-tooltip>
                </div>
            </template>
        </TagTiles>
        <TagWidget :data="data.clicked" :can-edit="canEdit" style="width: 30%"/>

        <v-dialog v-model="deleteDialog" @update:model-value="onCloseDelete" width="auto">
            <v-card title="Delete tag">
                <v-card-text>
                    Are you sure that you want to delete the tag <b>{{ data.toDelete ? data.toDelete.name : "" }}</b>?
                </v-card-text>
                <v-card-actions>
                    <v-btn color="warning" @click="onCancelDelete">cancel</v-btn>
                    <v-btn color="error" @click="deleteTag">delete</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup>
    import TagTiles from '@/components/tags/TagTiles.vue';
    import TagWidget from '@/components/tags/TagWidget.vue';
    import { reactive, onMounted } from 'vue';
    import { useApp } from '@/store/app';
    import DM from '@/use/data-manager';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';

    const app = useApp();
    const toast = useToast()
    const loader = useLoader();

    const props = defineProps({
        source: {
            type: String,
            required: true
        },
        canEdit: {
            type: Boolean,
            default: false
        },
        canDelete: {
            type: Boolean,
            default: false
        },
    });

    const deleteDialog = ref(false);
    const data = reactive({ clicked: null, selected: {}, toDelete: null })

    function onClick(tag) {
        if (data.clicked && data.clicked.id === tag.id) {
            data.clicked = null;
        } else {
            data.clicked = tag;
        }
    }
    function onDelete(tag) {
        if (tag && tag.id) {
            data.toDelete = tag;
            deleteDialog.value = true;
        }
    }
    function onCancelDelete() {
        deleteDialog.value = false;
        data.toDelete = null;
    }
    function onCloseDelete() {
        if (!deleteDialog.value) {
            data.toDelete = null;
        }
    }
    function deleteTag() {
        if (props.canDelete && data.toDelete && data.toDelete.id) {
            const name = data.toDelete.name;
            loader.post("delete/tags", { ids: [data.toDelete.id] })
                .then(() => {
                    data.clicked = null;
                    toast.success("deleted tag " + name);
                    app.needsReload("tags")
                    app.needsReload("datatags")
                })
            onCancelDelete();
        }
    }

    function readSelected() {
        const f = DM.getFilter(props.source, "id");
        if (f) {
            const obj = {};
            f.forEach(d => obj[d] = true)
            data.selected = obj;
        } else {
            data.selected = null;
        }
    }

    onMounted(readSelected)

    watch(() => app.selectionTime, readSelected)
</script>