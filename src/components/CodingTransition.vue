<template>
    <div ref="wrapper" v-if="oldCode && newCode">
        <h3>Transition from {{ app.getCodeName(oldCode) }} to {{ app.getCodeName(newCode) }}</h3>
        <div class="d-flex justify-center">
            <v-btn color="secondary" class="mr-1" @click="openGroupingDialog(false)">create tag group</v-btn>
            <v-btn :color="data.selectedTags.size > 0 ? 'secondary' : 'default'"
                @click="openGroupingDialog"
                :disabled="data.selectedTags.size === 0">group selected tags</v-btn>
        </div>

        <v-dialog v-model="groupingDialog" width="auto" min-width="500">
            <v-card>
                <v-card-title>Group Tags</v-card-title>
                <v-card-text>
                    <v-checkbox v-model="useExistingGroup"
                        density="compact"
                        :disabled="data.tagGroups.length === 0"
                        hide-details
                        hide-spin-buttons
                        label="add to existing tag group"/>

                    <v-select v-if="useExistingGroup"
                        v-model="chosenGroup"
                        :items="data.tagGroups"
                        item-title="name"
                        item-value="id"
                        density="compact"
                        label="Existing Tag Groups"
                        hide-details
                        hide-no-data
                        hide-spin-buttons/>

                    <div v-else>
                        <v-text-field v-model="newGroupName"
                            density="compact"
                            class="mb-2"
                            label="New Tag Group Name"
                            required
                            hide-details
                            hide-spin-buttons/>
                        <v-textarea v-model="newGroupDesc"
                            density="compact"
                            label="New Tag Group Description"
                            required
                            hide-details
                            hide-spin-buttons/>
                    </div>
                </v-card-text>

                <v-card-actions>
                    <v-btn class="ms-auto" color="warning" @click="cancelGrouping">cancel</v-btn>
                    <v-btn class="ms-2" color="primary" @click="submitGrouping">
                        {{ useExistingGroup ? 'okay' : 'create' }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <v-card v-if="groupPrompt" width="200"
            elevation="8"
            density="compact"
            :style="{ 'left': mouseXGroup+'px', 'top': mouseYGroup+'px' }"
            position="absolute"
            >
            <v-card-text>
                <div class="mb-2">
                    Delete tag group?
                    <v-btn prepend-icon="mdi-delete"
                    color="error"
                    block
                    class="mt-1"
                    @click="actionDeleteTagGroup"
                    density="comfortable">delete</v-btn>
                </div>
                <div v-if="data.selectedTags.size > 0">
                    Add currently selected tags to group?
                    <v-btn prepend-icon="mdi-plus"
                    color="primary"
                    block
                    class="mt-1"
                    @click="actionAddTagsToGroup"
                    density="comfortable">add</v-btn>
                </div>
            </v-card-text>
            <v-card-actions>
                <v-btn color="warning" class="ms-auto" @click="cancelGroupPrompt">cancel</v-btn>
            </v-card-actions>
        </v-card>

        <v-card v-if="connectionPrompt" width="200"
            position="absolute"
            elevation="8"
            density="compact"
            :style="{ 'left': mouseXConn+'px', 'top': mouseYConn+'px' }"
            >
            <v-card-text>
                <p>
                    Delete transition from tag
                    <b>{{ data.clickedTransObj.tag }}</b>
                    to group
                    <b>{{ data.clickedTransObj.group }}</b>?
                </p>
                <v-btn prepend-icon="mdi-delete"
                    color="error"
                    @click="actionDeleteCodeTrans"
                    density="comfortable"
                    block
                    class="mt-1"
                    >
                    delete
                </v-btn>
            </v-card-text>

            <v-card-actions>
                <v-btn color="warning" class="ms-auto" @click="cancelCodeTransPrompt">cancel</v-btn>
            </v-card-actions>
        </v-card>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { onMounted, reactive } from 'vue';
    import HBCBiModal from './vis/HBCBiModal.vue';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';
    import { storeToRefs } from 'pinia';
    import { useElementSize } from '@vueuse/core';

    const app = useApp();
    const loader = useLoader();
    const toast = useToast();

    const wrapper = ref(null);
    const wrapperSize = useElementSize(wrapper);

    const props = defineProps({
        oldCode: {
            type: Number,
            required: true
        },
        newCode: {
            type: Number,
            required: true
        },
    })

    const groupPrompt = ref(false);
    const connectionPrompt = ref(false);
    const clickedGroup = ref("");
    const clickedTrans = ref("");

    const mouseXGroup = ref(0);
    const mouseYGroup = ref(0);
    const mouseXConn = ref(0);
    const mouseYConn = ref(0);

    const groupingDialog = ref(false);
    const useExistingGroup = ref(false);
    const chosenGroup = ref("");
    const newGroupName = ref("");
    const newGroupDesc = ref("");

    const { dataLoading } = storeToRefs(app);

    let actionQueue = [];
    const data = reactive({
        tags: [],
        datatags: new Map(),

        tagsNew: [],
        datatagsNew: new Map(),

        tagTree: {},
        tagAssign: [],

        left: [],
        right: [],
        connections: [],

        selectedTags: new Set(),
    });

    function readData() {
        if (!props.oldCode || !props.newCode ||
            !DM.hasData("tags") || !DM.hasData("datatags") ||
            !DM.hasData("tagsNew") || !DM.hasData("datatagsNew") ||
            !DM.hasData("tag_assignments")
        ) {
            return;
        }

        data.tags = DM.getData("tags", false);
        data.datatags = d3.group(DM.getData("datatags", false), d => d.tag_id);

        data.tagsNew = DM.getData("tagsNew", false);
        data.datatagsNew = d3.group(DM.getData("datatags", false), d => d.tag_id);

        data.tagAssign = DM.getData("tag_assignments");
        data.tagTree = buildTagTree([{ id: -1, name: "root", parent: null }].concat(data.tagsNew))

        const f = DM.getFilter("tags", "id");
        if (f) {
            data.selectedTags = new Set(f)
        }

        if (actionQueue.length > 0) {
            let action = actionQueue.pop();
            do {
                switch(action.action) {
                    case "group tags":
                        addTagsToGroup(action.values);
                        break;
                }
                action = actionQueue.pop();
            } while (action)
        }
    }

    function buildTagTree(data) {
        return d3.stratify()
            .id(d => d.id)
            .parentId(d => d.parent)
            (data)
    }


    function onClickLeft(id) {
        if (data.selectedTags.has(id)) {
            data.selectedTags.delete(id)
        } else {
            data.selectedTags.add(id)
        }
        DM.setFilter("tags", "id", Array.from(data.selectedTags.values()))
        app.selectionTime = Date.now()
    }
    function onClickRight(id, event) {
        clickedGroup.value = id;
        groupPrompt.value = true;
        mouseXGroup.value = event.pageX - 210;
        mouseYGroup.value = event.pageY + 10;
    }
    function onClickConnection(from, to, event) {
        const g = data.tagGroups.find(d => d.id === to);
        const gItems = data.codeTrans.get(to)
        if (g && gItems) {
            const tag = data.tags.find(d => d.id === from);
            const t = gItems.find(d => d.tag_id === from);
            if (t && tag) {
                data.clickedTransObj = {
                    tag: tag.name,
                    group: g.name,
                };
                clickedTrans.value = t.id;
                connectionPrompt.value = true;
                mouseXConn.value = event.pageX + 10;
                mouseYConn.value = event.pageY + 10;
            }
        }
    }

    function openGroupingDialog(useExisting) {
        groupingDialog.value = true;
        useExistingGroup.value = useExisting !== undefined ? useExisting : data.tagGroups.length > 0;
    }
    function cancelGrouping() {
        newGroupName.value = "";
        newGroupDesc.value = "";
        chosenGroup.value = "";
        groupingDialog.value = false;
    }
    function submitGrouping() {
        let valid = false;
        if (!useExistingGroup.value && newGroupName.value && newGroupDesc) {
            valid = true;
            loader.post("add/tag_groups", {
                dataset: app.ds,
                old_code: props.oldCode,
                new_code: props.newCode,
                rows: [{ name: newGroupName.value, description: newGroupDesc.value, created: Date.now() }]
            }).then(() => {

                if (data.selectedTags.size > 0) {
                    actionQueue.push({
                        action: "group tags",
                        values: {
                            tags: Array.from(data.selectedTags.values()),
                            name: newGroupName.value
                        }
                    });
                }
                toast.success("added tag group " + newGroupName.value)
                app.needsReload("tag_groups");
                newGroupName.value = "";
                newGroupDesc.value = "";
            })

        } else if (useExistingGroup.value && chosenGroup.value) {
            valid = true;
            addTagsToGroup(Array.from(data.selectedTags.values()), chosenGroup.value)
        }

        if (valid) {
            groupingDialog.value = false;
        } else {
            toast.error("please select or create a tag group")
        }
    }

    async function addTagsToGroup(tags, group) {
        if (tags.length === 0 || !group) return;

        await loader.post("add/code_transitions", { group: group, rows: tags.map(d => ({ tag_id: d })) });
        toast.success(`added ${tags.length} tags to tag group`);
        app.needsReload("code_transitions");
    }

    function cancelGroupPrompt() {
        groupPrompt.value = false;
        clickedGroup.value = "";
    }
    function cancelCodeTransPrompt() {
        connectionPrompt.value = false;
        clickedTrans.value = "";
        data.clickedTransObj = null;
    }

    function actionDeleteTagGroup() {
        if (clickedGroup.value) {
            groupPrompt.value = false;
            loader.post("delete/tag_groups", { ids: [clickedGroup.value] })
                .then(() => {
                    toast.success("deleted 1 tag group")
                    clickedGroup.value = "";
                    app.needsReload("tag_groups");
                    app.needsReload("code_transitions");
                })
        }
    }
    function actionAddTagsToGroup() {
        if (clickedGroup.value && data.selectedTags.size > 0) {
            addTagsToGroup(Array.from(data.selectedTags.values()), clickedGroup.value)
            groupPrompt.value = false;
            clickedGroup.value = "";
        }
    }
    function actionDeleteCodeTrans() {
        if (clickedTrans.value) {
            connectionPrompt.value = false;
            loader.post("delete/code_transitions", { ids: [clickedTrans.value] })
                .then(() => {
                    toast.success("deleted 1 code transition")
                    clickedTrans.value = "";
                    data.clickedTransObj = null;
                    app.needsReload("code_transitions");
                })
        }
    }

    onMounted(readData)

    watch(() => ([dataLoading.value._all, dataLoading.value.coding]), function() {
        if (dataLoading.value._all === false || dataLoading.value.coding === false) {
            readData();
        }
    }, { deep: true });
    watch(() => ([
        dataLoading.value.codes,
        dataLoading.value.tags,
        dataLoading.value.datatags,
        dataLoading.value.tag_groups,
        dataLoading.value.code_transitions,
    ]), function(val) {
        if (val && (!val.some(d => d) || !val[4] || !val[5])) {
            readData();
        }
    }, { deep: true });

</script>