<template>
    <v-card color="surface-light" class="pa-2" :style="{ 'position': sticky ? 'sticky' : 'relative', 'top': 50+'px', 'right': 10+'px', height: '90vh', maxHeight: '95vh', minHeight: '60vh', width: width+'px', textAlign: 'center' }">
        <div class="mb-2">
            <v-btn-toggle v-model="viewMode" density="compact">

                <v-tooltip text="delete selected tags" location="top">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected == 0" density="compact" class="mr-1" icon="mdi-delete"
                        variant="text"
                        value="delete"></v-btn>
                    </template>
                </v-tooltip>
                <v-tooltip text="add children to selected tags" location="top">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected == 0" density="compact" class="mr-1" icon="mdi-plus"
                        variant="text"
                        value="add"></v-btn>
                    </template>
                </v-tooltip>

                <v-tooltip text="group selected tags" location="top">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected < 2" density="compact" class="mr-1" icon="mdi-group"
                        variant="text"
                        value="group"/>
                    </template>
                </v-tooltip>
                <v-tooltip text="move tags to other subtree" location="top">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected < 2" density="compact" class="mr-1" icon="mdi-graph"
                        variant="text"
                        value="move"></v-btn>
                    </template>
                </v-tooltip>
                <v-tooltip text="split into multiple tags" location="top">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected != 1" density="compact" class="mr-1" icon="mdi-call-split"
                        variant="text"
                        :color="numSelected != 1 ? 'default' : 'primary'" value="split"></v-btn>
                    </template>
                </v-tooltip>
                <v-tooltip text="merge multiple tags" location="top">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected < 2" density="compact" icon="mdi-call-merge"
                        variant="text"
                        value="merge"></v-btn>
                    </template>
                </v-tooltip>
            </v-btn-toggle>
        </div>

        <v-divider color="primary" opacity="1" class="mb-2"></v-divider>

        <div class="text-caption">
            <div v-if="viewMode === ''">select tags to perform actions</div>
            <AddView v-else-if="viewMode === 'add'"/>
            <DeleteView v-else-if="viewMode === 'delete'"/>
            <GroupView v-else-if="viewMode === 'group'"/>
            <MoveView v-else-if="viewMode === 'move'"/>
            <SplitView v-else-if="viewMode === 'split'"/>
            <MergeView v-else-if="viewMode === 'merge'"/>
        </div>
    </v-card>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { addTagAssignments, deleteTagAssignments } from '@/use/utility';
    import { storeToRefs } from 'pinia';
    import { ref, watch, onMounted } from 'vue';
    import AddView from './transition/AddView.vue';
    import DeleteView from './transition/DeleteView.vue';
    import GroupView from './transition/GroupView.vue';
    import MoveView from './transition/MoveView.vue';
    import SplitView from './transition/SplitView.vue';
    import MergeView from './transition/MergeView.vue';
    import { useToast } from 'vue-toastification';

    const props = defineProps({
        sticky: {
            type: Boolean,
            default: false
        },
        width: {
            type: [Number, String],
            default: 300
        },
    })
    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    const { allowEdit, oldCode, newCode } = storeToRefs(app)
    const emit = defineEmits([
        "select-all", "deselect-all",
        "add", "delete", "group", "children", "split", "merge"
    ])

    const numSelected = ref(0)
    const viewMode = ref("")
    const prevMode = ref("")

    const selectedOldTag = ref(null)
    const selectedNewTag = ref(null)

    async function deleteTagAssignment(oldTag, newTag) {
        if (!allowEdit.value) return;
        const old = DM.find("tag_assignments", d => d.old_tag == oldTag && d.new_tag == newTag);
        if (!old) {
            toast.error("tag assignment does not exist")
            return;
        }

        try {
            await deleteTagAssignments(old.id)
            toast.success("deleted tag assignment")
            selectedOldTag.value = null;
            selectedNewTag.value = null;
            DM.removeFilter("tags_old", "id")
            times.needsReload("tag_assignments");
        } catch {
            toast.error("error deleting tag assignment")
        }
    }
    async function assignTag(oldTag, newTag) {
        if (!allowEdit.value) return;
        if (!oldTag || !newTag) {
            toast.error("one of the tags is missing")
            return;
        }

        try {
            await addTagAssignments({
                old_tag: oldTag,
                new_tag: newTag,
                old_code: oldCode.value,
                new_code: newCode.value,
                description: "",
                created: Date.now()
            });
            toast.success("updated tag assignment");
            DM.removeFilter("tags_old", "id")
            times.needsReload("tag_assignments");
        } catch {
            toast.success(`error updating tag assignment`);
        }
    }

    function readSelected() {
        numSelected.value = DM.getSelectedIds("tags").size
        checkViewMode()
    }
    function checkViewMode() {
        if (numSelected.value === 0) {
            prevMode.value = viewMode.value;
            viewMode.value = ""
        } else if (viewMode.value === "") {
            viewMode.value = prevMode.value !== "" ? prevMode.value : "delete"
        }
    }

    onMounted(readSelected)

    watch(() => times.f_tags, readSelected)

</script>