<template>
    <v-sheet class="d-flex justify-center mb-2" style="position: fixed;">

        <div v-if="allowEdit">
        <v-tooltip text="add children to selected tags" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" rounded="sm" :disabled="numSelected == 0" density="comfortable" class="mr-1" icon="mdi-plus" color="primary" @click="emit('add')"></v-btn>
            </template>
        </v-tooltip>
        <v-tooltip text="delete selected tags" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" rounded="sm" :disabled="numSelected == 0" density="comfortable" class="mr-4" icon="mdi-delete" color="error" @click="emit('delete')"></v-btn>
            </template>
        </v-tooltip>

        <v-tooltip text="group selected tags" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" rounded="sm" :disabled="numSelected < 2" density="comfortable" class="mr-1" icon="mdi-group" color="primary" @click="emit('group')"></v-btn>
            </template>
        </v-tooltip>
        <v-tooltip text="add as children to first selected tag" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" rounded="sm" :disabled="numSelected < 2" density="comfortable" class="mr-1" icon="mdi-graph" color="primary" @click="emit('children')"></v-btn>
            </template>
        </v-tooltip>
        <v-tooltip text="split into multiple tags" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" rounded="sm" :disabled="numSelected == 0" density="comfortable" class="mr-1" icon="mdi-call-split" color="primary" @click="emit('split')"></v-btn>
            </template>
        </v-tooltip>
        <v-tooltip text="merge multiple tags" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" rounded="sm" :disabled="numSelected < 2" density="comfortable" class="mr-4" icon="mdi-call-merge" color="primary" @click="emit('merge')"></v-btn>
            </template>
        </v-tooltip>

        <v-tooltip text="select all tags" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1" icon="mdi-select-all" color="secondary" @click="emit('select-all')"></v-btn>
            </template>
        </v-tooltip>
        <v-tooltip text="deselect tags" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-4" icon="mdi-select" color="secondary" @click="emit('deselect-all')"></v-btn>
            </template>
        </v-tooltip>
        </div>

        <v-btn-toggle v-model="treeLayout" color="primary" density="compact" rounded="sm" elevation="2" divided mandatory variant="text" class="mr-4" @update:model-value="emit('tree-layout', treeLayout)">
            <v-tooltip text="cluster node-link layout with leaves on the same level" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="cluster" icon="mdi-family-tree"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="compact node-link layout" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="tidy" icon="mdi-file-tree"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="radial node-link layout" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="radial" icon="mdi-radar"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="compact treemap layout" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="treemap" icon="mdi-chart-tree"></v-btn>
                </template>
            </v-tooltip>
        </v-btn-toggle>

        <v-tooltip text="show tag assignments" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" rounded="sm" density="comfortable" class="mr-1"
                    :disabled="treeLayout != 'tidy' && treeLayout != 'cluster'"
                    :icon="showAssigned ? 'mdi-eye' : 'mdi-eye-off'"
                    color="secondary"
                    @click="toggleAssigned"></v-btn>
            </template>
        </v-tooltip>

        <v-btn-toggle v-if="allowEdit" v-model="assigMode" :disabled="!showAssigned" density="compact" rounded="sm" elevation="2" variant="text" class="mr-1" divided @update:model-value="emit('assign-mode', assigMode)">
            <v-tooltip text="add tag assignments" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="add" icon="mdi-link" color="primary"></v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="delete tag assignments" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="delete" icon="mdi-link-off" color="error"></v-btn>
                </template>
            </v-tooltip>
        </v-btn-toggle>
    </v-sheet>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import { ref, watch } from 'vue';

    const props = defineProps({
        sticky: {
            type: Boolean,
            default: false
        }
    })
    const app = useApp()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(app)

    const emit = defineEmits([
        "select-all", "deselect-all",
        "add", "delete", "group", "children", "split", "merge",
        "assign-mode", "show-links", "tree-layout"
    ])

    const treeLayout = ref(settings.treeLayout)
    const showAssigned = ref(false);
    const assigMode = ref(undefined);

    const numSelected = ref(0)

    function toggleAssigned() {
        showAssigned.value = !showAssigned.value;
        emit("show-links", showAssigned.value);
    }

    watch(() => times.f_tags, () => numSelected.value = DM.getSelectedIds("tags").size)

</script>