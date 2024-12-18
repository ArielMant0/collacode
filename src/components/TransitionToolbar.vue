<template>
    <v-card color="surface-light" class="pa-2" :style="{ 'position': sticky ? 'sticky' : 'relative', 'top': (sticky ? 50 : 0)+'px', 'right': 10+'px', maxHeight: '95vh', minHeight: '350px', width: width+'px', textAlign: 'center' }">
        <div class="mb-2">
            <v-btn-toggle v-model="viewMode" density="compact" @update:model-value="forceSwitch = false">

                <v-tooltip text="add children to selected tags" location="top" open-delay="150">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected == 0" density="compact" class="mr-1" icon="mdi-plus"
                        variant="text"
                        value="add"></v-btn>
                    </template>
                </v-tooltip>
                <v-tooltip text="delete selected tags" location="top" open-delay="150">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected == 0" density="compact" class="mr-1" icon="mdi-delete"
                        variant="text"
                        value="delete"></v-btn>
                    </template>
                </v-tooltip>

                <v-tooltip text="split selected tag" location="top" open-delay="150">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected != 1" density="compact" class="mr-1" icon="mdi-call-split"
                        variant="text"
                        :color="numSelected != 1 ? 'default' : 'primary'" value="split"></v-btn>
                    </template>
                </v-tooltip>
                <v-tooltip text="merge selected tags" location="top" open-delay="150">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected < 2" density="compact" icon="mdi-call-merge"
                        variant="text"
                        value="merge"></v-btn>
                    </template>
                </v-tooltip>

                <v-tooltip text="group selected tags" location="top" open-delay="150">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected < 2" density="compact" class="mr-1" icon="mdi-group"
                        variant="text"
                        value="group"/>
                    </template>
                </v-tooltip>
                <v-tooltip text="move tags to other subtree" location="top" open-delay="150">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm" :disabled="numSelected < 2" density="compact" class="mr-1" icon="mdi-graph"
                        variant="text"
                        value="move"></v-btn>
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
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { ref, watch, onMounted } from 'vue';
    import AddView from './transition/AddView.vue';
    import DeleteView from './transition/DeleteView.vue';
    import GroupView from './transition/GroupView.vue';
    import MoveView from './transition/MoveView.vue';
    import SplitView from './transition/SplitView.vue';
    import MergeView from './transition/MergeView.vue';

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
    const times = useTimes()

    const numSelected = ref(0)
    const viewMode = ref("")
    const prevMode = ref("")
    const forceSwitch = ref(false)

    function readSelected() {
        numSelected.value = DM.getSelectedIds("tags").size
        checkViewMode()
    }
    function checkViewMode() {
        if (numSelected.value > 0 && viewMode.value === "") {
            viewMode.value = prevMode.value !== "" ? prevMode.value : "add"
        } else if (numSelected.value === 0) {
            prevMode.value = viewMode.value;
            viewMode.value = ""
        } else if (numSelected.value === 1) {
            if (viewMode.value === "merge" || viewMode.value === "split" || viewMode.value === "group" || viewMode.value === "move") {
                prevMode.value = viewMode.value
                viewMode.value = "add"
                forceSwitch.value = true;
            }
        } else if (numSelected.value > 1 && viewMode.value === "split") {
            prevMode.value = viewMode.value
            viewMode.value = "add"
            forceSwitch.value = true;
        } else if (forceSwitch.value) {
            const tmp = viewMode.value
            viewMode.value = prevMode.value
            prevMode.value = tmp;
            forceSwitch.value = false;
        }
    }

    onMounted(readSelected)

    watch(() => times.f_tags, readSelected)

</script>