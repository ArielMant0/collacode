<template>
<div ref="el"  :style="{
    position: sticky ? 'absolute' : 'relative',
    right: '10px',
    minHeight: model ? (height ? height : '350px') : (height ? height : 'auto'),
    width: (model ? width : railWidth)+'px',
}">
    <v-card color="surface-light" class="pa-2" style="text-align: center;">
        <v-btn
            rounded="sm"
            density="comfortable"
            size="small"
            class="mb-2"
            @click="model = !model"
            block
            color="secondary"
            :icon="model ? 'mdi-arrow-right' : 'mdi-arrow-left'"/>

        <div v-if="model">
            <div class="mb-2">
                <v-btn-toggle v-model="viewMode" density="compact" @update:model-value="forceSwitch = false" color="primary">

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

            <div class="text-caption" :style="{ textAlign: 'left', maxHeight: maxContentHeight+'px', overflow: 'auto' }">
                <div v-if="numSelected === 0" style="text-align: center;">select tags to perform actions</div>
                <ShowView v-else-if="!viewMode"/>
                <AddView v-else-if="viewMode === 'add'"/>
                <DeleteView v-else-if="viewMode === 'delete'"/>
                <GroupView v-else-if="viewMode === 'group'"/>
                <MoveView v-else-if="viewMode === 'move'"/>
                <SplitView v-else-if="viewMode === 'split'"/>
                <MergeView v-else-if="viewMode === 'merge'"/>
            </div>
        </div>
        <div v-else>
            <span class="text-caption">{{ numSelected }}</span>
            <v-divider class="mt-2 mb-2"></v-divider>
            <div class="mb-2" :style="{ maxWidth: railWidth+'px' }">
                <v-btn-toggle v-model="viewMode" color="primary" density="compact" @update:model-value="onClickSmall" class="flex-column flex-start" :style="{ height: 'fit-content', maxWidth: railWidth+'px'}">
                    <v-tooltip text="add children to selected tags" location="top" open-delay="150">
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props" rounded="sm" :disabled="numSelected == 0" density="compact" class="mb-1" icon="mdi-plus"
                            variant="text"
                            value="add"></v-btn>
                        </template>
                    </v-tooltip>
                    <v-tooltip text="delete selected tags" location="top" open-delay="150">
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props" rounded="sm" :disabled="numSelected == 0" density="compact" class="mb-1" icon="mdi-delete"
                            variant="text"
                            value="delete"></v-btn>
                        </template>
                    </v-tooltip>

                    <v-tooltip text="split selected tag" location="top" open-delay="150">
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props" rounded="sm" :disabled="numSelected != 1" density="compact" class="mb-1" icon="mdi-call-split"
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
        </div>

    </v-card>
</div>
</template>

<script setup>
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { ref, watch, onMounted, computed } from 'vue';
    import AddView from './transition/AddView.vue';
    import DeleteView from './transition/DeleteView.vue';
    import GroupView from './transition/GroupView.vue';
    import MoveView from './transition/MoveView.vue';
    import SplitView from './transition/SplitView.vue';
    import MergeView from './transition/MergeView.vue';
    import ShowView from './transition/ShowView.vue';
    import { useParentElement, useWindowSize } from '@vueuse/core';

    const times = useTimes()

    const model = defineModel()
    const props = defineProps({
        sticky: {
            type: Boolean,
            default: false
        },
        width: {
            type: [Number, String],
            default: 300
        },
        railWidth: {
            type: [Number, String],
            default: 60
        },
        height: {
            type: [Number, String],
        }
    })

    const el = ref(null)
    const parent = useParentElement(el)
    const vpSize = useWindowSize()
    const maxContentHeight = computed(() => vpSize.height.value * 0.9 - 75)

    const numSelected = ref(0)
    const viewMode = ref("")
    const prevMode = ref("")
    const forceSwitch = ref(false)

    function readSelected() {
        numSelected.value = DM.getSelectedIds("tags").size
        checkViewMode()
    }
    function checkViewMode() {
        if (numSelected.value === 0) {
            prevMode.value = viewMode.value;
            viewMode.value = ""
        } else if (numSelected.value === 1) {
            if (viewMode.value === "merge" || viewMode.value === "split" || viewMode.value === "group" || viewMode.value === "move") {
                prevMode.value = viewMode.value
                viewMode.value = ""
                forceSwitch.value = true;
            }
        } else if (numSelected.value > 1 && viewMode.value === "split") {
            prevMode.value = viewMode.value
            viewMode.value = ""
            forceSwitch.value = true;
        } else if (forceSwitch.value) {
            const tmp = viewMode.value
            viewMode.value = prevMode.value
            prevMode.value = tmp;
            forceSwitch.value = false;
        }
    }
    function onClickSmall() {
        forceSwitch.value = false;
        model.value = true;
    }

    onMounted(function() {
        document.addEventListener("scroll", function() {
            if (props.sticky) {
                const { bottom } = parent.value.getBoundingClientRect()
                const myRect = el.value.getBoundingClientRect()
                const h = myRect.bottom - myRect.top
                if ((bottom - 50 - h) >= 0) {
                    el.value.style.top = (window.scrollY + 10) + "px"
                }
            }
        })
        const { top } = parent.value.getBoundingClientRect()
        el.value.style.top = top + "px"
        readSelected()
    })

    watch(() => times.f_tags, readSelected)

</script>