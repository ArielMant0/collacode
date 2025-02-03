<template>
<div ref="el"  :style="{
    position: sticky ? 'absolute' : 'relative',
    right: '10px',
    width: (model ? width : railWidth)+'px'
}">
    <v-card color="surface-light" class="pa-2" style="text-align: center">
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
            <div class="mb-2 d-flex align-center justify-center">
                <v-tooltip text="toggle tag assignment mode" location="top" open-delay="150">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" rounded="sm"
                            density="compact"
                            icon="mdi-connection"
                            variant="text"
                            @click="tagAssignMode = !tagAssignMode"
                            :color="tagAssignMode ? 'primary' : '#555'"/>
                    </template>
                </v-tooltip>

                <v-divider class="ml-2 mr-2" vertical></v-divider>

                <v-btn-toggle v-model="viewMode" density="compact" @update:model-value="forceSwitch = false" color="primary" :disabled="tagAssignMode">

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

            <div class="text-caption" :style="{ textAlign: 'left', maxHeight: maxContentHeight+'px', overflowY: 'auto', overflowX: 'hidden' }">
                <div v-if="!tagAssignMode && numSelected === 0" style="text-align: center;">select tags to perform actions</div>
                <TagAssignView v-else-if="tagAssignMode && !viewMode"/>
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

            <v-tooltip text="toggle tag assignment mode" location="left" open-delay="150">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" rounded="sm"
                        density="compact"
                        icon="mdi-connection"
                        variant="text"
                        @click="tagAssignMode = !tagAssignMode"
                        :color="tagAssignMode ? 'primary' : '#555'"/>
                </template>
            </v-tooltip>
            <v-divider class="mt-2 mb-2"></v-divider>

            <div class="mb-2" :style="{ maxWidth: railWidth+'px' }">
                <v-btn-toggle v-model="viewMode" color="primary" density="compact" @update:model-value="onClickSmall" class="flex-column flex-start" :style="{ height: 'fit-content', maxWidth: railWidth+'px'}">
                    <v-tooltip text="add children to selected tags" location="left" open-delay="150">
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props" rounded="sm" :disabled="numSelected == 0" density="compact" class="mb-1" icon="mdi-plus"
                            variant="text"
                            value="add"></v-btn>
                        </template>
                    </v-tooltip>
                    <v-tooltip text="delete selected tags" location="left" open-delay="150">
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props" rounded="sm" :disabled="numSelected == 0" density="compact" class="mb-1" icon="mdi-delete"
                            variant="text"
                            value="delete"></v-btn>
                        </template>
                    </v-tooltip>

                    <v-tooltip text="split selected tag" location="left" open-delay="150">
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props" rounded="sm" :disabled="numSelected != 1" density="compact" class="mb-1" icon="mdi-call-split"
                            variant="text"
                            :color="numSelected != 1 ? 'default' : 'primary'" value="split"></v-btn>
                        </template>
                    </v-tooltip>
                    <v-tooltip text="merge selected tags" location="left" open-delay="150">
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props" rounded="sm" :disabled="numSelected < 2" density="compact" icon="mdi-call-merge"
                            variant="text"
                            value="merge"></v-btn>
                        </template>
                    </v-tooltip>

                    <v-tooltip text="group selected tags" location="left" open-delay="150">
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props" rounded="sm" :disabled="numSelected < 2" density="compact" class="mr-1" icon="mdi-group"
                            variant="text"
                            value="group"/>
                        </template>
                    </v-tooltip>
                    <v-tooltip text="move tags to other subtree" location="left" open-delay="150">
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
    import { useParentElement, useWindowScroll, useWindowSize } from '@vueuse/core';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import TagAssignView from './transition/TagAssignView.vue';

    const times = useTimes()
    const settings = useSettings()
    const { tagAssignMode, transOld, transNew } = storeToRefs(settings)

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
    const vpSize = useWindowSize()
    const maxContentHeight = computed(() => props.height ? Math.max(200, props.height-200) : Math.max(400, vpSize.height.value - 250))

    const scrollState = useWindowScroll({ behavior: 'smooth'})

    const numSelected = ref(0)
    const viewMode = ref("")
    const prevMode = ref("")
    const forceSwitch = ref(false)

    function readSelected() {
        numSelected.value = DM.getSelectedIds("tags").size
        checkViewMode()
        checkTagAssignment()
    }

    function checkViewMode() {
        if (tagAssignMode.value) {
            prevMode.value = viewMode.value
            viewMode.value = ""
            forceSwitch.value = true;
        } else if (numSelected.value === 0) {
            prevMode.value = viewMode.value;
            viewMode.value = ""
        } else if (forceSwitch.value) {
            const tmp = viewMode.value
            viewMode.value = prevMode.value
            prevMode.value = tmp;
            forceSwitch.value = false;
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
        }
    }
    function onClickSmall() {
        forceSwitch.value = false;
        model.value = true;
    }

    async function checkTagAssignment() {
        if (tagAssignMode.value) {
            transNew.value = numSelected.value > 0 ?
                DM.getSelectedIdsArray("tags").at(-1) :
                -1
            transOld.value = DM.getSelectedIds("tags_old").size > 0 ?
                DM.getSelectedIdsArray("tags_old").at(-1) :
                -1
        } else if (!tagAssignMode.value) {
            DM.removeFilter("tags_old")
            transOld.value = -1;
            transNew.value = -1;
        }
    }

    function onScroll() {
        if (props.sticky) {
            if (!el.value) return
            const { top, bottom } = el.value.parentNode.parentNode.getBoundingClientRect()
            const myRect = el.value.getBoundingClientRect()
            const h = myRect.height;

            if (top - 50 > 0) {
                el.value.style.top = "10px"
            } else if (myRect.top + h + 25 < bottom) {
                el.value.style.top = (window.scrollY-50) + "px"
            } else if (h + 75 < bottom) {
                el.value.style.top = (window.scrollY-50) + "px"
            }
        }
    }

    onMounted(function() {
        document.addEventListener("scroll", onScroll)
        onScroll()
        readSelected()
    })

    watch(() => times.f_tags, readSelected)
    watch(() => times.f_tags_old, checkTagAssignment)
    watch(tagAssignMode, function() {
        checkViewMode()
        checkTagAssignment()
    })

    watch(scrollState.y, onScroll)

</script>