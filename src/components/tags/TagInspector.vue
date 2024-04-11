<template>
    <div class="d-flex flex-start align-start">
        <TagTiles :source="source" show-letter :include-intermediate="includeIntermediate" :selected="data.selected" allow-add :width="100">
            <template v-slot:actions="{ tag }">
                <div class="d-flex justify-space-between mt-1">
                    <v-icon v-bind="props" icon="mdi-delete" color="error" @click.stop="onDelete(tag)"/>
                    <v-icon v-bind="props" @click.stop="e => onClick(tag, e)" icon="mdi-pencil"/>
                    <v-tooltip v-if="tag.parent !== null && tag.parent !== -1" :text="tag.pathNames" location="top" open-delay="200">
                        <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" class="cursor-help" icon="mdi-tree-outline"/>
                        </template>
                    </v-tooltip>
                </div>
            </template>
        </TagTiles>

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

        <div v-if="data.clicked" :style="{ position: 'absolute', left: mouseX+'px', top: mouseY+'px', 'z-index': 3008  }">
            <v-sheet min-width="350" class="pa-2" rounded border>
                <TagWidget :data="data.clicked" :parents="source" :can-edit="canEdit" @update="resetClicked"/>
            </v-sheet>
        </div>
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
        includeIntermediate: {
            type: Boolean,
            default: false
        },
    });

    const mouseX = ref(0)
    const mouseY = ref(0)
    const deleteDialog = ref(false);
    const data = reactive({ clicked: null, selected: {}, toDelete: null })

    function onClick(tag, event) {
        if (data.clicked && data.clicked.id === tag.id) {
            data.clicked = null;
            mouseX.value = 0;
            mouseY.value = 0;
        } else {
            data.clicked = tag;
            mouseX.value = event.pageX - 10;
            mouseY.value = event.pageY - 20;
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
            const id = data.toDelete.id;
            loader.post("delete/tags", { ids: [id] })
                .then(() => {
                    data.clicked = null;
                    toast.success("deleted tag " + name);
                    DM.toggleFilter("tags", "id", [id])
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

    function update() {
        if (data.clicked) {
            const t = DM.getDataBy("tags", d => d.id === data.clicked.id);
            if (t.length > 0) {
                data.clicked = t[0];
            }
        }
    }
    function resetClicked() {
        data.clicked = null;
    }

    onMounted(readSelected)

    watch(() => app.selectionTime, readSelected)
    watch(() => app.dataLoading.tags, function(val) {
        if (val === false) {
            update()
        }
    })
</script>